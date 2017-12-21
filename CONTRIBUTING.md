
Gabbi gets better because of the contributions from the people who use
it. These contributions come in many forms:

* Joining the #gabbi channel on Freenode IRC at freenode.net and
  having a chat.
* Improvements to make the documentation more complete, more correct
  and typo free.
* Reporting and reviewing bugs in the
  [issues](https://github.com/cdent/gabbi/issues)
* Providing [pull requests](https://github.com/cdent/gabbi/pulls)
  containing fixes and new features. See [below](#pull-requests) for
  guidelines.

If you have an idea for a new feature it is best to review the
[Ideas](https://github.com/cdent/gabbi/wiki/Ideas) wiki page and the
existing issues and pull requests to see if there is existing work you
can contribute to. It's also worthwhile to ask around in IRC.

In general the default stance with gabbi is to avoid adding new features
if we can come up with some way to use the existing features to solve
the requirements of your tests. This helps to keep the test format
as clean and readable as possible.

If you reach an impasse, create an issue and provide as much info as you
can about your situation and together we can try to figure it out.

# Pull Requests

If you want to make a pull request, fork the gabbi repository and create
a new branch that will contain your changes. Name the branch something
meaningful and related to your change.

See the "Testing and Developing Gabbi" section of the the `README` for
information on setting up a reasonable working environment.

You should provide verbose commit messages on each of your commits. You
should not feel obliged to squash your commits into one commit. We want
to the see the full expression of your process and thinking.

When you push your branch back to Github please never force push.

If your pull request receives some comments and you need to make some
changes, please do them as _an additional commit_ on the branch used for
the pull request.

Any code you submit should follow the rules of
[pep8](https://www.python.org/dev/peps/pep-0008/). You can test that
it does by running `tox -epep8` in your checkout. Note that when you
run that the code will also be evaluated to be sure it follows some
standards established in the OpenStack development community (mostly
to do with import handling and line breaks).
