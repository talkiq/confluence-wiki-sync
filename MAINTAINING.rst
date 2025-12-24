===========
Maintaining
===========

Notes on maintaining the wiki sync script.

---------
Releasing
---------

The release cadence isn't fixed. A new release is created whenever the
version on main is non-trivially better than the latest released
version (whatever that means to the maintainer).

When you've decided that this has happened, pick a version number. We use
`Semantic Versioning <https://semver.org/>`_. For the purpose of this script,
an incompatible API change is either removing an entry from ``action.yml``,
adding a required one, or changing the default value of an optional one.

Make sure all the tests pass on main.

Tag the release using ``git tag -a v1.2``, for example. Include a short
description of the changes, and the output of ``git shortlog v1.1..HEAD``,
replacing ``v1.1`` with whatever the last release was.

Push the tag: ``git push --tags``.

Create a new GitHub release via
https://github.com/talkiq/confluence-wiki-sync/releases/new, making sure
"Publish this Action to the GitHub Marketplace" is checked.

You shouldn't need to change anything else on that page, just pick the correct
tag.

You can click "Generate release notes", and GitHub will generate its own
version of the git log. At the top, add your description of the release (the
first part of the git tag).

Publish the release.

Lastly, move the corresponding major release branch to the tag you just
created. For example, if you created the ``v1.2`` tag, move the ``v1`` branch
to point to the same commit. This allows clients to follow v1 and automatically
get backward-compatible improvements.


About tags for major versions
=============================

For major version changes, prefer using ``v2.0`` over ``v2`` as the tag. git
doesn't like it when a tag and a branch have the same name.

If there is a tag with the same name as the release branch, git will complain
when you try to push the branch. Just use the full name of the branch:

.. code-block:: bash

    $ git push origin v2
    error: src refspec v2 matches more than one
    error: failed to push some refs to 'github.com:talkiq/confluence-wiki-sync.git'

    $ git push origin refs/heads/v2:refs/heads/v2
    Total 0 (delta 0), reused 0 (delta 0), pack-reused 0 (from 0)
    To github.com:talkiq/confluence-wiki-sync.git
        6418101..4671ac9  v2 -> v2
