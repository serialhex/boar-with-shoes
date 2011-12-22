#!/bin/sh

macrotests/macrotest.sh || { echo "Macrotests failed"; exit 1; }
python blobrepo/tests/test_repository.py || { echo "Blobrepo unittests failed"; exit 1; }
python tests/test_workdir.py || { echo "Workdir unittests failed"; exit 1; }