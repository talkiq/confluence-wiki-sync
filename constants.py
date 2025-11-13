import os

if os.environ.get('GITHUB_ACTIONS'):
    # When running as a GitHub Action, this script runs inside the /github/workspace
    # directory, whereas the wiki-sync files are under /app (see the Dockerfile)
    APP_FOLDER = '../../app/'
else:
    # Otherwise, we're running the script from the base folder
    # NOTE: One day, we'll put the Python files under an src/ subfolder - see issue #75
    APP_FOLDER = ''

PANDOC_FILTERS_FOLDER = os.path.join(APP_FOLDER, 'pandoc_filters')
