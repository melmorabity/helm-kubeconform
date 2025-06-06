# SPDX-FileCopyrightText: © 2023 Mohamed El Morabity
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import contextlib
import importlib.metadata
from io import StringIO
from subprocess import CalledProcessError
import sys
import typing
from typing import Any
from unittest import TestCase
import unittest.mock

import helm_kubeconform.plugin
import helm_kubeconform.pre_commit

if typing.TYPE_CHECKING:
    from typing_extensions import Self


class TestPreCommit(TestCase):
    def setUp(self: Self) -> None:
        subprocess_patch = unittest.mock.patch(
            "helm_kubeconform.pre_commit.subprocess"
        )
        self.subprocess_mock = subprocess_patch.start()
        self.addCleanup(subprocess_patch.stop)
        self.subprocess_mock.run.return_value = 0

        path_patch = unittest.mock.patch("helm_kubeconform.pre_commit.Path")
        self.path_mock = path_patch.start()
        self.addCleanup(path_patch.stop)
        self.path_mock.return_value.is_file.return_value = True

        platform_patch = unittest.mock.patch(
            "helm_kubeconform.pre_commit.platform"
        )
        self.platform_mock = platform_patch.start()
        self.addCleanup(platform_patch.stop)

        plugin_main_patch = unittest.mock.patch("helm_kubeconform.plugin.main")
        self.plugin_main_mock = plugin_main_patch.start()
        self.addCleanup(plugin_main_patch.stop)
        self.plugin_main_mock.return_value = 0

    def test_invalid_args(self: Self) -> None:
        test_args: list[tuple[list[str], str]] = [
            ([], "error: the following arguments are required: task"),
            (["--help"], "error: the following arguments are required: task"),
            (["bad-task"], "error: argument task: invalid choice: 'bad-task'"),
        ]

        for arg in test_args:
            with self.subTest(arg=arg):
                argv, error = arg

                stderr = StringIO()

                with (
                    contextlib.redirect_stderr(stderr),
                    self.assertRaises(SystemExit) as exit_cm,
                ):
                    helm_kubeconform.pre_commit.main(argv=argv)

                self.assertEqual(exit_cm.exception.code, 2)
                self.assertIn(error, stderr.getvalue())

    def test_kubeconform_not_present(self: Self) -> None:
        test_args: list[dict[str, Any]] = [
            {"system": "Linux", "extra_env": {}},
            {"system": "Windows", "extra_env": {"SHELLOPTS": "igncr"}},
        ]

        for arg in test_args:
            with self.subTest(arg=arg):
                self.setUp()

                self.path_mock.return_value.is_file.return_value = False
                self.platform_mock.system.return_value = arg["system"]

                return_code = helm_kubeconform.pre_commit.main(
                    argv=["validate-charts"]
                )
                self.subprocess_mock.run.assert_called_once_with(
                    ["sh", unittest.mock.ANY],
                    check=True,
                    env={
                        **arg["extra_env"],
                        "HELM_PLUGIN_DIR": str(
                            helm_kubeconform.plugin.HELM_PLUGIN_DIR
                        ),
                        "HELM_PLUGIN_VERSION": importlib.metadata.version(
                            "helm-kubeconform"
                        ),
                        "http_proxy": unittest.mock.ANY,
                        "https_proxy": unittest.mock.ANY,
                        "no_proxy": unittest.mock.ANY,
                        "HTTP_PROXY": unittest.mock.ANY,
                        "HTTPS_PROXY": unittest.mock.ANY,
                        "NO_PROXY": unittest.mock.ANY,
                    },
                    stdout=sys.stderr,
                )
                self.assertEqual(return_code, 0)

    def test_kubeconform_present(self: Self) -> None:
        return_code = helm_kubeconform.pre_commit.main(
            argv=["validate-charts"]
        )
        self.subprocess_mock.run.assert_not_called()
        self.assertEqual(return_code, 0)

    def test_kubeconform_installation_failed(self: Self) -> None:
        self.path_mock.return_value.is_file.return_value = False
        self.subprocess_mock.run.side_effect = CalledProcessError(1, "error")

        return_code = helm_kubeconform.pre_commit.main(
            argv=["validate-charts"]
        )

        self.assertEqual(self.subprocess_mock.run.call_count, 1)
        self.assertEqual(return_code, 1)

    def test_chart_files_validation(self: Self) -> None:
        return_code = helm_kubeconform.pre_commit.main(
            argv=["validate-charts", "file1", "file2"]
        )

        self.plugin_main_mock.assert_called_once_with(
            argv=["file1", "file2"],
            validate_chart_files=True,
            validate_values_files=False,
        )
        self.assertEqual(return_code, 0)

    def test_chart_files_validation_failed(self: Self) -> None:
        self.plugin_main_mock.return_value = 1

        return_code = helm_kubeconform.pre_commit.main(
            argv=["validate-charts", "file1", "file2"]
        )

        self.plugin_main_mock.assert_called_once_with(
            argv=["file1", "file2"],
            validate_chart_files=True,
            validate_values_files=False,
        )
        self.assertEqual(return_code, 1)

    def test_values_files_validation(self: Self) -> None:
        return_code = helm_kubeconform.pre_commit.main(
            argv=["validate-values", "file1", "file2"]
        )

        self.plugin_main_mock.assert_called_once_with(
            argv=["file1", "file2"],
            validate_chart_files=False,
            validate_values_files=True,
        )
        self.assertEqual(return_code, 0)

    def test_values_files_validation_failed(self: Self) -> None:
        self.plugin_main_mock.return_value = 1

        return_code = helm_kubeconform.pre_commit.main(
            argv=["validate-values", "file1", "file2"]
        )

        self.plugin_main_mock.assert_called_once_with(
            argv=["file1", "file2"],
            validate_chart_files=False,
            validate_values_files=True,
        )
        self.assertEqual(return_code, 1)
