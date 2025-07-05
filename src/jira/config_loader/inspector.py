from typing import TYPE_CHECKING, Mapping

from mantis.cache import CacheMissException
from jira.config_loader.meta_model_factories import CreatemetaModelFactory, EditmetaModelFactory, MetaModelFactory

if TYPE_CHECKING:
    from jira.jira_client import JiraClient


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
    def get_createmeta_models(jira: 'JiraClient') -> dict[str, CreatemetaModelFactory]:
        d: dict[str, CreatemetaModelFactory] = {}
        for issuetype in jira.issues.allowed_types:
            metadata = jira.mantis.cache.get_createmeta_from_cache(issuetype)
            if not metadata:
                raise CacheMissException(f"{issuetype}")
            assert isinstance(metadata, dict)
            d[issuetype] = CreatemetaModelFactory(metadata, issuetype, jira)
        return d

    @staticmethod
    def get_editmeta_models(jira: 'JiraClient', issue_keys: list[str]) -> dict[str, EditmetaModelFactory]:    
        d: dict[str, EditmetaModelFactory] = {}
        for issue_key in issue_keys:
            issue = jira.issues.get(issue_key)
            metadata = issue.editmeta_data
            if not metadata:
                raise CacheMissException(f"{issue_key}")
            assert isinstance(metadata, dict), f'Editmeta for {issue_key} is not a dict. Got: {type(metadata)}): {metadata}'
            assert 'fields' in metadata.keys()
            d[issue_key] = EditmetaModelFactory(metadata, issue.issuetype, jira, issue.key)
        return d

    @classmethod
    def inspect(cls, jira: 'JiraClient') -> None:
        createmeta_model_data = cls.get_createmeta_models(jira)
        createmeta_all_keys = cls.get_field_names_from_all_types(createmeta_model_data)
        cls.print_table(jira.issues.allowed_types, createmeta_all_keys, createmeta_model_data)
        print()
        editmeta_model_data = cls.get_editmeta_models(jira, ['ECS-1', 'ECS-2', 'ECS-3', 'ECS-4', 'ECS-5'])
        editmeta_all_keys = cls.get_field_names_from_all_types(editmeta_model_data)
        cls.print_table(['ECS-1', 'ECS-2', 'ECS-3', 'ECS-4', 'ECS-5'], editmeta_all_keys, editmeta_model_data)
