Response Handlers
=================

Response handlers determine how an HTTP response is being processed and checked
against the expected result. For each entry starting with `response_`, the
respective class is invoked with the corresponding values:

    response_strings:
        - "lorem ipsum"
        - "dolor sit amet"

This creates an instance of `StringResponseHandler`, passing the value
`["lorem ipsum", "dolor sit amet"]` - it is then up to the response handler's
implementation to interpret both the actual response and the expected values,
thus determining whether the test passes or fails.

While the default handlers (as described in :doc:`format`) are sufficient for
most cases, it is possible to register additional custom handlers by passing a
subclass of :class:`~gabbi.handlers.ResponseHandler` to
:func:`~gabbi.driver.build_tests`::

    driver.build_tests(test_dir, loader, host=None,
                       intercept=simple_wsgi.SimpleWsgi,
                       response_handlers=[MyResponseHandler])

A subclass needs to define at least three things:

* ``test_key_suffix``: This, along with the prefix ``response_``, forms
  the key used in the test structure. It is a class level string.
* ``test_key_value``: The key's default value, either an empty list or empty
  dict. It is also a class level value.
* ``action``: An instance method which tests the expected values
  against the HTTP response - it is invoked for each entry, with the parameters
  depending on the default value. If ``test_key_value`` is a list, then the
  arguments to ``action`` are (in order):

  * ``self``: The current instance.
  * ``test``: The currently active ``HTTPTestCase``
  * ``item``: The current entry if ``test_key_value`` is a
    list, otherwise the key half of the key/value pair at this entry.
  * ``value``: None if ``test_key_value`` is a list, otherwise the
    value half of the key/value pair at this entry.

Optionally a subclass may also define a ``cleanup`` method which is
called once before the loop that calls ``action`` is run.
