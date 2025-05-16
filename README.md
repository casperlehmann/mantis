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

# Re-fetches config files
$ python main.py --action reset
['Epic', 'Subtask', 'Task', 'Story', 'Bug']

# Fornat the fetched json in the Jira cache
$ find .jira_cache -type f -name '*.json' -exec sh -c 'jq . "$1" > "$1.tmp" && mv "$1.tmp" "$1"' _ {} \;
```

For iterative testing, we can rely on the functions defined in `scripts/development-functions.sh` to reset and/or re-populate the cache and drafts directory:

```sh
reset_cache() {
  python main.py --action reset
}

jsonfmt() {
  python main.py --action reset
  find .jira_cache -type f -name '*.json' -exec sh -c 'jq . "$1" > "$1.tmp" && mv "$1.tmp" "$1"' _ {} \;
}

getandfmt() {
  jsonfmt
  python main.py --action get-issue ECS-1 ECS-2 ECS-3 ECS-4 ECS-5 ECS-6
}
```

Or to overwrite options on the command line (remember to set the JIRA_TOKEN env var):

```sh
$ python main.py \
    --user user@domain.com \
    --personal-access-token $JIRA_TOKEN \
    --jira-url=https://account.atlassian.net
[...]
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

See functions in `development-functions.sh`:

```sh
run_coverage() {
  pytest --cov
}

show_coverage() {
  pytest --cov-report html --cov
  open htmlcov/index.html
}
```

An example of the coverage report:

![Markdown coverage report](docs/img/pytest-coverage-html-report.png)

## Running MyPy

Ensuring typehint coverage (this is also run during [GitHub Actions](.github/workflows/python-app-ci.yml)).

```
$ mypy --disallow-untyped-calls --disallow-untyped-defs --disallow-incomplete-defs mantis
Success: no issues found in 10 source files
```

## Running Flake8

```sh
$ flake8 mantis --count --select=E9,F63,F7,F82 --show-source --statistics                 
0
$ $flake8 mantis --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
mantis/jira/__init__.py:1:1: F401 '.jira_auth.JiraAuth' imported but unused
mantis/jira/__init__.py:2:1: F401 '.jira_client.JiraClient' imported but unused
mantis/jira/__init__.py:3:1: F401 '.jira_issues.JiraIssue' imported but unused
mantis/jira/__init__.py:3:1: F401 '.jira_issues.JiraIssues' imported but unused
mantis/jira/__init__.py:4:1: F401 '.jira_options.JiraOptions' imported but unused
mantis/jira/__init__.py:4:1: F401 '.jira_options.parse_args' imported but unused
mantis/jira/__init__.py:5:1: F401 '.utils.JiraSystemConfigLoader' imported but unused
mantis/jira/utils/__init__.py:1:1: F401 '.cache.Cache' imported but unused
mantis/jira/utils/__init__.py:2:1: F401 '.jira_system_config_loader.JiraSystemConfigLoader' imported but unused
mantis/jira/utils/__init__.py:3:1: F401 '.jira_types.IssueType' imported but unused
mantis/jira/utils/__init__.py:3:1: F401 '.jira_types.IssueTypeFields' imported but unused
mantis/jira/utils/__init__.py:3:1: F401 '.jira_types.Project' imported but unused
12    F401 '.jira_auth.JiraAuth' imported but unused
12
```

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

# Persisting example payloads for tests

```sh
python main.py --action=reset
python main.py --action=get-issue ECS-1 ECS-2 ECS-3 ECS-4 ECS-5 ECS-6
[ECS-1] (Sample) User Authentication
[ECS-2] (Sample) Payment Processing
[ECS-3] (Sample) Credit Card Payment Integration
[ECS-4] (Sample) User Registration
[ECS-5] (Sample) Order Confirmation
[ECS-6] (Sample) User Login
```

# Copy to test data

Copy demo data to the test directory:

```sh
cp -rf drafts/ tests/data/drafts
cp -rf .jira_cache/* tests/data/jira_cache/
```

Format the JSON files using `jq`:

```sh
find tests/data/jira_cache -type f -name '*.json' -exec sh -c 'jq . "$1" > "$1.tmp" && mv "$1.tmp" "$1"' _ {} \;
```

Then anonomize the files:

```sh
find tests/data/ -type f -name '*.json' -exec sh -c '
  for file do
    # Format JSON with jq, then replace emails
    tmp="${file}.tmp"
    if jq . "$file" > "$tmp"; then
      # Replace emails with dummy value (e.g., dummy@example.com)
      sed -E -i.bak "s/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/dummy@example.com/g" "$tmp"
      mv "$tmp" "$file"
      rm "$tmp.bak"
    else
      echo "Invalid JSON: $file"
      rm -f "$tmp"
    fi
  done
' sh {} +
```

All in one function in `development-functions.sh`:

```sh
update_test_data() {
    cp -rf drafts/ tests/data/drafts
    cp -rf .jira_cache/* tests/data/jira_cache/
    format_test_data
    anonymize_test_data
}
```
