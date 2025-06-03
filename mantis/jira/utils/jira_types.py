import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
from tests.data import CacheData
data = CacheData().ecs_1

class Operation(Enum):
    add = "add"
    set = "set"
    remove = "remove"
    copy = "copy"
    edit = "edit"


class SchemaType(Enum):
    any = "any"
    array = "array"
    date = "date"
    issuelink = "issuelink"
    issuerestriction = "issuerestriction"
    issuetype = "issuetype"
    project = "project"
    string = "string"
    team = "team"
    user = "user"
    # 'comments-page' is editmeta only:
    comments_page = "comments-page"


class ItemsType(Enum):
    option = "option"
    design = "design.field.name"
    string = "string"
    attachment = "attachment"
    issuelinks = "issuelinks"


class _Schema(BaseModel):
    """The data type of the field.

    A 'JsonTypeBean' object. See docs for details:
    https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-issue-fields/#api-rest-api-2-field-get
    """
    type: SchemaType


class _SchemaHasSystem(_Schema):
    """Name of the field, if it is a system field.
    
    If the field is a system field, the name of the field.
    https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-issue-fields/#api-rest-api-2-field-get-response
    """
    system: str


class _SchemaHasItems(_Schema):
    """When the data type is an array, this specifies the type of field items within the array."""
    items: ItemsType


class _SchemaHasCustomCustomid(_Schema):
    """If the field is a custom field, this holds the URI and custom ID (int64)."""
    custom: str
    customId: int


class SchemaSystem(_SchemaHasSystem):
    """A component of the SchemaUnion type."""
    pass


class SchemaItemsSystem(_SchemaHasSystem, _SchemaHasItems):
    """A component of the SchemaUnion type."""
    pass


class SchemaCustomCustomid(_SchemaHasCustomCustomid):
    """A component of the SchemaUnion type."""
    pass


class SchemaItemsCustomCustomid(_SchemaHasCustomCustomid, _SchemaHasItems):
    """A component of the SchemaUnion type."""
    pass



# The union of all schema types.
SchemaUnion = SchemaSystem | SchemaItemsSystem | SchemaCustomCustomid | SchemaItemsCustomCustomid


class JiraIssueFieldSchema(BaseModel):
    """The data schema for the field."""
    required: bool
    alias_schema: SchemaUnion = Field(alias="schema")
    name: str
    key: str
    # hasDefaultValue: Only required for createmeta; only True for Reporter field
    hasDefaultValue: Optional[bool] = None
    autoCompleteUrl: Optional[str] = None
    operations: list[Operation] = []
    allowedValues: Optional[list[dict]] = None

    @property
    def schema_as_python_type(self) -> Any:
        simple_type = self.alias_schema.type
        if simple_type is SchemaType.string:
            return str
        elif simple_type is SchemaType.date:
            return datetime.date
        elif (
            isinstance(self.alias_schema, _SchemaHasItems)
            and simple_type is SchemaType.array
        ):
            item_type = self.alias_schema.items
            if item_type is ItemsType.string:
                return list[str]
            else:
                # Todo
                return list[Any]
        elif simple_type is SchemaType.array:
            return list[Any]
            return list[Any]
        elif simple_type in (
            SchemaType.issuetype,
            SchemaType.issuerestriction,
            SchemaType.issuelink,
            SchemaType.any,
            SchemaType.project,
            SchemaType.user,
            SchemaType.team,
            SchemaType.comments_page,
        ):
            return Any
        raise ValueError(
            f"No valid Python type implemented for {self.name} (type: {self.alias_schema.type})."
        )
