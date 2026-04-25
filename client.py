"""
Thin HTTP client wrapping the OpenMetadata REST API.
All endpoints are rooted at /api/v1/.
"""

import json
from typing import Any, Dict, List, Optional

import httpx


class APIError(Exception):
    """Raised when the OpenMetadata API returns an error response."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")


class OpenMetadataClient:
    def __init__(self, host: str, token: str):
        self.host = host.rstrip("/")
        self.base_url = self.host + "/api/v1"
        self._client = httpx.Client(
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
            follow_redirects=True,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _raise_for(self, response: httpx.Response) -> Any:
        if response.status_code == 401:
            raise APIError(401, "Authentication failed — check your token.")
        if response.status_code == 404:
            raise APIError(404, "Resource not found.")
        if response.status_code >= 400:
            try:
                body = response.json()
                msg = body.get("message") or body.get("error") or response.text
            except Exception:
                msg = response.text
            raise APIError(response.status_code, msg)
        if response.status_code == 204:
            return None
        return response.json()

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    # ------------------------------------------------------------------
    # Public HTTP methods
    # ------------------------------------------------------------------

    def get(self, path: str, params: Optional[Dict] = None) -> Any:
        return self._raise_for(self._client.get(self._url(path), params=params))

    def post(self, path: str, data: Any = None) -> Any:
        return self._raise_for(self._client.post(self._url(path), json=data))

    def put(self, path: str, data: Any) -> Any:
        return self._raise_for(self._client.put(self._url(path), json=data))

    def patch_jsonpatch(self, path: str, operations: List[Dict]) -> Any:
        """PATCH using the JSON Patch media type (RFC 6902)."""
        headers = {"Content-Type": "application/json-patch+json"}
        return self._raise_for(
            self._client.patch(self._url(path), content=json.dumps(operations), headers=headers)
        )

    # ------------------------------------------------------------------
    # Domain helpers
    # ------------------------------------------------------------------

    def login(self, email: str, password: str) -> str:
        """POST to /users/login and return the JWT access token."""
        url = f"{self.host}/api/v1/users/login"
        r = httpx.post(url, json={"email": email, "password": password}, timeout=30.0)
        if r.status_code != 200:
            try:
                msg = r.json().get("message", r.text)
            except Exception:
                msg = r.text
            raise APIError(r.status_code, f"Login failed: {msg}")
        return r.json()["accessToken"]

    def search(
        self,
        query: str = "*",
        index: str = "table_search_index",
        size: int = 25,
        from_: int = 0,
        query_filter: Optional[Dict] = None,
    ) -> Dict:
        params: Dict[str, Any] = {
            "q": query,
            "index": index,
            "from": from_,
            "size": size,
        }
        if query_filter:
            params["query_filter"] = json.dumps(query_filter)
        return self.get("search/query", params=params)

    def get_entity(self, entity_type: str, fqn: str, fields: Optional[str] = None) -> Dict:
        """GET /api/v1/{entity_type}/name/{fqn}"""
        params = {}
        if fields:
            params["fields"] = fields
        return self.get(f"{entity_type}/name/{fqn}", params=params or None)

    def get_lineage(
        self,
        entity_type: str,
        fqn: str,
        upstream_depth: int = 1,
        downstream_depth: int = 1,
    ) -> Dict:
        return self.get(
            f"lineage/{entity_type}/name/{fqn}",
            params={"upstreamDepth": upstream_depth, "downstreamDepth": downstream_depth},
        )

    def tag_entity(self, entity_type: str, entity_id: str, tag_fqn: str) -> Any:
        """Add a tag to an entity via JSON Patch."""
        op = [
            {
                "op": "add",
                "path": "/tags/-",
                "value": {
                    "tagFQN": tag_fqn,
                    "labelType": "Manual",
                    "state": "Confirmed",
                    "source": "Classification",
                },
            }
        ]
        return self.patch_jsonpatch(f"{entity_type}/{entity_id}", op)

    def untag_entity(self, entity_type: str, fqn: str, tag_fqn: str, entity_id: str) -> Any:
        """Remove a tag from an entity via JSON Patch (get current tags, remove target, put back)."""
        entity = self.get_entity(entity_type, fqn, fields="tags")
        tags = [t for t in (entity.get("tags") or []) if t.get("tagFQN") != tag_fqn]
        op = [{"op": "replace", "path": "/tags", "value": tags}]
        return self.patch_jsonpatch(f"{entity_type}/{entity_id}", op)

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
