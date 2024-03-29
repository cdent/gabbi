"""A sample pytest module."""

# For pathname munging
import os

# The module that build_tests comes from.
from gabbi import driver

# We need access to the WSGI application that hosts our service
from myapp import wsgiapp

# We're using fixtures in the YAML files, we need to know where to
# load them from.
from myapp.test import fixtures

# By convention the YAML files are put in a directory named
# "gabbits" that is in the same directory as the Python test file.
TESTS_DIR = 'gabbits'


def test_gabbits():
    test_dir = os.path.join(os.path.dirname(__file__), TESTS_DIR)
    # Pass "require_ssl=True" as an argument to force all tests
    # to use SSL in requests.
    test_generator = driver.py_test_generator(
        test_loader_name=__name__,
        test_dir, intercept=wsgiapp.app,
        fixture_module=fixtures)

    for test in test_generator:
        yield test
