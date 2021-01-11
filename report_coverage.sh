#!/bin/bash

function test_files() {
  find "$1" -name '*.py' -print
}

# The following commands require coveragee to be installed. i.e. pip install coverage  (or pip3 install coverage)
coverage run -m unittest $(test_files tests)
coverage run -m unittest $(test_files tests_flstudio)
coverage report
coverage html
echo "Open htmlcov/index.html in browser."
echo "file:///$(pwd)/htmlcov/index.html"
