"""A sample pytest module for pytest >= 3.0."""

# For pathname munging
import os

# The module that py_test_generator comes from.
from gabbi import driver

# We need test_pytest so that pytest test collection works properly.
# Without this, the pytest_generate_tests method below will not be
# called.
from gabbi.driver import test_pytest  # noqa

# We need access to the WSGI application that hosts our service
from myapp import wsgiapp

# We're using fixtures in the YAML files, we need to know where to
# load them from.
from myapp.test import fixtures

# By convention the YAML files are put in a directory named
# "gabbits" that is in the same directory as the Python test file.
TESTS_DIR = 'gabbits'


def pytest_generate_tests(metafunc):
    test_dir = os.path.join(os.path.dirname(__file__), TESTS_DIR)
    driver.py_test_generator(
        test_dir, intercept=wsgiapp.app,
        fixture_module=fixtures, metafunc=metafunc)
