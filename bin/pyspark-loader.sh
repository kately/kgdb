#!/bin/bash
script_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
app_home=$(pwd)

echo "++++++++++"
echo "app_home: ${app_home}"
echo "script_path: ${script_path}"
echo "++++++++++"

SPARK_VERSION=3.4.0

cd ${app_home}
export PYTHONPATH="${app_home}/src"

# run python linter check
flake8 

# dependencies
pkgs="org.apache.spark:spark-sql-kafka-0-10_2.12:${SPARK_VERSION}"

# run app
spark-submit --packages "${pkgs}" src/spark/loader.py
