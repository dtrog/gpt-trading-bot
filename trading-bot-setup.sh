#!/bin/bash

# trading-bot-setup.sh — Automate setup for Trading Bot

set -e

# Install dependencies (Ubuntu/Debian)
echo "Installing system packages..."
sudo apt update
sudo apt install -y make build-essential libssl-dev zlib1g-dev   libbz2-dev libreadline-dev libsqlite3-dev curl libncursesw5-dev   xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

# Install pyenv
if ! command -v pyenv &> /dev/null; then
  echo "Installing pyenv..."
  curl https://pyenv.run | bash
  echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
  echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
  echo 'eval "$(pyenv init -)"' >> ~/.bashrc
  echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
  exec "$SHELL"
else
  echo "pyenv is already installed."
fi

# Install and activate Python version
PYTHON_VERSION=3.11.9
ENV_NAME=trading-bot-env

if ! pyenv versions | grep -q $PYTHON_VERSION; then
  echo "Installing Python $PYTHON_VERSION..."
  pyenv install $PYTHON_VERSION
fi

if ! pyenv virtualenvs | grep -q $ENV_NAME; then
  echo "Creating virtualenv $ENV_NAME..."
  pyenv virtualenv $PYTHON_VERSION $ENV_NAME
fi

pyenv activate $ENV_NAME

# Set local version
echo "$ENV_NAME" > .python-version

# Install dependencies
echo "Installing Python requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# Ready
echo "Setup complete. You can now run: python bot.py"