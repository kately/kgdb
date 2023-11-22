#!/bin/bash
base_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

echo "base_path: ${base_path}"

# src dir
src_dir="${base_path}/../src"

# run python linter check
flake8 

# run app
python3 ${src_dir}/kgraph/kg.py
