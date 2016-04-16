#!/bin/bash -e
# Run the tests and confirm that the stuff we expect to skip or fail
# does.

GREP_FAIL_MATCH='expected failures=11,'
GREP_SKIP_MATCH='skipped=2,'
GREP_UXSUC_MATCH='unexpected successes=1'
PYTEST_MATCH='2 skipped, 11 xfailed'

python setup.py testr && \
    for match in "${GREP_FAIL_MATCH}" "${GREP_UXSUC_MATCH}" "${GREP_SKIP_MATCH}"; do
        testr last --subunit | subunit2pyunit 2>&1 | \
            grep "${match}"
    done

# Make sure pytest failskips too
py.test gabbi | grep "$PYTEST_MATCH"
