#!/bin/sh

# SPDX-FileCopyrightText: © 2023 Mohamed El Morabity
# SPDX-License-Identifier: GPL-3.0-or-later

set -o errexit
set -o nounset

# Environment variables injected by Helm when running a plugin
HELM_PLUGIN_NAME=${HELM_PLUGIN_NAME:-kubeconform}
HELM_DEBUG=${HELM_DEBUG-}

_debug() {
    if [ "$HELM_DEBUG" = true ]; then
        echo "Debug: $HELM_PLUGIN_NAME: $1" >&2
    fi
}

_warning() {
    echo "Warning: $HELM_PLUGIN_NAME: $1" >&2
}

_error() {
    echo "Error: $HELM_PLUGIN_NAME: $1" >&2
    exit 1
}

_command_exists() {
    command -v "$1" >/dev/null
}

_download() {
    if _command_exists curl; then
        _debug "Use curl to download $1"

        # Manage Windows implementation of curl
        if _command_exists cygpath; then
            set -- "$1" "$(cygpath -w "$2")"
        fi

        curl -fLs "$1" -o "$2"
    elif _command_exists wget; then
        _debug "Use wget to download $1"
        wget -q "$1" -O "$2"
    else
        _error "curl or wget is required to download Kubeconform"
    fi
}

# Injected by Helm when running a plugin
if [ -z "${HELM_PLUGIN_DIR-}" ]; then
    _error "HELM_PLUGIN_DIR environment variable is not set"
fi

if [ -z "${HELM_PLUGIN_VERSION-}" ]; then
    HELM_PLUGIN_VERSION=$(sed -n "s/^[[:space:]]*version[[:space:]]*:[[:space:]]*//p" "$HELM_PLUGIN_DIR/plugin.yaml")
fi

if _command_exists cygpath; then
    HELM_PLUGIN_DIR=$(cygpath -u "$HELM_PLUGIN_DIR")
fi

PLATFORM=$(uname -s)
_debug "Check whether $PLATFORM platform is supported"
KUBECONFORM_ARCHIVE_EXT=.tar.gz
KUBECONFORM_EXT=
case $PLATFORM in
    Linux)
        KUBECONFORM_PLATFORM=linux
        ;;
    Darwin)
        KUBECONFORM_PLATFORM=darwin
        ;;
    CYGWIN* | MINGW* | MSYS*)
        KUBECONFORM_PLATFORM=windows
        KUBECONFORM_ARCHIVE_EXT=.zip
        KUBECONFORM_EXT=.exe
        ;;
    *)
        _error "$PLATFORM platform is not supported"
        ;;
esac

if [ "$KUBECONFORM_PLATFORM" = windows ] && ! _command_exists unzip; then
    _error "unzip is required to install Kubeconform"
fi

ARCH=$(uname -m)
_debug "Check whether $ARCH architecture is supported"
case $ARCH in
    x86_64)
        KUBECONFORM_ARCH=amd64
        ;;
    i*86)
        if [ $KUBECONFORM_PLATFORM = darwin ]; then
            _error "$ARCH architecture is not supported"
        fi
        KUBECONFORM_ARCH=386
        ;;
    aarch64)
        KUBECONFORM_ARCH=arm64
        ;;
    arm*)
        KUBECONFORM_ARCH=armv6
        ;;
    *)
        _error "$ARCH architecture is not supported"
        ;;
esac

TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT INT QUIT

KUBECONFORM_VERSION=${HELM_PLUGIN_VERSION%.*}
KUBECONFORM_GITHUB_PROJECT="yannh/kubeconform"
KUBECONFORM_URL_BASE=https://github.com/$KUBECONFORM_GITHUB_PROJECT/releases/download/v$KUBECONFORM_VERSION

KUBECONFORM_ARCHIVE_FILE=kubeconform-$KUBECONFORM_PLATFORM-$KUBECONFORM_ARCH$KUBECONFORM_ARCHIVE_EXT
KUBECONFORM_ARCHIVE_URL=$KUBECONFORM_URL_BASE/$KUBECONFORM_ARCHIVE_FILE
KUBECONFORM_ARCHIVE_PATH=$TEMP_DIR/$KUBECONFORM_ARCHIVE_FILE

KUBECONFORM_CHECKSUM_URL=$KUBECONFORM_URL_BASE/CHECKSUMS

KUBECONFORM_DIR=$HELM_PLUGIN_DIR
KUBECONFORM_FILE=kubeconform$KUBECONFORM_EXT
KUBECONFORM_PATH=$KUBECONFORM_DIR/$KUBECONFORM_FILE

_debug "Download Kubeconform $KUBECONFORM_VERSION archive from $KUBECONFORM_ARCHIVE_URL to $KUBECONFORM_ARCHIVE_PATH"
_download "$KUBECONFORM_ARCHIVE_URL" "$KUBECONFORM_ARCHIVE_PATH" || _error "Error while downloading Kubeconform archive from $KUBECONFORM_ARCHIVE_URL"

_debug "Check sum downloaded archive $KUBECONFORM_ARCHIVE_PATH"
_download "$KUBECONFORM_CHECKSUM_URL" - | grep "\b$KUBECONFORM_ARCHIVE_FILE\b" | {
    cd "$TEMP_DIR"
    if _command_exists sha256sum; then
        _debug "Use sha256sum for checksuming"
        # Busybox
        if sha256sum --help 2>&1 | grep -qi busybox; then
            sha256sum -c -s
        else
            sha256sum -c --status
        fi
    # MacOSX
    elif _command_exists shasum; then
        _debug "Using shasum for checksuming"
        shasum -a 256 -c -s
    else
        _warning "Skipping SHA-256 checksuming (sha256sum or shasum unavailable)"
    fi
} || _error "Unable to validate checksum for $KUBECONFORM_ARCHIVE_PATH"

_debug "Extract Kubeconform executable from archive $KUBECONFORM_ARCHIVE_PATH to $KUBECONFORM_DIR"
mkdir -p "$KUBECONFORM_DIR"
if [ "$KUBECONFORM_ARCHIVE_EXT" = .zip ]; then
    if _command_exists cygpath; then
        # Manage non-Cygwin versions of unzip in PATH (for example the one provided by Git for Windows)
        KUBECONFORM_ARCHIVE_PATH=$(cygpath -w "$KUBECONFORM_ARCHIVE_PATH")
        KUBECONFORM_DIR=$(cygpath -w "$KUBECONFORM_DIR")
    fi

    unzip -oqj "$KUBECONFORM_ARCHIVE_PATH" -d "$KUBECONFORM_DIR" "$KUBECONFORM_FILE"
else
    tar -xzf "$KUBECONFORM_ARCHIVE_PATH" -C "$KUBECONFORM_DIR" "$KUBECONFORM_FILE"
fi
chmod +x "$KUBECONFORM_PATH"
