import typing
import pydantic_core
import pytest

from mantis.jira.config_loader.jira_types import _Schema, JiraIssueFieldSchema, SchemaCustomCustomid, SchemaItemsSystem, SchemaSystem


class TestJiraIssueFieldSchemaPythonType:
    def test_schema_no_type_raises_validation_error(self):
        with pytest.raises(pydantic_core._pydantic_core.ValidationError):
            _Schema.model_validate({})
        x = _Schema.model_validate({'type': 'anything'})
        assert isinstance(x, _Schema)

    def field_template(self, schema: dict) -> dict:
        return {
            'required': True,
            'schema': schema,
            'name': 'Summary',
            'key': 'summary'
        }

    def test_field_string(self):
        schema = self.field_template({
            'type': 'string',
            "system": "description"
        })
        x = JiraIssueFieldSchema.model_validate(schema)
        assert x.alias_schema.type == 'string'
        assert isinstance(x.alias_schema, SchemaSystem)

    def test_field_system(self):
        schema = self.field_template({
            'type': 'array',
            'system': 'summary',
        })
        x = JiraIssueFieldSchema.model_validate(schema)
        assert x.alias_schema.type == 'array'
        assert isinstance(x.alias_schema, SchemaSystem)
        assert x.schema_as_python_type == list[typing.Any]

    def test_field_items_system(self):
        schema = self.field_template({
            'type': 'array',
            'system': 'summary',
            'items': 'string'
        })
        x = JiraIssueFieldSchema.model_validate(schema)
        assert x.alias_schema.type == 'array'
        assert isinstance(x.alias_schema, SchemaItemsSystem)
        assert x.schema_as_python_type == list[str]

    def test_field_array_custom_customid(self):
        schema = self.field_template({
            'type': 'array',
            'custom': 'a',
            'customId': 1
        })
        x = JiraIssueFieldSchema.model_validate(schema)
        assert x.alias_schema.type == 'array'
        assert isinstance(x.alias_schema, SchemaCustomCustomid)
        assert x.schema_as_python_type == list[typing.Any]

    def test_field_custom_customid(self):
        schema = self.field_template({
            'type': 'required',
            'custom': 'a',
            'customId': 1
        })
        x = JiraIssueFieldSchema.model_validate(schema)
        assert x.alias_schema.type == 'required'
        assert isinstance(x.alias_schema, SchemaCustomCustomid)
        assert x.schema_as_python_type == typing.Any

    def test_field_some_type(self, capsys):
        schema = self.field_template({
            'type': 'some_type',
            'system': 'a'
        })
        x = JiraIssueFieldSchema.model_validate(schema)
        assert x.alias_schema.type == 'some_type'
        assert isinstance(x.alias_schema, SchemaSystem)
        assert isinstance(x.alias_schema.type, str)
        assert x.schema_as_python_type == typing.Any
        captured = capsys.readouterr()
        assert captured.out == "Unmatched simple_type: ['some_type']\n"
        assert captured.err == ""

