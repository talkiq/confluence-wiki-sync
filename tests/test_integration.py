"""
End-to-end tests that make sure the correct Confluence pages are
created/updated, and with the correct content
"""
import tempfile
import os
from unittest import mock

import wiki_sync


@mock.patch('wiki_sync.get_repository_root')
@mock.patch('atlassian.Confluence')
def test_page_is_created_under_correct_root(mock_wiki, get_repo_root_mock):
    file_name = 'hello.md'
    file_contents = 'Hello, World'

    with tempfile.TemporaryDirectory() as repo_root:
        get_repo_root_mock.return_value = repo_root

        doc_file_path = os.path.join(repo_root, file_name)
        with open(doc_file_path, mode='w', encoding='utf-8') as doc_file:
            print(file_contents, file=doc_file)

        root_page_id = 12345
        root_page_title = 'My docs'
        space_name = 'SPACE'

        wiki_client = mock_wiki.return_value
        wiki_client.get_page_id.return_value = root_page_id

        os.environ['GITHUB_REPOSITORY'] = 'owner/repo'
        os.environ['INPUT_ROOT-PAGE-TITLE'] = root_page_title
        os.environ['INPUT_SPACE-NAME'] = space_name
        os.environ['INPUT_TOKEN'] = ''
        os.environ['INPUT_USER'] = ''
        os.environ['INPUT_WIKI-BASE-URL'] = ''

        wiki_sync.sync_files([file_name])

        wiki_client.get_page_id.assert_called_once_with(
                space_name, root_page_title)

        call_args_list = wiki_client.update_or_create.call_args_list
        assert len(call_args_list) == 1
        kwargs = call_args_list[0].kwargs
        assert kwargs['parent_id'] == root_page_id
        assert kwargs['title'] == f'repo/{file_name}'
        assert file_contents in kwargs['body']
        assert kwargs['representation'] == 'wiki'
