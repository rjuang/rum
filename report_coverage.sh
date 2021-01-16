#!/bin/bash

function test_files() {
  find "$1" -name '*.py' -print
}

rm -fr htmlcov
# The following commands require coveragee to be installed. i.e. pip install coverage  (or pip3 install coverage)
coverage erase
sleep 3
coverage run -a -m unittest $(test_files tests)
coverage run -a -m unittest $(test_files tests_flstudio)
coverage report --omit='tests/**/*','tests_flstudio/**/*','**/**/__init__.py','tests_flstudio/*','tests/*'
coverage html --omit='tests*','*/__init__.py'

echo "Open htmlcov/index.html in browser."
echo "file:///$(pwd)/htmlcov/index.html"
