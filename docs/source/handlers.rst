Response Handlers
=================

Responses handlers are code which control the evaluation of the
HTTP response in each test. For example the `response_strings` key
described in :doc:`format` is a response handler. In many cases the
default handlers described there will be sufficient for creating
useful tests. When they are not, it is possible to add custom
handlers by subclassing :class:`~gabbi.handlers.ResponseHandler` and
adding that class in a call to :func:`~gabbi.driver.build_tests`::

    driver.build_tests(test_dir, loader, host=None,
                       intercept=simple_wsgi.SimpleWsgi,
                       response_handlers=[TestResponseHandler])

A subclass needs to define at least three things:

* ``test_key_suffix``: This, along with the prefix ``response_`` forms
  the key used in the test structure. It is a class level string.
* ``test_key_value``: The default value for this key if there is
  nothing there. This needs to be an empty list or empty dict. It is
  also a class level value.
* ``action``: A method in the class which tests the expected values
  against the HTTP response. A loop is made across each entry in the
  test key with data passed to action:
  If ``test_key_value`` is a list, then the arguments to``action`` are (in order):

  * ``self``: The current object.
  * ``test``: The currently active ``HTTPTestCase``
  * ``item``: The current entry in the loop if ``test_key_value`` is a
    list, otherwise the key half of the key/value pair at this entry.
  * ``value``: None if ``test_key_value`` is a list, otherwise the
    value half of the key/value pair at this entry.

Optionally a subclass may also define a ``cleanup`` method which is
called once before the loop that calls ``action`` is run.
