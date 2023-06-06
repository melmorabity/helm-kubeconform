#!/usr/bin/env python
# Copyright © 2023 Mohamed El Morabity
# SPDX-License-Identifier: GPL-3.0-or-later

"""A pre-commit wrapper script for the helm-kubeconform plugin."""

from argparse import ArgumentParser
import os
from pathlib import Path
import platform
import subprocess
from typing import List
from typing import Optional

import plugin


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for the pre-commit wrapper script.

    Returns:
        int: The status code for the pre-commit script.
    """
    parser = ArgumentParser(
        description="Pre-commit wrapper for the helm kubeconform plugin",
        add_help=False,
    )
    parser.add_argument(
        "task",
        choices=["validate-charts", "validate-values"],
    )
    args, plugin_args = parser.parse_known_args(argv)

    env = {
        "HELM_PLUGIN_DIR": plugin.HELM_PLUGIN_DIR,
        # Ensure that the Kubeconform installation script has access to the
        # network environment variables
        "http_proxy": os.getenv("http_proxy", ""),
        "https_proxy": os.getenv("https_proxy", ""),
        "no_proxy": os.getenv("no_proxy", ""),
        "HTTP_PROXY": os.getenv("HTTP_PROXY", ""),
        "HTTPS_PROXY": os.getenv("HTTPS_PROXY", ""),
        "NO_PROXY": os.getenv("NO_PROXY", ""),
    }
    # Allow shell scripts with CR EOLs to run on Windows (depending on Git
    # `core.autocrlf` setting)
    if platform.system() == "Windows":
        env["SHELLOPTS"] = "igncr"

    # Ensure kubeconform is installed
    if not Path(plugin.KUBECONFORM_BIN).is_file():
        subprocess.run(
            [
                "sh",
                Path(plugin.HELM_PLUGIN_DIR, "install.sh"),
            ],
            check=True,
            env=env,
        )

    return plugin.main(
        argv=plugin_args,
        validate_chart_files=args.task == "validate-charts",
        validate_values_files=args.task == "validate-values",
    )


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
