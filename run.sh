#!/bin/bash

app="./App"

mkdir -p Import
mkdir -p Photos

touch process.log
date >> "$app/process.log"

/usr/bin/python "$app/process.py" >> "$app/process.log"

echo '' >> "$app/process.log"
