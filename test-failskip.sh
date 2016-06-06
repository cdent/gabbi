#!/bin/bash -e
# Run the tests and confirm that the stuff we expect to skip or fail
# does.

# this would be somewhat less complex in bash4..
shopt -s nocasematch
[[ "${GABBI_SKIP_NETWORK:-false}" == "true" ]] && SKIP=7 || SKIP=2
shopt -u nocasematch

GREP_FAIL_MATCH='expected failures=12,'
GREP_SKIP_MATCH="skipped=$SKIP,"
GREP_UXSUC_MATCH='unexpected successes=1'
# This skip is always 2 because the pytest tests don't
# run the live tests.
PYTEST_MATCH='2 skipped, 12 xfailed'

python setup.py testr && \
    for match in "${GREP_FAIL_MATCH}" "${GREP_UXSUC_MATCH}" "${GREP_SKIP_MATCH}"; do
        testr last --subunit | subunit2pyunit 2>&1 | \
            grep "${match}"
    done

# Make sure pytest failskips too
py.test gabbi | grep "$PYTEST_MATCH"
