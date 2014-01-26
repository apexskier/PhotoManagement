#!/bin/bash

app="./App"
cwd=$(pwd)

mkdir -p Import
mkdir -p Photos

python3 "$app/process.py" -i "$cwd/Import" -d "$cwd/Photos" -r
