#/bin/bash

function test_files() {
  find "$1" -name '*.py' -print
}

python3 -m unittest $(test_files tests)
python3 -m unittest $(test_files tests_flstudio)

