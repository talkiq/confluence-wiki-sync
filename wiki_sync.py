#!/usr/bin/env python3
"""
This tool looks for modified doc files, transforms them into JIRA markdown and
uploads them to Confluence
"""

import logging
import os
import re
import subprocess
import sys
from typing import Dict, List

import atlassian
import pypandoc


# The format of a link in JIRA markdown is [link name|link]
# We only need a capture group for the link itself
# TODO handle links like [link], which happen when the link name is the same as
# the link itself
JIRA_LINK_PATTERN = re.compile(r'\[[^|\n]+\|([^|\n]+)\]')


def get_files_to_sync(changed_files: str) -> List[str]:
    return [f for f in changed_files.split() if should_sync_file(f)]


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


def sync_files(files: List[str]) -> bool:
    had_errors = False

    wiki_client = atlassian.Confluence(
        os.environ['INPUT_WIKI-BASE-URL'],
        username=os.environ['INPUT_USER'],
        password=os.environ['INPUT_TOKEN'],
        cloud=True,
    )

    root_page_id = wiki_client.get_page_id(
        os.environ['INPUT_SPACE-NAME'], os.environ['INPUT_ROOT-PAGE-TITLE']
    )
    logging.debug('The base root ID is %s', root_page_id)

    github_repo = os.environ['GITHUB_REPOSITORY']  # eg. 'octocat/Hello-World'
    # TODO consider getting the name of the default branch and using that
    # instead of HEAD
    # Could be an optional parameter in action.yml
    url_root_for_file = f'https://github.com/{github_repo}/blob/HEAD/'
    repo_name = github_repo.split('/')[1]

    repo_root = get_repository_root()

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
        absolute_file_path = os.path.join(repo_root, file_path)

        if not os.path.exists(absolute_file_path):
            # TODO delete corresponding wiki page
            logging.warning(
                'File %s not found. Deleting a wiki page is not currently'
                ' supported, so you will have to delete it manually',
                absolute_file_path,
            )
            continue

        try:
            formatted_content = get_formatted_file_content(
                wiki_client, repo_root, file_path, url_root_for_file, repo_name
            )
            content = read_only_warning + formatted_content
        except Exception:
            logging.exception('Error converting file %s:', absolute_file_path)
            had_errors = True
            continue

        try:
            create_or_update_pages_for_file(
                wiki_client, root_page_id, repo_name, file_path, content
            )
        except Exception:
            logging.exception('Error uploading file %s:', absolute_file_path)
            had_errors = True
            continue

    return had_errors


def get_formatted_file_content(
    wiki_client: atlassian.Confluence,
    repo_root: str,
    file_path: str,
    gh_root: str,
    repo_name: str,
) -> str:
    """
    Takes the absolute path of a file and returns its contents formatted as
    JIRA markdown.

    Updates relative links to point to a Confluence page if it exists, or to a
    GitHub page.
    """
    # keys are relative links; values are what they should be replaced with
    links_to_replace: Dict[str, str] = {}

    absolute_file_path = os.path.join(repo_root, file_path)
    formated_file_contents = pypandoc.convert_file(absolute_file_path, 'jira')

    for link in re.findall(JIRA_LINK_PATTERN, formated_file_contents):
        # Most links are HTTP - don't waste time with them
        if link.startswith('http'):
            continue

        target_path = os.path.join(os.path.split(absolute_file_path)[0], link)
        target_path = os.path.normpath(target_path)
        if not os.path.exists(target_path):  # Not actually a relative link
            continue

        target_from_root = os.path.relpath(target_path, start=repo_root)

        wiki_page_info = wiki_client.get_page_by_title(
            os.environ['INPUT_SPACE-NAME'], f'{repo_name}/{target_from_root}'
        )
        if wiki_page_info:
            # The link is to a file that has a Confluence page
            # Let's link to the page directly
            target_page_url = (
                os.environ['INPUT_WIKI-BASE-URL']
                + '/wiki'
                + wiki_page_info['_links']['webui']
            )
            links_to_replace[link] = target_page_url
        else:
            # No existing Confluence page - link to GitHub
            links_to_replace[link] = gh_root + target_from_root

    # Replace relative links
    for relative_link, new_link in links_to_replace.items():
        formated_file_contents = formated_file_contents.replace(
            f'|{relative_link}]', f'|{new_link}]'
        )

    return formated_file_contents


def get_repository_root() -> str:
    repo_root = ''
    with subprocess.Popen(
        ['git', 'rev-parse', '--show-toplevel'], stdout=subprocess.PIPE
    ) as proc:
        repo_root = proc.communicate()[0].rstrip().decode('utf-8')
    return repo_root


def create_or_update_pages_for_file(
    wiki_client: atlassian.Confluence,
    root_page_id: int,
    repo_name: str,
    file_name: str,
    content: str,
) -> None:
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
    wiki_client.update_or_create(
        parent_id=current_root_id, title=title, body=content, representation='wiki'
    )


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    try:
        files_to_sync = get_files_to_sync(os.environ['INPUT_MODIFIED-FILES'])
        logging.info('Files to be synced: %s', files_to_sync)

        had_sync_errors = sync_files(files_to_sync)

        sys.exit(1 if had_sync_errors else 0)
    except Exception:
        logging.exception('Unhandled exception')
        sys.exit(1)
