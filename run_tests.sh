#!/bin/bash

# Navigate to the main directory and run tests with proper Python path
cd main
PYTHONPATH=. pytest "$@" 