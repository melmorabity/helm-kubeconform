# Kubeconform Helm plugin

[![Linting](https://github.com/melmorabity/helm-kubeconform/actions/workflows/linting.yml/badge.svg)](https://github.com/melmorabity/helm-kubeconform/actions/workflows/linting.yml) [![Unit tests](https://github.com/melmorabity/helm-kubeconform/actions/workflows/unit_tests.yml/badge.svg)](https://github.com/melmorabity/helm-kubeconform/actions/workflows/unit_tests.yml) [![codecov](https://codecov.io/gh/melmorabity/helm-kubeconform/branch/main/graph/badge.svg)](https://codecov.io/gh/melmorabity/helm-kubeconform) [![Acceptance tests](https://github.com/melmorabity/helm-kubeconform/actions/workflows/acceptance_tests.yml/badge.svg)](https://github.com/melmorabity/helm-kubeconform/actions/workflows/acceptance_tests.yml)

helm-kubeconform is a [Helm](https://helm.sh/) plugin for validating Helm charts against the Kubernetes schemas, using [Kubeconform](https://github.com/yannh/kubeconform/).

This plugin was inspired by the [Kubeval Helm plugin](https://github.com/instrumenta/helm-kubeval/).

## Installation

Install the latest version of the plugin using the built-in plugin manager:

```console
helm plugin install https://github.com/melmorabity/helm-kubeconform --version 0.6.6.1
```

The installer will download and install the Kubeconform binary available for the running platform. As a result, this plugin only supports platforms for which a binary is available [on the Kubeconform release page](https://github.com/yannh/kubeconform/releases).

> **Warning**
>
> * This plugin supports Helm 3.10 or later
> * This plugin requires Python 3.8 or later
> * `curl` or `wget` are required for installation.
> * Since Helm plugin installation relies on the `sh` interpreter, it is only supported on Microsoft Windows through [Cywgin](https://www.cygwin.com/) or [MSYS2](https://www.msys2.org/).

## Usage

The plugin runs `helm template` and passes its output to Kubeconform. The plugin accepts most flags from [`helm template`](https://helm.sh/docs/helm/helm_template/), as well as most flags from [Kubeconform](https://github.com/yannh/kubeconform#Usage). The plugin will automatically pass Kubeconform options to Kubeconform, and all others to Helm.

```console
helm kubeconform chart [flags]

positional arguments:
  chart                 chart

options:
  -h, --help            show this help message and exit

Helm template options:
  -a strings, --api-versions strings
                        Kubernetes api versions used for Capabilities.APIVersions
  --atomic              if set, the installation process deletes the installation on failure. The --wait flag will be set automatically if --atomic is used
  --ca-file string      verify certificates of HTTPS-enabled servers using this CA bundle
  --cert-file string    identify HTTPS client using this SSL certificate file
  --create-namespace    create the release namespace if not present
  --dependency-update   update dependencies if they are missing before installing the chart
  --description string  add a custom description
  --devel               use development versions, too. Equivalent to version '>0.0.0-0'. If --version is set, this is ignored
  --disable-openapi-validation
                        if set, the installation process will not validate rendered templates against the Kubernetes OpenAPI Schema
  --dry-run             simulate an install
  --enable-dns          enable DNS lookups when rendering templates
  --force               force resource updates through a replacement strategy
  -g, --generate-name   generate the name (and omit the NAME parameter)
  --include-crds        include CRDs in the templated output
  --is-upgrade          set .Release.IsUpgrade instead of .Release.IsInstall
  --key-file string     identify HTTPS client using this SSL key file
  --keyring string      location of public keys used for verification (default "~/.gnupg/pubring.gpg")
  --kube-version string Kubernetes version used for Capabilities.KubeVersion
  --name-template string
                        specify template used to name the release
  --no-hooks            prevent hooks from running during install
  --pass-credentials    pass credentials to all domains
  --password string     chart repository password where to locate the requested chart
  --post-renderer postRendererString
                        the path to an executable to be used for post rendering. If it exists in $PATH, the binary will be used, otherwise it will try to look for the executable at the given path
  --post-renderer-args postRendererArgsSlice
                        an argument to the post-renderer (can specify multiple) (default [])
  --render-subchart-notes
                        if set, render subchart notes along with the parent
  --replace             re-use the given name, only if that name is a deleted release which remains in the history. This is unsafe in production
  --repo string         chart repository url where to locate the requested chart
  --set stringArray     set values on the command line (can specify multiple or separate values with commas: key1=val1,key2=val2)
  --set-file stringArray
                        set values from respective files specified via the command line (can specify multiple or separate values with commas: key1=path1,key2=path2)
  --set-json stringArray
                        set JSON values on the command line (can specify multiple or separate values with commas: key1=jsonval1,key2=jsonval2)
  --set-literal stringArray
                        set a literal STRING value on the command line
  --set-string stringArray
                        set STRING values on the command line (can specify multiple or separate values with commas: key1=val1,key2=val2)
  -s stringArray, --show-only stringArray
                        only show manifests rendered from the given templates
  --skip-crds           if set, no CRDs will be installed. By default, CRDs are installed if not already present
  --skip-tests          skip tests from templated output
  --timeout duration    time to wait for any individual Kubernetes operation (like Jobs for hooks) (default 5m0s)
  --username string     chart repository username where to locate the requested chart
  --validate            validate your manifests against the Kubernetes cluster you are currently pointing at. This is the same validation performed on an install
  -f strings, --values strings
                        specify values in a YAML file or a URL (can specify multiple)
  --verify              verify the package before using it
  --version string      specify a version constraint for the chart version to use. This constraint can be a specific tag (e.g. 1.1.1) or it may reference a valid range (e.g. ^2.0.0). If this is not specified, the latest version is used
  --wait                if set, will wait until all Pods, PVCs, Services, and minimum number of Pods of a Deployment, StatefulSet, or ReplicaSet are in a ready state before marking the release as successful. It will wait for as long as --timeout
  --wait-for-jobs       if set and --wait enabled, will wait until all Jobs have been completed before marking the release as successful. It will wait for as long as --timeout
  --burst-limit int     client-side default throttling limit (default 100)
  --debug               enable verbose output
  --kube-apiserver string
                        the address and the port for the Kubernetes API server
  --kube-as-group stringArray
                        group to impersonate for the operation, this flag can be repeated to specify multiple groups.
  --kube-as-user string
                        username to impersonate for the operation
  --kube-ca-file string
                        the certificate authority file for the Kubernetes API server connection
  --kube-context string
                        name of the kubeconfig context to use
  --kube-insecure-skip-tls-verify
                        if true, the Kubernetes API server's certificate will not be checked for validity. This will make your HTTPS connections insecure
  --kube-tls-server-name string
                        server name to use for Kubernetes API server certificate validation. If it is not provided, the hostname used to contact the server is used
  --kube-token string   bearer token used for authentication
  --kubeconfig string   path to the kubeconfig file
  -n string, --namespace string
                        namespace scope for this request (default "default")
  --registry-config string
                        path to the registry config file (default "~/.config/helm/registry/config.json")
  --repository-cache string
                        path to the file containing cached repository indexes (default "~/.cache/helm/repository")
  --repository-config string
                        path to the file containing repository names and URLs (default "~/.config/helm/repositories.yaml")

Kubeconform options:
  --cache string        cache schemas downloaded via HTTP to this folder
  --exit-on-error       immediately stop execution when the first error is encountered
  --ignore-missing-schemas
                        skip files with missing schemas instead of failing
  --skip-tls-verify     disable verification of the server's SSL certificate. This will make your HTTPS connections insecure
  --goroutines int      number of goroutines to run concurrently (default 4)
  --output string       output format - json, junit, pretty, tap, text (default "text")
  --reject string       comma-separated list of kinds or GVKs to reject
  --schema-location value
                        override schemas location search path (can be specified multiple times)
  --skip string         comma-separated list of kinds or GVKs to ignore
  --strict              disallow additional properties not in schema or duplicated keys
  --summary             print a summary at the end (ignored for junit output)
  --verbose             print results for all resources (ignored for tap and junit output)
```

As an example of usage, here is `helm kubeconform` running against a Helm chart.

```console
$ helm kubeconform tests/fixtures/chart-k8s/
$ echo $?
0
```

```console
$ helm kubeconform tests/fixtures/chart-k8s/ --values tests/fixtures/good_values.yaml --verbose --summary
stdin - ServiceAccount release-name-chart-k8s is valid
stdin - Service release-name-chart-k8s is valid
stdin - Deployment release-name-chart-k8s is valid
Summary: 3 resources found parsing stdin - Valid: 3, Invalid: 0, Errors: 0, Skipped: 0
```

```console
$ helm kubeconform tests/fixtures/chart-k8s/ --values tests/fixtures/bad_values.yaml --verbose --summary
stdin - ServiceAccount release-name-chart-k8s is valid
stdin - Service release-name-chart-k8s is valid
stdin - Deployment release-name-chart-k8s is invalid: problem validating schema. Check JSON formatting: jsonschema: '/spec/replicas' does not validate with https://raw.githubusercontent.com/yannh/kubernetes-json-schema/master/master-standalone/deployment-apps-v1.json#/properties/spec/properties/replicas/type: expected integer or null, but got string
Summary: 3 resources found parsing stdin - Valid: 2, Invalid: 1, Errors: 0, Skipped: 0
Error: plugin "kubeconform" exited with error
```

The plugin supports schema location override, [just like Kubeconform](https://github.com/yannh/kubeconform#Overriding-schemas-location). CRDs can be passed to the plugin using the `--schema-location` option, as well as OpenShift JSON schemas:

```console
$ helm kubeconform tests/fixtures/chart-ocp/ --schema-location 'https://raw.githubusercontent.com/melmorabity/openshift-json-schemas/main/v4.14-standalone{{ .StrictSuffix }}/{{ .ResourceKind }}.json' --verbose --summary
stdin - Service release-name-test-ocp is valid
stdin - DeploymentConfig release-name-test-ocp is valid
Summary: 2 resources found parsing stdin - Valid: 2, Invalid: 0, Errors: 0, Skipped: 0
```

## Pre-commit

This project provides two hooks for [pre-commit](https://pre-commit.com/) that you can use to automatically lint Helm charts before committing them to your repository:

* `helm-kubeconform`: to validate Helm chart files
* `helm-kubeconform-values`: to validate values files against a given Helm chart

### `helm-kubeconform`

This hook validates files that are part of one or more Helm charts in a Git repository.

To enable the hook, add the following lines to the `repos` list in the project's `.pre-commit-config.yaml` file:

```yaml
repos:
  - repo: https://github.com/melmorabity/helm-kubeconform
    rev: 0.6.6.1
    hooks:
      - id: helm-kubeconform
```

This hook supports all options provided by the Helm plugin (using the `args` key). If the charts are located in a sub-directory, it is recommended to set up the `files` key to limit the validation to that specific directory, resulting in improved performance:

```yaml
repos:
  - repo: https://github.com/melmorabity/helm-kubeconform
    rev: 0.6.6.1
    hooks:
      - id: helm-kubeconform
        files: ^tests/fixtures/chart-.+?/
```

### `helm-kubeconform-values`

This hook validates values files against a Helm chart, which can be especially helpful for charts from a remote repository.

To enable the hook, add the following lines to the `repos` list in the project's `.pre-commit-config.yaml` file:

```yaml
repos:
  - repo: https://github.com/melmorabity/helm-kubeconform
    rev: 0.6.6.1
    hooks:
      - id: helm-kubeconform-values
```

This hook supports all options provided by the Helm plugin but requires a chart to be passed as argument (using the `args` key). However, it is strongly recommended to set up the `files` key to restrict validation to actual values files since the hook checks all YAML/JSON files in the repository by default:

```yaml
repos:
  - repo: https://github.com/melmorabity/helm-kubeconform
    rev: 0.6.6.1
    hooks:
      - id: helm-kubeconform-values
        args:
          - tests/fixtures/chart-k8s
        files: ^tests/fixtures/.+?_values\.yaml$
```

## Copyright and license

© 2023 Mohamed El Morabity

Licensed under the [GNU GPL, version 3.0 or later](LICENSE).
