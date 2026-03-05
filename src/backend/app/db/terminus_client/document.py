"""Document CRUD, query, and schema operations for TerminusDB."""

import gzip
import json
from time import time
from typing import List, Optional, Union

from collections.abc import Iterable

from terminusdb_client.errors import InterfaceError
from terminusdb_client.woqlquery.woql_query import WOQLQuery

from app.db.errors import DatabaseError
from app.db.woql_utils import (
    _args_as_payload,
    _clean_dict,
    _finish_response,
    _result2stream,
)

from .models import GraphType, WoqlResult


class DocumentMixin:
    """Mixin for document and schema operations."""

    def _conv_to_dict(self, obj):
        if isinstance(obj, dict):
            return _clean_dict(obj)
        elif hasattr(obj, "to_dict"):
            return obj.to_dict()
        elif hasattr(obj, "_to_dict"):
            if hasattr(obj, "_isinstance") and obj._isinstance:
                if hasattr(obj.__class__, "_subdocument"):
                    raise ValueError("Subdocument cannot be added directly")
                (d, refs) = obj._obj_to_dict()
                self._references = {**self._references, **refs}
                return d
            else:
                return obj._to_dict()
        else:
            raise ValueError("Object cannot convert to dictionary")

    def _unseen(self, seen):
        unseen = []
        for key in self._references:
            if key not in seen:
                unseen.append(self._references[key])
        return unseen

    def _convert_document(self, document, graph_type):
        if not isinstance(document, list):
            document = [document]

        seen = {}
        objects = []
        while document != []:
            for item in document:
                if hasattr(item, "to_dict") and graph_type != "schema":
                    raise InterfaceError(
                        "Inserting Schema object into non-schema graph."
                    )
                item_dict = self._conv_to_dict(item)
                if hasattr(item, "_capture"):
                    seen[item._capture] = item_dict
                else:
                    if isinstance(item_dict, list):
                        objects += item_dict
                    else:
                        objects.append(item_dict)

            document = self._unseen(seen)

        return list(seen.values()) + objects

    async def query_document(
        self,
        document_template: dict,
        graph_type: GraphType = GraphType.INSTANCE,
        skip: int = 0,
        count: Optional[int] = None,
        as_list: bool = False,
        get_data_version: bool = False,
        **kwargs,
    ) -> Union[Iterable, list]:
        """Retrieves all documents that match a given document template."""
        self._check_connection()

        payload = {"query": document_template, "graph_type": graph_type}
        payload["skip"] = skip
        if count is not None:
            payload["count"] = count
        add_args = ["prefixed", "minimized", "unfold"]
        for the_arg in add_args:
            if the_arg in kwargs:
                payload[the_arg] = kwargs[the_arg]
        headers = self._default_headers.copy()
        headers["X-HTTP-Method-Override"] = "GET"
        result = await self._session.post(
            self._documents_url(),
            headers=headers,
            json=payload,
            auth=self._auth(),
        )
        if get_data_version:
            result, version = _finish_response(result, get_data_version)
            return_obj = _result2stream(result)
            if as_list:
                return list(return_obj), version
            else:
                return return_obj, version

        return_obj = _result2stream(_finish_response(result))
        if as_list:
            return list(return_obj)
        else:
            return return_obj

    async def get_documents(
        self,
        iri_ids: List[str],
        graph_type: GraphType = GraphType.INSTANCE.value,
        get_data_version: bool = False,
        **kwargs,
    ) -> List[dict]:
        """Retrieves the documents of the iri_ids."""
        add_args = ["prefixed", "minimized", "unfold"]
        self._check_connection()
        payload = {"graph_type": graph_type}
        for the_arg in add_args:
            if the_arg in kwargs:
                payload[the_arg] = kwargs[the_arg]

        result = await self._session.post(
            self._documents_url() + "/",
            headers={**self._default_headers, "X-HTTP-Method-Override": "GET"},
            json={"ids": iri_ids},
            auth=self._auth(),
        )

        if get_data_version:
            result, version = _finish_response(result, get_data_version)
            return json.loads(result), version

        return _result2stream(_finish_response(result))

    async def get_document(
        self,
        iri_id: str,
        graph_type: GraphType = GraphType.INSTANCE.value,
        get_data_version: bool = False,
        **kwargs,
    ) -> dict:
        """Retrieves the document of the iri_id."""
        add_args = ["prefixed", "minimized", "unfold"]
        self._check_connection()
        payload = {"id": iri_id, "graph_type": graph_type}
        for the_arg in add_args:
            if the_arg in kwargs:
                payload[the_arg] = kwargs[the_arg]

        result = await self._session.get(
            self._documents_url() + "/",
            headers=self._default_headers,
            params=payload,
            auth=self._auth(),
        )

        if get_data_version:
            result, version = _finish_response(result, get_data_version)
            return json.loads(result), version

        return json.loads(_finish_response(result))

    async def get_documents_by_type(
        self,
        doc_type: str,
        graph_type: GraphType = GraphType.INSTANCE,
        skip: int = 0,
        count: Optional[int] = None,
        as_list: bool = False,
        get_data_version=False,
        **kwargs,
    ) -> Union[Iterable, list]:
        """Retrieves the documents by type."""
        return await self.get_all_documents(
            graph_type,
            skip,
            count,
            as_list,
            get_data_version,
            doc_type=doc_type,
            **kwargs,
        )

    async def get_all_documents(
        self,
        graph_type: GraphType = GraphType.INSTANCE.value,
        skip: int = 0,
        count: Optional[int] = None,
        as_list: bool = False,
        get_data_version: bool = False,
        doc_type: Optional[str] = None,
        **kwargs,
    ) -> Union[Iterable, list, tuple]:
        """Retrieves all available documents."""
        add_args = ["prefixed", "unfold"]
        self._check_connection()
        payload = _args_as_payload(
            {
                "graph_type": graph_type,
                "skip": skip,
                "type": doc_type,
                "count": count,
            }
        )
        for the_arg in add_args:
            if the_arg in kwargs:
                payload[the_arg] = kwargs[the_arg]
        result = await self._session.get(
            self._documents_url(),
            headers=self._default_headers,
            params=payload,
            auth=self._auth(),
        )

        if get_data_version:
            result, version = _finish_response(result, get_data_version)
            return_obj = _result2stream(result)
            if as_list:
                return list(return_obj), version
            else:
                return return_obj, version

        return_obj = _result2stream(_finish_response(result))
        if as_list:
            return list(return_obj)
        else:
            return return_obj

    async def get_existing_classes(self):
        """Get all the existing classes (only ids) in a database."""
        all_existing_obj = await self.get_all_documents(graph_type="schema")
        all_existing_class = {}
        for item in all_existing_obj:
            if item.get("@id"):
                all_existing_class[item["@id"]] = item
        return all_existing_class

    async def insert_document(
        self,
        document: Union[
            dict,
            List[dict],
            "Schema",
            "DocumentTemplate",
            List["DocumentTemplate"],
        ],
        graph_type: GraphType = GraphType.INSTANCE.value,
        full_replace: bool = False,
        commit_msg: Optional[str] = None,
        last_data_version: Optional[str] = None,
        compress: Union[str, int] = 1024,
        raw_json: bool = False,
        branch_name: Optional[str] = None,
    ) -> None:
        """Inserts the specified document(s)."""
        import warnings

        self._check_connection()
        params = self._generate_commit(commit_msg)
        params["graph_type"] = graph_type
        if full_replace:
            params["full_replace"] = "true"
        else:
            params["full_replace"] = "false"
        params["raw_json"] = "true" if raw_json else "false"

        headers = self._default_headers.copy()
        if last_data_version is not None:
            headers["TerminusDB-Data-Version"] = last_data_version

        self._references = {}
        new_doc = self._convert_document(document, graph_type)
        all_docs = list(self._references.values())
        self._references = {}

        if len(new_doc) == 0:
            return

        if full_replace:
            if new_doc[0].get("@type") != "@context":
                raise ValueError(
                    "The first item in document need to be dictionary "
                    "representing the context object."
                )
        else:
            if new_doc[0].get("@type") == "@context":
                warnings.warn(
                    "To replace context, need to use `full_replace` or "
                    "`replace_document`, skipping context object now.",
                    stacklevel=2,
                )
                new_doc.pop(0)

        result = await self._session.post(
            self._documents_url(branch_name=branch_name),
            headers=headers,
            params=params,
            json=new_doc,
            auth=self._auth(),
        )

        result = json.loads(_finish_response(result))

        if isinstance(all_docs, list):
            for idx, item in enumerate(all_docs):
                if hasattr(item, "_obj_to_dict") and not hasattr(
                    item, "_backend_id"
                ):
                    item._backend_id = result[idx]
        return result

    async def replace_document(
        self,
        document: Union[
            dict,
            List[dict],
            "Schema",
            "DocumentTemplate",
            List["DocumentTemplate"],
        ],
        graph_type: GraphType = GraphType.INSTANCE.value,
        commit_msg: Optional[str] = None,
        last_data_version: Optional[str] = None,
        compress: Union[str, int] = 1024,
        create: bool = False,
        raw_json: bool = False,
    ) -> dict:
        """Updates the specified document(s)."""
        self._check_connection()
        params = self._generate_commit(commit_msg)
        params["graph_type"] = graph_type
        params["create"] = "true" if create else "false"
        params["raw_json"] = "true" if raw_json else "false"

        headers = self._default_headers.copy()
        if last_data_version is not None:
            headers["TerminusDB-Data-Version"] = last_data_version

        self._references = {}
        new_doc = self._convert_document(document, graph_type)
        all_docs = list(self._references.values())
        self._references = {}

        json_string = json.dumps(new_doc).encode("utf-8")
        if compress != "never" and len(json_string) > compress:
            headers.update(
                {"Content-Encoding": "gzip", "Content-Type": "application/json"}
            )
            result = await self._session.put(
                self._documents_url(),
                headers=headers,
                params=params,
                content=gzip.compress(json_string),
                auth=self._auth(),
            )
        else:
            result = await self._session.put(
                self._documents_url(),
                headers=headers,
                params=params,
                json=new_doc,
                auth=self._auth(),
            )
        result = json.loads(_finish_response(result))
        if isinstance(all_docs, list):
            for idx, item in enumerate(all_docs):
                if hasattr(item, "_obj_to_dict") and not hasattr(
                    item, "_backend_id"
                ):
                    item._backend_id = result[idx][
                        len("terminusdb:///data/"):
                    ]
        return result

    async def update_document(
        self,
        document: Union[
            dict,
            List[dict],
            "Schema",
            "DocumentTemplate",
            List["DocumentTemplate"],
        ],
        graph_type: GraphType = GraphType.INSTANCE.value,
        commit_msg: Optional[str] = None,
        last_data_version: Optional[str] = None,
        compress: Union[str, int] = 1024,
    ) -> None:
        """Updates the specified document(s). Add if not existed."""
        await self.replace_document(
            document, graph_type, commit_msg, last_data_version, compress, True
        )

    async def delete_document(
        self,
        document: Union[str, list, dict, Iterable],
        graph_type: GraphType = GraphType.INSTANCE.value,
        commit_msg: Optional[str] = None,
        last_data_version: Optional[str] = None,
    ) -> None:
        """Delete the specified document(s)."""
        self._check_connection()
        doc_id = []
        if not isinstance(document, (str, list, dict)) and hasattr(
            document, "__iter__"
        ):
            document = list(document)
        if not isinstance(document, list):
            document = [document]
        for doc in document:
            if hasattr(doc, "_obj_to_dict"):
                (doc, refs) = doc._obj_to_dict()
            if isinstance(doc, dict) and doc.get("@id"):
                doc_id.append(doc.get("@id"))
            elif isinstance(doc, str):
                doc_id.append(doc)
        params = self._generate_commit(commit_msg)
        params["graph_type"] = graph_type

        headers = self._default_headers.copy()
        if last_data_version is not None:
            headers["TerminusDB-Data-Version"] = last_data_version

        _finish_response(
            await self._session.request(
                method="DELETE",
                url=self._documents_url(),
                headers=headers,
                params=params,
                json=doc_id,
                auth=self._auth(),
            )
        )

    async def has_doc(
        self,
        doc_id: str,
        graph_type: GraphType = GraphType.INSTANCE,
    ) -> bool:
        """Check if a certain document exists in a database."""
        self._check_connection()

        response = await self._session.get(
            self._documents_url(),
            headers=self._default_headers,
            json={"id": doc_id, "graph_type": graph_type},
            auth=self._auth(),
        )
        try:
            _finish_response(response)
            return True
        except DatabaseError as exception:
            body = exception.error_obj
            if (
                exception.status_code == 404
                and "api:error" in body
                and body["api:error"]["@type"] == "api:DocumentNotFound"
            ):
                return False
            raise exception

    async def get_class_frame(self, class_name):
        """Get the frame of the class. Info about all properties of that class."""
        self._check_connection()
        opts = {"type": class_name}
        result = await self._session.get(
            self._class_frame_url(),
            headers=self._default_headers,
            params=opts,
            auth=self._auth(),
        )
        return json.loads(_finish_response(result))

    def commit(self):
        """Not implemented: open transactions not supported."""

    async def query(
        self,
        woql_query: Union[dict, WOQLQuery],
        commit_msg: Optional[str] = None,
        get_data_version: bool = False,
        last_data_version: Optional[str] = None,
        streaming: bool = False,
    ) -> Union[dict, str, WoqlResult]:
        """Execute a WOQL query."""
        self._check_connection()
        query_obj = {"commit_info": self._generate_commit(commit_msg)}
        if isinstance(woql_query, WOQLQuery):
            request_woql_query = woql_query.to_dict()
        else:
            request_woql_query = woql_query
        query_obj["query"] = request_woql_query
        query_obj["streaming"] = streaming

        headers = self._default_headers.copy()
        if last_data_version is not None:
            headers["TerminusDB-Data-Version"] = last_data_version

        if streaming:
            async with self._session.stream(
                "POST",
                self._query_url(),
                headers=headers,
                json=query_obj,
                auth=self._auth(),
            ) as response:
                lines = response.aiter_lines()
                return await WoqlResult(lines)._init()

        result = await self._session.post(
            self._query_url(),
            headers=headers,
            json=query_obj,
            auth=self._auth(),
        )

        if get_data_version:
            result, version = _finish_response(result, get_data_version)
            result = json.loads(result)
        else:
            result = json.loads(_finish_response(result))

        if result.get("inserts") or result.get("deletes"):
            return "Commit successfully made."
        elif get_data_version:
            return result, version
        else:
            return result
