# SPDX-FileCopyrightText: © 2023 Mohamed El Morabity
# SPDX-License-Identifier: GPL-3.0-or-later

"""A pre-commit wrapper for the helm-kubeconform plugin."""

from __future__ import annotations

from argparse import ArgumentParser
import importlib.metadata
import os
from pathlib import Path
import platform
import subprocess
from subprocess import CalledProcessError
import sys

import helm_kubeconform.plugin


def main(argv: list[str] | None = None) -> int:
    """Entry point for the pre-commit wrapper.

    Args:
        argv (list[str] | None, optional): Command-line arguments.

    Returns:
        int: The status code for the pre-commit script.
    """
    parser = ArgumentParser(
        description="Pre-commit wrapper for the helm kubeconform plugin",
        add_help=False,
    )
    parser.add_argument("task", choices=["validate-charts", "validate-values"])
    args, plugin_args = parser.parse_known_args(argv)

    env = {
        "HELM_PLUGIN_DIR": helm_kubeconform.plugin.HELM_PLUGIN_DIR,
        "HELM_PLUGIN_VERSION": importlib.metadata.version("helm-kubeconform"),
        # Ensure that the Kubeconform installation script has access to the
        # network environment variables
        "http_proxy": os.getenv("http_proxy", ""),  # noqa: SIM112
        "https_proxy": os.getenv("https_proxy", ""),  # noqa: SIM112
        "no_proxy": os.getenv("no_proxy", ""),  # noqa: SIM112
        "HTTP_PROXY": os.getenv("HTTP_PROXY", ""),
        "HTTPS_PROXY": os.getenv("HTTPS_PROXY", ""),
        "NO_PROXY": os.getenv("NO_PROXY", ""),
    }
    # Allow shell scripts with CR EOLs to run on Windows (depending on Git
    # `core.autocrlf` setting)
    if platform.system() == "Windows":
        env["SHELLOPTS"] = "igncr"

    # Ensure Kubeconform is installed
    if not Path(helm_kubeconform.plugin.KUBECONFORM_BIN).is_file():
        try:
            subprocess.run(
                ["sh", Path(__file__).parent / "install.sh"],
                check=True,
                env=env,
                stdout=sys.stderr,
            )
        except CalledProcessError as ex:
            return ex.returncode

    return helm_kubeconform.plugin.main(
        argv=plugin_args,
        validate_chart_files=args.task == "validate-charts",
        validate_values_files=args.task == "validate-values",
    )
