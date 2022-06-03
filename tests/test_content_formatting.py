"""Tests that file content is updated properly

e.g. relative links, escaping special JIRA strings"""

import os
import tempfile
from unittest import mock

import pytest

from content_converter import ContentConverter


GH_ROOT = 'https://root/github/path/'
REPO_NAME = 'GenericRepo'


def setup_function():
    os.environ['INPUT_SPACE-NAME'] = 'MySpace'
    os.environ['INPUT_WIKI-BASE-URL'] = 'http://mywiki.atlassian.net'


@pytest.fixture
def wiki_mock():
    m = mock.Mock()
    m.get_page_by_title.return_value = None
    return m


def test_http_link(wiki_mock):
    with tempfile.TemporaryDirectory() as repo_root:
        # Create the doc file with an HTTP link
        doc_path = 'new_doc.md'
        doc_abs_path = os.path.join(repo_root, doc_path)
        with open(doc_abs_path, mode='w', encoding='utf-8') as doc_file:
            print('Check out this [link](https://example.org)', file=doc_file)

        converter = ContentConverter(wiki_mock, repo_root, GH_ROOT, REPO_NAME)
        output = converter.convert_file_contents(doc_path)

        assert output == 'Check out this [link|https://example.org]\n'


def test_link_to_file_both_in_root(wiki_mock):
    with tempfile.TemporaryDirectory() as repo_root:
        # Create a file that the doc will link to
        linked_file_path = 'linked_file.py'
        linked_file_abs_path = os.path.join(repo_root, linked_file_path)
        write_something_to_file(linked_file_abs_path)

        # Create the doc file with a link to the other one
        doc_path = 'new_doc.md'
        doc_abs_path = os.path.join(repo_root, doc_path)
        with open(doc_abs_path, mode='w', encoding='utf-8') as doc_file:
            contents = f'Check out this [other file]({linked_file_path})'
            print(contents, file=doc_file)

        converter = ContentConverter(wiki_mock, repo_root, GH_ROOT, REPO_NAME)
        output = converter.convert_file_contents(doc_path)

        expected_gh_link = f'{GH_ROOT}{linked_file_path}'
        expected_output = f'Check out this [other file|{expected_gh_link}]\n'
        assert output == expected_output


def test_link_to_file_in_same_non_root_folder(wiki_mock):
    with tempfile.TemporaryDirectory() as repo_root:
        os.makedirs(os.path.join(repo_root, 'foo'))
        # Create a file that the doc will link to
        linked_file_name = 'linked_file.py'
        linked_file_path = os.path.join('foo', 'linked_file.py')
        linked_file_abs_path = os.path.join(repo_root, linked_file_path)
        write_something_to_file(linked_file_abs_path)

        # Create the doc file with a link to the other one
        doc_path = os.path.join('foo', 'new_doc.md')
        doc_abs_path = os.path.join(repo_root, doc_path)
        with open(doc_abs_path, mode='w', encoding='utf-8') as doc_file:
            contents = f'Check out this [other file]({linked_file_name})'
            print(contents, file=doc_file)

        converter = ContentConverter(wiki_mock, repo_root, GH_ROOT, REPO_NAME)
        output = converter.convert_file_contents(doc_path)

        expected_gh_link = f'{GH_ROOT}{linked_file_path}'
        expected_output = f'Check out this [other file|{expected_gh_link}]\n'
        assert output == expected_output


def test_link_to_file_in_child_folder(wiki_mock):
    with tempfile.TemporaryDirectory() as repo_root:
        # Create a file that the doc will link to (in a subfolder)
        os.makedirs(os.path.join(repo_root, 'foo', 'bar'))
        linked_doc_path = os.path.join('foo', 'bar', 'linked_file.py')
        linked_doc_abs_path = os.path.join(repo_root, linked_doc_path)
        write_something_to_file(linked_doc_abs_path)

        # Create the doc file with a link to the other one
        doc_path = 'new_doc.md'
        doc_abs_path = os.path.join(repo_root, doc_path)
        with open(doc_abs_path, mode='w', encoding='utf-8') as doc_file:
            contents = f'Check out this [other file]({linked_doc_path})'
            print(contents, file=doc_file)

        converter = ContentConverter(wiki_mock, repo_root, GH_ROOT, REPO_NAME)
        output = converter.convert_file_contents(doc_path)

        expected_gh_link = f'{GH_ROOT}{linked_doc_path}'
        expected_output = f'Check out this [other file|{expected_gh_link}]\n'
        assert output == expected_output


def test_link_to_file_in_parent_folder(wiki_mock):
    with tempfile.TemporaryDirectory() as repo_root:
        # Create a file that the doc will link to
        linked_doc_path = 'linked_file.py'
        linked_doc_abs_path = os.path.join(repo_root, linked_doc_path)
        write_something_to_file(linked_doc_abs_path)

        # Create the doc file in a subfolder, with a link to the other one
        os.makedirs(os.path.join(repo_root, 'foo', 'bar'))
        doc_path = os.path.join('foo', 'bar', 'new_doc.md')
        doc_abs_path = os.path.join(repo_root, doc_path)
        with open(doc_abs_path, mode='w', encoding='utf-8') as doc_file:
            contents = 'Check out this [other file](../../linked_file.py)'
            print(contents, file=doc_file)

        converter = ContentConverter(wiki_mock, repo_root, GH_ROOT, REPO_NAME)
        output = converter.convert_file_contents(doc_path)

        expected_gh_link = f'{GH_ROOT}linked_file.py'
        expected_output = f'Check out this [other file|{expected_gh_link}]\n'
        assert output == expected_output


def test_simplified_link(wiki_mock):
    # Link where the name of the link is the same as the link itself
    with tempfile.TemporaryDirectory() as repo_root:
        # Create a file that the doc will link to
        linked_doc_path = 'linked_file.py'
        linked_doc_abs_path = os.path.join(repo_root, linked_doc_path)
        write_something_to_file(linked_doc_abs_path)

        # Create the doc file with a link to the other one
        doc_path = 'new_doc.md'
        doc_abs_path = os.path.join(repo_root, doc_path)
        with open(doc_abs_path, mode='w', encoding='utf-8') as doc_file:
            contents = f'Check out [{linked_doc_path}]({linked_doc_path})'
            print(contents, file=doc_file)

        converter = ContentConverter(wiki_mock, repo_root, GH_ROOT, REPO_NAME)
        output = converter.convert_file_contents(doc_path)

        expected_link = f'[{linked_doc_path}|{GH_ROOT}{linked_doc_path}]'
        assert output == f'Check out {expected_link}\n'


def test_link_to_non_existing_file(wiki_mock):
    with tempfile.TemporaryDirectory() as repo_root:
        # Create the doc file with a link to a non-existing file
        doc_path = 'new_doc.md'
        doc_abs_path = os.path.join(repo_root, doc_path)
        with open(doc_abs_path, mode='w', encoding='utf-8') as doc_file:
            contents = 'Check out this [other file](non_existing.py)'
            print(contents, file=doc_file)

        converter = ContentConverter(wiki_mock, repo_root, GH_ROOT, REPO_NAME)
        output = converter.convert_file_contents(doc_path)

        # Output is the same
        assert output == 'Check out this [other file|non_existing.py]\n'


def test_link_to_file_that_exists_on_confluence(wiki_mock):
    space = 'WikiSpace'
    os.environ['INPUT_SPACE-NAME'] = space
    wiki_url = 'http://mywiki.atlassian.net'
    os.environ['INPUT_WIKI-BASE-URL'] = wiki_url

    with tempfile.TemporaryDirectory() as repo_root:
        # Create a file that the doc will link to
        linked_file_name = 'linked_file.py'
        linked_doc_path = os.path.join(repo_root, linked_file_name)
        write_something_to_file(linked_doc_path)

        # When the wiki client wants to know whether the linked file has an
        # existing Confluence page, say yes
        wiki_mock.get_page_by_title.return_value = {
            '_links': {'webui': f'/spaces/{space}/pages/123'}
        }

        # Create the doc file with a link to the other one
        doc_path = os.path.join(repo_root, 'new_doc.md')
        with open(doc_path, mode='w', encoding='utf-8') as doc_file:
            contents = f'Check out this [other file]({linked_file_name})'
            print(contents, file=doc_file)

        converter = ContentConverter(wiki_mock, repo_root, GH_ROOT, REPO_NAME)
        output = converter.convert_file_contents(doc_path)

        wiki_link = f'{wiki_url}/wiki/spaces/{space}/pages/123'
        expected_output = f'Check out this [other file|{wiki_link}]\n'
        assert output == expected_output

        wiki_mock.get_page_by_title.assert_called_once_with(
            space, f'{REPO_NAME}/linked_file.py'
        )


def test_several_links_on_same_line(wiki_mock):
    with tempfile.TemporaryDirectory() as repo_root:
        # Create file that the doc will link to
        linked_file_name = 'linked_file.py'
        write_something_to_file(os.path.join(repo_root, linked_file_name))
        linked_file_name_2 = 'linked_file_2.go'
        write_something_to_file(os.path.join(repo_root, linked_file_name_2))

        # Create the doc file with a link to the other one
        doc_path = 'new_doc.md'
        doc_abs_path = os.path.join(repo_root, doc_path)
        with open(doc_abs_path, mode='w', encoding='utf-8') as doc_file:
            contents = (
                f'Check out this [file]({linked_file_name})'
                f' and also [that one]({linked_file_name_2})'
            )
            print(contents, file=doc_file)

        converter = ContentConverter(wiki_mock, repo_root, GH_ROOT, REPO_NAME)
        output = converter.convert_file_contents(doc_path)

        expected_gh_links = [
            f'{GH_ROOT}{linked_file_name}',
            f'{GH_ROOT}{linked_file_name_2}',
        ]
        expected_output = (
            f'Check out this [file|{expected_gh_links[0]}] and'
            f' also [that one|{expected_gh_links[1]}]\n'
        )
        assert output == expected_output


def test_simple_link_to_image(wiki_mock):
    with tempfile.TemporaryDirectory() as repo_root:
        # Create an image that the doc will link to (in a subfolder)
        os.makedirs(os.path.join(repo_root, 'foo', 'bar'))
        linked_doc_path = os.path.join('foo', 'bar', 'cool_image.png')
        linked_doc_abs_path = os.path.join(repo_root, linked_doc_path)
        # The file isn't actually an image, but that's not important
        write_something_to_file(linked_doc_abs_path)

        # The wiki page doesn't have any attachments
        wiki_mock.get_attachments_from_content.return_value = {'results': []}

        # Create the doc file with a link to the other one
        doc_path = os.path.join(repo_root, 'new_doc.md')
        with open(doc_path, mode='w', encoding='utf-8') as doc_file:
            contents = f'Check out ![]({linked_doc_path})'
            print(contents, file=doc_file)

        converter = ContentConverter(wiki_mock, repo_root, GH_ROOT, REPO_NAME)
        output = converter.convert_file_contents(doc_path)

        # Even though the image isn't in the same folder as the document, the
        # name of the image attached to the wiki page is just the file name
        assert output == 'Check out !cool_image.png!\n'

        wiki_mock.attach_file.assert_called_once()


def test_simple_link_to_image_new_page(wiki_mock):
    """Same as the previous one, but the wiki page didn't already exist"""
    with tempfile.TemporaryDirectory() as repo_root:
        # Create an image that the doc will link to (in a subfolder)
        os.makedirs(os.path.join(repo_root, 'foo', 'bar'))
        linked_doc_path = os.path.join('foo', 'bar', 'cool_image.png')
        linked_doc_abs_path = os.path.join(repo_root, linked_doc_path)
        # The file isn't actually an image, but that's not important
        write_something_to_file(linked_doc_abs_path)

        # The wiki page doesn't exist
        wiki_mock.get_page_id.return_value = None

        # Create the doc file with a link to the other one
        doc_path = os.path.join(repo_root, 'new_doc.md')
        with open(doc_path, mode='w', encoding='utf-8') as doc_file:
            contents = f'Check out ![]({linked_doc_path})'
            print(contents, file=doc_file)

        converter = ContentConverter(wiki_mock, repo_root, GH_ROOT, REPO_NAME)
        output = converter.convert_file_contents(doc_path)

        # Even though the image isn't in the same folder as the document, the
        # name of the image attached to the wiki page is just the file name
        assert output == 'Check out !cool_image.png!\n'

        # File wasn't attached during content conversion, because the wiki page doesn't
        # exist at that time.
        wiki_mock.attach_file.assert_not_called()
        # Remember the information of the file to be attached
        assert converter.files_to_attach_to_last_page == [linked_doc_path]


def test_link_to_image_with_params(wiki_mock):
    with tempfile.TemporaryDirectory() as repo_root:
        # Create an image that the doc will link to
        linked_doc_path = 'cool_image.png'
        linked_doc_abs_path = os.path.join(repo_root, linked_doc_path)
        # The file isn't actually an image, but that's not important
        write_something_to_file(linked_doc_abs_path)

        # The wiki page doesn't have any attachments
        wiki_mock.get_attachments_from_content.return_value = {'results': []}

        # Create the doc file with a link to the other one
        doc_path = os.path.join(repo_root, 'new_doc.md')
        with open(doc_path, mode='w', encoding='utf-8') as doc_file:
            contents = f'Check out ![Cool image]({linked_doc_path})'
            print(contents, file=doc_file)

        converter = ContentConverter(wiki_mock, repo_root, GH_ROOT, REPO_NAME)
        output = converter.convert_file_contents(doc_path)

        assert output == f'Check out !{linked_doc_path}|alt=Cool image!\n'
        wiki_mock.attach_file.assert_called_once()


def test_jira_macro():
    with tempfile.TemporaryDirectory() as repo_root:
        doc_path = os.path.join(repo_root, 'new_doc.md')
        with open(doc_path, mode='w', encoding='utf-8') as doc_file:
            print('Bash example using ${SOME_VARIABLE}', file=doc_file)

        converter = ContentConverter(wiki_mock, repo_root, GH_ROOT, REPO_NAME)
        output = converter.convert_file_contents(doc_path)

        assert output == r'Bash example using $\{SOME_VARIABLE\}' + '\n'


def write_something_to_file(file_path: str) -> None:
    with open(file_path, mode='w', encoding='utf-8') as doc_file:
        print('Not important - file only needs to exist', file=doc_file)
