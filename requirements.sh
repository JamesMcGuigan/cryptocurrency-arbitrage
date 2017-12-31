#!/usr/bin/env bash
set -x

if [[ ! -d ./venv ]]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip-compile
pip-sync
jupyter serverextension enable --py jupyterlab --sys-prefix