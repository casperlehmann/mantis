from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from mantis.jira.jira_issues import JiraIssue


class IssueField:
    def __init__(self, issue: 'JiraIssue', key) -> None:
        self.issue = issue
        self.key = key

    def _extract_name_from_cached_object(self, editmeta_type: str, createmeta_type: str):
        value_from_cache = self.issue.get_field(self.key)
        if value_from_cache is None:
            #raise ValueError(f'value_from_cache is None for key: {key}')
            name_from_cache = None
        elif self.key in ('project', 'status'):
            name_from_cache = value_from_cache['name']
        elif isinstance(value_from_cache, str):
            assert editmeta_type == 'string' and createmeta_type == 'string'
            name_from_cache = value_from_cache
        elif editmeta_type == 'user' or createmeta_type == 'user':
            name_from_cache = value_from_cache.get('displayName')
        elif editmeta_type in ('issuelink', 'issuetype'):
            name_from_cache = 'issuelink/issuetype'
        elif editmeta_type == 'N/A' and createmeta_type == 'N/A':
            raise ValueError(
                f"Both editmeta_type and createmeta_type are N/A. This field ('{self.key}') probably shouldn't be updated like this. editmeta_type: '{editmeta_type}'. createmeta_type: '{createmeta_type}'.")
        elif editmeta_type == 'N/A' or createmeta_type == 'N/A':
            raise NotImplementedError(f"editmeta_type == 'N/A' or createmeta_type == 'N/A' for '{self.key}'")
        else:
            name_from_cache = value_from_cache.get('name')
        return name_from_cache

    def _extract_meta_types(self, key: str) -> tuple[str, str]:
        createmeta_schema = self.issue.createmeta_factory.field_by_key(key)
        editmeta_schema = self.issue.editmeta_factory.field_by_key(key)
        if key == 'project':
            # project is not in createmeta because createmeta is specific to the project, e.g.:
            # issue/createmeta/ECS/issuetypes/10001
            createmeta_type = '?'
            editmeta_type = '?'
        elif key == 'parent':
            # PUT /rest/api/3/issue/{issueIdOrKey}
            # parent not in https://caspertestaccount.atlassian.net/rest/api/latest/issue/ecs-1/editmeta
            # But docs say it's fine: https://caspertestaccount.atlassian.net/rest/api/latest/issue/ecs-1/
            # The parent field may be set by key or ID. For standard issue types, the parent may be removed by setting update.parent.set.none to true. 
            createmeta_type = '?'
            editmeta_type = '?'
        elif key == 'reporter':
            # reporter might be disabled:
            # https://community.developer.atlassian.com/t/issue-createmeta-projectidorkey-issuetypes-issuetypeid-does-not-send-the-reporter-field-anymore/80973
            createmeta_type = 'user'
            editmeta_type = 'user'
            # Assign issue endpoint:
            # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-assignee-put
        elif key == 'status':
            # To transition an issue, POST tp the dedicated endpoint
            # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-transitions-post
            # https://caspertestaccount.atlassian.net/rest/api/latest/issue/ecs-1/transitions
            # To list transitions, send a GET request
            # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-transitions-get
            createmeta_type = '?'
            editmeta_type = '?'
        elif not (editmeta_schema or createmeta_schema):
            if key in self.issue.non_meta_fields:
                raise ValueError(f'Expected: Field "{key}" cannot be set.')
            else:
                raise ValueError(f'Field "{key}" is in neither createmeta nor editmeta schema.')
        elif not editmeta_schema:
            assert createmeta_schema
            if key in self.issue.non_editmeta_fields:
                editmeta_type = 'N/A'
                createmeta_type = createmeta_schema['schema']['type']
            else:
                raise ValueError(f'Field {key} is not in editmeta_schema.')
        elif not createmeta_schema:
            if key in self.issue.non_createmeta_fields:
                createmeta_type = 'N/A'
                editmeta_type = editmeta_schema['schema']['type']
            else:
                raise ValueError(f'Field {key} is not in createmeta_schema.')
        else:
            editmeta_type = editmeta_schema['schema']['type']
            createmeta_type = createmeta_schema['schema']['type']
        return editmeta_type, createmeta_type
