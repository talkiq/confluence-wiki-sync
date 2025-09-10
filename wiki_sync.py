#!/usr/bin/env python3
"""
This tool looks for modified doc files, transforms them into JIRA markdown and
uploads them to Confluence
"""

import logging
import os
import sys

import atlassian

import content_converter


def get_files_to_sync(changed_files: str) -> list[str]:
    return [f for f in changed_files.split('|') if should_sync_file(f)]


def should_sync_file(file_name: str) -> bool:
    # TODO Consider getting a list of extensions from action.yml
    if not (file_name.endswith('.md') or file_name.endswith('.rst')):
        return False

    ignored_folders = os.environ['INPUT_IGNORED-FOLDERS'].split(' ')
    for ignored_folder in ignored_folders:
        if not ignored_folder:
            continue  # Ignore extra spaces

        if not ignored_folder.endswith('/'):
            ignored_folder = ignored_folder + '/'

        if len(os.path.commonprefix([ignored_folder, file_name])) == len(
            ignored_folder
        ):
            logging.info(
                'Skipping file %s because folder %s is ignored',
                file_name,
                ignored_folder,
            )
            return False

    return True


def sync_files(files: list[str]) -> bool:
    """
    param files: List of file paths relative to the repository root
    returns: True if the sync was successful

    The script runs at the root of the repo as well, so the paths are also relative to
    the current script."""
    success = True

    wiki_client = _create_wiki_client()

    root_page_id = _get_root_page_id(wiki_client)
    if not root_page_id:
        return False

    logging.debug('The base root ID is %s', root_page_id)

    github_repo = os.environ['GITHUB_REPOSITORY']  # eg. 'octocat/Hello-World'
    repo_name = github_repo.split('/')[1]

    default_git_branch = os.environ['INPUT_DEFAULT-GIT-BRANCH']
    url_root_for_file = f'https://github.com/{github_repo}/blob/{default_git_branch}/'

    converter = content_converter.ContentConverter(
        wiki_client, url_root_for_file, repo_name
    )

    for file_path in files:
        read_only_warning = (
            '{info:title=Imported content|icon=true}'
            f'This content has been imported from the {repo_name} repository.'
            '\nYou can find (and modify) the original at'
            f' {url_root_for_file + file_path}.{{info}}\n'
            '{warning:title=Do not update this page directly|icon=true}'
            'Your modifications would be lost the next time the source file'
            ' is updated.{warning}\n'
        )

        if not os.path.exists(file_path):
            # See #9
            logging.warning(
                'File %s not found. Deleting a wiki page is not currently'
                ' supported, so you will have to delete it manually',
                file_path,
            )
            continue

        try:
            formatted_content = converter.convert_file_contents(file_path)
            content = read_only_warning + formatted_content
        except Exception:
            logging.exception('Error converting file %s:', file_path)
            success = False
            continue

        try:
            page_id = create_or_update_pages_for_file(
                wiki_client, root_page_id, repo_name, file_path, content
            )
        except Exception:
            logging.exception('Error uploading file %s:', file_path)
            success = False
            continue

        # Image attachments are decided when parsing the JIRA markdown contents of the
        # file. If the file is new in the latest commit, its wiki page hadn't been
        # created at that stage. So we go back and attach these images now.
        for attachment_path in converter.files_to_attach_to_last_page:
            try:
                logging.info('Attaching file %s to page %s', attachment_path, page_id)
                wiki_client.attach_file(filename=attachment_path, page_id=page_id)
            except Exception:
                logging.exception(
                    'Error attaching %s to %s:', attachment_path, file_path
                )
                success = False
                continue

    return success


def _create_wiki_client() -> None:
    return atlassian.Confluence(
        os.environ['INPUT_WIKI-BASE-URL'],
        username=os.environ['INPUT_USER'],
        password=os.environ['INPUT_TOKEN'],
        cloud=True,
    )


def _get_root_page_id(wiki_client) -> None:
    space_name = os.environ['INPUT_SPACE-NAME']
    root_page_title = os.environ['INPUT_ROOT-PAGE-TITLE']
    root_page_id = wiki_client.get_page_id(space_name, root_page_title)

    if not root_page_id:
        logging.error(
            'Could not find root page %s in space %s', root_page_title, space_name
        )
    return root_page_id


def create_or_update_pages_for_file(
    wiki_client: atlassian.Confluence,
    root_page_id: int,
    repo_name: str,
    file_name: str,
    content: str,
) -> str:
    """Returns the ID of the created/updated page"""
    # The git docs live in a tree under the root page, with the same
    # tree structure as in the git repo.
    # We need to navigate the tree to find where the page lives,
    # creating intermediate pages if they don't exist.
    space_name = os.environ['INPUT_SPACE-NAME']
    current_root_id = root_page_id
    file_path, _ = os.path.split(file_name)

    if file_path:
        page_title = repo_name
        for current_folder in file_path.split(os.sep):
            page_title += f'/{current_folder}'
            sub_page_id = wiki_client.get_page_id(space_name, page_title)
            if sub_page_id:
                logging.debug('Page %s exists with id %s', page_title, sub_page_id)
                current_root_id = sub_page_id
            else:  # Page doesn't exist
                logging.info(
                    'Creating intermediate page %s under root %s',
                    page_title,
                    current_root_id,
                )
                response = wiki_client.create_page(
                    space=space_name,
                    title=page_title,
                    body='{children:sort=title|excerpt=none|all=true}',
                    parent_id=current_root_id,
                    representation='wiki',
                )
                current_root_id = response['id']
            logging.debug('Current root ID is %s', current_root_id)

    title = f'{repo_name}/{file_name}'
    logging.info('Creating or updating page %s under root %s', title, current_root_id)
    # TODO Consider making the page read-only
    response = wiki_client.update_or_create(
        parent_id=current_root_id, title=title, body=content, representation='wiki'
    )
    return response['id']


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('atlassian.confluence').setLevel(logging.INFO)
    logging.getLogger('atlassian.rest_client').setLevel(logging.INFO)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.INFO)

    try:
        files_to_sync = get_files_to_sync(os.environ['INPUT_MODIFIED-FILES'])
        logging.info('Files to be synced: %s', files_to_sync)

        sync_success = sync_files(files_to_sync)

        sys.exit(0 if sync_success else 1)
    except Exception:
        logging.exception('Unhandled exception')
        sys.exit(1)
