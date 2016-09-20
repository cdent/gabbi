#!/bin/bash
# Run a test which is limited to just one request from a file that
# contains many requests and confirm that only one was run and that
# it did actually run.
#
# This covers a situation where the change of intercepts to fixtures
# broke limiting tests and we never knew.

GREP_TEST_MATCH='tests.test_intercept.self_checklimit.test_request ... ok'
GREP_COUNT_MATCH='Ran 1 '

python setup.py testr --testr-args="checklimit" && \
    testr last --subunit | subunit2pyunit 2>&1 | \
    grep "${GREP_TEST_MATCH}" && \
    testr last | grep "${GREP_COUNT_MATCH}"
