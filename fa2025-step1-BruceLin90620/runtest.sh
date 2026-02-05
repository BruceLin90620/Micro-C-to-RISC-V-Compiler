#!/bin/bash

for f in $(ls tests/*.uC | sort -V); do
    echo "=== Running $f ==="
    if ! env PYTHONPATH=build/ python3 python/compiler.py "$f"; then
        echo "[ERROR] $f fail"
    fi
    echo ""
done
