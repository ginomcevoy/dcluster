# dcluster

*Create and manage Docker clusters, optionally run Ansible on the cluster.*

## Features

* Creates a docker network, ensures that the network subnet is available.
* Uses a template to create a Dockerfile for docker-compose, then calls docker-compose to instantiate containers attached to the docker network.
* Can choose a cluster "flavor" from existing templates at /usr/share/dcluster/flavors.
* The cluster "flavors" can be customized and extended to use specific containers and environment variables. The user may add more flavors.

## Usage

* Create a cluster of 2 compute nodes identified by "my\_cluster":

  ```dcluster create my_cluster 2```

* Create a cluster with a custom flavor:

  ```dcluster create -f slurm slurm_cluster 3```

* List current clusters:

  ```dcluster list```

* Details about a cluster:

  ```dcluster show my_cluster```

* Stop a cluster (will stop containers and leave the network active):

  ```dcluster stop my_cluster```

* Start a previously stopped cluster: 

  ```dcluster start my_cluster```

* Remove a cluster (will remove containers and  the network):

  ```dcluster rm my_cluster```

## Requirements

* Docker 17.06.0+

* docker-compose 1.25.0+

  ```sudo curl -L "https://github.com/docker/compose/releases/download/1.25.0/docker-compose-$(uname -m)" -o /usr/bin/docker-compose && chmod +x /usr/bin/docker-compose```

  
* docker python API 4.0.0+

  ```pip install --user docker```

Note: use ```dcluster init``` to attempt to download docker API and docker-compose automatically.

## Running the tests

Run the binary supplied in the source code, requires `pytest`. Note: a development environment is assumed,
where the configuration files have not been yet deployed to the target filesystem.

```bash
./scripts/dcluster-test --pytest
```

The tests may be run after the installation via RPM as follows:

```bash
pytest -v dcluster/tests
```

Note: the tests may fail if the parameters of the original configuration are changed.

## Packaging

Please use the provided script to generate the RPMs in addition to the egg-info package:

```bash
./scripts/build-rpm.sh
```

You may need to install requirements for setup beforehand, using 

```bash
pip install --user -r deployment/requirements.txt
```

## Generating the documentation page

This project uses Sphinx and AutoAPI to generate its documentation page.

```bash
cd docs && make html
```

You may need to install requirements for docs beforehand, using 

```bash
pip install --user -r deployment/requirements-docs.txt
```

## (TODO) Generating the test reports

The following commands generate the html test report and the associated badge. 

```bash
pytest --junitxml=junit.xml -v runitmockit/tests/
ant -f ci_tools/generate-junit-html.xml
python ci_tools/generate-junit-badge.py
```

### Merging pull requests with edits - memo

As explained in github ('get commandline instructions'):

```bash
git checkout -b <git_name>-<feature_branch> master
git pull https://github.com/ginomcevoy/dcluster.git <feature_branch> --no-commit --ff-only
```

if the second step does not work, do a normal auto-merge (do not use **rebase**!):

```bash
git pull https://github.com/ginomcevoy/dcluster.git <feature_branch> --no-commit
```
