"""
End-to-end tests that make sure the correct Confluence pages are
created/updated, and with the correct content
"""

import os
from unittest import mock

import pytest

import wiki_sync


@pytest.fixture
def use_temp_dir(tmp_path):
    # tmp_path is the path to a pytest-provided temporary folder
    # Run the test inside it, so the files it creates are cleaned up afterwards
    os.chdir(tmp_path)
    os.makedirs('foo/bar')
    yield


@pytest.fixture
def wiki_mock():
    with mock.patch('atlassian.Confluence') as mock_confluence:
        yield mock_confluence.return_value


def test_page_is_created_under_correct_root(use_temp_dir, wiki_mock):
    file_name = 'hello.md'
    file_contents = 'Hello, World'

    with open(file_name, mode='w', encoding='utf-8') as doc_file:
        print(file_contents, file=doc_file)

    root_page_id = 12345
    root_page_title = 'My docs'
    space_name = 'SPACE'

    wiki_mock.get_page_id.return_value = root_page_id
    set_up_dummy_environment(space_name, root_page_title)

    wiki_sync.sync_files([file_name])

    wiki_mock.get_page_id.assert_called_once_with(space_name, root_page_title)

    call_args_list = wiki_mock.update_or_create.call_args_list
    assert len(call_args_list) == 1
    kwargs = call_args_list[0].kwargs
    assert kwargs['parent_id'] == root_page_id
    assert kwargs['title'] == f'repo/{file_name}'
    assert file_contents in kwargs['body']
    assert kwargs['representation'] == 'wiki'


def test_page_created_with_attached_image(use_temp_dir, wiki_mock):
    """When a new file references an image, the wiki page needs to be created and the
    image needs to be attached to it"""
    file_path = 'hello.md'
    attachment_name = 'some-image.jpg'
    attachment_path = f'images/{attachment_name}'
    file_contents = f'![A cool image]({attachment_path})'

    with open(file_path, mode='w', encoding='utf-8') as file:
        print(file_contents, file=file)

    # The file isn't actually an image, but that's not important
    os.makedirs('images', exist_ok=True)
    with open(attachment_path, mode='w', encoding='utf-8') as attachment:
        print('foobar', file=attachment)

    root_page_id = 12345
    doc_page_id = 67890
    root_page_title = 'My docs'
    space_name = 'SPACE'

    # Root page exists but doc page doesn't
    wiki_mock.get_page_id.side_effect = [root_page_id, None]
    wiki_mock.update_or_create.return_value = {'id': doc_page_id}
    set_up_dummy_environment(space_name, root_page_title)

    wiki_sync.sync_files([file_path])

    wiki_mock.get_page_id.assert_has_calls(
        [
            # First one to find the root, to create the new page under it
            mock.call(space_name, root_page_title),
            # Second one to check whether the page already exists, when looking at
            # the image link
            mock.call(space_name, f'repo/{file_path}'),
        ]
    )
    wiki_mock.update_or_create.assert_called_once()
    wiki_mock.attach_file.assert_called_once_with(
        filename=attachment_path, page_id=doc_page_id
    )


def test_new_image_attachment_to_existing_page(use_temp_dir, wiki_mock):
    """When an existing file starts referencing an image, the image needs to be attached
    to the wiki page"""
    file_path = 'hello.md'
    attachment_name = 'some-image.jpg'
    attachment_path = f'images/{attachment_name}'
    file_contents = f'![A cool image]({attachment_path})'

    with open(file_path, mode='w', encoding='utf-8') as file:
        print(file_contents, file=file)

    # The file isn't actually an image, but that's not important
    os.makedirs('images', exist_ok=True)
    with open(attachment_path, mode='w', encoding='utf-8') as attachment:
        print('foobar', file=attachment)

    root_page_id = 12345
    doc_page_id = 67890
    root_page_title = 'My docs'
    space_name = 'SPACE'

    # Both root page and doc page exist
    wiki_mock.get_page_id.side_effect = [root_page_id, doc_page_id]
    wiki_mock.update_or_create.return_value = {'id': doc_page_id}
    # No existing attachments on the doc page
    wiki_mock.get_attachments_from_content.return_value = {'results': []}
    set_up_dummy_environment(space_name, root_page_title)

    wiki_sync.sync_files([file_path])

    wiki_mock.get_page_id.assert_has_calls(
        [
            # First one to find the root, to create the new page under it
            mock.call(space_name, root_page_title),
            # Second one to check whether the page already exists, when looking at
            # the image link
            mock.call(space_name, f'repo/{file_path}'),
        ]
    )
    wiki_mock.update_or_create.assert_called_once()
    wiki_mock.attach_file.assert_called_once_with(
        filename=attachment_path, page_id=doc_page_id
    )


def test_root_does_not_exist(wiki_mock):
    """#11"""
    set_up_dummy_environment('SPACE', 'My docs')
    wiki_mock.get_page_id.return_value = None

    success = wiki_sync.sync_files(['foo.md'])

    assert not success
    wiki_mock.update_or_create.assert_not_called()


def set_up_dummy_environment(space_name: str, root_page_title: str) -> None:
    os.environ['GITHUB_REPOSITORY'] = 'owner/repo'
    os.environ['INPUT_DEFAULT-GIT-BRANCH'] = 'main'
    os.environ['INPUT_ROOT-PAGE-TITLE'] = root_page_title
    os.environ['INPUT_SPACE-NAME'] = space_name
    os.environ['INPUT_TOKEN'] = ''
    os.environ['INPUT_USER'] = ''
    os.environ['INPUT_WIKI-BASE-URL'] = ''
