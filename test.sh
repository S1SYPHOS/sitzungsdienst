#!/bin/bash

# Iterate over all PDF files ..
for file in test/*.pdf; do
    # .. testing for parsing errors
    echo "Testing $file .."
    python main.py "$file"
done
