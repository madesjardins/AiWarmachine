#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)
export AIWARMACHINE_PYTHON_DIR=$SCRIPT_DIR/python
export TITLES_DIRPATH=$SCRIPT_DIR/titles
export PYTHONPATH=$PYTHONPATH:$AIWARMACHINE_PYTHON_DIR:$TITLES_DIRPATH
export TEMP_DIRPATH=$SCRIPT_DIR/temp
export PIPER_DIRPATH=$SCRIPT_DIR/apps/piper
echo $AIWARMACHINE_PYTHON_DIR
python $AIWARMACHINE_PYTHON_DIR/launch_aiwarmachine.py
