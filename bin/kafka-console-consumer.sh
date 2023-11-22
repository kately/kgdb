#!/bin/bash
script_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
app_home=$(pwd)

echo "++++++++++"
echo "app_home: ${app_home}"
echo "script_path: ${script_path}"
echo "++++++++++"

cd ${app_home}
export PYTHONPATH="${app_home}/src"

# run python linter check
# flake8 

# run app
python3 src/kafka/consumer.py "$@"
