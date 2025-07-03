import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field

class Operation(Enum):
    add = "add"
    set = "set"
    remove = "remove"
    copy = "copy"
    edit = "edit"


class SchemaType(Enum):
    any = "any"
    array = "array"
    # 'comments-page' is editmeta only:
    comments_page = "comments-page"
    date = "date"
    issuelink = "issuelink"
    issuerestriction = "issuerestriction"
    issuetype = "issuetype"
    number = "number"
    option = "option"
    priority = "priority"
    project = "project"
    string = "string"
    system = "system"
    team = "team"
    timetracking = "timetracking"
    user = "user"


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
    type: SchemaType | str


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
        if simple_type == SchemaType.string.value:
            return str
        elif simple_type == SchemaType.date.value:
            return datetime.date
        elif simple_type == SchemaType.array.value:
            if (isinstance(self.alias_schema, _SchemaHasItems)):
                item_type = self.alias_schema.items
                if item_type is ItemsType.string:
                    return list[str]
                else:
                    # Todo
                    return list[Any]
            elif isinstance(self.alias_schema, SchemaCustomCustomid):
                    return list[Any]
            elif isinstance(self.alias_schema, SchemaSystem):
                    return list[Any]
            else:
                raise ValueError(f'Schema is an array, but has no items or custom: "{self.name}". Type: {self.alias_schema} | {type(self.alias_schema).__name__:<20}')
        elif simple_type != SchemaType.array.value and isinstance(self.alias_schema, _SchemaHasItems):
            raise ValueError(f'Schema has items, but is not an array: "{self.name}". Type: {self.alias_schema} | {SchemaType.array}')
        elif isinstance(self.alias_schema, SchemaCustomCustomid):
            return Any
        
        elif simple_type in ([_.value for _ in (
            SchemaType.any,
            SchemaType.array,
            SchemaType.comments_page,
            SchemaType.date,
            SchemaType.issuelink,
            SchemaType.issuerestriction,
            SchemaType.issuetype,
            SchemaType.number,
            SchemaType.option,
            SchemaType.priority,
            SchemaType.project,
            SchemaType.string,
            SchemaType.system,
            SchemaType.team,
            SchemaType.timetracking,
            SchemaType.user,
        )]):
            return Any

        if isinstance(simple_type, str):
            print (f'Unmatched simple_type: {[simple_type]}')
            return Any
        raise ValueError(
            f"No valid Python type implemented for {self.name} (type: {self.alias_schema.type})."
        )
