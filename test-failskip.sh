#!/bin/bash
# Run the tests and confirm that the stuff we expect to skip or fail
# does.

GREP_FAIL_MATCH='expected failures=5'
GREP_SKIP_MATCH='skips=2'

python setup.py testr && \
    testr last --subunit | subunit2pyunit 2>&1 | \
    grep "${GREP_FAIL_MATCH}" && \
    testr last | grep "${GREP_SKIP_MATCH}"
