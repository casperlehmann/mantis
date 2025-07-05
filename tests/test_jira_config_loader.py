import json
import pytest

from mantis.mantis_client import MantisClient
from tests.data import get_issuetypes_response, update_projects_cache_response, CacheData


def list_system_cache_contents(fake_jira: MantisClient) -> set[str]:
        return {str(_).split('/')[-1] for _ in fake_jira.cache.system.iterdir()}


class TestConfigLoader:
    def test_config_loader_update_issuetypes_writes_to_cache(self, fake_mantis: MantisClient, requests_mock):
        requests_mock.get(f'{fake_mantis.http.api_url}/issue/createmeta/TEST/issuetypes', json=get_issuetypes_response)

        set_with_no_issuetypes = list_system_cache_contents(fake_mantis)
        assert set_with_no_issuetypes == {'createmeta', 'editmeta', 'createmeta_schemas', 'editmeta_schemas'}, (
            f"System cache expected 2 values. Got: {set_with_no_issuetypes}")

        fake_mantis.jira.system_config_loader.get_issuetypes(force_skip_cache = True)
        set_with_issuetypes = list_system_cache_contents(fake_mantis)
        assert set_with_issuetypes == {'createmeta', 'editmeta', 'createmeta_schemas', 'issuetypes.json', 'editmeta_schemas'}, (
            f"System cache expected 3 values. Got: {fake_mantis.cache.system}")

    def test_config_loader_loop_yields_files(self, fake_mantis: MantisClient, requests_mock):
        requests_mock.get(f'{fake_mantis.http.api_url}/issue/createmeta/TEST/issuetypes', json=get_issuetypes_response)
        assert len(list(fake_mantis.jira.system_config_loader.loop_createmeta())) == 0
        # cache something
        with open(fake_mantis.cache.createmeta / "some_file.json", "w") as f:
            f.write("{}")
        assert len(list(fake_mantis.jira.system_config_loader.loop_createmeta())) == 1

    def test_update_project_data(self, fake_mantis: MantisClient, requests_mock):
        requests_mock.get(f'{fake_mantis.http.api_url}/project', json=update_projects_cache_response)

        # Test initial state
        if (fake_mantis.cache.system / 'projects.json').exists():
            raise FileExistsError('File "projects.json" should not exist yet')
        assert fake_mantis.jira._project_id is None

        # Fetch and cache projects data (without updating the object)
        got_projects = fake_mantis.jira.system_config_loader.get_projects(force_skip_cache = True)
        assert isinstance(got_projects, list)
        assert len(got_projects) == 2
        assert {_['id'] for _ in got_projects} == {'10000', '10001'}

        # Check side-effect
        if not (fake_mantis.cache.system / 'projects.json').exists():
            raise FileNotFoundError('File "projects.json" should have been created')
        
        # Note: Private jira._project_id is still None, even after the file has been written.
        assert fake_mantis.jira._project_id is None
        # Note: Only once the public jira.project_id is queried does the private one get updated
        assert fake_mantis.jira.project_id == '10000'
        assert fake_mantis.jira._project_id == '10000'
        
        # Test projects response
        got_project_ids_as_ints = {_['id'] for _ in got_projects}
        assert got_project_ids_as_ints == {'10000', '10001'}, (
            'We expect two projects in len(update_projects_cache_response): '
            f'{len(update_projects_cache_response)} Got {got_project_ids_as_ints}')

    def test_update_issuetypes_data(self, fake_mantis: MantisClient, requests_mock):
        requests_mock.get(f'{fake_mantis.http.api_url}/issue/createmeta/TEST/issuetypes', json=CacheData().issuetypes)

        # Fetch and cache issuetypes data
        if (fake_mantis.cache.system / 'issuetypes.json').exists():
            raise FileExistsError('File "issuetypes.json" should not exist yet')
        
        got_issuetypes = fake_mantis.jira.system_config_loader.get_issuetypes()
        assert isinstance(got_issuetypes, dict)
        assert 'issueTypes' in got_issuetypes
        assert isinstance(got_issuetypes['issueTypes'], list)

        expected_issue_ids: set[str] = set(map(str, list(range(10001, 10006))))
        got_issue_ids_as_ints = {_['id'] for _ in got_issuetypes['issueTypes']}

        assert len(got_issuetypes['issueTypes']) == 5, f'Expected 5 issueTypes. Got {len(got_issuetypes)}: {got_issuetypes}'
        assert got_issue_ids_as_ints == expected_issue_ids
        if not (fake_mantis.cache.system / 'issuetypes.json').exists():
            raise FileNotFoundError('File "issuetypes.json" should have been created')

    @pytest.mark.slow
    def test_update_createmeta(self, fake_mantis: MantisClient, requests_mock):
        requests_mock.get(f'{fake_mantis.http.api_url}/issue/createmeta/TEST/issuetypes', json=CacheData().issuetypes)
        requests_mock.get(f'{fake_mantis.http.api_url}/issue/createmeta/TEST/issuetypes/10001', json=CacheData().createmeta_epic)
        requests_mock.get(f'{fake_mantis.http.api_url}/issue/createmeta/TEST/issuetypes/10002', json=CacheData().createmeta_subtask)
        requests_mock.get(f'{fake_mantis.http.api_url}/issue/createmeta/TEST/issuetypes/10003', json=CacheData().createmeta_task)
        requests_mock.get(f'{fake_mantis.http.api_url}/issue/createmeta/TEST/issuetypes/10004', json=CacheData().createmeta_story)
        requests_mock.get(f'{fake_mantis.http.api_url}/issue/createmeta/TEST/issuetypes/10005', json=CacheData().createmeta_bug)

        if (fake_mantis.cache.createmeta / 'createmeta_story.json').exists():
            raise FileExistsError('File "createmeta_story.json" should not exist yet')
        allowed_types = fake_mantis.jira.system_config_loader.fetch_and_update_all_createmeta()
        if not (fake_mantis.cache.createmeta / 'createmeta_story.json').exists():
            raise FileNotFoundError('File "createmeta_story.json" should have been created')
        
        assert set(allowed_types) == set(['Epic', 'Subtask', 'Task', 'Story', 'Bug'])

        def get_allowed_issuetype_name(filename):
            with open(fake_mantis.cache.createmeta / filename, "r") as f:
                createmeta_story = json.load(f)
            issuetype = [field for field in createmeta_story["fields"] if field['key'] == 'issuetype'][0]
            return issuetype['allowedValues'][0]['name']
        
        assert get_allowed_issuetype_name("createmeta_epic.json") == 'Epic'
        assert get_allowed_issuetype_name("createmeta_subtask.json") == 'Subtask'
        assert get_allowed_issuetype_name("createmeta_task.json") == 'Task'
        assert get_allowed_issuetype_name("createmeta_story.json") == 'Story'
        assert get_allowed_issuetype_name("createmeta_bug.json") == 'Bug'

    @pytest.mark.slow
    def test_compile_plugins(self, fake_mantis: MantisClient, requests_mock):
        requests_mock.get(f'{fake_mantis.http.api_url}/project', json={"name": "Testtype"})
        assert str(fake_mantis.plugins_dir) != ".jira_cache_test"

        with open(fake_mantis.cache.createmeta / "Testtype.json", "w") as f:
            f.write('{"name": "Testtype"}')

        assert (len(list(fake_mantis.plugins_dir.iterdir())) == 0), f"Not empty: {fake_mantis.plugins_dir}"
        fake_mantis.jira.system_config_loader.compile_plugins()
        assert len(list(fake_mantis.plugins_dir.iterdir())) == 1
