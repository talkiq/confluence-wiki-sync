"""Tests that the correct files are considered for sync"""
import os

import main


def test_no_ignored_folder():
    os.environ['INPUT_IGNORED-FOLDERS'] = ''

    # MD and RST files should be synched
    assert main.should_sync_file('file.md')
    assert main.should_sync_file('file.rst')

    # Even in subfolders
    assert main.should_sync_file('foo/file.md')
    assert main.should_sync_file('bar/baz/file.rst')

    # Other files shouldn't be
    assert not main.should_sync_file('file')
    assert not main.should_sync_file('file.c')
    assert not main.should_sync_file('foo/file.py')


def test_one_ignored_folder():
    os.environ['INPUT_IGNORED-FOLDERS'] = 'foo/'

    assert not main.should_sync_file('foo/file.md')
    assert not main.should_sync_file('foo/bar/file.md')

    assert main.should_sync_file('bar/file.md')
    assert main.should_sync_file('bar/foo/file.md')
    assert main.should_sync_file('foo.md')


def test_one_ignored_folder_with_ommited_slash():
    os.environ['INPUT_IGNORED-FOLDERS'] = 'foo'

    assert not main.should_sync_file('foo/file.md')
    assert not main.should_sync_file('foo/bar/file.md')

    assert main.should_sync_file('food/file.md')
    assert main.should_sync_file('bar/file.md')
    assert main.should_sync_file('bar/foo/file.md')
    assert main.should_sync_file('foo.md')
    assert main.should_sync_file('food.md')


def test_ignored_subfolder():
    os.environ['INPUT_IGNORED-FOLDERS'] = 'foo/bar'

    assert not main.should_sync_file('foo/bar/file.md')
    assert not main.should_sync_file('foo/bar/baz/file.md')

    assert main.should_sync_file('foo/baraka/file.md')


def test_several_ignored_folders():
    os.environ['INPUT_IGNORED-FOLDERS'] = 'foo/ bar/'

    assert not main.should_sync_file('foo/file.md')
    assert not main.should_sync_file('bar/file.md')

    assert main.should_sync_file('baz/file.md')
