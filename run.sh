#!/bin/bash

app="./App"

mkdir -p Import
mkdir -p Photos

/usr/bin/python "$app/process.py"
