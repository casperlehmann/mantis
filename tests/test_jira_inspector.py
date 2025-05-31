import json
import pytest

from typing import Any

from mantis.jira import JiraClient
from mantis.jira.utils.cache import CacheMissException
from mantis.jira.utils.jira_system_config_loader import Inspector
from tests.data import CacheData


class TestInspector:
    def test_print_table(self, capsys):
        column_order: list[str] = ["a"]
        all_field_keys: set[str] = {"placeholder"}
        issuetype_field_map: dict[str, Any] = {'a': {'placeholder':''}}
        data_out = Inspector.print_table(column_order, all_field_keys, issuetype_field_map)
        assert data_out is None
        captured = capsys.readouterr()
        expected = (
            "                     - a         ",
            "placeholder          - 1         ",
            "                     - a         ",
        )
        for actual_line, expected_line in zip(captured.out.split("\n"), expected):
            assert actual_line.strip() == expected_line.strip()

    def test_print_table_raises_on_non_existent_key(self, capsys):
        column_order: list[str] = ["a"]
        all_field_keys: set[str] = {"placeholder"}
        issuetype_field_map: dict[str, Any] = {'a': {'placeholder':''}}
        _ = Inspector.print_table(column_order, all_field_keys, issuetype_field_map)
        with pytest.raises(ValueError):
            Inspector.print_table(["non-existent"], {"placeholder"}, issuetype_field_map)

    def test_get_project_field_keys_from_cache(self, fake_jira: JiraClient):
        fake_jira.issues._allowed_types = ["Test"] # To avoid calling load_allowed_types
        with pytest.raises(CacheMissException):
            Inspector.get_createmeta_models(fake_jira)

        with open(fake_jira.cache.createmeta / "createmeta_test.json", "w") as f:
            json.dump(CacheData().createmeta_epic, f)
        from_cache = Inspector.get_createmeta_models(fake_jira)
        assert from_cache
