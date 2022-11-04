"""Tests that relative links are updated properly"""
# Pylint seems to be confused by Pytest fixtures
# pylint: disable=redefined-outer-name
import os
import tempfile
from unittest import mock

import pytest

import wiki_sync


GH_ROOT = 'https://root/github/path/'
REPO_NAME = 'GenericRepo'


def setup():
    os.environ['INPUT_SPACE-NAME'] = 'MySpace'
    os.environ['INPUT_WIKI-BASE-URL'] = 'http://mywiki.atlassian.net'


@pytest.fixture
def wiki_mock():
    m = mock.Mock()
    m.get_page_by_title.return_value = None
    return m


@pytest.fixture
def get_repo_root_mock():
    return mock.patch('wiki_sync.get_repository_root')


def test_http_link(wiki_mock, get_repo_root_mock):
    with tempfile.TemporaryDirectory() as repo_root:
        get_repo_root_mock.return_value = repo_root

        # Create the doc file with an HTTP link
        doc_path = os.path.join(repo_root, 'new_doc.md')
        with open(doc_path, mode='w', encoding='utf-8') as doc_file:
            print('Check out this [link](https://example.org)', file=doc_file)

        output = wiki_sync.get_formatted_file_content(
                wiki_mock, repo_root, doc_path, GH_ROOT, REPO_NAME)

        assert output == 'Check out this [link|https://example.org]\n'


def test_link_to_file_both_in_root(wiki_mock, get_repo_root_mock):
    with tempfile.TemporaryDirectory() as repo_root:
        get_repo_root_mock.return_value = repo_root

        # Create a file that the doc will link to
        linked_file_name = 'linked_file.py'
        linked_doc_path = os.path.join(repo_root, linked_file_name)
        write_something_to_file(linked_doc_path)

        # Create the doc file with a link to the other one
        doc_path = os.path.join(repo_root, 'new_doc.md')
        with open(doc_path, mode='w', encoding='utf-8') as doc_file:
            contents = f'Check out this [other file]({linked_file_name})'
            print(contents, file=doc_file)

        output = wiki_sync.get_formatted_file_content(
                wiki_mock, repo_root, doc_path, GH_ROOT, REPO_NAME)

        expected_gh_link = f'{GH_ROOT}{linked_file_name}'
        expected_output = f'Check out this [other file|{expected_gh_link}]\n'
        assert output == expected_output


def test_link_to_file_in_same_non_root_folder(wiki_mock, get_repo_root_mock):
    with tempfile.TemporaryDirectory() as repo_root:
        get_repo_root_mock.return_value = repo_root

        os.makedirs(os.path.join(repo_root, 'foo'))
        # Create a file that the doc will link to
        linked_file_name = 'linked_file.py'
        linked_doc_path = os.path.join(repo_root, 'foo', linked_file_name)
        write_something_to_file(linked_doc_path)

        # Create the doc file with a link to the other one
        doc_path = os.path.join(repo_root, 'foo', 'new_doc.md')
        with open(doc_path, mode='w', encoding='utf-8') as doc_file:
            contents = f'Check out this [other file]({linked_file_name})'
            print(contents, file=doc_file)

        output = wiki_sync.get_formatted_file_content(
                wiki_mock, repo_root, doc_path, GH_ROOT, REPO_NAME)

        expected_gh_link = f'{GH_ROOT}foo/{linked_file_name}'
        expected_output = f'Check out this [other file|{expected_gh_link}]\n'
        assert output == expected_output


def test_link_to_file_in_child_folder(wiki_mock, get_repo_root_mock):
    with tempfile.TemporaryDirectory() as repo_root:
        get_repo_root_mock.return_value = repo_root

        # Create a file in a subfolder, that the doc will link to
        os.makedirs(os.path.join(repo_root, 'foo', 'bar'))
        linked_file_name = 'foo/bar/linked_file.py'
        linked_doc_path = os.path.join(repo_root, linked_file_name)
        write_something_to_file(linked_doc_path)

        # Create the doc file with a link to the other one
        doc_path = os.path.join(repo_root, 'new_doc.md')
        with open(doc_path, mode='w', encoding='utf-8') as doc_file:
            contents = f'Check out this [other file]({linked_file_name})'
            print(contents, file=doc_file)

        output = wiki_sync.get_formatted_file_content(
                wiki_mock, repo_root, doc_path, GH_ROOT, REPO_NAME)

        expected_gh_link = f'{GH_ROOT}foo/bar/linked_file.py'
        expected_output = f'Check out this [other file|{expected_gh_link}]\n'
        assert output == expected_output


def test_link_to_file_in_parent_folder(wiki_mock, get_repo_root_mock):
    with tempfile.TemporaryDirectory() as repo_root:
        get_repo_root_mock.return_value = repo_root

        # Create a file that the doc will link to
        linked_file_name = 'linked_file.py'
        linked_doc_path = os.path.join(repo_root, linked_file_name)
        write_something_to_file(linked_doc_path)

        # Create the doc file in a subfolder, with a link to the other one
        os.makedirs(os.path.join(repo_root, 'foo', 'bar'))
        doc_path = os.path.join(repo_root, 'foo/bar/new_doc.md')
        with open(doc_path, mode='w', encoding='utf-8') as doc_file:
            contents = 'Check out this [other file](../../linked_file.py)'
            print(contents, file=doc_file)

        output = wiki_sync.get_formatted_file_content(
                wiki_mock, repo_root, doc_path, GH_ROOT, REPO_NAME)

        expected_gh_link = f'{GH_ROOT}linked_file.py'
        expected_output = f'Check out this [other file|{expected_gh_link}]\n'
        assert output == expected_output


@pytest.mark.xfail(reason='Will be implemented in #19')
def test_simplified_link(wiki_mock, get_repo_root_mock):
    # Link where the name of the link is the same as the link itself
    with tempfile.TemporaryDirectory() as repo_root:
        get_repo_root_mock.return_value = repo_root

        # Create a file that the doc will link to
        linked_file_name = 'linked_file.py'
        linked_doc_path = os.path.join(repo_root, linked_file_name)
        write_something_to_file(linked_doc_path)

        # Create the doc file with a link to the other one
        doc_path = os.path.join(repo_root, 'new_doc.md')
        with open(doc_path, mode='w', encoding='utf-8') as doc_file:
            contents = f'Check out [{linked_file_name}]({linked_file_name})'
            print(contents, file=doc_file)

        output = wiki_sync.get_formatted_file_content(
                wiki_mock, repo_root, doc_path, GH_ROOT, REPO_NAME)

        expected_link = f'[{linked_file_name}|{GH_ROOT}linked_file.py'
        assert output == f'Check out {expected_link}\n'


def test_link_to_non_existing_file(wiki_mock, get_repo_root_mock):
    with tempfile.TemporaryDirectory() as repo_root:
        get_repo_root_mock.return_value = repo_root

        # Create the doc file with a link to a non-existing file
        doc_path = os.path.join(repo_root, 'new_doc.md')
        with open(doc_path, mode='w', encoding='utf-8') as doc_file:
            contents = 'Check out this [other file](non_existing.py)'
            print(contents, file=doc_file)

        output = wiki_sync.get_formatted_file_content(
                wiki_mock, repo_root, doc_path, GH_ROOT, REPO_NAME)

        # Output is the same
        assert output == 'Check out this [other file|non_existing.py]\n'


def test_link_to_file_that_exists_on_confluence(wiki_mock, get_repo_root_mock):
    os.environ['INPUT_WIKI-BASE-URL'] = 'http://mywiki.atlassian.net'

    with tempfile.TemporaryDirectory() as repo_root:
        get_repo_root_mock.return_value = repo_root

        # Create a file that the doc will link to
        linked_file_name = 'linked_file.py'
        linked_doc_path = os.path.join(repo_root, linked_file_name)
        write_something_to_file(linked_doc_path)

        # When the wiki client wants to know whether the linked file has an
        # existing Confluence page, say yes
        wiki_mock.get_page_by_title.return_value = {
            '_links': {
                'webui': '/spaces/SPACE/pages/123'
                }
            }

        # Create the doc file with a link to the other one
        doc_path = os.path.join(repo_root, 'new_doc.md')
        with open(doc_path, mode='w', encoding='utf-8') as doc_file:
            contents = f'Check out this [other file]({linked_file_name})'
            print(contents, file=doc_file)

        output = wiki_sync.get_formatted_file_content(
                wiki_mock, repo_root, doc_path, GH_ROOT, REPO_NAME)

        wiki_link = 'http://mywiki.atlassian.net/wiki/spaces/SPACE/pages/123'
        expected_output = (f'Check out this [other file|{wiki_link}]\n')
        assert output == expected_output


def write_something_to_file(file_path: str) -> None:
    with open(file_path, mode='w', encoding='utf-8') as doc_file:
        print('Not important - file only needs to exist', file=doc_file)
