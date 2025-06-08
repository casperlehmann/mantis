from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from mantis.jira.jira_issues import JiraIssue


class IssueField:
    def __init__(self, issue: 'JiraIssue', key: str) -> None:
        self.issue = issue
        self.key = key

    def _extract_name_from_cached_object(self):
        value_from_cache = self.issue.get_field(self.key)
        assert self.editmeta_type == self.createmeta_type
        if value_from_cache is None:
            #raise ValueError(f'value_from_cache is None for key: {self.key}')
            return None
        elif self.key in ('project', 'status', 'issuetype'):
            return value_from_cache['name']
        elif isinstance(value_from_cache, str):
            assert self.editmeta_type == 'string' and self.createmeta_type == 'string'
            return value_from_cache
        elif self.editmeta_type == 'user' or self.createmeta_type == 'user':
            return value_from_cache.get('displayName')
        elif self.editmeta_type in ('issuelink'):
            return 'issuelink'
        elif self.editmeta_type == 'N/A' and self.createmeta_type == 'N/A':
            raise ValueError(
                f"Both editmeta_type and createmeta_type are N/A. This field ('{self.key}') probably shouldn't be updated like this. editmeta_type: '{self.editmeta_type}'. createmeta_type: '{self.createmeta_type}'.")
        elif self.editmeta_type == 'N/A' or self.createmeta_type == 'N/A':
            raise NotImplementedError(f"editmeta_type == 'N/A' or createmeta_type == 'N/A' for '{self.key}'")
        else:
            return value_from_cache.get('name')

    @property
    def editmeta_schema(self):
        return self.issue.editmeta_factory.field_by_key(self.key)

    @property
    def editmeta_type(self):
        if self.key == 'project':
            # project is not in createmeta because createmeta is specific to the project, e.g.:
            # issue/createmeta/ECS/issuetypes/10001
            return '?'
        elif self.key == 'parent':
            # PUT /rest/api/3/issue/{issueIdOrKey}
            # parent not in https://caspertestaccount.atlassian.net/rest/api/latest/issue/ecs-1/editmeta
            # But docs say it's fine: https://caspertestaccount.atlassian.net/rest/api/latest/issue/ecs-1/
            # The parent field may be set by key or ID. For standard issue types, the parent may be removed by setting update.parent.set.none to true. 
            return '?'
        elif self.key == 'reporter':
            # reporter might be disabled:
            # https://community.developer.atlassian.com/t/issue-createmeta-projectidorkey-issuetypes-issuetypeid-does-not-send-the-reporter-field-anymore/80973
            return 'user'
            # Assign issue endpoint:
            # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-assignee-put
        elif self.key == 'status':
            # To transition an issue, POST tp the dedicated endpoint
            # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-transitions-post
            # https://caspertestaccount.atlassian.net/rest/api/latest/issue/ecs-1/transitions
            # To list transitions, send a GET request
            # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-transitions-get
            return '?'
        elif self.editmeta_schema:
            return self.editmeta_schema['schema']['type']
        else:
            if self.key in self.issue.non_editmeta_fields:
                return 'N/A'
            else:
                raise ValueError(f'Field {self.key} is not in editmeta_schema.')

    @property
    def createmeta_schema(self):
        return self.issue.createmeta_factory.field_by_key(self.key)

    @property
    def createmeta_type(self):
        if self.key == 'project':
            # project is not in createmeta because createmeta is specific to the project, e.g.:
            # issue/createmeta/ECS/issuetypes/10001
            return '?'
        elif self.key == 'parent':
            # PUT /rest/api/3/issue/{issueIdOrKey}
            # parent not in https://caspertestaccount.atlassian.net/rest/api/latest/issue/ecs-1/editmeta
            # But docs say it's fine: https://caspertestaccount.atlassian.net/rest/api/latest/issue/ecs-1/
            # The parent field may be set by key or ID. For standard issue types, the parent may be removed by setting update.parent.set.none to true. 
            return '?'
        elif self.key == 'reporter':
            # reporter might be disabled:
            # https://community.developer.atlassian.com/t/issue-createmeta-projectidorkey-issuetypes-issuetypeid-does-not-send-the-reporter-field-anymore/80973
            return 'user'
            # Assign issue endpoint:
            # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-assignee-put
        elif self.key == 'status':
            # To transition an issue, POST tp the dedicated endpoint
            # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-transitions-post
            # https://caspertestaccount.atlassian.net/rest/api/latest/issue/ecs-1/transitions
            # To list transitions, send a GET request
            # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-transitions-get
            return '?'
        elif self.createmeta_schema:
            return self.createmeta_schema['schema']['type']
        else:
            if self.key in self.issue.non_createmeta_fields:
                return 'N/A'
            else:
                raise ValueError(f'Field {self.key} is not in createmeta_schema.')

    @property
    def value_from_draft(self):
        return self.issue.draft.get(self.key, None)

    def check_field(self) -> bool:
        """Check the existance and status of a field in the issue."""
        # if self.value_from_draft is None:
        #     raise ValueError(f'value_from_cache is None for key: {self.key}')

        if self.createmeta_type == self.editmeta_type == 'N/A':
            if self.key in self.issue.non_meta_fields:
                raise ValueError(f'Expected: Field "{self.key}" cannot be set.')
            else:
                raise ValueError(f'Field "{self.key}" is in neither createmeta nor editmeta schema.')

        if self.editmeta_type != self.createmeta_type:
            raise ValueError(f'editmeta_type ({self.editmeta_type}) and createmeta_type ({self.createmeta_type}) are not equal')
        
        name_from_cache = self._extract_name_from_cached_object()
        # create_auto_complete_url = self.issue.createmeta_data["fields"][self.key].get("autoCompleteUrl") if self.key in self.issue.createmeta_data["fields"] else None
        edit_auto_complete_url = self.issue.editmeta_data["fields"][self.key].get("autoCompleteUrl") if self.key in self.issue.editmeta_data["fields"] else None
        # assert create_auto_complete_url == edit_auto_complete_url, f'{create_auto_complete_url} != {edit_auto_complete_url}'
        type_part = f'(type: {self.editmeta_type}):'
        update_part = f'{str(name_from_cache)}' if name_from_cache == self.value_from_draft else f'{name_from_cache} -> {self.value_from_draft}'

        print(f'{self.key:<10} {type_part:<20} {update_part:<35} (autoCompleteUrl: {edit_auto_complete_url})')
        return True

    @property
    def payload(self):
        if self.editmeta_type in {'string'}:
            pass
        elif self.editmeta_type in {'issuetype', 'user'}:
            pass
        elif self.editmeta_type in {'team'}:
            raise NotImplementedError('Convert team name to id.')
            return self.value_from_draft
        else:
            raise NotImplementedError(f'Type: {self.editmeta_type}')

    def update_field_from_draft(self):
        data = {
            "fields": {
                self.key: self.payload
            }
        }
