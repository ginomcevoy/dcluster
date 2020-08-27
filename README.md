# dcluster

*Create and manage Docker clusters, optionally run Ansible on the cluster.*

## Features

* Creates a docker network, ensures that the network subnet is available.
* Uses a template to create a Dockerfile for docker-compose, then calls docker-compose to instantiate containers attached to the docker network.
* The containers are spinned up with an SSH server and tini (--init) for proper zombie process reaping.
* Can choose a cluster "flavor" from existing templates at /usr/share/dcluster/flavors.
* The cluster "flavors" can be customized and extended to use specific containers and environment variables. The user may add more cluster flavors.
* Example:

  ```
  $ dcluster create --flavor simple my_cluster 2
  (...)

  $ dcluster show my_cluster

Cluster: my_cluster
------------------------
Network: 172.30.0.0/24

  hostname       ip_address      container
  ------------------------------------------------
  head           172.30.0.253    my_cluster-head
  node001        172.30.0.1      my_cluster-node001
  node002        172.30.0.2      my_cluster-node002

  $ dcluster ssh my_cluster head
  [root@head ~]#
  ```

## Requirements

* Docker 17.06.0+

* docker-compose 1.25.0+ with template 3.7 (support for 'init' variable)

  ```sudo curl -L "https://github.com/docker/compose/releases/download/1.25.0/docker-compose-$(uname -m)" -o /usr/bin/docker-compose && chmod +x /usr/bin/docker-compose```

* docker python API 4.0.0+

  ```pip install --user docker```

Note: use ```dcluster init``` to attempt to download docker API and docker-compose automatically.

## Limitations

* Tested only on CentOS 7 and CentOS 8 (Fedora and RHEL should work), also not in a clean environment yet (TODO try this in a clean VM!)
  The default packaging (non-RPM) is not supported yet!

* The RPMs can be installed but not all requirements are met. dcluster also requires docker API (pip install docker) and docker-compose.
  As a workaround, dcluster can try to install these additional requirements (requires internet access) using:
  ```
  dcluster init
  ```

* The container image requires an installation of an SSH server that supports root access (PermitRootLogin yes).
  Here is an example to install the SSH server for a base CentOS image.
  From the host, create a container based on a base CentOS image (7.7 as example):
  ```
  docker run -it --name dcluster-with-ssh centos:7.7.1908
  ```

  This should open the container terminal, install SSH server and create host keys:
  ```
  yum install -y openssh-server
  ssh-keygen -A
  ```

  Commit this image to docker in the host and clean up:
  ```
  docker commit dcluster-with-ssh centos:7.7.1908-ssh
  docker stop dcluster-with-ssh
  docker rm dcluster-with-ssh
  ```

* The default flavor (simple) is pointing to centos:7.7.1908-ssh, which immediately fails if this image is not available. TODO let this be a variable managed by configuration, and that the user can override using --image

* User-provided Ansible playbooks will be supported very soon...

## Usage

Note: Read the limitations and requirements before trying it out!

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

Note: more requirements may be missing, TODO!

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
