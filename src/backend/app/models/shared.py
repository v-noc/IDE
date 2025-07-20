from pydantic import BaseModel

class NodePosition(BaseModel):
    line_no: int
    col_offset: int
    end_line_no: int
    end_col_offset: int
