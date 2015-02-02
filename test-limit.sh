#!/bin/bash
# Run a test which is limited to just one request from a file that
# contains many requests and confirm that only one was run and that
# it did actually run.
#
# This covers a situation where the change of intercepts to fixtures
# broke limiting tests and we never knew.

GREP_MATCH='gabbi.driver.test_intercept_self_checklimit.test_request ... ok'

python setup.py testr --testr-args="checklimit" && \
    testr last --subunit | subunit2pyunit 2>&1 | \
    grep "${GREP_MATCH}"
