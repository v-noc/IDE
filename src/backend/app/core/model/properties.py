from typing import Optional
from pydantic import BaseModel, Field


class CodePosition(BaseModel):

    line_no: int
    col_offset: int
    end_line_no: int
    end_col_offset: int


class TypeKeyValuesProperties(BaseModel):

    varname: str = Field(
        ...,
        description="The key of the type key-value pair."
    )
    varType: str = Field(..., description="The type of the variable.")
    position: CodePosition = Field(
        ...,
        description="The position of the variable."
    )


class ThemeConfig(BaseModel):
    navbarColor: Optional[str] = Field(
        default=None,
        description="The color of the navbar."
    )
    leftSidebarColor: Optional[str] = Field(
        default=None,
        description="The color of the left sidebar."
    )
    rightSidebarColor: Optional[str] = Field(
        default=None,
        description="The color of the right sidebar."
    )
    backgroundColor: Optional[str] = Field(
        default=None,
        description="The color of the background."
    )

    textColor: Optional[str] = Field(
        default=None,
        description="The color of the text."
    )
    iconColor: Optional[str] = Field(
        default=None,
        description="The color of the icon."
    )
    cardColor: Optional[str] = Field(
        default=None,
        description="The color of the card."
    )
