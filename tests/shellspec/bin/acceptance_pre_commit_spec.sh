# SPDX-FileCopyrightText: © 2023 Mohamed El Morabity
# SPDX-License-Identifier: GPL-3.0-or-later

# shellcheck shell=sh

REPO_DIR=$PWD
PRE_COMMIT_CONF_FILE=$REPO_DIR/pre-commit-test.yaml
PRE_COMMIT_HOME=/tmp/helm-kubeconform

K8S_CHART_DIR=$REPO_DIR/tests/fixtures/chart-k8s
OCP_CHART_DIR=$REPO_DIR/tests/fixtures/chart-ocp
OCP_SCHEMA_URL="https://raw.githubusercontent.com/melmorabity/openshift-json-schemas/main/{{ .NormalizedKubernetesVersion }}-standalone{{ .StrictSuffix }}/{{ .ResourceKind }}.json"
VALID_VALUES_FILE=$REPO_DIR/tests/fixtures/good_values.yaml
INVALID_VALUES_FILE=$REPO_DIR/tests/fixtures/bad_values.yaml

FILE_SEP=/
KUBECONFORM_EXE=kubeconform
PYTHON_VERSION=$(python -c "import sys; sys.stdout.write('{0.major}.{0.minor}'.format(sys.version_info))")

if command -v cygpath >/dev/null; then
    PRE_COMMIT_CONF_FILE=$(cygpath -w "$PRE_COMMIT_CONF_FILE")
    PRE_COMMIT_HOME=$(cygpath -w "$PRE_COMMIT_HOME")

    K8S_CHART_DIR=$(cygpath -w "$K8S_CHART_DIR")
    OCP_CHART_DIR=$(cygpath -w "$OCP_CHART_DIR")
    VALID_VALUES_FILE=$(cygpath -w "$VALID_VALUES_FILE")
    INVALID_VALUES_FILE=$(cygpath -w "$INVALID_VALUES_FILE")
    REPO_DIR=$(cygpath -w "$REPO_DIR")

    # shellcheck disable=SC1003
    FILE_SEP='\'
    KUBECONFORM_EXE=kubeconform.exe

    PYENV_SITE_PACKAGES_SUBDIR="py_env-python$PYTHON_VERSION${FILE_SEP}Lib${FILE_SEP}site-packages"
else
    PYENV_SITE_PACKAGES_SUBDIR="py_env-python$PYTHON_VERSION/lib/python$PYTHON_VERSION/site-packages"
fi

export PRE_COMMIT_HOME

setUpPreCommit() {
    cat <<EOF >"$1"
---
repos:
  - repo: $REPO_DIR
    rev: $(git rev-parse HEAD)
    hooks:
      - id: $2
        args: ${3:-[]}
EOF
}

cleanAll() {
    rm -rf "$PRE_COMMIT_HOME" "$PRE_COMMIT_CONF_FILE"
}

Describe "Run pre-commit hook helm-kubeconform"
Before cleanAll
AfterAll cleanAll
Example "without argument"
{
    setUpPreCommit "$PRE_COMMIT_CONF_FILE" helm-kubeconform
}
When run command pre-commit run -c "$PRE_COMMIT_CONF_FILE" helm-kubeconform --files
The status should be success
The output should match pattern "*Helm charts validation*(no files to check)Skipped*"
The error should be blank
The path "$PRE_COMMIT_HOME/repo"*"/$KUBECONFORM_EXE" should not be file
End
Example "with valid Kubernetes chart files in $K8S_CHART_DIR"
{
    setUpPreCommit "$PRE_COMMIT_CONF_FILE" helm-kubeconform
}
When run command pre-commit run -c "$PRE_COMMIT_CONF_FILE" helm-kubeconform --files "$K8S_CHART_DIR${FILE_SEP}values.yaml" "$K8S_CHART_DIR${FILE_SEP}templates${FILE_SEP}_helpers.tpl"
The status should be success
The output should match pattern "*Helm charts validation*Passed*"
The error should be blank
The path "$PRE_COMMIT_HOME/repo"*"/$PYENV_SITE_PACKAGES_SUBDIR/helm_kubeconform/$KUBECONFORM_EXE" should be executable
End
Example "with invalid Kubernetes chart files in $OCP_CHART_DIR"
{
    setUpPreCommit "$PRE_COMMIT_CONF_FILE" helm-kubeconform
}
When run command pre-commit run -c "$PRE_COMMIT_CONF_FILE" helm-kubeconform --files "$OCP_CHART_DIR${FILE_SEP}values.yaml" "$OCP_CHART_DIR${FILE_SEP}templates${FILE_SEP}_helpers.tpl"
The status should be failure
The output should include "could not find schema for DeploymentConfig"
The output should include "kubeconform: [ERROR] Helm chart ${OCP_CHART_DIR#"$REPO_DIR$FILE_SEP"} validation failed"
The error should be blank
End
Example "with valid OpenShift chart files in $OCP_CHART_DIR"
{
    setUpPreCommit "$PRE_COMMIT_CONF_FILE" helm-kubeconform "['--kube-version', '4.10', '--schema-location', '$OCP_SCHEMA_URL']"
}
When run command pre-commit run -c "$PRE_COMMIT_CONF_FILE" helm-kubeconform --files "$OCP_CHART_DIR${FILE_SEP}values.yaml" "$OCP_CHART_DIR${FILE_SEP}templates${FILE_SEP}_helpers.tpl"
The status should be success
The output should match pattern "*Helm charts validation*Passed*"
The error should be blank
End
End

Describe "Run pre-commit hook helm-kubeconform-values"
Before cleanAll
AfterAll cleanAll
Example "without argument"
{
    setUpPreCommit "$PRE_COMMIT_CONF_FILE" helm-kubeconform-values
}
When run command pre-commit run -c "$PRE_COMMIT_CONF_FILE" helm-kubeconform-values --files
The status should be success
The output should match pattern "*Helm chart values validation*(no files to check)Skipped*"
The error should be blank
The path "$PRE_COMMIT_HOME/repo"*"/$PYENV_SITE_PACKAGES_SUBDIR/helm_kubeconform/$KUBECONFORM_EXE" should not be file
End
Example "with Kubernetes chart $K8S_CHART_DIR and valid values file $VALID_VALUES_FILE"
{
    setUpPreCommit "$PRE_COMMIT_CONF_FILE" helm-kubeconform-values "['$K8S_CHART_DIR']"
}
When run command pre-commit run -c "$PRE_COMMIT_CONF_FILE" helm-kubeconform-values --files "$VALID_VALUES_FILE"
The status should be success
The output should match pattern "*Helm chart values validation*Passed*"
The error should be blank
The path "$PRE_COMMIT_HOME/repo"*"/$PYENV_SITE_PACKAGES_SUBDIR/helm_kubeconform/$KUBECONFORM_EXE" should be executable
End
Example "with Kubernetes chart $K8S_CHART_DIR and invalid values file $INVALID_VALUES_FILE"
{
    setUpPreCommit "$PRE_COMMIT_CONF_FILE" helm-kubeconform-values "['$K8S_CHART_DIR']"
}
When run command pre-commit run -c "$PRE_COMMIT_CONF_FILE" helm-kubeconform-values --files "$INVALID_VALUES_FILE"
The status should be failure
The output should include "expected integer or null, but got string"
The output should include "kubeconform: [ERROR] Helm values file ${INVALID_VALUES_FILE#"$REPO_DIR$FILE_SEP"} validation failed"
The error should be blank
End
Example "with OpenShift chart $OCP_CHART_DIR and valid values file $VALID_VALUES_FILE"
{
    setUpPreCommit "$PRE_COMMIT_CONF_FILE" helm-kubeconform-values "['$K8S_CHART_DIR', '--kube-version', '4.10', '--schema-location', '$OCP_SCHEMA_URL']"
}
When run command pre-commit run -c "$PRE_COMMIT_CONF_FILE" helm-kubeconform-values --files "$VALID_VALUES_FILE"
The status should be success
The output should match pattern "*Helm chart values validation*Passed*"
The error should be blank
End
End
