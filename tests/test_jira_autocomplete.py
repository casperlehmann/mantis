from mantis.jira.jira_client import JiraClient


class TestJiraAutocomplete:
    def test_get_suggestions(self, fake_jira: JiraClient, requests_mock):
        return_value = {'results': [{'value': 'abc123', 'displayName': '<b>Marcus</b> Aurelius - <b>marcus</b>@rome.gov'}]}
        requests_mock.get(fake_jira.api_url + '/jql/autocompletedata/suggestions?fieldName=reporter&fieldValue=Marcus', json=return_value)
        suggestions = fake_jira.auto_complete.get_suggestions('reporter', 'Marcus')
        assert len(suggestions) == 1
        assert suggestions[0].display_name == 'Marcus Aurelius - marcus@rome.gov'
