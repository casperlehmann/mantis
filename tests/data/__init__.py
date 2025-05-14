import json

from .update_projects_cache_response import update_projects_cache_response
from .get_issuetypes_response import get_issuetypes_response

class CacheData:
    with open('tests/data/jira_cache/issues/ECS-1.json', 'r') as f:
        ecs_1 = json.load(f)

    with open('tests/data/jira_cache/issues/ECS-2.json', 'r') as f:
        ecs_2 = json.load(f)

    with open('tests/data/jira_cache/issues/ECS-3.json', 'r') as f:
        ecs_3 = json.load(f)

    with open('tests/data/jira_cache/issues/ECS-4.json', 'r') as f:
        ecs_4 = json.load(f)

    with open('tests/data/jira_cache/issues/ECS-5.json', 'r') as f:
        ecs_5 = json.load(f)

    with open('tests/data/jira_cache/issues/ECS-6.json', 'r') as f:
        ecs_6 = json.load(f)

    with open('tests/data/jira_cache/system/issuetypes.json', 'r') as f:
        issuetypes = json.load(f)

    with open('tests/data/jira_cache/system/projects.json', 'r') as f:
        projects = json.load(f)

    with open('tests/data/jira_cache/system/issuetype_fields/createmeta_bug.json', 'r') as f:
        createmeta_bug = json.load(f)

    with open('tests/data/jira_cache/system/issuetype_fields/createmeta_epic.json', 'r') as f:
        createmeta_epic = json.load(f)

    with open('tests/data/jira_cache/system/issuetype_fields/createmeta_story.json', 'r') as f:
        createmeta_story = json.load(f)

    with open('tests/data/jira_cache/system/issuetype_fields/createmeta_subtask.json', 'r') as f:
        createmeta_subtask = json.load(f)

    with open('tests/data/jira_cache/system/issuetype_fields/createmeta_task.json', 'r') as f:
        createmeta_task = json.load(f)
