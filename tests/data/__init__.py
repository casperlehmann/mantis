import json
from typing import Any

from .update_projects_cache_response import update_projects_cache_response
from .get_issuetypes_response import get_issuetypes_response

class CacheData:
    @property
    def ecs_1(self) -> Any:
        with open('tests/data/jira_cache/issues/ECS-1.json', 'r') as f:
            return json.load(f)

    @property
    def ecs_2(self) -> Any:
        with open('tests/data/jira_cache/issues/ECS-2.json', 'r') as f:
            return json.load(f)

    @property
    def ecs_3(self) -> Any:
        with open('tests/data/jira_cache/issues/ECS-3.json', 'r') as f:
            return json.load(f)

    @property
    def ecs_4(self) -> Any:
        with open('tests/data/jira_cache/issues/ECS-4.json', 'r') as f:
            return json.load(f)

    @property
    def ecs_5(self) -> Any:
        with open('tests/data/jira_cache/issues/ECS-5.json', 'r') as f:
            return json.load(f)

    @property
    def ecs_6(self) -> Any:
        with open('tests/data/jira_cache/issues/ECS-6.json', 'r') as f:
            return json.load(f)

    @property
    def issuetypes(self) -> Any:
        with open('tests/data/jira_cache/system/issuetypes.json', 'r') as f:
            return json.load(f)

    @property
    def projects(self) -> Any:
        with open('tests/data/jira_cache/system/projects.json', 'r') as f:
            return json.load(f)

    @property
    def createmeta_bug(self) -> Any:
        with open('tests/data/jira_cache/system/createmeta/createmeta_bug.json', 'r') as f:
            return json.load(f)

    @property
    def createmeta_epic(self) -> Any:
        with open('tests/data/jira_cache/system/createmeta/createmeta_epic.json', 'r') as f:
            return json.load(f)

    @property
    def createmeta_story(self) -> Any:
        with open('tests/data/jira_cache/system/createmeta/createmeta_story.json', 'r') as f:
            return json.load(f)

    @property
    def createmeta_subtask(self) -> Any:
        with open('tests/data/jira_cache/system/createmeta/createmeta_subtask.json', 'r') as f:
            return json.load(f)

    @property
    def createmeta_task(self) -> Any:
        with open('tests/data/jira_cache/system/createmeta/createmeta_task.json', 'r') as f:
            return json.load(f)
