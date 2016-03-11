Response Handlers
=================

.. highlight:: yaml

Response handlers determine how an HTTP response will be processed and checked
against an expected result. For each entry starting with `response_`, an
associated class is invoked with corresponding values. For example
if the following lines are in a test::

    response_strings:
        - "lorem ipsum"
        - "dolor sit amet"

these lines create an instance of ``StringResponseHandler``, passing the value
``["lorem ipsum", "dolor sit amet"]``. The response handler
implementation interprets the response and the expected values, determining
whether the test passes or fails.

.. highlight:: python

While the default handlers (as described in :doc:`format`) are sufficient for
most cases, it is possible to register additional custom handlers by passing a
subclass of :class:`~gabbi.handlers.ResponseHandler` to
:meth:`~gabbi.driver.build_tests`::

    driver.build_tests(test_dir, loader, host=None,
                       intercept=simple_wsgi.SimpleWsgi,
                       response_handlers=[MyResponseHandler])

With ``gabbi-run``, custom handlers can be loaded via the
``--response-handler`` option -- see
:meth:`~gabbi.runner.load_response_handlers` for details.

A subclass needs to define at least three things:

* ``test_key_suffix``: This, along with the prefix ``response_``, forms
  the key used in the test structure. It is a class level string.
* ``test_key_value``: The key's default value, either an empty list (``[]``)
  or empty dict (``{}``). It is a class level value.
* ``action``: An instance method which tests the expected values
  against the HTTP response - it is invoked for each entry, with the parameters
  depending on the default value. The arguments to ``action`` are (in order):

  * ``self``: The current instance.
  * ``test``: The currently active ``HTTPTestCase``
  * ``item``: The current entry if ``test_key_value`` is a
    list, otherwise the key half of the key/value pair at this entry.
  * ``value``: ``None`` if ``test_key_value`` is a list, otherwise the
    value half of the key/value pair at this entry.

Optionally a subclass may also define a ``preprocess`` method which is
called once before the loop that calls ``action`` is run.
``preprocess`` is passed the current test instance which may be
modified in place if required. One possible reason to do this would
be to process the ``test.output`` into another form (e.g. a parsed
DOM) only once rather than per test assertion. Since ``ResponseHandler``
classes will run in an unpredictable order it is best to add new
attributes on the test instance instead of changing the value of
existing attributes.
