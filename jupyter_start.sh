#!/usr/bin/env bash

source venv/bin/activate
jupyter lab &
echo $! > jupyter.pid