"""Diff, patch, and apply operations for TerminusDB."""

import json
from typing import List, Union

import httpx

from app.db.woql_utils import _finish_response

from .models import Patch


class DiffMixin:
    """Mixin for diff and patch operations. Requires _conv_to_dict from DocumentMixin."""

    def _convert_diff_document(self, document):
        if isinstance(document, list):
            new_doc = []
            for item in document:
                item_dict = self._conv_to_dict(item)
                new_doc.append(item_dict)
        else:
            new_doc = self._conv_to_dict(document)
        return new_doc

    async def apply(
        self,
        before_version,
        after_version,
        branch=None,
        message=None,
        author=None,
    ):
        """Diff two different commits and apply changes on branch."""
        self._check_connection()
        branch = branch if branch else self.branch
        return json.loads(
            _finish_response(
                await self._session.post(
                    self._apply_url(branch=branch),
                    headers=self._default_headers,
                    json={
                        "commit_info": self._generate_commit(message, author),
                        "before_commit": before_version,
                        "after_commit": after_version,
                    },
                    auth=self._auth(),
                )
            )
        )

    async def diff_object(self, before_object, after_object):
        """Diff two different objects."""
        self._check_connection(check_db=False)
        return json.loads(
            _finish_response(
                await self._session.post(
                    self._diff_url(),
                    headers=self._default_headers,
                    json={
                        "before": before_object,
                        "after": after_object,
                    },
                    auth=self._auth(),
                )
            )
        )

    async def diff_version(self, before_version, after_version):
        """Diff two different versions (branch or commit)."""
        self._check_connection(check_db=False)
        return json.loads(
            _finish_response(
                await self._session.post(
                    self._diff_url(),
                    headers=self._default_headers,
                    json={
                        "before_data_version": before_version,
                        "after_data_version": after_version,
                    },
                    auth=self._auth(),
                )
            )
        )

    async def diff(
        self,
        before: Union[
            str,
            dict,
            List[dict],
            "Schema",
            "DocumentTemplate",
            List["DocumentTemplate"],
        ],
        after: Union[
            str,
            dict,
            List[dict],
            "Schema",
            "DocumentTemplate",
            List["DocumentTemplate"],
        ],
        document_id: Union[str, None] = None,
    ):
        """Perform diff on 2 sets of document(s), result in a Patch object."""
        request_dict = {}
        for key, item in {"before": before, "after": after}.items():
            if isinstance(item, str):
                request_dict[f"{key}_data_version"] = item
            else:
                request_dict[key] = self._convert_diff_document(item)
        if document_id is not None:
            if "before_data_version" in request_dict:
                if (
                    document_id[: len("terminusdb:///data")]
                    == "terminusdb:///data"
                ):
                    request_dict["document_id"] = document_id
                else:
                    raise ValueError(
                        f"Valid document id starts with "
                        f"`terminusdb:///data`, but got {document_id}"
                    )
            else:
                raise ValueError(
                    "`document_id` can only be used with a data version or "
                    "commit ID as `before`, not a document object"
                )
        if self._connected:
            result = _finish_response(
                await self._session.post(
                    self._diff_url(),
                    headers=self._default_headers,
                    json=request_dict,
                    auth=self._auth(),
                )
            )
        else:
            async with httpx.AsyncClient() as tmp_client:
                result = _finish_response(
                    await tmp_client.post(
                        self.server_url,
                        headers=self._default_headers,
                        json=request_dict,
                    )
                )
        return Patch(json=result)

    async def patch(
        self,
        before: Union[
            dict,
            List[dict],
            "Schema",
            "DocumentTemplate",
            List["DocumentTemplate"],
        ],
        patch: Patch,
    ):
        """Apply the patch object to the before object. Does not commit."""
        request_dict = {
            "before": self._convert_diff_document(before),
            "patch": patch.content,
        }

        if self._connected:
            result = _finish_response(
                await self._session.post(
                    self._patch_url(),
                    headers=self._default_headers,
                    json=request_dict,
                    auth=self._auth(),
                )
            )
        else:
            async with httpx.AsyncClient() as tmp_client:
                result = _finish_response(
                    await tmp_client.post(
                        self.server_url,
                        headers=self._default_headers,
                        json=request_dict,
                    )
                )
        return json.loads(result)

    async def patch_resource(
        self,
        patch: Patch,
        branch=None,
        message=None,
        author=None,
        match_final_state=True,
    ):
        """Apply the patch object to the given resource."""
        commit_info = self._generate_commit(message, author)
        request_dict = {
            "patch": patch.content,
            "message": commit_info["message"],
            "author": commit_info["author"],
            "match_final_state": match_final_state,
        }
        patch_url = self._branch_base("patch", branch)

        result = _finish_response(
            await self._session.post(
                patch_url,
                headers=self._default_headers,
                json=request_dict,
                auth=self._auth(),
            )
        )
        return json.loads(result)
