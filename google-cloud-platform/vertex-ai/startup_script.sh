#!/bin/bash

STORAGE_BUCKET="vertex_ai/startup_scripts"
PYTHON_VERSION=3.8.2
VENV_NAME="modelling"

mkdir /home/startup_scripts
cd /home/startup_scripts

{
echo "---------Started Startup Script at $(date)---------"

echo "---------Copying Startup Scripts from Cloud Storage---------"

gsutil -m cp "gs://${STORAGE_BUCKET}/*" /home/startup_scripts

echo "---------Installing Build Dependencies for pyenv---------"

sudo apt update
sudo apt install -y build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev curl \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

echo "---------Cloning the pyenv git repository---------"

GIT_SSL_NO_VERIFY=true git clone https://github.com/pyenv/pyenv.git /home/jupyter/.pyenv

sleep 60

echo "---------Setting up the bash shell environment for pyenv---------"
} >> logfile.log 2>&1

{
echo 'export PYENV_ROOT=/home/jupyter/.pyenv'
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"'
echo 'eval "$(pyenv init -)"'
} >> /home/jupyter/.bashrc

{
echo 'export PYENV_ROOT=/home/jupyter/.pyenv'
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"'
echo 'eval "$(pyenv init -)"'
} >> /home/jupyter/.profile

chown jupyter:jupyter /home/jupyter/.profile

export PYENV_ROOT=/home/jupyter/.pyenv
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

{
source /home/jupyter/.bashrc

echo "-----Current Python Version-----$(pyenv versions)"

echo "---------Installing pyenv-virtualenv as a plugin---------"

GIT_SSL_NO_VERIFY=true git clone https://github.com/pyenv/pyenv-virtualenv.git "$(pyenv root)/plugins/pyenv-virtualenv"

sleep 60

chown -R jupyter:jupyter /home/jupyter/.pyenv/

source /home/jupyter/.bashrc

echo "---------Installing Python version 3.8.2---------"

pyenv install "${PYTHON_VERSION}"

echo "---------Creating Virtual Environment---------"

pyenv virtualenv "${PYTHON_VERSION}" "${VENV_NAME}"

echo "---------Activating the Virtual Environment---------"

pyenv activate "${VENV_NAME}"

echo "-----Current Python Version-----$(pyenv versions)"

echo "---------Installing Project Dependencies from requirements.txt---------"

pip install --upgrade pip

pip install -r /home/startup_scripts/requirements.txt

echo "---------Ended Startup Script at $(date)---------"
} >> logfile.log 2>&1
