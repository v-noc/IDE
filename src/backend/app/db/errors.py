"""Custom errors for TerminusDB client, compatible with both httpx.Response and dict (streaming WOQL errors)."""

import json
from typing import Optional, Union

import httpx


class DatabaseError(Exception):
    """Exception for errors related to the database.

    Accepts both httpx.Response (HTTP API) and dict (streaming WOQL errors).
    """

    def __init__(self, response: Optional[Union[httpx.Response, dict]] = None):
        super().__init__()
        self.error_obj: Optional[dict] = None
        self.status_code: Optional[int] = None

        if response is None:
            self.message = "Unknown Error - No error message from response."
            return

        if isinstance(response, dict):
            self._init_from_dict(response)
        else:
            self._init_from_httpx_response(response)

    def _init_from_dict(self, err_dict: dict) -> None:
        """Handle streaming WOQL error responses (dict from json.loads)."""
        self.error_obj = err_dict
        self.status_code = None
        details = json.dumps(err_dict, indent=4, sort_keys=True)

        if err_dict.get("api:message"):
            self.message = err_dict["api:message"] + "\n" + details
        elif "api:error" in err_dict and isinstance(err_dict["api:error"], dict):
            err = err_dict["api:error"]
            if err.get("vio:message"):
                self.message = err["vio:message"] + "\n" + details
            else:
                self.message = "Unknown Error:\n" + details
        else:
            self.message = "Unknown Error:\n" + details

    def _init_from_httpx_response(self, response: httpx.Response) -> None:
        """Handle httpx.Response from HTTP API calls."""
        self.status_code = response.status_code

        if not response.text:
            self.message = "Unknown Error - No error message from response."
            return

        content_type = response.headers.get("content-type", "")
        if content_type[: len("application/json")] == "application/json":
            try:
                self.error_obj = response.json()
            except Exception:
                self.error_obj = None
                self.message = response.text
                return

            details = json.dumps(self.error_obj, indent=4, sort_keys=True)
            if self.error_obj.get("api:message"):
                self.message = self.error_obj["api:message"] + "\n" + details
            elif "api:error" in self.error_obj and self.error_obj["api:error"].get(
                "vio:message"
            ):
                self.message = (
                    self.error_obj["api:error"]["vio:message"] + "\n" + details
                )
            else:
                self.message = "Unknown Error:\n" + details
        else:
            self.error_obj = None
            self.message = response.text

    def __str__(self) -> str:
        return self.message
