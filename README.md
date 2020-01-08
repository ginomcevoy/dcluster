# dcluster

*Create and manage Docker clusters, optionally run Ansible on the cluster.*

## Requirements

docker-compose

```sudo curl -L "https://github.com/docker/compose/releases/download/1.25.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/bin/docker-compose && chmod +x /usr/bin/docker-compose
```

## Running the tests

Run the binary supplied in the source code, requires `pytest`. Note: a development environment is assumed,
where the configuration files have not been yet deployed to the target filesystem.

```bash
PYTHONPATH=. DCLUSTER_DEV=true pytest -v dcluster/tests
```

The tests may be run after the installation via RPM as follows:

```bash
pytest -v dcluster/tests
```

Note: the tests may fail if the parameters of the original configuration are changed.

## Packaging

Please use the provided script to generate the RPMs in addition to the egg-info package:

```bash
./build-rpm.sh
```

(TODO) You may need to install requirements for setup beforehand, using 

```bash
pip install -r ci_tools/requirements-setup.txt
```

## (TODO) Generating the documentation page

This project uses `mkdocs` to generate its documentation page. Therefore building a local copy of the doc page may be done using:

```bash
mkdocs build -f docs/mkdocs.yml
```

(TODO) You may need to install requirements for doc beforehand, using 

```bash
pip install -r ci_tools/requirements-doc.txt
```

## Generating the test reports

The following commands generate the html test report and the associated badge. 

```bash
pytest --junitxml=junit.xml -v runitmockit/tests/
ant -f ci_tools/generate-junit-html.xml
python ci_tools/generate-junit-badge.py
```

### Merging pull requests with edits - memo

Ax explained in github ('get commandline instructions'):

```bash
git checkout -b <git_name>-<feature_branch> master
git pull https://github.com/ginomcevoy/dcluster.git <feature_branch> --no-commit --ff-only
```

if the second step does not work, do a normal auto-merge (do not use **rebase**!):

```bash
git pull https://github.com/ginomcevoy/dcluster.git <feature_branch> --no-commit
```

Finally review the changes, possibly perform some modifications, and commit.
