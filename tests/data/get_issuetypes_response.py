get_issuetypes_response = {
    "startAt": 0,
    "maxResults": 50,
    "total": 5,
    "issueTypes": [
        {
            "self": "https://caspertestaccount.atlassian.net/rest/api/3/issuetype/99999",
            "id": "99999",
            "description": "Fake type for testing.",
            "iconUrl": "https://notreal.com",
            "name": "Testtype",
            "untranslatedName": "Testtype",
            "subtask": False,
            "avatarId": 99999,
            "hierarchyLevel": -1,
            "scope": {
                "type": "PROJECT",
                "project": {
                    "id": "10000"
                }
            }
        },
        {
            "self": "https://caspertestaccount.atlassian.net/rest/api/3/issuetype/10009",
            "id": "10009",
            "description": "Subtasks track small pieces of work that are part of a larger task.",
            "iconUrl": "https://caspertestaccount.atlassian.net/rest/api/2/universal_avatar/view/type/issuetype/avatar/10316?size=medium",
            "name": "Subtask",
            "untranslatedName": "Subtask",
            "subtask": True,
            "avatarId": 10316,
            "hierarchyLevel": -1,
            "scope": {
                "type": "PROJECT",
                "project": {
                    "id": "10001"
                }
            }
        },
        {
            "self": "https://caspertestaccount.atlassian.net/rest/api/3/issuetype/10002",
            "id": "10002",
            "description": "Subtasks track small pieces of work that are part of a larger task.",
            "iconUrl": "https://caspertestaccount.atlassian.net/rest/api/2/universal_avatar/view/type/issuetype/avatar/10316?size=medium",
            "name": "Subtask",
            "untranslatedName": "Subtask",
            "subtask": True,
            "avatarId": 10316,
            "hierarchyLevel": -1,
            "scope": {
                "type": "PROJECT",
                "project": {
                    "id": "10000"
                }
            }
        },
        {
            "self": "https://caspertestaccount.atlassian.net/rest/api/3/issuetype/10004",
            "id": "10004",
            "description": "Stories track functionality or features expressed as user goals.",
            "iconUrl": "https://caspertestaccount.atlassian.net/rest/api/2/universal_avatar/view/type/issuetype/avatar/10315?size=medium",
            "name": "Story",
            "untranslatedName": "Story",
            "subtask": False,
            "avatarId": 10315,
            "hierarchyLevel": 0,
            "scope": {
                "type": "PROJECT",
                "project": {
                    "id": "10000"
                }
            }
        },
        {
            "self": "https://caspertestaccount.atlassian.net/rest/api/3/issuetype/10005",
            "id": "10005",
            "description": "Bugs track problems or errors.",
            "iconUrl": "https://caspertestaccount.atlassian.net/rest/api/2/universal_avatar/view/type/issuetype/avatar/10303?size=medium",
            "name": "Bug",
            "untranslatedName": "Bug",
            "subtask": False,
            "avatarId": 10303,
            "hierarchyLevel": 0,
            "scope": {
                "type": "PROJECT",
                "project": {
                    "id": "10000"
                }
            }
        },
        {
            "self": "https://caspertestaccount.atlassian.net/rest/api/3/issuetype/10003",
            "id": "10003",
            "description": "Tasks track small, distinct pieces of work.",
            "iconUrl": "https://caspertestaccount.atlassian.net/rest/api/2/universal_avatar/view/type/issuetype/avatar/10318?size=medium",
            "name": "Task",
            "untranslatedName": "Task",
            "subtask": False,
            "avatarId": 10318,
            "hierarchyLevel": 0,
            "scope": {
                "type": "PROJECT",
                "project": {
                    "id": "10000"
                }
            }
        },
        {
            "self": "https://caspertestaccount.atlassian.net/rest/api/3/issuetype/10007",
            "id": "10007",
            "description": "Stories track functionality or features expressed as user goals.",
            "iconUrl": "https://caspertestaccount.atlassian.net/rest/api/2/universal_avatar/view/type/issuetype/avatar/10300?size=medium",
            "name": "Story",
            "untranslatedName": "Story",
            "subtask": False,
            "avatarId": 10300,
            "hierarchyLevel": 0
        },
        {
            "self": "https://caspertestaccount.atlassian.net/rest/api/3/issuetype/10006",
            "id": "10006",
            "description": "Tasks track small, distinct pieces of work.",
            "iconUrl": "https://caspertestaccount.atlassian.net/rest/api/2/universal_avatar/view/type/issuetype/avatar/10318?size=medium",
            "name": "Task",
            "untranslatedName": "Task",
            "subtask": False,
            "avatarId": 10318,
            "hierarchyLevel": 0,
            "scope": {
                "type": "PROJECT",
                "project": {
                    "id": "10001"
                }
            }
        },
        {
            "self": "https://caspertestaccount.atlassian.net/rest/api/3/issuetype/10001",
            "id": "10001",
            "description": "Epics track collections of related bugs, stories, and tasks.",
            "iconUrl": "https://caspertestaccount.atlassian.net/rest/api/2/universal_avatar/view/type/issuetype/avatar/10307?size=medium",
            "name": "Epic",
            "untranslatedName": "Epic",
            "subtask": False,
            "avatarId": 10307,
            "hierarchyLevel": 1,
            "scope": {
                "type": "PROJECT",
                "project": {
                    "id": "10000"
                }
            }
        },
        {
            "self": "https://caspertestaccount.atlassian.net/rest/api/3/issuetype/10000",
            "id": "10000",
            "description": "A big user story that needs to be broken down. Created by Jira Software - do not edit or delete.",
            "iconUrl": "https://caspertestaccount.atlassian.net/images/icons/issuetypes/epic.svg",
            "name": "Epic",
            "untranslatedName": "Epic",
            "subtask": False,
            "hierarchyLevel": 1
        },
        {
            "self": "https://caspertestaccount.atlassian.net/rest/api/3/issuetype/10008",
            "id": "10008",
            "description": "Epics track collections of related bugs, stories, and tasks.",
            "iconUrl": "https://caspertestaccount.atlassian.net/rest/api/2/universal_avatar/view/type/issuetype/avatar/10307?size=medium",
            "name": "Epic",
            "untranslatedName": "Epic",
            "subtask": False,
            "avatarId": 10307,
            "hierarchyLevel": 1,
            "scope": {
                "type": "PROJECT",
                "project": {
                    "id": "10001"
                }
            }
        }
    ]
}