# Mantis

Quick actions for Jira.

## Getting started

Setup environment with venv:

```sh
$ python -m venv .venv
$ . .venv/bin/activate
$ pip install -r requirements.txt
```

Fill out the options toml:

```sh
$ cp options-example.toml options.toml
$ vi options.toml
```

Run the tests:

```sh
pytest
```

Run also the tests marked as skipped (Note: This will make calls to Jira api if configured):

```sh
EXECUTE_SKIPPED=1 pytest
```

Run tests every time a file changes (using `pytest-xdist`):

```sh
pytest -f
```

Run your first script:

```sh
$ python main.py TASK-1
[TASK-1] Setup Jira

$ python main.py --action fetch-issuetypes
Updated local cache for issuetypes:
[{'description': 'Created by Jira Agile - do not edit or delete. Issue type '
                 'for a user story.',
  'id': 6,
  'name': 'Story'},
[...]
```

Or to overwrite options on the command line:

```sh
$ python jira/jira_options.py --user user@domain.com --personal-access-token $JIRA_TOKEN --jira-url=https://account.atlassian.net
```

