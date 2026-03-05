import copy
import json
from enum import Enum

from app.db.errors import DatabaseError
from app.db.woql_utils import _clean_dict, _dt_dict, _dt_list


class WoqlResult:
    """Iterator for streaming WOQL results."""

    def __init__(self, lines):
        self.preface = None
        self.postscript = {}
        self._lines = lines

    async def _init(self):
        preface_line = await self._lines.__anext__()
        preface = json.loads(preface_line)

        if not ("@type" in preface and preface["@type"] == "PrefaceRecord"):
            raise DatabaseError(response=preface)
        self.preface = preface
        return self

    def _check_error(self, document):
        if "@type" in document:
            if document["@type"] == "Binding":
                return document
            if document["@type"] == "PostscriptRecord":
                self.postscript = document
                raise StopAsyncIteration()

        raise DatabaseError(response=document)

    def variable_names(self):
        return self.preface["names"]

    def __aiter__(self):
        return self

    async def __anext__(self):
        line = await self._lines.__anext__()
        return self._check_error(json.loads(line))


class Patch:
    def __init__(self, json=None):
        if json:
            self.from_json(json)
        else:
            self.content = None

    @property
    def update(self):
        def swap_value(swap_item):
            result_dict = {}
            for key, item in swap_item.items():
                if isinstance(item, dict):
                    operation = item.get("@op")
                    if operation is not None and operation == "SwapValue":
                        result_dict[key] = item.get("@after")
                    elif operation is None:
                        result_dict[key] = swap_value(item)
            return result_dict

        return swap_value(self.content)

    @update.setter
    def update(self):
        raise Exception("Cannot set update for patch")

    @update.deleter
    def update(self):
        raise Exception("Cannot delete update for patch")

    @property
    def before(self):
        def extract_before(extract_item):
            before_dict = {}
            for key, item in extract_item.items():
                if isinstance(item, dict):
                    value = item.get("@before")
                    if value is not None:
                        before_dict[key] = value
                    else:
                        before_dict[key] = extract_before(item)
                else:
                    before_dict[key] = item
            return before_dict

        return extract_before(self.content)

    @before.setter
    def before(self):
        raise Exception("Cannot set before for patch")

    @before.deleter
    def before(self):
        raise Exception("Cannot delete before for patch")

    def from_json(self, json_str):
        content = json.loads(json_str)
        if isinstance(content, dict):
            self.content = _dt_dict(content)
        else:
            self.content = _dt_list(content)

    def to_json(self):
        return json.dumps(_clean_dict(self.content))

    def copy(self):
        return copy.deepcopy(self)


class GraphType(str, Enum):
    """Type of graph."""

    INSTANCE = "instance"
    SCHEMA = "schema"
