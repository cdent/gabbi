#!/bin/bash
# Run a test that confirms that a verbose test will output a response body
# when there is no content-type.

stestr run "intercept.verbosity" | grep '^notempty' >/dev/null
