#!/usr/bin/env bash

if [[ ! -d ./venv ]]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip-compile
pip-sync
jupyter serverextension enable --py jupyterlab --sys-prefix

# Allow 4 letter currency codes for cryptocurrency
sed -i 's/^REGEX_CURRENCY_CODE = .*/REGEX_CURRENCY_CODE = re.compile("^[A-Z]+$")/' venv/lib/python*/site-packages/money/money.py
