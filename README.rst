===========================
Confluence Docs Sync Action
===========================

This GitHub Action watches for changes in files with certain extensions
(currently hardcoded to ``.md`` and ``.rst``), converts them to Confluence wiki
markup using `Pandoc <https://pandoc.org/>`_, and uploads them to Confluence
Cloud.

The resulting Confluence pages are arranged in a tree under the root page, with
the same tree structure as in the git repo. Folders also get their dedicated
wiki page, containing a list of their children pages. The name of each page is
the path of the file in the repo, to guarantee uniqueness within the Confluence
space.

---------------
Getting started
---------------

Here is a simple configuration file. The checkout step is necessary and it
requires ``fetch-depth`` to be at least 2, so the script can compare the last
two commits and get a list of modified files.

.. code-block:: yaml

  # .github/workflows/my-workflow.yml
  jobs:
    wiki-sync:
      runs-on: ubuntu-latest
      steps:
        - name: Checkout
          uses: actions/checkout@v2
          with:
            fetch-depth: 2

        - name: Wiki Sync
          uses: dialpad/confluence-docs-sync@v1
          with:
            wiki-base-url: https://example.org
            user: user@domain.tld
            token: ${{ secrets.TOKEN }}
            space-name: CoolSpace
            root-page-title: Root page

It is recommended to save the Confluence token as a GitHub secret.

-------------
Configuration
-------------

The Getting Started example shows all the required parameters.

Check out `action.yml <./action.yml>`_ to get the list of configuration options.
For example, you can selectively ignore folders by passing them in a
space-separated list:

.. code-block:: yaml

  - name: Wiki Sync
    uses: dialpad/confluence-docs-sync@v1
    with:
      ignored_folders: 'foo/ bar/baz/'
      [...]

-----------
Development
-----------

Coding standards
================

Our coding standards are pretty much just `PEP 8
<https://www.python.org/dev/peps/pep-0008/>`_, and are managed using
`pre-commit <https://pre-commit.com>`_.

Install it with ``pip install pre-commit``, and install the pre-commit hooks
with ``pre-commit install``.

The same linters run in CI, and you can also run them with ``pre-commit run
--all-files``.

Local run
=========

You can test locally using `act <https://github.com/nektos/act>`_.

Copy the simple configuration above, remove the Checkout step, and update the
``uses:`` line to be ``uses: ./``.

Then run ``act -b``.

``act`` takes a ``--secret-file`` argument so you can pass secrets to it by
putting them in a file (say, ``.secrets``):

.. code-block:: text

   TOKEN=mytoken

Then ``act -b --secret-file .secrets``
