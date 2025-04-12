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

Run your first script:

```sh
$ python jira/jira_options.py
```

Or to overwrite options on the command line:

```sh
$ python jira/jira_options.py --user user@domain.com --personal-access-token $JIRA_TOKEN --jira-url=https://account.atlassian.net
```
