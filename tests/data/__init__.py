import json

from .update_projects_cache_response import update_projects_cache_response
from .get_issuetypes_response import get_issuetypes_response

class CacheData:
    @property
    def ecs_1(self):
        with open('tests/data/jira_cache/issues/ECS-1.json', 'r') as f:
            return json.load(f)

    @property
    def ecs_2(self):
        with open('tests/data/jira_cache/issues/ECS-2.json', 'r') as f:
            return json.load(f)

    @property
    def ecs_3(self):
        with open('tests/data/jira_cache/issues/ECS-3.json', 'r') as f:
            return json.load(f)

    @property
    def ecs_4(self):
        with open('tests/data/jira_cache/issues/ECS-4.json', 'r') as f:
            return json.load(f)

    @property
    def ecs_5(self):
        with open('tests/data/jira_cache/issues/ECS-5.json', 'r') as f:
            return json.load(f)

    @property
    def ecs_6(self):
        with open('tests/data/jira_cache/issues/ECS-6.json', 'r') as f:
            return json.load(f)

    @property
    def issuetypes(self):
        with open('tests/data/jira_cache/system/issuetypes.json', 'r') as f:
            return json.load(f)

    @property
    def projects(self):
        with open('tests/data/jira_cache/system/projects.json', 'r') as f:
            return json.load(f)

    @property
    def createmeta_bug(self):
        with open('tests/data/jira_cache/system/issuetype_fields/createmeta_bug.json', 'r') as f:
            return json.load(f)

    @property
    def createmeta_epic(self):
        with open('tests/data/jira_cache/system/issuetype_fields/createmeta_epic.json', 'r') as f:
            return json.load(f)

    @property
    def createmeta_story(self):
        with open('tests/data/jira_cache/system/issuetype_fields/createmeta_story.json', 'r') as f:
            return json.load(f)

    @property
    def createmeta_subtask(self):
        with open('tests/data/jira_cache/system/issuetype_fields/createmeta_subtask.json', 'r') as f:
            return json.load(f)

    @property
    def createmeta_task(self):
        with open('tests/data/jira_cache/system/issuetype_fields/createmeta_task.json', 'r') as f:
            return json.load(f)
