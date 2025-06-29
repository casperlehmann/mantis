from mantis.mantis_client import MantisClient
from tests.data import CacheData


class TestJiraAutocomplete:
    def test_get_suggestions(self, fake_mantis: MantisClient, requests_mock):
        accountId = CacheData().placeholder_account['accountId']
        return_value = {'results': [{'value': accountId, 'displayName': '<b>Marcus</b> Aurelius - <b>marcus</b>@rome.gov'}]}
        requests_mock.get(fake_mantis.http.api_url + '/jql/autocompletedata/suggestions?fieldName=reporter&fieldValue=Marcus', json=return_value)
        suggestions = fake_mantis.jira.auto_complete.get_suggestions('reporter', 'Marcus')
        assert len(suggestions) == 1
        assert suggestions[0].display_name == 'Marcus Aurelius - marcus@rome.gov'
