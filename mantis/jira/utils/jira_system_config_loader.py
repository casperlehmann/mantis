import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Generator, Mapping

from datamodel_code_generator import DataModelType, InputFileType, generate
from pydantic import ValidationError
import requests

from mantis.jira.utils.cache import CacheMissException
from mantis.jira.utils.jira_types import IssueTypeFields, ProjectFieldKeys

if TYPE_CHECKING:
    from mantis.jira.jira_client import JiraClient
    from mantis.jira.utils import Cache


class JiraSystemConfigLoader:
    def __init__(self, client: "JiraClient") -> None:
        self.client = client

    @property
    def cache(self) -> 'Cache':
        return self.client.cache

    def loop_issuetype_fields(self) -> Generator[Path, Any, None]:
        for file in self.cache.issuetype_fields.iterdir():
            yield file

    def update_projects_cache(self) -> list[dict[str, Any]]:
        url = 'project'
        response = self.client._get(url)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(e.response.reason)
            print(e.response.content)
            exit()
        payload: list[dict[str, Any]] = response.json()
        self.cache.write_to_system_cache("projects.json", json.dumps(payload))
        return payload
    
    def get_projects(self) -> list[dict[str, Any]]:
        if not self.client._no_read_cache:
            projects = self.cache.get_projects_from_system_cache()
            if projects:
                assert isinstance(projects, list), f"To satisfy the type checker. Got: {projects}"
                return projects
        return self.update_projects_cache()

    def update_issuetypes_cache(self) -> dict[str, Any]:
        url = f'issue/createmeta/{self.client.project_name}/issuetypes'
        response = self.client._get(url)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(e.response.reason)
            print(e.response.content)
            exit()

        issuetypes: dict[str, Any] = response.json()
        assert isinstance(issuetypes, dict), f'issuetypes is not a dict: {issuetypes}'
        assert 'issueTypes' in issuetypes, f"'issueTypes' not in issuetypes. Got: {issuetypes}"
        assert isinstance(issuetypes['issueTypes'], list), "issuetypes['issueTypes'] is not a list. Got: {issuetypes}"

        self.cache.write_issuetypes_to_system_cache(issuetypes)
        return issuetypes

    def get_issuetypes(self) -> dict[str, Any]:
        if not self.client._no_read_cache:
            from_cache = self.cache.get_issuetypes_from_system_cache()
            if from_cache:
                return from_cache
        return self.update_issuetypes_cache()

    def get_issuetypes_for_project(self) -> dict[str, Any]:
        data = self.get_issuetypes()
        self.cache.write_issuetypes_to_system_cache(data)
        try:
            assert len(data)
        except AssertionError as e:
            raise ValueError('List of issuetypes has length of zero. Something is probably very wrong.') from e
        return data

    def update_project_field_keys(self) -> list[str]:
        issuetypes: dict[str, Any] = self.get_issuetypes_for_project()

        assert isinstance(issuetypes, dict)#
        assert 'issueTypes' in issuetypes, f'issueTypes has no issueTypes {issuetypes}'

        nested_issuetypes: list[dict[str, Any]] = issuetypes['issueTypes']

        for issuetype in nested_issuetypes:
            assert 'name' in issuetype.keys()
            assert 'id' in issuetype.keys()
            issuetype_name = issuetype['name']
            issuetype_id = issuetype['id']
            response = self.client.get_createmeta(self.client.project_name, issuetype_id)
            response.raise_for_status()
            data: list[dict[str, Any]] = response.json()
            self.cache.write_createmeta(issuetype_name, data)
        return self.client.issues.load_allowed_types()

    def compile_plugins(self) -> None:
        for input_file in self.cache.iter_dir("issuetype_fields"):
            with open(input_file, "r") as f:
                content = f.read()
            # Remove the .json extension
            name = input_file.name[:-5].replace("-", "_").replace("_", "_").lower()
            output_path = self.client.plugins_dir / f"{name}.py"
            generate(
                content,
                input_file_type=InputFileType.Json,
                input_filename=str(input_file),
                output=output_path,
                output_model_type=DataModelType.PydanticV2BaseModel,
            )
        for input_file in self.client.cache.iter_dir("issues"):
            print(f'input_file: {input_file}')
            with open(input_file, "r") as f:
                content = f.read()
            # Remove the .json extension
            name = input_file.name[:-5].replace("-", "_").replace("_", "_").lower()
            output_path = self.client.plugins_dir / f"{name}.py"
            generate(
                content,
                input_file_type=InputFileType.Json,
                input_filename=str(input_file),
                output=output_path,
                output_model_type=DataModelType.PydanticV2BaseModel,
            )

    def get_all_keys_from_nested_dicts(
        self, data: Mapping[str, ProjectFieldKeys]
    ) -> set[str]:
        d: dict[str, list[str]] = {}
        all_field_keys: set[str] = set()
        for issuetype, field_keys in data.items():
            d[issuetype] = field_keys.fields
            all_field_keys = all_field_keys.union(set(d[issuetype]))
        return all_field_keys

    def print_table(
        self,
        column_order: list[str],
        all_field_keys: set[str],
        issuetype_field_map: Mapping[str, ProjectFieldKeys],
    ) -> None:
        def print_header_footer() -> None:
            print(f"{'':<20} - ", end="")
            for issuetype_name in column_order:
                if issuetype_name not in issuetype_field_map.keys():
                    raise ValueError("column_order contains non-existent key")
                print(f"{issuetype_name:<10}", end="")
            print()

        print_header_footer()
        for each in all_field_keys:
            print(f"{each:<20} - ", end="")
            for _, project_field_keys in issuetype_field_map.items():
                print(
                    f"{'1   ' if each in project_field_keys.fields else '':<10}",
                    end="",
                )
            print()
        print_header_footer()

    def get_project_field_keys_from_cache(self) -> Dict[str, ProjectFieldKeys]:
        d: Dict[str, ProjectFieldKeys] = {}
        for issuetype in self.client.issues.allowed_types:
            try:
                loaded_json = self.cache.get_createmeta_from_issuetype_fields_cache(issuetype)
                issuetype_fields = IssueTypeFields.model_validate(loaded_json)
            except ValidationError as e:
                raise CacheMissException(
                    f"issuetype {issuetype} does not exist. Did you remember to download types?"
                ) from e
            d[issuetype] = ProjectFieldKeys(issuetype, issuetype_fields)
        return d

    def inspect(self) -> None:
        data = self.get_project_field_keys_from_cache()
        all_keys = self.get_all_keys_from_nested_dicts(data)
        self.print_table(self.client.issues.allowed_types, all_keys, data)
