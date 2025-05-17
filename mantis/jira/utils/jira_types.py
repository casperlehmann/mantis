import datetime
from enum import Enum
from typing import Any, Optional, Union
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
    type: SchemaType


class _SchemaHasSystem(_Schema):
    system: str


class _SchemaHasItems(_Schema):
    items: ItemsType


class _SchemaHasCustomCustomid(_Schema):
    custom: str
    customId: int


class SchemaSystem(_SchemaHasSystem):
    pass


class SchemaItemsSystem(_SchemaHasSystem, _SchemaHasItems):
    pass


class SchemaCustomCustomid(_SchemaHasCustomCustomid):
    pass


class SchemaItemsCustomCustomid(_SchemaHasCustomCustomid, _SchemaHasItems):
    pass


SchemaUnion = Union[
    SchemaSystem, SchemaItemsSystem, SchemaCustomCustomid, SchemaItemsCustomCustomid
]


class JiraIssueFieldSchema(BaseModel):
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
