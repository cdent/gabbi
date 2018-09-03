#!/bin/bash -e
# Run the tests and confirm that the stuff we expect to skip or fail
# does.

# this would be somewhat less complex in bash4..
shopt -s nocasematch
[[ "${GABBI_SKIP_NETWORK:-false}" == "true" ]] && SKIP=7 || SKIP=2
shopt -u nocasematch

FAILS=12

GREP_FAIL_MATCH="expected failures=$FAILS"
GREP_SKIP_MATCH="skipped=$SKIP,"
# This skip is always 2 because the pytest tests don't
# run the live tests.
PYTEST_MATCH="$SKIP skipped, $FAILS xfailed"

stestr run && \
    for match in "${GREP_FAIL_MATCH}" "${GREP_SKIP_MATCH}"; do
        stestr last --subunit | subunit2pyunit 2>&1 | \
            grep "${match}"
    done

# Make sure pytest failskips too
py.test gabbi | grep "$PYTEST_MATCH"
