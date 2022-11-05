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
                wiki_mock, doc_path, GH_ROOT, REPO_NAME)

        assert output == 'Check out this [link|https://example.org]\n'


def test_link_to_file_in_same_folder(wiki_mock, get_repo_root_mock):
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
                wiki_mock, doc_path, GH_ROOT, REPO_NAME)

        expected_output = ('Check out this'
                           f' [other file|{GH_ROOT}{linked_doc_path}]\n')
        assert output == expected_output


def test_link_to_file_in_child_folder(wiki_mock, get_repo_root_mock):
    with tempfile.TemporaryDirectory() as repo_root:
        get_repo_root_mock.return_value = repo_root

        # Create a file that the doc will link to (in a subfolder)
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
                wiki_mock, doc_path, GH_ROOT, REPO_NAME)

        expected_output = ('Check out this'
                           f' [other file|{GH_ROOT}{linked_doc_path}]\n')
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
                wiki_mock, doc_path, GH_ROOT, REPO_NAME)

        expected_output = ('Check out this'
                           f' [other file|{GH_ROOT}{linked_doc_path}]\n')
        assert output == expected_output


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
                wiki_mock, doc_path, GH_ROOT, REPO_NAME)

        expected_link = f'[{linked_file_name}|{GH_ROOT}{linked_doc_path}]'
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
                wiki_mock, doc_path, GH_ROOT, REPO_NAME)

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
                wiki_mock, doc_path, GH_ROOT, REPO_NAME)

        wiki_link = 'http://mywiki.atlassian.net/wiki/spaces/SPACE/pages/123'
        expected_output = (f'Check out this [other file|{wiki_link}]\n')
        assert output == expected_output


def test_simple_link_to_image(wiki_mock, get_repo_root_mock):
    with tempfile.TemporaryDirectory() as repo_root:
        get_repo_root_mock.return_value = repo_root

        # Create an image that the doc will link to (in a subfolder)
        os.makedirs(os.path.join(repo_root, 'foo', 'bar'))
        linked_file_name = 'foo/bar/cool_image.png'
        linked_doc_path = os.path.join(repo_root, linked_file_name)
        # The file isn't actually an image, but that's not important
        write_something_to_file(linked_doc_path)

        # The wiki page doesn't have any attachments
        wiki_mock.get_attachments_from_content.return_value = {'results': []}

        # Create the doc file with a link to the other one
        doc_path = os.path.join(repo_root, 'new_doc.md')
        with open(doc_path, mode='w', encoding='utf-8') as doc_file:
            contents = f'Check out ![]({linked_file_name})'
            print(contents, file=doc_file)

        output = wiki_sync.get_formatted_file_content(
                wiki_mock, doc_path, GH_ROOT, REPO_NAME)

        # Even though the image isn't in the same folder as the document, the
        # name of the image attached to the wiki page is just the file name
        assert output == 'Check out !cool_image.png!\n'

        wiki_mock.attach_file.assert_called_once()


def test_link_to_image_with_params(wiki_mock, get_repo_root_mock):
    with tempfile.TemporaryDirectory() as repo_root:
        get_repo_root_mock.return_value = repo_root

        # Create an image that the doc will link to
        linked_file_name = 'cool_image.png'
        linked_doc_path = os.path.join(repo_root, linked_file_name)
        # The file isn't actually an image, but that's not important
        write_something_to_file(linked_doc_path)

        # The wiki page doesn't have any attachments
        wiki_mock.get_attachments_from_content.return_value = {'results': []}

        # Create the doc file with a link to the other one
        doc_path = os.path.join(repo_root, 'new_doc.md')
        with open(doc_path, mode='w', encoding='utf-8') as doc_file:
            contents = f'Check out ![Cool image]({linked_file_name})'
            print(contents, file=doc_file)

        output = wiki_sync.get_formatted_file_content(
                wiki_mock, doc_path, GH_ROOT, REPO_NAME)

        assert output == f'Check out !{linked_file_name}|alt=Cool image!\n'
        wiki_mock.attach_file.assert_called_once()


def write_something_to_file(file_path: str) -> None:
    with open(file_path, mode='w', encoding='utf-8') as doc_file:
        print('Not important - file only needs to exist', file=doc_file)
