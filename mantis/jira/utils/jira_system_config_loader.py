import json
import requests

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Generator, KeysView, Optional

from datamodel_code_generator import DataModelType, InputFileType, generate
from pydantic import BaseModel, create_model

from mantis.jira.utils.cache import CacheMissException
from mantis.jira.utils.jira_types import JiraIssueFieldSchema

if TYPE_CHECKING:
    from mantis.jira.jira_client import JiraClient
    from mantis.jira.utils import Cache


class CreatemetaModelFactory:
    # Fields created by Jira that are present in the issue json, but cannot
    # be set by the user.
    ignored_non_meta_field = (
        "statuscategorychangedate",
        "components",
        "timespent",
        # 'environment' is a legacy field (and only relevant in editmeta)
        # "environment"
    )

    def __init__(self, jira: "JiraClient", type_name: str):
        self.jira = jira
        self.type_name = type_name.lower()
        self.out_fields: dict[str, Any] = {}
        self.getters: dict[str, str] = {}
        self.attributes: list[str] = []
        self.createmeta = self.jira.cache.get_createmeta_from_issuetype_fields_cache(self.type_name)
        if not self.createmeta:
            raise CacheMissException(f"{self.type_name}")
        self.createmeta_fields: list[dict[str, Any]] = self.createmeta["fields"]
        self.create_model()

    def keys(self) -> KeysView[str]:
        return self.out_fields.keys()

    def create_model(self) -> None:
        fields_model = self._create_fields_model()
        self._add_aliases_for_custom_fields(fields_model)
        outer_schema_with_nested_fields: dict[str, Any]= {
            "key": str,
            "id": str,
            "fields": fields_model,
        }
        issue_model = create_model("IssueModel", **outer_schema_with_nested_fields)
        self.model = issue_model

    def assign_python_type(self, meta: JiraIssueFieldSchema, meta_field_key: str) -> None:
        python_type = meta.schema_as_python_type
        if meta.required:
            self.out_fields[meta_field_key] = (python_type, ...)
        else:
            self.out_fields[meta_field_key] = (Optional[python_type], None)

    def assign_attributes_and_getters(self, meta: JiraIssueFieldSchema, meta_field_key: str) -> None:
        if meta_field_key.startswith("customfield_"):
            cleaned_name = meta.name.lower().replace(" ", "_")
            self.getters[cleaned_name] = meta_field_key
            self.attributes.append(meta.name.lower())
        else:
            self.attributes.append(meta_field_key)

    def _create_fields_model(self) -> type[BaseModel]:
        for meta_field_value in self.createmeta_fields:
            assert isinstance(meta_field_value, dict), (
                f"meta_field_value is type {type(meta_field_value)}, should be dict. "
                f"Got: {meta_field_value}. From {self.createmeta_fields}"
            )
            try:
                meta_field_key: str = meta_field_value["key"]
            except KeyError as e:
                raise ValueError(f"List values: {meta_field_value}") from e
            if meta_field_key in self.ignored_non_meta_field:
                continue
            meta = JiraIssueFieldSchema.model_validate(meta_field_value)
            assert meta_field_value["name"] == meta.name, (
                f"Meta field names for {meta.key} don't match: {meta_field_value['name']} != {meta.name}"
                # For example:
                # (assignee)            Assignee == Assignee
                # (customfield_10031)   development == development
                # (issuetype)           Issue Type == Issue Type
            )
            self.assign_python_type(meta, meta_field_key)
            self.assign_attributes_and_getters(meta, meta_field_key)
        fields_model = create_model("CreatemetaModel", **self.out_fields)
        return fields_model

    def _add_aliases_for_custom_fields(self, fields_model: type[BaseModel]) -> None:
        """Adds human readable aliases for custom fields on a Fields object.

        This allows us to access any custom field attribute by their name field name, in addition to its key.
        For example, it maps:
        instance.fields.rank -> instance.fields.customfield_10019
        """

        def make_property(field_name: str) -> property:
            return property(lambda self: getattr(self, field_name))

        for alias, original_name in self.getters.items():
            setattr(fields_model, alias, make_property(original_name))

    def make(self, issue_payload: dict) -> BaseModel:
        return self.model.model_validate(issue_payload)


class JiraSystemConfigLoader:
    def __init__(self, client: "JiraClient") -> None:
        self.client = client

    def attempt(self, issue_id: str, issue_type: str) -> None:
        with open(f".jira_cache/issues/{issue_id}.json", "r") as f:
            data = json.load(f)
        fields = CreatemetaModelFactory(self.client, issue_type)
        loaded = fields.make(data)
        assert loaded.key == issue_id  # type: ignore
        print(loaded.key)
        print(loaded.fields.description)
        assert loaded.fields.customfield_10031 == loaded.fields.development

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
            raise ValueError(
                'List of issuetypes has length of zero. '
                'Something is probably very wrong.'
            ) from e
        return data

    def update_project_field_keys(self) -> list[str]:
        issuetypes: dict[str, Any] = self.get_issuetypes_for_project()

        assert isinstance(issuetypes, dict)
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

    def get_all_keys_from_nested_dicts(self, data: dict[str, CreatemetaModelFactory]) -> set[str]:
        d: dict[str, list[str]] = {}
        all_field_keys: set[str] = set()
        for issuetype, field_keys in data.items():
            field_keys = list(field_keys.keys())
            d[issuetype] = field_keys
            all_field_keys = all_field_keys.union(set(d[issuetype]))
        return all_field_keys

    def print_table(
        self,
        column_order: list[str],
        all_field_keys: set[str],
        issuetype_field_map: dict[str, CreatemetaModelFactory],
    ) -> None:
        def print_header_footer() -> None:
            print(f"{'':<20} - ", end="")
            for issuetype_name in column_order:
                assert isinstance(issuetype_name, str)
                if issuetype_name not in issuetype_field_map.keys():
                    raise ValueError(
                        f'column_order contains non-existent key: {issuetype_name}.'
                        f'Expected one of: {issuetype_field_map.keys()}')
                print(f"{issuetype_name:<10}", end="")
            print()

        print_header_footer()
        for each in all_field_keys:
            print(f"{each:<20} - ", end="")
            for project_field_keys in issuetype_field_map.values():
                print(
                    f"{'1   ' if each in project_field_keys.keys() else '':<10}",
                    end="",
                )
            print()
        print_header_footer()

    def get_project_field_keys_from_cache(self) -> Dict[str, CreatemetaModelFactory]:
        d: dict[str, CreatemetaModelFactory] = {}
        for issuetype in self.client.issues.allowed_types:
            d[issuetype] = CreatemetaModelFactory(self.client, issuetype)
        return d

    def inspect(self) -> None:
        data = self.get_project_field_keys_from_cache()
        all_keys = self.get_all_keys_from_nested_dicts(data)
        self.print_table(self.client.issues.allowed_types, all_keys, data)
