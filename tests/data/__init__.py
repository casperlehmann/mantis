import json
from typing import Any

from tests.data.get_issuetypes_response import get_issuetypes_response
from tests.data.get_names import get_names
from tests.data.update_projects_cache_response import update_projects_cache_response


class CacheData:
    @property
    def ecs_1(self) -> dict:
        with open('tests/data/jira_cache/issues/ECS-1.json', 'r') as f:
            return json.load(f)

    @property
    def ecs_2(self) -> dict:
        with open('tests/data/jira_cache/issues/ECS-2.json', 'r') as f:
            return json.load(f)

    @property
    def ecs_3(self) -> dict:
        with open('tests/data/jira_cache/issues/ECS-3.json', 'r') as f:
            return json.load(f)

    @property
    def ecs_4(self) -> dict:
        with open('tests/data/jira_cache/issues/ECS-4.json', 'r') as f:
            return json.load(f)

    @property
    def ecs_5(self) -> dict:
        with open('tests/data/jira_cache/issues/ECS-5.json', 'r') as f:
            return json.load(f)

    @property
    def ecs_6(self) -> dict:
        with open('tests/data/jira_cache/issues/ECS-6.json', 'r') as f:
            return json.load(f)

    @property
    def issuetypes(self) -> dict:
        with open('tests/data/jira_cache/system/issuetypes.json', 'r') as f:
            return json.load(f)

    @property
    def projects(self) -> dict:
        with open('tests/data/jira_cache/system/projects.json', 'r') as f:
            return json.load(f)

    @property
    def createmeta_bug(self) -> dict:
        with open('tests/data/jira_cache/system/createmeta/createmeta_bug.json', 'r') as f:
            return json.load(f)

    @property
    def createmeta_epic(self) -> dict:
        with open('tests/data/jira_cache/system/createmeta/createmeta_epic.json', 'r') as f:
            return json.load(f)

    @property
    def createmeta_story(self) -> dict:
        with open('tests/data/jira_cache/system/createmeta/createmeta_story.json', 'r') as f:
            return json.load(f)

    @property
    def createmeta_subtask(self) -> dict:
        with open('tests/data/jira_cache/system/createmeta/createmeta_subtask.json', 'r') as f:
            return json.load(f)

    @property
    def createmeta_task(self) -> dict:
        with open('tests/data/jira_cache/system/createmeta/createmeta_task.json', 'r') as f:
            return json.load(f)

    @property
    def placeholder_account(self) -> dict[str, str]:
        return {
            "accountId": "492581:638245r0-3d02-ki30-kchs-3kjd92hafjmz",
            "emailAddress": "marcus@rome.gov",
            "displayName": "Marcus Aurelius",
        }

    @property
    def get_names(self) -> dict[str, Any]:
        # issue/ECS-2?expand=names
        return get_names

all = {
    "get_issuetypes_response": get_issuetypes_response,
    "update_projects_cache_response": update_projects_cache_response,
    # "CacheData": CacheData,
    # "get_names": get_names,
}
