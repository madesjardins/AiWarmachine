#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)
export AIWARMACHINE_PYTHON_DIR=$SCRIPT_DIR/python
export PYTHONPATH=$PYTHONPATH:$AIWARMACHINE_PYTHON_DIR
echo $AIWARMACHINE_PYTHON_DIR
python $AIWARMACHINE_PYTHON_DIR/launch_aiwarmachine.py
