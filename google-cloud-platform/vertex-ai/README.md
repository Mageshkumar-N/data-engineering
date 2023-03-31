# <center>Provisioning User-Managed Vertex AI Notebook

The script is intended to be used as a startup script for user-managed Vertex AI Notebook instances to provision the AI/ML environment with all the dependencies installed. 

The script installs the required version of Python and creates a <a href="https://realpython.com/python-virtual-environments-a-primer/">virtual environment</a> on top of it where the project dependencies are <a href="https://realpython.com/intro-to-pyenv/">managed</a>. We are using <a href="https://github.com/pyenv/pyenv">pyenv</a> and its plugin <a href="https://github.com/pyenv/pyenv-virtualenv">pyenv-virtualenv</a> for this purpose.

## Table of Contents

> * [Usage](#Usage)
> * [Installing pyenv](#pyenv)
> * [Installing pyenv-virtualenv](#venv)
> * [Installing Project Dependencies](#dependencies)
> * [Development Notes and Issues Faced](#notes)

### Usage <a name="Usage"></a>

1. Create a Cloud Storage Bucket to pass the startup script to <a href="https://cloud.google.com/vertex-ai/docs/workbench/user-managed/create-new#create-with-options">Vertex AI Notebook</a> instance.
2. In the `startup_script.sh` file, set the variable STORAGE_BUCKET, PYTHON_VERSION, and VENV_NAME as required.
3. Update the `requirements.txt` file with the dependencies as required for the AI/ML project.
4. Upload both the files to the Storage Bucket.
5. Create the Notebook instance using the <a href="https://cloud.google.com/sdk/gcloud/reference/notebooks/instances/create">gcloud</a> CLI with the values updated accordingly.

```shell
gcloud notebooks instances create test-instance \
  --vm-image-project=deeplearning-platform-release \
  --vm-image-family=common-cpu-notebooks \
  --machine-type=n1-standard-1 \
  --location=us-central1-a \
  --post-startup-script=gs://vertex_ai/startup_scripts/startup_script.sh \
  --subnet=projects/shared-vpc/regions/us-central1/subnetworks/shared-vpc-dev-subnet-us-central \
  --no-public-ip
 ```

### Installing pyenv <a name="pyenv"></a>

<a href="https://github.com/pyenv/pyenv/wiki#suggested-build-environment">Build dependencies</a> for the Linux distribution is first installed.

```shell
sudo apt update
sudo apt install -y build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev curl \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
```

The <a href="https://github.com/pyenv/pyenv#automatic-installer">automatic installer</a> provided by pyenv is used for installation. 

```shell
curl https://pyenv.run | bash
```

The bash shell environment is then set up for pyenv.

```shell
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
```

```shell
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.profile
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.profile
echo 'eval "$(pyenv init -)"' >> ~/.profile
```

The shell is restarted.

```shell
exec "$SHELL"
```

### Installing pyenv-virtualenv <a name="venv"></a>

pyenv-virtualenv is installed as a plugin to the pyenv.

```shell
GIT_SSL_NO_VERIFY=true git clone https://github.com/pyenv/pyenv-virtualenv.git $(pyenv root)/plugins/pyenv-virtualenv
```

The shell is restarted.

```shell
exec "$SHELL"
```

### Installing Project Dependencies in Virtual Environment <a name=dependencies></a>

The required Python version is installed. 

```shell
pyenv install 3.8.2
```

A virtual environment using the required python version as base is created.

```shell
pyenv virtualenv 3.8.2 modelling
```

The virtual environment is then activated.

```shell
pyenv activate modelling
```

The project dependencies that are added in a requirements.txt file is copied from the Cloud Storage bucket.

```shell
mkdir /home/startup_scripts
cd /home/startup_scripts
gsutil cp gs://vertex_ai/startup-scripts/requirements.txt .
```

Dependencies are installed within the virtual environment.

```shell
pip install -r ./requirements.txt >> logfile.log
```

### Development Notes and Issues Faced <a name="notes"></a>

1. Use <a href="https://www.shellcheck.net/">Spell Check</a> to validate the shell scripts for errors, warnings, and/or suggestions.

2. We are unable to install pyenv using the recommended `curl` command due to `SSL Certificate Problem`.

* To resolve this, an initial attempt is made to run the `curl` command ignoring certificate verification using `curl -k` option. But it is failed as the given curl URL is redirecting to another URL which again fails with the same SSL certificate issue. When an attempt is made to curl the redirected URL, it again fails as the same is redirected again to Github repository.

* Hence, the repository is cloned using `git clone` but passing `GIT_SSL_NO_VERIFY=true` to skip certificate verification.

3. The command `exec "$SHELL"` has caused the script to end abruptly without executing the remaining set of commands that are expected after restarting the shell.

* To resolve this, the entire script is split into multiple scripts each ending with the `exec` command and all the individual scripts are called sequentially from a parent script using the `bash` command. But this did not solve the problem as the parent script/session too is ended abruptly when the child script/session encountered this command.

* Instead of the above command, `source ~/.bashrc` is used to reload the PATH variables of the .bashrc file. This solved the problem of ending the scripts abruptly and helped proceed with the remaining set of commands. The multiple scripts are merged back as a single script to be executed in the same session.

4. Even after sourcing the .bashrc file, `pyenv: command not found` error is thrown.

* It is identified that the PATH variables are set and .bashrc file is executed immediately after cloning the git repository. Hence, `sleep 60` is added to wait for the cloning to be completed. Another point to be noted is that the script without `sleep` command runs successfully when executed from the terminal but fails while running as a startup script.

* When we source the .bashrc file, the PATH variables are not available for the sessions that are started earlier before sourcing the file. Hence, the script fails to run `pyenv` with command not found exception. This is resolved by setting the PATH variables directly to the current session apart from exporting them to the .bashrc and .profile files.

5. The `pyenv` is not available for the jupyter user but only for the root. 

* Since the startup scripts are run as a root user, all our installations and PATH variables refer to the /root directory and unavailable for use by the jupyter users. To resolve this, the installation path of pyenv is changed from `"$HOME/.pyenv` to `/home/jupyter/.pyenv` and the PATH variables are accordingly set in the `/home/jupyter/.bashrc` and `/home/jupyter/.profile` instead of /root.

6. We are now able to create a virtual environment but the installation of dependencies from requirements.txt file is failed because of older version of `pip`.

* pyenv comes with a default pip which is not upgraded even when pyenv is upgraded. To resolve this, pip is upgraded using  `pip install --upgrade pip` before attemting to install project dependencies in the virtual env.

7. Once the virtual env and the requirements are installed, an error `pyenv: cannot rehash: /home/jupyter/.pyenv/shims isn't writable` is thrown on starting the terminal everytime.

* The ownership of the folders `/home/jupyter/.pyenv` and `/home/jupyter/.profile` are changed from root to jupyter.
