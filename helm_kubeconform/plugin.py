#!/usr/bin/env python

# SPDX-FileCopyrightText: © 2023 Mohamed El Morabity
# SPDX-License-Identifier: GPL-3.0-or-later

"""A Helm plugin for validating Helm charts using Kubeconform."""

from __future__ import annotations

from argparse import Action
from argparse import ArgumentParser
import logging
import os
from pathlib import Path
import platform
import re
import subprocess
from subprocess import CalledProcessError
import sys
import typing
from typing import Any
from typing import Sequence

if typing.TYPE_CHECKING:  # pragma: no cover
    from argparse import Namespace

# Environment variables injected by Helm when running a plugin
HELM_PLUGIN_DIR = os.getenv("HELM_PLUGIN_DIR", str(Path(__file__).parent))
HELM_BIN = os.getenv("HELM_BIN", "helm")
HELM_PLUGIN_NAME = os.getenv("HELM_PLUGIN_NAME", "kubeconform")
HELM_DEBUG = os.getenv("HELM_DEBUG")

KUBECONFORM_BIN = str(
    Path(HELM_PLUGIN_DIR, "kubeconform").with_suffix(
        ".exe" if platform.system() == "Windows" else ""
    )
)

# `helm template` flags to disable
_HELM_IGNORED_FLAGS = {
    # Handled by ArgumentParser
    "--help",
    # Useless since `helm template` output is written on stdout
    "--output-dir",
    "--release-name",
    # Actually not supported by Helm >= 3.10 when running a plugin
    "--insecure-skip-tls-verify",
}
# Mapping between `helm template` and Kubeconform flags with same purpose
_HELM_KUBECONFORM_COMMON_FLAGS = {
    "--debug": "-debug",
    "--kube-version": "-kubernetes-version",
}
# Kubeconform flags to disabe
_KUBECONFORM_IGNORED_FLAGS = {
    # Handled by ArgumentParser
    "-h",
    # Kubeconform input is read from stdin
    "-ignore-filename-pattern",
    # Useless
    "-v",
}
# Kubeconform flags to rename
_KUBECONFORM_RENAMED_FLAGS = {
    # Avoid conflict with `helm` -n flag
    "-n": "--goroutines",
    # Avoid conflict with `helm` --insecure-skip-tls-verify flag
    "-insecure-skip-tls-verify": "--skip-tls-verify",
}

_HELM_TEMPLATE_ARGPARSE_DEST = "helm_template"
_KUBECONFORM_ARGPARSE_DEST = "kubeconform"

logging.basicConfig(format=f"{HELM_PLUGIN_NAME}: [%(levelname)s] %(message)s")


# Validate a Helm chart using Kubeconform
def _validate(
    helm_template_args: Sequence[str], kubeconform_args: Sequence[str]
) -> int:
    helm_template_command = [HELM_BIN, "template", *helm_template_args]
    kubeconform_command = [KUBECONFORM_BIN, *kubeconform_args]

    logging.debug("Running %s", " ".join(helm_template_command))
    try:
        # Render Helm chart on stdout
        helm_template_process = subprocess.run(
            helm_template_command, stdout=subprocess.PIPE, check=True
        )
    except CalledProcessError as ex:
        return ex.returncode

    logging.debug("Running %s", " ".join(kubeconform_command))
    try:
        # - Validate rendered Helm chart using Kubeconform from stdin
        # - Redirect Kubeconform stdout to stderr
        subprocess.run(
            kubeconform_command,
            input=helm_template_process.stdout,
            stdout=sys.stderr,
            check=True,
        )
    except CalledProcessError as ex:
        return ex.returncode

    return 0


# Return the path to the Helm chart directory that a file belongs to, or `None`
# if not found
def _get_helm_chart_directory(path: Path) -> Path | None:
    directory = path if path.is_dir() else path.parent
    # A chart directory must contain a Chart.yaml file
    chart_file = directory / "Chart.yaml"
    if chart_file.is_file():
        return directory
    # / is reached
    if directory.parent == directory:
        return None

    # Check parent directory
    return _get_helm_chart_directory(directory.parent)


# Return all Helm chart directories the specified files belong to
def _get_all_helm_chart_directories(*path: Path) -> set[Path]:
    return {
        chart_dir for f in path if (chart_dir := _get_helm_chart_directory(f))
    }


# For all chart file passed to the function:
# - get the Helm chart directories they belong to
# - validate each chart directory
# - stop and return status when a chart fails to validate with the specified
#   values
def _validate_from_helm_chart_files(
    helm_template_args: Sequence[str],
    kubeconform_args: Sequence[str],
    chart_files: Sequence[Path],
) -> int:
    for chart_dir in _get_all_helm_chart_directories(*chart_files):
        result = _validate(
            [*helm_template_args, str(chart_dir)], kubeconform_args
        )
        if result > 0:
            logging.error("Helm chart %s validation failed", chart_dir)
            return result

    return 0


# For each values file passed to the script:
# - validate specified Helm chart with the values file
# - stop and return status when chart fails to validate
def _validate_helm_values_files(
    helm_template_args: Sequence[str],
    kubeconform_args: Sequence[str],
    values_files: Sequence[Path],
) -> int:
    for value_file in values_files:
        result = _validate(
            [*helm_template_args, "--values", str(value_file)],
            kubeconform_args,
        )
        if result > 0:
            logging.error("Helm values file %s validation failed", value_file)
            return result

    return 0


# Custom argparse action to process a flag and its arguments, and append them
# to one or two namespace attributes
def _command_flag(
    extra_dest: str | None = None, extra_const: str | None = None
) -> type[Action]:
    class _CommandFlagAction(Action):
        def __call__(
            self,
            _parser: ArgumentParser,
            namespace: Namespace,
            values: str | Sequence[Any] | None = None,
            option_string: str | None = None,
        ) -> None:
            for dest, const in (
                (self.dest, self.const),
                (extra_dest, extra_const),
            ):
                if not dest:
                    continue

                items = getattr(namespace, dest, None) or []

                if option_arg := const or option_string:
                    items.append(option_arg)
                if values:
                    arg_values = (
                        [str(v) for v in values]
                        if isinstance(values, list)
                        else [str(values)]
                    )
                    items.extend(arg_values)

                setattr(namespace, dest, items)

    return _CommandFlagAction


# Retrieve the help text for the `helm template` command, extract the available
# options from it, and add them to a dedicated group in an argument parser
def _add_helm_template_flags(parser: ArgumentParser) -> None:
    # Dump help text for the `helm template` command
    help_output = subprocess.check_output(
        [HELM_BIN, "template", "--help"], text=True
    )
    # Extract flag and description for each option in help text
    matches = re.findall(
        r"^\s*(?:(-\w),\s*)?(--\w[\w-]*)(?:\s(\w+))?(?:\s+(.+?))$",
        help_output,
        re.MULTILINE,
    )

    group = parser.add_argument_group("Helm template options")

    # Add each `helm template` option to argument parser
    for short_flag, flag, argument_type, description in matches:
        if flag in _HELM_IGNORED_FLAGS:
            continue

        name_or_flags = [short_flag, flag] if short_flag else [flag]

        argument_options = {
            "help": description,
            "dest": _HELM_TEMPLATE_ARGPARSE_DEST,
            "action": _command_flag(),
            "metavar": argument_type,
        }

        # `helm template` flags that must also be passed to the `kubeconform`
        # command
        if flag in _HELM_KUBECONFORM_COMMON_FLAGS:
            argument_options["action"] = _command_flag(
                _KUBECONFORM_ARGPARSE_DEST,
                _HELM_KUBECONFORM_COMMON_FLAGS[flag],
            )

        if not argument_type:
            argument_options["nargs"] = 0
        elif argument_type == "int":
            argument_options["type"] = int

        group.add_argument(*name_or_flags, **argument_options)


# Retrieve the help text for the `kubeconform` command, extract the available
# options from it, and add them to a dedicated group in an argument parser
def _add_kubeconform_flags(parser: ArgumentParser) -> None:
    # Dump help text for the `helm template` command
    help_output = subprocess.check_output([KUBECONFORM_BIN, "-h"], text=True)
    # Extract flag and description for each option in help text
    matches = re.findall(
        r"^\s*(--?\w[\w-]*)(?:[ \t]+(\w+?)$)?(?:\n?[ \t]+\b([^-].*?)$)?",
        help_output,
        re.MULTILINE,
    )

    group = parser.add_argument_group("Kubeconform options")

    flags_to_ignore = _KUBECONFORM_IGNORED_FLAGS.union(
        _HELM_KUBECONFORM_COMMON_FLAGS.values()
    )

    # Add each `kubeconform` option to argument parser
    for flag, argument_type, description in matches:
        if flag in flags_to_ignore:
            continue

        plugin_flag = flag

        # Kubeconform long options start with one dash. Use double dash for
        # consistency with Helm long options
        if len(_f := flag.lstrip("-")) > 1:
            plugin_flag = f"--{_f}"

        plugin_flag = _KUBECONFORM_RENAMED_FLAGS.get(flag, plugin_flag)

        argument_options = {
            "help": description,
            "dest": _KUBECONFORM_ARGPARSE_DEST,
            "action": _command_flag(),
            "const": flag,
            "metavar": argument_type,
        }

        if not argument_type:
            argument_options["nargs"] = 0
        elif argument_type == "int":
            argument_options["type"] = int

        group.add_argument(plugin_flag, **argument_options)


# Argument parser for the script
def _argument_parser(
    chart_files: bool = False, values_files: bool = False
) -> ArgumentParser:
    parser = ArgumentParser(
        prog=f"helm {HELM_PLUGIN_NAME}",
        description=(
            f"helm-{HELM_PLUGIN_NAME} is a Helm plugin for validating Helm "
            "charts against the Kubernetes schemas, using Kubeconform."
        ),
    )

    if chart_files:
        parser.add_argument(
            "chart_files",
            nargs="+",
            type=Path,
            help="files belonging to a chart to validate",
            metavar="chart_file",
        )
    else:
        parser.add_argument("chart", help="chart")

        if values_files:
            parser.add_argument(
                "values",
                nargs="+",
                type=Path,
                help="Values files. The chart will be validated against each "
                "of them",
            )

    _add_helm_template_flags(parser)
    _add_kubeconform_flags(parser)

    return parser


# Entry point for the Helm plugin runner
def main(
    argv: list[str] | None = None,
    validate_chart_files: bool = False,
    validate_values_files: bool = False,
) -> int:
    """Entry point for the Helm plugin wrapper.

    Args:
        argv (list[str] | None, optional): Command-line arguments.
        validate_chart_files (bool, optional): If `True`, the entry point will
            accept a set of files, supposed to belong to Helm charts, as
            the only positional arguments. For each of them the corresponding
            chart directory will be computed and validated.
        validate_values_files (bool, optional): If `True`, the entry point will
            accept a set of Helm values files as extra positional
            arguments, in addition to the chart argument.

    Returns:
        int: The status code for the wrapper.
    """
    try:
        parser = _argument_parser(
            chart_files=validate_chart_files,
            values_files=validate_values_files,
        )
    except OSError as ex:
        logging.error(ex)
        return ex.errno
    except CalledProcessError as ex:
        return ex.returncode

    args = parser.parse_args(argv)

    helm_template_args = (
        getattr(args, _HELM_TEMPLATE_ARGPARSE_DEST, None) or []
    )
    kubeconform_args = getattr(args, _KUBECONFORM_ARGPARSE_DEST, None) or []

    # HELM_DEBUG environment variable is set to "true" when helm is called
    # with --debug flag
    if HELM_DEBUG == "true":
        helm_template_args.append("--debug")
        kubeconform_args.append("-debug")

    if "--debug" in helm_template_args or "-debug" in kubeconform_args:
        logging.getLogger().setLevel(logging.DEBUG)

    if validate_chart_files:
        return _validate_from_helm_chart_files(
            helm_template_args, kubeconform_args, args.chart_files
        )

    helm_template_args.append(args.chart)

    if validate_values_files:
        return _validate_helm_values_files(
            helm_template_args, kubeconform_args, args.values
        )

    return _validate(helm_template_args, kubeconform_args)


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
