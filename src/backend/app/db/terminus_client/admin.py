"""Organization, user, and role management for TerminusDB."""

import json
from typing import Optional

from app.db.woql_utils import _finish_response


class AdminMixin:
    """Mixin for organization, user, and role management."""

    async def create_organization(self, org: str) -> Optional[dict]:
        """Add a new organization."""
        self._check_connection(check_db=False)
        result = await self._session.post(
            f"{self._organization_url()}/{org}",
            headers=self._default_headers,
            auth=self._auth(),
        )
        return json.loads(_finish_response(result))

    async def get_organization_users(self, org: str) -> Optional[dict]:
        """Returns a list of users in an organization."""
        self._check_connection(check_db=False)
        result = await self._session.get(
            f"{self._organization_url()}/{org}/users",
            headers=self._default_headers,
            auth=self._auth(),
        )
        return json.loads(_finish_response(result))

    async def get_organization_user(
        self, org: str, username: str
    ) -> Optional[dict]:
        """Returns user info related to an organization."""
        self._check_connection(check_db=False)
        result = await self._session.get(
            f"{self._organization_url()}/{org}/users/{username}",
            headers=self._default_headers,
            auth=self._auth(),
        )
        return json.loads(_finish_response(result))

    async def get_organization_user_databases(
        self, org: str, username: str
    ) -> Optional[dict]:
        """Returns the databases available to a user in an organization."""
        self._check_connection(check_db=False)
        result = await self._session.get(
            f"{self._organization_url()}/{org}/users/{username}/databases",
            headers=self._default_headers,
            auth=self._auth(),
        )
        return json.loads(_finish_response(result))

    async def get_organizations(self) -> Optional[dict]:
        """Returns a list of organizations in the database."""
        self._check_connection(check_db=False)
        result = await self._session.get(
            self._organization_url(),
            headers=self._default_headers,
            auth=self._auth(),
        )
        return json.loads(_finish_response(result))

    async def get_organization(self, org: str) -> Optional[dict]:
        """Returns a specific organization."""
        self._check_connection(check_db=False)
        result = await self._session.get(
            f"{self._organization_url()}/{org}",
            headers=self._default_headers,
            auth=self._auth(),
        )
        return json.loads(_finish_response(result))

    async def delete_organization(self, org: str) -> Optional[dict]:
        """Deletes a specific organization."""
        self._check_connection(check_db=False)
        result = await self._session.delete(
            f"{self._organization_url()}/{org}",
            headers=self._default_headers,
            auth=self._auth(),
        )
        return json.loads(_finish_response(result))

    async def change_capabilities(
        self, capability_change: dict
    ) -> Optional[dict]:
        """Change the capabilities of a certain user."""
        self._check_connection(check_db=False)
        result = await self._session.post(
            self._capabilities_url(),
            headers=self._default_headers,
            json=capability_change,
            auth=self._auth(),
        )
        return json.loads(_finish_response(result))

    async def add_role(self, role: dict) -> Optional[dict]:
        """Add a new role."""
        self._check_connection(check_db=False)
        result = await self._session.post(
            self._roles_url(),
            headers=self._default_headers,
            json=role,
            auth=self._auth(),
        )
        return json.loads(_finish_response(result))

    async def change_role(self, role: dict) -> Optional[dict]:
        """Change role actions for a particular role."""
        self._check_connection(check_db=False)
        result = await self._session.put(
            self._roles_url(),
            headers=self._default_headers,
            json=role,
            auth=self._auth(),
        )
        return json.loads(_finish_response(result))

    async def get_available_roles(self) -> Optional[dict]:
        """Get the available roles for the current authenticated user."""
        self._check_connection(check_db=False)
        result = await self._session.get(
            self._roles_url(),
            headers=self._default_headers,
            auth=self._auth(),
        )
        return json.loads(_finish_response(result))

    async def add_user(
        self, username: str, password: str
    ) -> Optional[dict]:
        """Add a new user."""
        self._check_connection(check_db=False)
        result = await self._session.post(
            self._users_url(),
            headers=self._default_headers,
            json={"name": username, "password": password},
            auth=self._auth(),
        )
        return json.loads(_finish_response(result))

    async def get_user(self, username: str) -> Optional[dict]:
        """Get a user."""
        self._check_connection(check_db=False)
        result = await self._session.get(
            f"{self._users_url()}/{username}",
            headers=self._default_headers,
            auth=self._auth(),
        )
        return json.loads(_finish_response(result))

    async def get_users(self) -> Optional[dict]:
        """Get all users."""
        self._check_connection(check_db=False)
        result = await self._session.get(
            self._users_url(),
            headers=self._default_headers,
            auth=self._auth(),
        )
        return json.loads(_finish_response(result))

    async def delete_user(self, username: str) -> Optional[dict]:
        """Delete a user."""
        self._check_connection(check_db=False)
        result = await self._session.delete(
            f"{self._users_url()}/{username}",
            headers=self._default_headers,
            auth=self._auth(),
        )
        return json.loads(_finish_response(result))

    async def change_user_password(
        self, username: str, password: str
    ) -> Optional[dict]:
        """Change user's password."""
        self._check_connection(check_db=False)
        result = await self._session.put(
            self._users_url(),
            headers=self._default_headers,
            json={"name": username, "password": password},
            auth=self._auth(),
        )
        return json.loads(_finish_response(result))
