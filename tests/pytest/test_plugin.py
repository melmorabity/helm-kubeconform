# SPDX-FileCopyrightText: © 2023 Mohamed El Morabity
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import contextlib
from io import StringIO
import os
from pathlib import Path
import re
from subprocess import CalledProcessError
import sys
import typing
from unittest import TestCase
import unittest.mock

import helm_kubeconform.plugin

if typing.TYPE_CHECKING:
    from typing_extensions import Self

MOCK_HELM_TEMPLATE_HELP = """
Usage:
    helm template [NAME] [CHART] [flags]

Flags:
    -h, --help             help for template
    --kube-version string  Kubernetes version
    --output-dir string    writes the executed templates in output-dir
    --verify               verify the package before using it
    -f, --values strings   specify values in a YAML file or a URL

Global Flags:
    --burst-limit int       client-side default throttling limit
    --debug                 enable verbose output
    -n, --namespace string  namespace scope for this request
"""

MOCK_KUBECONFORM_HELP = """
Usage: kubeconform [OPTION]... [FILE OR FOLDER]...

    -h  show help information
    -insecure-skip-tls-verify
        disable verification of the server's SSL certificate
    -kubernetes-version string
        version of Kubernetes to validate against
    -n int
        number of goroutines to run concurrently
    -reject string
        comma-separated list of kinds or GVKs to reject
    -strict
        disallow additional properties not in schema or duplicated keys
"""


class TestRun(TestCase):
    def setUp(self: Self) -> None:
        subprocess_patch = unittest.mock.patch(
            "helm_kubeconform.plugin.subprocess"
        )
        self.subprocess_mock = subprocess_patch.start()
        self.addCleanup(subprocess_patch.stop)

        self.subprocess_mock.check_output.side_effect = [
            MOCK_HELM_TEMPLATE_HELP,
            MOCK_KUBECONFORM_HELP,
        ]

    def test_help(self: Self) -> None:
        stdout = StringIO()
        with (
            contextlib.redirect_stdout(stdout),
            self.assertRaises(SystemExit) as exit_cm,
        ):
            helm_kubeconform.plugin.main(argv=["--help"])

        self.assertEqual(exit_cm.exception.code, 0)

        self.assertIn("--kube-version string", stdout.getvalue())
        self.assertIn("--verify", stdout.getvalue())
        self.assertIn("--skip-tls-verify", stdout.getvalue())
        self.assertIn("--goroutines", stdout.getvalue())
        self.assertIn("--reject string", stdout.getvalue())
        self.assertIn("--strict", stdout.getvalue())

        if sys.version_info >= (3, 13):
            self.assertIn("-n, --namespace string", stdout.getvalue())
            self.assertIn("-f, --values strings", stdout.getvalue())
        else:
            self.assertIn("-n string, --namespace string", stdout.getvalue())
            self.assertIn("-f strings, --values strings", stdout.getvalue())

        self.assertNotIn("--output-dir", stdout.getvalue())
        self.assertNotIn("--release-name", stdout.getvalue())
        self.assertNotIn("--insecure-skip-tls-verify", stdout.getvalue())
        self.assertNotIn("--kubernetes-version", stdout.getvalue())

    def test_options(self: Self) -> None:
        test_args = (
            {
                "plugin_args": ["chart"],
                "helm_template_command": [
                    helm_kubeconform.plugin.HELM_BIN,
                    "template",
                    "chart",
                ],
                "kubeconform_command": [
                    helm_kubeconform.plugin.KUBECONFORM_BIN
                ],
            },
            {
                "plugin_args": ["chart", "--verify"],
                "helm_template_command": [
                    helm_kubeconform.plugin.HELM_BIN,
                    "template",
                    "--verify",
                    "chart",
                ],
                "kubeconform_command": [
                    helm_kubeconform.plugin.KUBECONFORM_BIN
                ],
            },
            {
                "plugin_args": ["chart", "--debug"],
                "helm_template_command": [
                    helm_kubeconform.plugin.HELM_BIN,
                    "template",
                    "--debug",
                    "chart",
                ],
                "kubeconform_command": [
                    helm_kubeconform.plugin.KUBECONFORM_BIN,
                    "-debug",
                ],
            },
            {
                "plugin_args": ["chart", "--kube-version", "1.26.2"],
                "helm_template_command": [
                    helm_kubeconform.plugin.HELM_BIN,
                    "template",
                    "--kube-version",
                    "1.26.2",
                    "chart",
                ],
                "kubeconform_command": [
                    helm_kubeconform.plugin.KUBECONFORM_BIN,
                    "-kubernetes-version",
                    "1.26.2",
                ],
            },
            {
                "plugin_args": ["chart", "--goroutines", "4"],
                "helm_template_command": [
                    helm_kubeconform.plugin.HELM_BIN,
                    "template",
                    "chart",
                ],
                "kubeconform_command": [
                    helm_kubeconform.plugin.KUBECONFORM_BIN,
                    "-n",
                    "4",
                ],
            },
            {
                "plugin_args": ["chart", "--skip-tls-verify"],
                "helm_template_command": [
                    helm_kubeconform.plugin.HELM_BIN,
                    "template",
                    "chart",
                ],
                "kubeconform_command": [
                    helm_kubeconform.plugin.KUBECONFORM_BIN,
                    "-insecure-skip-tls-verify",
                ],
            },
        )

        for arg in test_args:
            with self.subTest(arg=arg):
                self.setUp()

                calls = [
                    unittest.mock.call(
                        arg["helm_template_command"],
                        stdout=unittest.mock.ANY,
                        check=True,
                    ),
                    unittest.mock.call(
                        arg["kubeconform_command"],
                        input=unittest.mock.ANY,
                        stdout=sys.stderr,
                        check=True,
                    ),
                ]

                return_code = helm_kubeconform.plugin.main(
                    argv=arg["plugin_args"]
                )
                self.assertEqual(return_code, 0)
                self.subprocess_mock.run.assert_has_calls(calls)
                self.assertEqual(self.subprocess_mock.run.call_count, 2)

    @unittest.mock.patch("helm_kubeconform.plugin.HELM_DEBUG", "true")
    def test_helm_debug(self: Self) -> None:
        calls = [
            unittest.mock.call(
                [
                    helm_kubeconform.plugin.HELM_BIN,
                    "template",
                    "--debug",
                    "chart",
                ],
                stdout=unittest.mock.ANY,
                check=True,
            ),
            unittest.mock.call(
                [helm_kubeconform.plugin.KUBECONFORM_BIN, "-debug"],
                input=unittest.mock.ANY,
                stdout=sys.stderr,
                check=True,
            ),
        ]

        with self.assertLogs(level="DEBUG") as context_manager:
            return_code = helm_kubeconform.plugin.main(argv=["chart"])

        self.assertEqual(return_code, 0)
        self.subprocess_mock.run.assert_has_calls(calls=calls)
        self.assertEqual(self.subprocess_mock.run.call_count, 2)
        self.assertIn(
            "DEBUG:helm_kubeconform.plugin:Running helm template --debug "
            "chart",
            context_manager.output,
        )
        self.assertIn(
            "DEBUG:helm_kubeconform.plugin:Running "
            f"{helm_kubeconform.plugin.KUBECONFORM_BIN} -debug",
            context_manager.output,
        )

    def test_help_processing_failure(self: Self) -> None:
        errors = [
            {
                "exception": CalledProcessError(1, "helm template --help"),
                "return_code": 1,
            },
            {
                "exception": FileNotFoundError(
                    2, os.strerror(2), helm_kubeconform.plugin.KUBECONFORM_BIN
                ),
                "return_code": 2,
            },
        ]
        for error in errors:
            with self.subTest(error=error):
                self.subprocess_mock.check_output.side_effect = error[
                    "exception"
                ]

                return_code = helm_kubeconform.plugin.main(argv=["chart"])
                self.assertEqual(return_code, error["return_code"])

    def test_helm_template_failure(self: Self) -> None:
        self.subprocess_mock.run.side_effect = CalledProcessError(
            2, "helm template"
        )

        return_code = helm_kubeconform.plugin.main(argv=["chart"])

        self.assertEqual(return_code, 2)
        self.assertEqual(self.subprocess_mock.run.call_count, 1)

    def test_kubeconform_failure(self: Self) -> None:
        self.subprocess_mock.run.side_effect = [
            unittest.mock.DEFAULT,
            CalledProcessError(2, "kubeconform"),
        ]

        return_code = helm_kubeconform.plugin.main(argv=["chart"])
        self.assertEqual(return_code, 2)
        self.assertEqual(self.subprocess_mock.run.call_count, 2)

    def test_chart_files_as_args(self: Self) -> None:
        return_code = helm_kubeconform.plugin.main(
            argv=[
                str(Path("/does/not/exist")),
                str(Path("tests/fixtures/chart-k8s/templates/_helpers.tpl")),
                str(Path("tests/fixtures/chart-k8s/Chart.yaml")),
                str(Path("tests/fixtures/chart-ocp/values.yaml")),
                "README.md",
            ],
            validate_chart_files=True,
        )

        self.assertEqual(return_code, 0)

        for chart in (
            str(Path("tests/fixtures/chart-k8s")),
            str(Path("tests/fixtures/chart-ocp")),
        ):
            self.subprocess_mock.run.assert_has_calls(
                [
                    unittest.mock.call(
                        [helm_kubeconform.plugin.HELM_BIN, "template", chart],
                        stdout=unittest.mock.ANY,
                        check=True,
                    ),
                    unittest.mock.call(
                        [helm_kubeconform.plugin.KUBECONFORM_BIN],
                        input=unittest.mock.ANY,
                        stdout=sys.stderr,
                        check=True,
                    ),
                ]
            )

        self.assertEqual(self.subprocess_mock.run.call_count, 4)

    def test_chart_file_as_args_failure(self: Self) -> None:
        self.subprocess_mock.run.side_effect = [
            unittest.mock.DEFAULT,
            CalledProcessError(2, "kubeconform"),
        ]

        test_paths = [
            Path("tests/fixtures/chart-k8s/Chart.yaml"),
            Path("tests/fixtures/chart-ocp/values.yaml"),
        ]

        with self.assertLogs(level="ERROR") as context_manager:
            return_code = helm_kubeconform.plugin.main(
                argv=[str(p) for p in test_paths], validate_chart_files=True
            )

        self.assertEqual(return_code, 2)
        self.assertEqual(self.subprocess_mock.run.call_count, 2)
        test_paths_regex = "|".join(
            re.escape(str(p.parent)) for p in test_paths
        )
        self.assertRegex(
            context_manager.output[0],
            rf"ERROR:helm_kubeconform.plugin:Helm chart ({test_paths_regex}) "
            r"validation failed",
        )

    def test_values_as_args(self: Self) -> None:
        values = ["values1.yml", "values2.yml"]
        return_code = helm_kubeconform.plugin.main(
            argv=["chart", *values], validate_values_files=True
        )

        self.assertEqual(return_code, 0)

        for value in values:
            self.subprocess_mock.run.assert_has_calls(
                [
                    unittest.mock.call(
                        [
                            helm_kubeconform.plugin.HELM_BIN,
                            "template",
                            "chart",
                            "--values",
                            value,
                        ],
                        stdout=unittest.mock.ANY,
                        check=True,
                    ),
                    unittest.mock.call(
                        [helm_kubeconform.plugin.KUBECONFORM_BIN],
                        input=unittest.mock.ANY,
                        stdout=sys.stderr,
                        check=True,
                    ),
                ]
            )

        self.assertEqual(self.subprocess_mock.run.call_count, 2 * len(values))

    def test_values_as_args_failure(self: Self) -> None:
        self.subprocess_mock.run.side_effect = [
            CalledProcessError(1, "helm template"),
            CalledProcessError(2, "kubeconform"),
        ]

        with self.assertLogs(level="ERROR") as context_manager:
            return_code = helm_kubeconform.plugin.main(
                argv=["chart", "values1.yml", "values2.yml"],
                validate_values_files=True,
            )

        self.assertEqual(return_code, 1)
        self.assertEqual(self.subprocess_mock.run.call_count, 1)
        self.assertIn(
            "ERROR:helm_kubeconform.plugin:Helm values file values1.yml "
            "validation failed",
            context_manager.output,
        )
