import dataclasses
import enum
import logging
import os
import re

import atlassian
import pypandoc

import constants

# GENERAL NOTE about the regex patterns: we want them to be non-greedy
# https://docs.python.org/3/howto/regex.html#greedy-versus-non-greedy

# The format of a link in JIRA markdown is [link name|link]
JIRA_LINK_PATTERN = re.compile(r'\[(.+?)\|(.+?)\]')
# If the link doesn't have a name, then it's simply [link]
JIRA_UNNAMED_LINK_PATTERN = re.compile(r'\[([^|\n]+?)\]')
# The format of an image in JIRA markdown is
# !filename.png! or !some_pic.png|alt=image!
JIRA_SIMPLE_IMG_PATTERN = re.compile(r'!([^|\n]+?)!')
JIRA_IMG_PATTERN_WITH_PARAMS = re.compile(r'!(.+?)\|(.+?)!')


class RelativeLinkType(enum.Enum):
    GENERIC = 0  # [text|link] or [link]
    IMAGE = 1  # !file.ext|alt=text! or !file.ext!


@dataclasses.dataclass
class RelativeLink:
    """Represents a relative link

    Contains information to allow updating the link to something that works on wiki"""

    link_type: RelativeLinkType
    text: str  # Text associated with the link (link name, alt text, ...)
    original_link: str  # Link in the original document. Relative to said document.
    target_path: str  # Path of the file being linked to, from repository root
    wiki_link: str  # Link to be used in the final wiki page


class ContentConverter:
    """A wrapper around Pandoc, with Confluence-specific improvements

    After conversion to JIRA markdown, fixes relative links and keeps a list of files to
    be attached to the page later"""

    def __init__(
        self,
        wiki_client: atlassian.Confluence,
        gh_root: str,
        repo_name: str,
    ) -> str:
        self.wiki_client = wiki_client
        self.gh_root = gh_root
        self.repo_name = repo_name

        self.files_to_attach_to_last_page: list[str] = []

    def convert_file_contents(self, file_path: str) -> str:
        self.files_to_attach_to_last_page = []

        _, file_ext = os.path.splitext(file_path)

        filters = []
        if file_ext == '.rst':
            filters = [f'{constants.PANDOC_FILTERS_FOLDER}/rst_note_warning.lua']

        formated_file_contents = pypandoc.convert_file(
            file_path, 'jira', filters=filters
        )

        return self._replace_relative_links(file_path, formated_file_contents)

    def _replace_relative_links(self, file_path: str, contents: str) -> str:
        links: list[RelativeLink] = []

        for pattern in (
            JIRA_LINK_PATTERN,
            JIRA_UNNAMED_LINK_PATTERN,
            JIRA_SIMPLE_IMG_PATTERN,
            JIRA_IMG_PATTERN_WITH_PARAMS,
        ):
            links.extend(self._extract_relative_links(file_path, contents, pattern))

        if links:
            logging.debug(
                'Found %s relative links in %s: %s', len(links), file_path, links
            )

        for link in links:
            # First we decide what the wiki link will be
            if link.link_type == RelativeLinkType.GENERIC:
                wiki_page_name = f'{self.repo_name}/{link.target_path}'
                wiki_page_info = self.wiki_client.get_page_by_title(
                    os.environ['INPUT_SPACE-NAME'], wiki_page_name
                )
                if wiki_page_info:
                    # The link is to a file that has a Confluence page
                    # Let's link to the page directly
                    target_page_url = (
                        os.environ['INPUT_WIKI-BASE-URL']
                        + '/wiki'
                        + wiki_page_info['_links']['webui']
                    )
                    link.wiki_link = target_page_url
                else:
                    # No existing Confluence page - link to GitHub
                    link.wiki_link = self.gh_root + link.target_path

            elif link.link_type == RelativeLinkType.IMAGE:
                _, attachment_name = os.path.split(link.target_path)
                link.wiki_link = attachment_name

                wiki_page_name = f'{self.repo_name}/{file_path}'
                page_id = self.wiki_client.get_page_id(
                    os.environ['INPUT_SPACE-NAME'], wiki_page_name
                )

                if page_id:
                    self._attach_to_page(page_id, link.target_path)
                else:  # Page doesn't exist yet (is being created)
                    logging.debug(
                        "%s needs to be attached to page %s, which hasn't"
                        ' been created yet',
                        link.target_path,
                        wiki_page_name,
                    )
                    self.files_to_attach_to_last_page.append(link.target_path)

            else:
                raise Exception(f'Unexpected relative link type {link.link_type}')

            # Then we replace the relative links
            contents = self._replace_relative_link(contents, link)

        return contents

    def _extract_relative_links(
        self, file_path: str, file_contents: str, pattern: re.Pattern
    ) -> list[RelativeLink]:
        links: list[RelativeLink] = []

        for matching_groups in re.findall(pattern, file_contents):
            text = target = ''
            link_type = RelativeLinkType.GENERIC
            if pattern == JIRA_LINK_PATTERN:
                text = matching_groups[0]
                target = matching_groups[1]
            elif pattern == JIRA_UNNAMED_LINK_PATTERN:
                text = target = matching_groups
            elif pattern == JIRA_SIMPLE_IMG_PATTERN:
                link_type = RelativeLinkType.IMAGE
                text = target = matching_groups
            elif pattern == JIRA_IMG_PATTERN_WITH_PARAMS:
                link_type = RelativeLinkType.IMAGE
                text = matching_groups[1]
                target = matching_groups[0]
            else:
                raise Exception(f'Unexpected link pattern {pattern}')

            # Most links are HTTP(S) and therefore not relative links - don't waste time
            if target.startswith('http'):
                continue

            # Find the absolute path of the target file
            file_dir = os.path.dirname(file_path)
            target_path = os.path.normpath(os.path.join(file_dir, target))
            if not os.path.exists(target_path):  # Not actually a relative link
                continue

            links.append(
                RelativeLink(
                    link_type=link_type,
                    text=text,
                    original_link=target,
                    target_path=target_path,
                    wiki_link='',  # Will be filled in later
                )
            )

        return links

    def _replace_relative_link(self, text: str, link: RelativeLink) -> str:
        if link.link_type == RelativeLinkType.GENERIC:
            if link.text == link.original_link:
                # This means the JIRA markdown is simply [link]
                # Keep the text and update the link
                return text.replace(
                    f'[{link.original_link}]', f'[{link.text}|{link.wiki_link}]'
                )
            else:  # Normal [text|link] link
                return text.replace(f'|{link.original_link}]', f'|{link.wiki_link}]')

        elif link.link_type == RelativeLinkType.IMAGE:
            if link.text == link.original_link:
                # This means the JIRA markdown is simply !file.ext!
                return text.replace(f'!{link.original_link}!', f'!{link.wiki_link}!')
            else:
                # Image with parameters, like !some_pic.png|alt=image!
                return text.replace(f'!{link.original_link}|', f'!{link.wiki_link}|')

        else:
            logging.warning(
                'Unexpected link type %s - returning text as is.', link.link_type
            )
            return text

    def _attach_to_page(self, page_id: str, attachment_path: str) -> None:
        _, attachment_name = os.path.split(attachment_path)

        # TODO This doesn't handle the case of a doc file including two different
        # images with the same file name (#23)
        logging.debug('Looking for an attachment named %s', attachment_name)
        attachments = self.wiki_client.get_attachments_from_content(
            page_id, filename=attachment_name
        )['results']

        if attachments:
            logging.debug('%s attachment(s) found', len(attachments))
            # TODO Figure out whether we want to update the image (#24)
            # The API doesn't tell us when the file was last updated, so we can't
            # compare that to the last commit on that file
        else:
            logging.info('Attaching file %s to page %s', attachment_path, page_id)
            self.wiki_client.attach_file(filename=attachment_path, page_id=page_id)
