# SPDX-FileCopyrightText: © 2023 Mohamed El Morabity
# SPDX-License-Identifier: GPL-3.0-or-later

# shellcheck shell=sh

eval "$(helm env)"
HELM_BIN=$(command -v helm)
K8S_CHART_LOCATION=$PWD/tests/fixtures/chart-k8s
OCP_CHART_LOCATION=$PWD/tests/fixtures/chart-ocp
OCP_SCHEMA_URL="https://raw.githubusercontent.com/melmorabity/openshift-json-schemas/main/{{ .NormalizedKubernetesVersion }}-standalone{{ .StrictSuffix }}/{{ .ResourceKind }}.json"
VALID_CHART_VALUES=$PWD/tests/fixtures/good_values.yaml
INVALID_CHART_VALUES=$PWD/tests/fixtures/bad_values.yaml
KUBECONFORM_BIN=$HELM_PLUGINS/helm-kubeconform/kubeconform

if command -v cygpath >/dev/null; then
    HELM_BIN=$(cygpath -w "$HELM_BIN")
    KUBECONFORM_BIN=$(cygpath -w "$KUBECONFORM_BIN").exe

    K8S_CHART_LOCATION=$(cygpath -w "$K8S_CHART_LOCATION")
    OCP_CHART_LOCATION=$(cygpath -w "$OCP_CHART_LOCATION")
    VALID_CHART_VALUES=$(cygpath -w "$VALID_CHART_VALUES")
    INVALID_CHART_VALUES=$(cygpath -w "$INVALID_CHART_VALUES")
fi

helm_plugin_installed() {
    helm plugin list | grep -q "^kubeconform\b"
}

uninstall_helm_plugin() {
    if helm_plugin_installed; then
        helm plugin uninstall kubeconform >/dev/null
    fi
}

install_helm_plugin() {
    if ! helm_plugin_installed; then
        helm plugin install . >/dev/null
    fi
}

setUpAll() {
    uninstall_helm_plugin
    install_helm_plugin
}

cleanUpAll() {
    uninstall_helm_plugin
    rm -f "$KUBECONFORM_BIN"
}

BeforeAll setUpAll
AfterAll cleanUpAll

Describe "Display help"
Parameters
"-h"
"--help"
End
Example "with $1 option"
When run command helm kubeconform "$@"
The status should be success
The output should include "usage: helm kubeconform"
The output should not include "--output-dir"
The output should not include "--release-name"
The output should not include "--insecure-skip-tls-verify"
The output should not include " -kubernetes-version"
The output should not include " -insecure-skip-tls-verify"
The error should be blank
End
End

Describe "Run plugin"
Example "without argument"
When run command helm kubeconform
The status should be failure
The output should be blank
The error should include "helm kubeconform: error: the following arguments are required: chart"
End
Example "with invalid option"
When run command helm kubeconform chart --xyz
The status should be failure
The output should be blank
The error should include "helm kubeconform: error: unrecognized arguments: --xyz"
End
Example "with invalid number of positional parameters"
When run command helm kubeconform chart extra
The status should be failure
The output should be blank
The error should include "helm kubeconform: error: unrecognized arguments: extra"
End
Example "with unsupported option --insecure-skip-tls-verify"
When run command helm kubeconform chart --insecure-skip-tls-verify
The status should be failure
The output should be blank
The error should include "Error: unknown flag: --insecure-skip-tls-verify"
End
End

Describe "Run plugin with 'helm template' disabled option"
Parameters
"--output-dir" /tmp
"--release-name" name
End
Example "$1"
When run command helm kubeconform chart "$@"
The status should be failure
The output should be blank
The error should include "helm kubeconform: error: unrecognized arguments: $1"
End
End

Describe "Validate Kubernetes chart"
Example "$K8S_CHART_LOCATION without values"
When run command helm kubeconform "$K8S_CHART_LOCATION"
The status should be success
The output should be blank
The error should be blank
End
Example "$K8S_CHART_LOCATION with debugging enabled"
When run command helm kubeconform --debug "$K8S_CHART_LOCATION"
The status should be success
The output should be blank
The error should include "kubeconform: [DEBUG] Running $HELM_BIN template --debug $K8S_CHART_LOCATION"
The error should include "[debug] CHART PATH: $K8S_CHART_LOCATION"
The error should include "kubeconform: [DEBUG] Running $KUBECONFORM_BIN -debug"
The error should include "using schema found at"
End
End

Describe "Validate Kubernetes chart"
Parameters
"-f"
"--values"
End
Example "$K8S_CHART_LOCATION with valid values $VALID_CHART_VALUES"
When run command helm kubeconform "$K8S_CHART_LOCATION" "$1" "$VALID_CHART_VALUES"
The status should be success
The output should be blank
The error should be blank
End
Example "$K8S_CHART_LOCATION with invalid values $INVALID_CHART_VALUES"
When run command helm kubeconform "$K8S_CHART_LOCATION" "$1" "$INVALID_CHART_VALUES"
The status should be failure
The error should include "expected integer or null, but got string"
The error should include 'Error: plugin "kubeconform" exited with error'
End
End

Describe "Validate local OpenShift chart"
Parameters
"-f"
"--values"
End
Example "$OCP_CHART_LOCATION with valid values $VALID_CHART_VALUES"
When run command helm kubeconform "$K8S_CHART_LOCATION" "$1" "$VALID_CHART_VALUES" --kube-version 4.10 --schema-location "$OCP_SCHEMA_URL"
The status should be success
The output should be blank
The error should be blank
End
Example "$OCP_CHART_LOCATION with invalid values $INVALID_CHART_VALUES"
When run command helm kubeconform "$K8S_CHART_LOCATION" "$1" "$INVALID_CHART_VALUES" --kube-version 4.10 --schema-location "$OCP_SCHEMA_URL"
The status should be failure
The error should include "expected integer or null, but got string"
The error should include 'Error: plugin "kubeconform" exited with error'
End
End
