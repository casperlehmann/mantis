from abc import ABC, abstractmethod
import json

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Generator, KeysView, Mapping, Optional

from datamodel_code_generator import DataModelType, InputFileType, generate
from pydantic import BaseModel, create_model

from mantis.jira.utils.cache import CacheMissException
from mantis.jira.utils.jira_types import JiraIssueFieldSchema

if TYPE_CHECKING:
    from mantis.jira.jira_client import JiraClient
    from mantis.jira.utils import Cache


class MetaModelFactory(ABC):
    # Fields created by Jira that are present in the issue json, but cannot
    # be set by the user. These are overwritten in sub-classes.
    ignored_non_meta_field: set[str] = set()

    @abstractmethod
    def __init__(self, metadata: dict[str, Any]):
        self.out_fields: dict[str, Any] = {}
        self.getters: dict[str, str] = {}
        self.attributes: list[str] = []
        self.metadata = metadata
        if "fields" not in metadata.keys():
            raise ValueError(
                f'The provided data "metadata" does not contain a keys named "fields". Got: {metadata.keys()}')
        self.meta_fields: list[dict[str, Any]] | dict[str, dict[str, Any]] = metadata["fields"]

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

    @property
    def _iter_meta_fields(self) -> Generator[dict[str, Any], Any, None]:
        """Iterate through meta object.
        
        Unified interface for createmeta (list[dict]) and editmeta (dict[str, dict])."""
        for _meta_field_value in self.meta_fields:
            if isinstance(_meta_field_value, dict):
                assert isinstance(self.meta_fields, list)
                yield _meta_field_value
            elif isinstance(_meta_field_value, str):
                assert isinstance(self.meta_fields, dict)
                yield self.meta_fields[_meta_field_value]
            else:
                raise ValueError('Meta object has an unexpected schema.')
    
    def _create_fields_model(self) -> type[BaseModel]:
        for meta_field_value in self._iter_meta_fields:

            assert isinstance(meta_field_value, dict), (
                f"meta_field_value is type {type(meta_field_value)}, should be dict. "
                f"Got: {meta_field_value}. From {self.meta_fields}"
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
        fields_model = create_model("MetaModelFields", **self.out_fields)
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


class CreatemetaModelFactory(MetaModelFactory):
    ignored_non_meta_field = {
        "statuscategorychangedate",
        "components",
        "timespent",
    }

    def __init__(self, metadata: Dict[str, Any]):
        super().__init__(metadata)
        self.process = 'createmeta'
        assert isinstance(self.meta_fields, list), f'CreatemetaModelFactory.meta_fields should be of type list. Got: {type(self.meta_fields)}'
        self.create_model()


class EditmetaModelFactory(MetaModelFactory):
    ignored_non_meta_field = {
        "statuscategorychangedate",
        "components",
        "timespent",
        # 'environment' is a legacy field (and only relevant in editmeta)
        "environment"
    }

    def __init__(self, metadata: Dict[str, Any]):
        super().__init__(metadata)
        self.process = 'editmeta'
        assert isinstance(self.meta_fields, dict), f'EditmetaModelFactory.meta_fields should be of type dict. Got: {type(self.meta_fields)}'
        self.create_model()


class JiraSystemConfigLoader:
    def __init__(self, client: "JiraClient") -> None:
        self.client = client

    def attempt(self, issue_id: str, issuetype_name: str) -> None:
        with open(f".jira_cache/issues/{issue_id}.json", "r") as f:
            data = json.load(f)

        metadata = self.client.cache.get_createmeta_from_cache(issuetype_name)
        if not metadata:
            raise CacheMissException(f"{issuetype_name}")
        assert isinstance(metadata, dict)
        fields = CreatemetaModelFactory(metadata)
        loaded = fields.make(data)
        assert loaded.key == issue_id  # type: ignore
        print(loaded.key)  # type: ignore
        print(loaded.fields.description)  # type: ignore
        assert loaded.fields.customfield_10031 == loaded.fields.development  # type: ignore

    @property
    def cache(self) -> 'Cache':
        return self.client.cache

    def loop_createmeta(self) -> Generator[Path, Any, None]:
        for file in self.cache.createmeta.iterdir():
            yield file
    
    def get_projects(self, force_skip_cache: bool = False) -> list[dict[str, Any]]:
        if not self.client._no_read_cache or force_skip_cache:
            projects = self.cache.get_projects_from_system_cache()
            if projects:
                assert isinstance(projects, list), f"To satisfy the type checker. Got: {projects}"
                return projects
        projects = self.client.get_projects()
        self.cache.write_to_system_cache("projects.json", json.dumps(projects))
        return projects

    def get_issuetypes(self, force_skip_cache: bool = False) -> dict[str, list[dict[str, Any]]]:
        if not self.client._no_read_cache or force_skip_cache:
            from_cache = self.cache.get_issuetypes_from_system_cache()
            if from_cache:
                return from_cache
        issuetypes = self.client.get_issuetypes()
        assert isinstance(issuetypes, dict)
        if len(issuetypes.keys()) == 0:
            raise ValueError(
                'List of issuetypes has length of zero. Something is probably very wrong.')
        assert 'issueTypes' in issuetypes, f'issueTypes has no issueTypes {issuetypes}'
        self.cache.write_issuetypes_to_system_cache(issuetypes)
        return issuetypes

    def get_createmeta(self, issuetype_name: str, force_skip_cache: bool = False) -> dict[str, list[dict[str, Any]]]:
        if not self.client._no_read_cache or force_skip_cache:
            from_cache = self.cache.get_createmeta_from_cache(issuetype_name)
            if from_cache:
                return from_cache
        issuetype_id = self.client.issuetype_name_to_id(issuetype_name)
        issuetypes = self.client.get_createmeta(issuetype_id)
        assert isinstance(issuetypes, dict)
        if len(issuetypes.keys()) == 0:
            raise ValueError(
                'List of issuetypes has length of zero. Something is probably very wrong.')
        assert 'issueTypes' in issuetypes, f'issueTypes has no issueTypes {issuetypes}'
        self.cache.write_issuetypes_to_system_cache(issuetypes)
        return issuetypes

    def fetch_and_update_all_createmeta(self) -> list[str]:
        """Updates all createmate from upstream, returns updated list of allowed types"""
        issuetypes: dict[str, list[dict[str, Any]]] = self.get_issuetypes(force_skip_cache = False)
        nested_issuetypes = issuetypes['issueTypes']

        for issuetype in nested_issuetypes:
            data = self._update_single_createmeta(issuetype)
        return self.client.issues.load_allowed_types()

    def _update_single_createmeta(self, issuetype: dict[str, Any]) -> dict[str, Any]:
        assert 'name' in issuetype.keys()
        assert 'id' in issuetype.keys()
        issuetype_name: str = issuetype['name']
        issuetype_id: str = issuetype['id']
        assert isinstance(issuetype_name, str)
        assert isinstance(issuetype_id, str)
        data: dict[str, Any] = self.client.get_createmeta(issuetype_id)
        assert isinstance(data, dict)
        self.cache.write_createmeta(issuetype_name, data)
        return data        
        fields = CreatemetaModelFactory(self.client, issuetype_name)#, f'issuetype_name: {issuetype_name}'
        return fields.make(data)


    def compile_plugins(self) -> None:
        for input_file in self.cache.iter_dir("createmeta"):
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

    def inspect(self) -> None:
        Inspector.inspect(self.client)


class Inspector:
    @staticmethod
    def get_field_names_from_all_types(data: Mapping[str, MetaModelFactory]) -> set[str]:
        d: dict[str, set[str]] = {}
        all_field_keys: set[str] = set()
        for issuetype, factory in data.items():
            assert isinstance(factory, MetaModelFactory)
            all_field_keys = all_field_keys.union(set(factory.keys()))
        return all_field_keys

    @staticmethod
    def print_table(
        column_order: list[str],
        all_field_keys: set[str],
        issuetype_field_map: Mapping[str, MetaModelFactory],
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
        for each in sorted(all_field_keys):
            print(f"{each:<20} - ", end="")
            for project_field_keys in issuetype_field_map.values():
                print(
                    f"{'1   ' if each in project_field_keys.keys() else '':<10}",
                    end="",
                )
            print()
        print_header_footer()

    @staticmethod
    def get_createmeta_models(client: 'JiraClient') -> dict[str, CreatemetaModelFactory]:    
        d: dict[str, CreatemetaModelFactory] = {}
        for issuetype in client.issues.allowed_types:
            metadata = client.cache.get_createmeta_from_cache(issuetype)
            if not metadata:
                raise CacheMissException(f"{issuetype}")
            assert isinstance(metadata, dict)
            d[issuetype] = CreatemetaModelFactory(metadata)
        return d

    @staticmethod
    def get_editmeta_models(client: 'JiraClient', issue_keys: list[str]) -> dict[str, EditmetaModelFactory]:    
        d: dict[str, EditmetaModelFactory] = {}
        for issue_key in issue_keys:
            metadata = client.issues.get(issue_key).editmeta
            if not metadata:
                raise CacheMissException(f"{issue_key}")
            assert isinstance(metadata, dict)
            assert 'fields' in metadata.keys()
            d[issue_key] = EditmetaModelFactory(metadata)
        return d

    @classmethod
    def inspect(cls, client: 'JiraClient') -> None:
        createmeta_model_data = cls.get_createmeta_models(client)
        createmeta_all_keys = cls.get_field_names_from_all_types(createmeta_model_data)
        cls.print_table(client.issues.allowed_types, createmeta_all_keys, createmeta_model_data)
        print()
        editmeta_model_data = cls.get_editmeta_models(client, ['ECS-1', 'ECS-2', 'ECS-3', 'ECS-4', 'ECS-5'])
        editmeta_all_keys = cls.get_field_names_from_all_types(editmeta_model_data)
        cls.print_table(['ECS-1', 'ECS-2', 'ECS-3', 'ECS-4', 'ECS-5'], editmeta_all_keys, editmeta_model_data)
