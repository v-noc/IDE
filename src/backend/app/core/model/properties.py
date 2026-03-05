from typing import Optional
from pydantic import BaseModel, Field


class CodePosition(BaseModel):
    id: Optional[str] = Field(alias="@id",
                              default=None, description="The ID of the code position.")
    line_no: int
    col_offset: int
    end_line_no: int
    end_col_offset: int


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
