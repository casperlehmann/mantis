# Mantis

Command line interface for writing and maintaining your Jira tasks from the command line.
Edit locally in your preferred editor and sync to Jira when ready.

## Getting started

### Setup environment with venv:

```sh
$ python -m venv .venv
$ . .venv/bin/activate
$ pip install -r requirements.txt
```

### Generate a Jira token:

Head over to your Jira and under [manage-profile / security 
/ api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens),
click on `Create API token`

> [!WARNING]
> Don't share this code with anyone, please read the official Jira docs on
[API authentication](https://developer.atlassian.com/cloud/jira/platform/basic-auth-for-rest-apis/))
and [API tokens](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/)
if you need more information.

### Fill out the options toml:

```sh
$ cp options-example.toml options.toml
$ vi options.toml
```

Your `options.toml` needs to be filled out with your personal data,
including the Jira token you just created.
It should **not** be added to source control.
You new file should look something like the following example:

```toml
[jira]
user = "name@company.com"
url = "https://company-account.atlassian.net"
project = "TEAMNAME"
personal-access-token = "qwerqwer-asdfasdf-zxcvzxcv"
cache-dir = ".jira_cache"
```

### Then run the tests:

```sh
$ pytest
```

## Running the CLI

```sh
$ python main.py --action test-auth
Connected as user: Admin9000

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

Or to overwrite options on the command line (remember to set the JIRA_TOKEN env var):

```sh
$ python mantis/jira/jira_options.py \
    --user user@domain.com \
    --personal-access-token $JIRA_TOKEN \
    --jira-url=https://account.atlassian.net
JiraOptions successfully instantiated
```

## Extended testing

```sh
$ pytest

#Run also the tests marked as skipped (Note: This will make calls to Jira api if configured):
$ EXECUTE_SKIPPED=1 pytest

# Run tests every time a file changes (using `pytest-xdist`):
$ pytest -f

# Show test coverage for each file
$ pytest --cov

# Generate coverage report (written to ./htmlcov)
$ pytest --cov-report html --cov
```

An example of the coverage report:

![Markdown coverage report](docs/img/pytest-coverage-html-report.png)

# Generate types

```python
from plugins import model
for x in dir(model): print (x)
... 
Assignee
Attachment
AvatarUrls
BaseModel
Components
Configuration
Customfield10001
Customfield10002
Customfield10003
[...]
```

