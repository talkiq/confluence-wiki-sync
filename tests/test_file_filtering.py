"""Tests that the correct files are considered for sync"""

import os

import wiki_sync


def test_no_ignored_folder():
    os.environ['INPUT_IGNORED-FOLDERS'] = ''

    # MD and RST files should be synched
    assert wiki_sync.should_sync_file('file.md')
    assert wiki_sync.should_sync_file('file.rst')

    # Even in subfolders
    assert wiki_sync.should_sync_file('foo/file.md')
    assert wiki_sync.should_sync_file('bar/baz/file.rst')

    # Other files shouldn't be
    assert not wiki_sync.should_sync_file('file')
    assert not wiki_sync.should_sync_file('file.c')
    assert not wiki_sync.should_sync_file('foo/file.py')


def test_one_ignored_folder():
    os.environ['INPUT_IGNORED-FOLDERS'] = 'foo/'

    assert not wiki_sync.should_sync_file('foo/file.md')
    assert not wiki_sync.should_sync_file('foo/bar/file.md')

    assert wiki_sync.should_sync_file('bar/file.md')
    assert wiki_sync.should_sync_file('bar/foo/file.md')
    assert wiki_sync.should_sync_file('foo.md')


def test_one_ignored_folder_with_ommited_slash():
    os.environ['INPUT_IGNORED-FOLDERS'] = 'foo'

    assert not wiki_sync.should_sync_file('foo/file.md')
    assert not wiki_sync.should_sync_file('foo/bar/file.md')

    assert wiki_sync.should_sync_file('food/file.md')
    assert wiki_sync.should_sync_file('bar/file.md')
    assert wiki_sync.should_sync_file('bar/foo/file.md')
    assert wiki_sync.should_sync_file('foo.md')
    assert wiki_sync.should_sync_file('food.md')


def test_ignored_subfolder():
    os.environ['INPUT_IGNORED-FOLDERS'] = 'foo/bar'

    assert not wiki_sync.should_sync_file('foo/bar/file.md')
    assert not wiki_sync.should_sync_file('foo/bar/baz/file.md')

    assert wiki_sync.should_sync_file('foo/baraka/file.md')


def test_several_ignored_folders():
    os.environ['INPUT_IGNORED-FOLDERS'] = 'foo/ bar/'

    assert not wiki_sync.should_sync_file('foo/file.md')
    assert not wiki_sync.should_sync_file('bar/file.md')

    assert wiki_sync.should_sync_file('baz/file.md')
