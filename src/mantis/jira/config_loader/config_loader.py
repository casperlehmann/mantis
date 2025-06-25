from abc import ABC, abstractmethod
import json

from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Generator, KeysView, Mapping, Optional
import warnings

from datamodel_code_generator import DataModelType, InputFileType, generate
from pydantic import BaseModel, PydanticDeprecatedSince20, create_model

from mantis.cache import CacheMissException
from mantis.jira.config_loader.jira_types import JiraIssueFieldSchema

if TYPE_CHECKING:
    from mantis.jira.jira_client import JiraClient
    from mantis.cache import Cache


class MetaModelFactory(ABC):
    # Required to be provided by concrete subclasses:
    process: ClassVar[str]

    # Fields created by Jira that are present in the issue json, but cannot
    # be set by the user. These are overwritten in sub-classes.
    ignored_non_meta_field: ClassVar[set[str]]

    @abstractmethod
    def __init__(self, metadata: dict[str, Any]):
        self.out_fields: dict[str, Any] = {}
        self.getters: dict[str, str] = {}
        self.attributes: list[str] = []
        self.metadata = metadata
        if "fields" not in metadata.keys():
            raise ValueError(
                f'The provided data "metadata" does not contain a keys named "fields". Got: {metadata.keys()}')

    @abstractmethod
    def field_by_key(self, key: str) -> Any | None:
        pass

    @abstractmethod
    def _write_plugin(self) -> None:
        pass

    @property
    def meta_fields(self) -> list[dict[str, Any]] | dict[str, dict[str, Any]]:
        return self.metadata["fields"]

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
        if isinstance(self.meta_fields, dict):
            container = list(self.meta_fields.values())
        elif isinstance(self.meta_fields, list):
            container = self.meta_fields
        else:
            raise ValueError('Meta object has an unexpected schema.')
                
        for _meta_field_value in container:
            if not isinstance(_meta_field_value, dict):
                raise ValueError('Meta object has an unexpected schema.')
            yield _meta_field_value
    
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
    process = 'createmeta'
    ignored_non_meta_field = {
        "statuscategorychangedate",
        "components",
        "timespent",
    }

    def __init__(self, metadata: Dict[str, Any], issuetype_name: str, client: "JiraClient", write_plugin: bool=True) -> None:
        super().__init__(metadata)
        self.client = client
        self.issuetype_name = issuetype_name
        if isinstance(self.meta_fields, dict):
            raise ValueError('CreatemetaModelFactory.meta_fields should be of type list. '
                             'Got dict. Did you accidentally pass be an "editmeta"?')
        if not isinstance(self.meta_fields, list):
            raise TypeError(
                f'CreatemetaModelFactory.meta_fields should be of type list. Got: {type(self.meta_fields)}')
        self.create_model()
        if write_plugin:
            self._write_plugin()

    def _write_plugin(self) -> None:
        schema = self.model.model_json_schema()
        self.client.cache.write_createmeta_schema(self.issuetype_name, schema)
        output_plugin = self.client.plugins_dir / f'{self.issuetype_name.lower()}_createmeta.py'
        warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)
        generate(
            json.dumps(schema),
            input_file_type=InputFileType.JsonSchema,
            output=output_plugin,
            output_model_type=DataModelType.PydanticV2BaseModel,
        )

    def field_by_key(self, key: str, default: Any | None = None) -> Any | None:
        return next((item for item in self._iter_meta_fields if item.get('key') == key), default)

class EditmetaModelFactory(MetaModelFactory):
    process = 'editmeta'
    ignored_non_meta_field = {
        "statuscategorychangedate",
        "components",
        "timespent",
        # 'environment' is a legacy field (and only relevant in editmeta)
        "environment"
    }

    def __init__(self, metadata: Dict[str, Any], issuetype_name: str, client: "JiraClient", issue_key: str, write_plugin: bool=True) -> None:
        super().__init__(metadata)
        self.client = client
        self.issuetype_name = issuetype_name
        self.issue_key = issue_key
        if isinstance(self.meta_fields, list):
            raise ValueError('EditmetaModelFactory.meta_fields should be of type dict. '
                             'Got list. Did you accidentally pass be a "createmeta"?')
        if not isinstance(self.meta_fields, dict):
            raise TypeError(
                f'EditmetaModelFactory.meta_fields should be of type dict. Got: {type(self.meta_fields)}')
        self.create_model()
        if write_plugin:
            self._write_plugin()

    def field_by_key(self, key: str, default: Any | None = None) -> Any | None:
        assert isinstance(self.meta_fields, dict), 'Asserting to satisfy type checker.'
        return self.meta_fields.get(key, default)

    def _write_plugin(self) -> None:
        schema = self.model.model_json_schema()
        self.client.cache.write_editmeta_schema(self.issue_key, schema)
        output_plugin = self.client.plugins_dir / f'{self.issue_key.lower()}_editmeta.py'
        warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)
        generate(
            json.dumps(schema),
            input_file_type=InputFileType.JsonSchema,
            output=output_plugin,
            output_model_type=DataModelType.PydanticV2BaseModel,
        )


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
        fields = CreatemetaModelFactory(metadata, issuetype_name, self.client)
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

    def loop_editmeta(self) -> Generator[Path, Any, None]:
        for file in self.cache.editmeta.iterdir():
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

    def get_createmeta(self, issuetype_name: str, force_skip_cache: bool = False) -> dict[str, int | list[dict[str, Any]]]:
        if not self.client._no_read_cache or force_skip_cache:
            from_cache = self.cache.get_createmeta_from_cache(issuetype_name)
            if from_cache:
                return from_cache
        issuetype_id = self.client.issuetype_name_to_id(issuetype_name)
        createmeta = self.client.get_createmeta(issuetype_id)
        if not isinstance(createmeta, dict):
            raise ValueError(f'The createmeta object should be a dict. Got: {type(createmeta)}')
        if len(createmeta.keys()) == 0:
            raise ValueError(
                'No content in createmeta. Something is probably very wrong.')
        if not 'fields' in createmeta:
            raise ValueError(f'The createmeta has no fields. Got: {createmeta.keys()}')
        self.cache.write_createmeta(issuetype_name, createmeta)
        return createmeta

    def get_editmeta(self, issue_key: str, force_skip_cache: bool = False) -> dict[str, int | list[dict[str, Any]]]:
        if not self.client._no_read_cache or force_skip_cache:
            from_cache = self.cache.get_editmeta_from_cache(issue_key)
            if from_cache:
                return from_cache
        editmeta = self.client.get_editmeta(issue_key)
        if not isinstance(editmeta, dict):
            raise ValueError(f'The editmeta object should be a dict. Got: {type(editmeta)}')
        if len(editmeta.keys()) == 0:
            raise ValueError(
                'No content in editmeta. Something is probably very wrong.')
        if not 'fields' in editmeta:
            raise ValueError(f'The editmeta has no fields. Got: {editmeta.keys()}')
        
        self.cache.write_editmeta(issue_key, editmeta)
        return editmeta

    def fetch_and_update_all_createmeta(self) -> list[str]:
        """Updates all createmate from upstream, returns updated list of allowed types"""
        issuetypes: dict[str, list[dict[str, Any]]] = self.get_issuetypes(force_skip_cache = False)
        nested_issuetypes = issuetypes['issueTypes']

        for issuetype_data in nested_issuetypes:
            issuetype_name: str = issuetype_data['name']
            data = self._update_single_createmeta(issuetype_name)
            # Run CreatemetaModelFactory to dump schemas
            fields = CreatemetaModelFactory(data, issuetype_name, self.client)
        return self.client.issues.load_allowed_types()

    def _update_single_createmeta(self, issuetype_name: str) -> dict[str, Any]:
        data: dict[str, Any] = self.get_createmeta(issuetype_name)
        assert isinstance(data, dict)
        self.cache.write_createmeta(issuetype_name, data)
        return data

    def _update_single_editmeta(self, issue_key: str) -> dict[str, Any]:
        print(f'Getting editmeta for {issue_key}')
        data: dict[str, Any] = self.client.get_editmeta(issue_key)
        assert isinstance(data, dict)
        self.cache.write_editmeta(issue_key, data)
        return data

    def compile_plugins(self) -> None:
        for input_file in self.cache.iter_dir("createmeta"):
            with open(input_file, "r") as f:
                content = f.read()
            # Remove the .json extension
            name = input_file.name[:-5].replace("-", "_").replace("_", "_").lower()
            output_path = self.client.plugins_dir / f"{name}.py"
            warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)
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
            warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)
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
            d[issuetype] = CreatemetaModelFactory(metadata, issuetype, client)
        return d

    @staticmethod
    def get_editmeta_models(client: 'JiraClient', issue_keys: list[str]) -> dict[str, EditmetaModelFactory]:    
        d: dict[str, EditmetaModelFactory] = {}
        for issue_key in issue_keys:
            issue = client.issues.get(issue_key)
            metadata = issue.editmeta_data
            if not metadata:
                raise CacheMissException(f"{issue_key}")
            assert isinstance(metadata, dict), f'Editmeta for {issue_key} is not a dict. Got: {type(metadata)}): {metadata}'
            assert 'fields' in metadata.keys()
            d[issue_key] = EditmetaModelFactory(metadata, issue.issuetype, client, issue.key)
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
