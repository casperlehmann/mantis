from abc import ABC, abstractmethod
import json

from typing import TYPE_CHECKING, Any, ClassVar, Dict, Generator, KeysView, Mapping, Optional
import warnings

from datamodel_code_generator import DataModelType, InputFileType, generate
from pydantic import BaseModel, PydanticDeprecatedSince20, create_model

from mantis.jira.config_loader.jira_types import JiraIssueFieldSchema

if TYPE_CHECKING:
    from mantis.jira.jira_client import JiraClient


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
        self.client.mantis.cache.write_createmeta_schema(self.issuetype_name, schema)
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
        self.client.mantis.cache.write_editmeta_schema(self.issue_key, schema)
        output_plugin = self.client.plugins_dir / f'{self.issue_key.lower()}_editmeta.py'
        warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)
        generate(
            json.dumps(schema),
            input_file_type=InputFileType.JsonSchema,
            output=output_plugin,
            output_model_type=DataModelType.PydanticV2BaseModel,
        )
