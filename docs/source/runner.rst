YAML Runner
===========

If there is a running web service that needs to be tested and
creating a test loader with :meth:`~gabbi.driver.build_tests` is
either inconvenient or overkill it is possible to run YAML test
files directly from the command line with the console-script
``gabbi-run``. It accepts YAML on ``stdin``, generates and runs
tests and outputs a summary of the results.

The provided YAML may not use custom :doc:`fixtures` but otherwise
uses the default :doc:`format`. :doc:`host` information is either
expressed directly in the YAML file or provided on the command
line::

    gabbi-run [host[:port]] < /my/test.yaml
