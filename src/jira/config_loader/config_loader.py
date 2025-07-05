import json

from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator
import warnings

from datamodel_code_generator import DataModelType, InputFileType, generate
from pydantic import PydanticDeprecatedSince20

from mantis.cache import CacheMissException
from jira.config_loader.inspector import Inspector
from jira.config_loader.meta_model_factories import CreatemetaModelFactory

if TYPE_CHECKING:
    from jira.jira_client import JiraClient
    from mantis.cache import Cache


class JiraSystemConfigLoader:
    def __init__(self, jira: "JiraClient") -> None:
        self.jira = jira

    def attempt(self, issue_id: str, issuetype_name: str) -> None:
        with open(f".jira_cache/issues/{issue_id}.json", "r") as f:
            data = json.load(f)

        metadata = self.jira.mantis.cache.get_createmeta_from_cache(issuetype_name)
        if not metadata:
            raise CacheMissException(f"{issuetype_name}")
        assert isinstance(metadata, dict)
        fields = CreatemetaModelFactory(metadata, issuetype_name, self.jira)
        loaded = fields.make(data)
        assert loaded.key == issue_id  # type: ignore
        print(loaded.key)  # type: ignore
        print(loaded.fields.description)  # type: ignore
        assert loaded.fields.customfield_10031 == loaded.fields.development  # type: ignore

    @property
    def cache(self) -> 'Cache':
        return self.jira.mantis.cache

    def loop_createmeta(self) -> Generator[Path, Any, None]:
        for file in self.cache.createmeta.iterdir():
            yield file

    def loop_editmeta(self) -> Generator[Path, Any, None]:
        for file in self.cache.editmeta.iterdir():
            yield file

    def get_projects(self, force_skip_cache: bool = False) -> list[dict[str, Any]]:
        if not self.jira.mantis._no_read_cache or force_skip_cache:
            projects = self.cache.get_projects_from_system_cache()
            if projects:
                assert isinstance(projects, list), f"To satisfy the type checker. Got: {projects}"
                return projects
        projects = self.jira.get_projects()
        self.cache.write_to_system_cache("projects.json", json.dumps(projects))
        return projects

    def get_issuetypes(self, force_skip_cache: bool = False) -> dict[str, list[dict[str, Any]]]:
        if not self.jira.mantis._no_read_cache or force_skip_cache:
            from_cache = self.cache.get_issuetypes_from_system_cache()
            if from_cache:
                return from_cache
        issuetypes = self.jira.get_issuetypes()
        assert isinstance(issuetypes, dict)
        if len(issuetypes.keys()) == 0:
            raise ValueError(
                'List of issuetypes has length of zero. Something is probably very wrong.')
        assert 'issueTypes' in issuetypes, f'issueTypes has no issueTypes {issuetypes}'
        self.cache.write_issuetypes_to_system_cache(issuetypes)
        return issuetypes

    def get_createmeta(self, issuetype_name: str, force_skip_cache: bool = False) -> dict[str, int | list[dict[str, Any]]]:
        if not self.jira.mantis._no_read_cache or force_skip_cache:
            from_cache = self.cache.get_createmeta_from_cache(issuetype_name)
            if from_cache:
                return from_cache
        issuetype_id = self.jira.issuetype_name_to_id(issuetype_name)
        createmeta = self.jira.get_createmeta(issuetype_id)
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
        if not self.jira.mantis._no_read_cache or force_skip_cache:
            from_cache = self.cache.get_editmeta_from_cache(issue_key)
            if from_cache:
                return from_cache
        editmeta = self.jira.get_editmeta(issue_key)
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
            fields = CreatemetaModelFactory(data, issuetype_name, self.jira)
        return self.jira.issues.load_allowed_types()

    def _update_single_createmeta(self, issuetype_name: str) -> dict[str, Any]:
        data: dict[str, Any] = self.get_createmeta(issuetype_name)
        assert isinstance(data, dict)
        self.cache.write_createmeta(issuetype_name, data)
        return data

    def _update_single_editmeta(self, issue_key: str) -> dict[str, Any]:
        print(f'Getting editmeta for {issue_key}')
        data: dict[str, Any] = self.jira.get_editmeta(issue_key)
        assert isinstance(data, dict)
        self.cache.write_editmeta(issue_key, data)
        return data

    def compile_plugins(self) -> None:
        for input_file in self.cache.iter_dir("createmeta"):
            with open(input_file, "r") as f:
                content = f.read()
            # Remove the .json extension
            name = input_file.name[:-5].replace("-", "_").replace("_", "_").lower()
            output_path = self.jira.mantis.plugins_dir / f"{name}.py"
            warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)
            generate(
                content,
                input_file_type=InputFileType.Json,
                input_filename=str(input_file),
                output=output_path,
                output_model_type=DataModelType.PydanticV2BaseModel,
            )
        for input_file in self.jira.mantis.cache.iter_dir("issues"):
            print(f'input_file: {input_file}')
            with open(input_file, "r") as f:
                content = f.read()
            # Remove the .json extension
            name = input_file.name[:-5].replace("-", "_").replace("_", "_").lower()
            output_path = self.jira.mantis.plugins_dir / f"{name}.py"
            warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)
            generate(
                content,
                input_file_type=InputFileType.Json,
                input_filename=str(input_file),
                output=output_path,
                output_model_type=DataModelType.PydanticV2BaseModel,
            )

    def inspect(self) -> None:
        Inspector.inspect(self.jira)
