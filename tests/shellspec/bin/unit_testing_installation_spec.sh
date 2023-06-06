# SPDX-FileCopyrightText: © 2023 Mohamed El Morabity
# SPDX-License-Identifier: GPL-3.0-or-later

# shellcheck shell=sh

# Variables passed by Helm
export HELM_PLUGIN_NAME=kubeconform
export HELM_PLUGIN_DIR="$PWD"

PLUGIN_VERSION=$(sed -n "s/^[[:space:]]*version[[:space:]]*:[[:space:]]*//p" "$HELM_PLUGIN_DIR/plugin.yaml")
KUBECONFORM_URL=https://github.com/yannh/kubeconform
TMP_DIR=/tmp/tmpdir

is_windows() {
    case $1 in
        CYGWIN* | MINGW* | MSYS*) return 0 ;;
        *) return 1 ;;
    esac
}

command_called() {
    echo "shellspec: calling $*" >&2
}

# Command mocks
mktemp() { echo "$TMP_DIR"; }
rm() { :; }
curl() { command_called "curl" "$@"; }
# shellcheck disable=SC2317
wget() { command_called "wget" "$@"; }
mkdir() { :; }
chmod() { command_called chmod "$@"; }
cd() { :; }

platform_mocks() {
    _mockOS=$1
    _mockArch=$2

    if [ "$_mockOS" = Darwin ]; then
        shasum() { command_called shasum "$@"; }
    else
        sha256sum() { command_called sha256sum "$@"; }
    fi

    if is_windows "$_mockOS"; then
        cygpath() {
            case "$1" in
                "-w") echo "C:$2" | sed "s/\//\\\/g" ;;
                *) echo "$2" ;;
            esac
        }

        unzip() { command_called unzip "$@"; }
    else
        tar() { command_called tar "$@"; }
    fi

    uname() {
        case "$1" in
            -s)
                echo "$_mockOS"
                ;;
            -m)
                echo "$_mockArch"
                ;;
        esac
    }
}

Describe "Install plugin"
Parameters:matrix
Linux/x86_64 Linux/i686 Linux/aarch64 Linux/armv7l Darwin/x86_64 Darwin/aarch64 CYGWIN_NT-10.0-1904/x86_64 CYGWIN_NT-10.0-1904/i686 MINGW64_NT-10.0-19044/x86_64 MINGW64_NT-10.0-19044/aarch64 MINGW32_NT-10.0-19044/armv8l
# shellcheck disable=SC2218
curl wget
false true
End
Example "on $1 with $2 available"
{
    os=${1%/*}
    arch=${1#*/}

    HELM_DEBUG=$3

    platform_mocks "$os" "$arch"

    case "$os" in
        Linux) kubeconformOS=linux ;;
        Darwin) kubeconformOS=darwin ;;
        CYGWIN* | MINGW* | MSYS*) kubeconformOS=windows ;;
    esac

    case "$arch" in
        x86_64) kubeconformArch=amd64 ;;
        i*86) kubeconformArch=386 ;;
        aarch64) kubeconformArch=arm64 ;;
        arm*) kubeconformArch=armv6 ;;
    esac

    kubeconformArchive=kubeconform-$kubeconformOS-$kubeconformArch
    if is_windows "$os"; then
        kubeconformArchive=$kubeconformArchive.zip
    else
        kubeconformArchive=$kubeconformArchive.tar.gz
    fi

    if [ "$2" = curl ]; then
        unset wget
    else
        unset curl
    fi
}
When run source ./helm_kubeconform/install.sh
The status should be success
The output should be blank
The error should match pattern "*shellspec: calling $2 * $KUBECONFORM_URL/releases/download/v${PLUGIN_VERSION%.*}/$kubeconformArchive *"
if [ "$2" = curl ]; then
    The error should not include "shellspec: calling wget "
else
    The error should not include "shellspec: calling curl "
fi
The error should match pattern "*shellspec: calling $2 * $KUBECONFORM_URL/releases/download/v${PLUGIN_VERSION%.*}/CHECKSUMS *"
if [ "$os" = Darwin ]; then
    The error should include "shellspec: calling shasum -a 256 "
else
    The error should include "shellspec: calling sha256sum -c --status"
fi
if is_windows "$os"; then
    The error should match pattern "*shellspec: calling unzip * $(cygpath -w "$TMP_DIR/$kubeconformArchive") *"
    The error should not include "shellspec: calling tar "
    The error should include "shellspec: calling chmod +x $HELM_PLUGIN_DIR/kubeconform.exe"
else
    The error should match pattern "*shellspec: calling tar * $TMP_DIR/$kubeconformArchive *"
    The error should not include "shellspec: calling unzip "
    The error should include "shellspec: calling chmod +x $HELM_PLUGIN_DIR/kubeconform"
fi
if [ "$HELM_DEBUG" = true ]; then
    The error should include "Debug: $HELM_PLUGIN_NAME: "
fi
End
End

Describe "Install plugin on unsupported environment"
Parameters
FreeBSD x86_64 "FreeBSD platform is not supported"
Linux mips "mips architecture is not supported"
Darwin i686 "i686 architecture is not supported"
End
Example "$1/$2"
{
    platform_mocks "$1" "$2"
}
When run source ./helm_kubeconform/install.sh
The status should be failure
The output should be blank
The error should include "Error: $HELM_PLUGIN_NAME: $3"
End
End

Describe "Install plugin"
Parameters
Linux/x86_64 Linux/i686 Linux/aarch64 Linux/armv7l Darwin/x86_64 Darwin/aarch64 CYGWIN_NT-10.0-1904/x86_64 CYGWIN_NT-10.0-1904/i686 MINGW64_NT-10.0-19044/x86_64 MINGW64_NT-10.0-19044/aarch64 MINGW32_NT-10.0-19044/armv8l
End
Example "on $1 without any downloader"
{
    os=${1%/*}
    arch=${1#*/}
    platform_mocks "$os" "$arch"
    unset curl wget
}
When run source ./helm_kubeconform/install.sh
The status should be failure
The output should be blank
The error should include "Error: $HELM_PLUGIN_NAME: curl or wget is required to download Kubeconform"
End
End

Describe "Install plugin"
Parameters
Linux/x86_64 Linux/i686 Linux/aarch64 Linux/armv7l Darwin/x86_64 Darwin/aarch64 CYGWIN_NT-10.0-1904/x86_64 CYGWIN_NT-10.0-1904/i686 MINGW64_NT-10.0-19044/x86_64 MINGW64_NT-10.0-19044/aarch64 MINGW32_NT-10.0-19044/armv8l
End
Example "on $1 without SHA-256 check tools"
{
    os=${1%/*}
    arch=${1#*/}
    platform_mocks "$os" "$arch"
    if [ "$os" = Darwin ]; then
        unset shasum
    else
        unset sha256sum
    fi
}
When run source ./helm_kubeconform/install.sh
The status should be success
The output should be blank
The error should include "Warning: $HELM_PLUGIN_NAME: Skipping SHA-256 checksuming"
The error should include "shellspec: calling chmod +x $HELM_PLUGIN_DIR/kubeconform"
End
End

Describe "Install plugin"
Parameters
CYGWIN_NT-10.0-1904/x86_64 CYGWIN_NT-10.0-1904/i686 MINGW64_NT-10.0-19044/x86_64 MINGW64_NT-10.0-19044/aarch64 MINGW32_NT-10.0-19044/armv8l
End
Example on Windows without unzip
{
    os=${1%/*}
    arch=${1#*/}
    platform_mocks "$os" "$arch"
    unset unzip
}
When run source ./helm_kubeconform/install.sh
The status should be failure
The output should be blank
The error should include "Error: $HELM_PLUGIN_NAME: unzip is required to install Kubeconform"
End
End

Describe "Install plugin"
Parameters
x86_64 i686 aarch64 armv7l
End
Example "on Linux/$1 with Busybox implementation of sha256sum"
{
    platform_mocks Linux "$1"
    unset sha256sum
    sha256sum() {
        if [ "$1" = --help ]; then
            echo "BusyBox v1.36.0 (2023-05-05 06:41:49 UTC) multi-call binary." >&2
        fi
        command_called sha256sum "$@"
    }
}
When run source ./helm_kubeconform/install.sh
The status should be success
The output should be blank
The error should include "shellspec: calling sha256sum -c -s"
The error should include "shellspec: calling chmod +x $HELM_PLUGIN_DIR/kubeconform"
End
End

Describe "Install plugin"
Parameters
CYGWIN_NT-10.0-1904/x86_64 CYGWIN_NT-10.0-1904/i686 MINGW64_NT-10.0-19044/x86_64 MINGW64_NT-10.0-19044/aarch64 MINGW32_NT-10.0-19044/armv8l
End
Example "on $1 with unset Helm environment variable HELM_PLUGIN_DIR"
{
    os=${1%/*}
    arch=${1#*/}
    platform_mocks "$os" "$arch"
    unset HELM_PLUGIN_DIR
}
When run source ./helm_kubeconform/install.sh
The status should be failure
The output should be blank
The error should include "Error: $HELM_PLUGIN_NAME: HELM_PLUGIN_DIR environment variable is not set"
End
End

Describe "Install plugin"
Parameters:matrix
Linux/x86_64 Linux/i686 Linux/aarch64 Linux/armv7l Darwin/x86_64 Darwin/aarch64 CYGWIN_NT-10.0-1904/x86_64 CYGWIN_NT-10.0-1904/i686 MINGW64_NT-10.0-19044/x86_64 MINGW64_NT-10.0-19044/aarch64 MINGW32_NT-10.0-19044/armv8l
# shellcheck disable=SC2218
curl wget
End
Example "on $1 with download failure"
{
    os=${1%/*}
    arch=${1#*/}

    platform_mocks "$os" "$arch"

    if [ "$2" = curl ]; then
        curl() { false; }
        unset wget
    else
        wget() { false; }
        unset curl
    fi
}
When run source ./helm_kubeconform/install.sh
The status should be failure
The output should be blank
The error should include "Error: $HELM_PLUGIN_NAME: Error while downloading "
End
End

Describe "Install plugin"
Parameters:matrix
Linux/x86_64 Linux/i686 Linux/aarch64 Linux/armv7l Darwin/x86_64 Darwin/aarch64 CYGWIN_NT-10.0-1904/x86_64 CYGWIN_NT-10.0-1904/i686 MINGW64_NT-10.0-19044/x86_64 MINGW64_NT-10.0-19044/aarch64 MINGW32_NT-10.0-19044/armv8l
End
Example "on $1 with checksum failure"
{
    os=${1%/*}
    arch=${1#*/}

    platform_mocks "$os" "$arch"

    if [ "$_mockOS" = Darwin ]; then
        shasum() { false; }
    else
        sha256sum() { false; }
    fi
}
When run source ./helm_kubeconform/install.sh
The status should be failure
The output should be blank
The error should include "Error: $HELM_PLUGIN_NAME: Unable to validate checksum "
End
End
