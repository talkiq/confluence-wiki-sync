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
first part of the git tag). Note that GitHub will use the first line as the
title of the release.

Publish the release.

Lastly, move the corresponding major release branch to the tag you just
created. For example, if you created the ``v1.2`` tag, move the ``v1`` branch
to point to the same commit. This allows clients to follow v1 and automatically
get backward-compatible improvements.
