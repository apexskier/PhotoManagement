#!/bin/bash

mkdir -p Import
mkdir -p Photos

touch process.log
date >> process.log

/usr/bin/python process.py >> process.log

echo '' >> process.log
