"""Todo tests."""

import pytest
from httpx import AsyncClient


async def get_auth_token(client: AsyncClient, email: str = "todo@example.com") -> str:
    """Helper to register and get auth token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_todo(client: AsyncClient):
    """Test creating a new todo."""
    token = await get_auth_token(client, "create@example.com")

    response = await client.post(
        "/api/v1/todos",
        json={"title": "Test Todo", "description": "A test todo item"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Todo"
    assert data["description"] == "A test todo item"
    assert data["completed"] is False


@pytest.mark.asyncio
async def test_get_todos(client: AsyncClient):
    """Test getting todo list."""
    token = await get_auth_token(client, "list@example.com")

    # Create a todo first
    await client.post(
        "/api/v1/todos",
        json={"title": "List Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Get todos
    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_update_todo(client: AsyncClient):
    """Test updating a todo."""
    token = await get_auth_token(client, "update@example.com")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Update Me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Update it
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Title", "completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_delete_todo(client: AsyncClient):
    """Test deleting a todo."""
    token = await get_auth_token(client, "delete@example.com")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Delete Me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Delete it
    response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_single_todo(client: AsyncClient):
    """Test getting a single todo by ID."""
    token = await get_auth_token(client, "single@example.com")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Single Todo", "description": "Get me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Get it
    response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Single Todo"


@pytest.mark.asyncio
async def test_user_cannot_read_update_or_delete_another_users_todo(
    client: AsyncClient,
):
    """Todo ownership applies to read, update, and delete operations."""
    owner_token = await get_auth_token(client, "owner@example.com")
    other_user_token = await get_auth_token(client, "other@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    other_user_headers = {"Authorization": f"Bearer {other_user_token}"}

    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Private Todo", "description": "Keep this"},
        headers=owner_headers,
    )
    todo_id = create_response.json()["id"]

    read_response = await client.get(
        f"/api/v1/todos/{todo_id}", headers=other_user_headers
    )
    update_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Stolen Todo"},
        headers=other_user_headers,
    )
    delete_response = await client.delete(
        f"/api/v1/todos/{todo_id}", headers=other_user_headers
    )

    assert read_response.status_code == 403
    assert update_response.status_code == 403
    assert delete_response.status_code == 403

    owner_read_response = await client.get(
        f"/api/v1/todos/{todo_id}", headers=owner_headers
    )
    assert owner_read_response.json()["title"] == "Private Todo"


@pytest.mark.asyncio
async def test_completed_toggle_from_true_to_false_persists(client: AsyncClient):
    token = await get_auth_token(client, "toggle@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_response = await client.post(
        "/api/v1/todos", json={"title": "Toggle me"}, headers=headers
    )
    todo_id = create_response.json()["id"]

    await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers=headers,
    )
    false_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers=headers,
    )
    read_response = await client.get(
        f"/api/v1/todos/{todo_id}", headers=headers
    )

    assert false_response.status_code == 200
    assert false_response.json()["completed"] is False
    assert read_response.json()["completed"] is False


@pytest.mark.asyncio
async def test_partial_title_update_preserves_description(client: AsyncClient):
    token = await get_auth_token(client, "partial@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Original", "description": "Must remain"},
        headers=headers,
    )
    todo_id = create_response.json()["id"]

    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Renamed"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Renamed"
    assert response.json()["description"] == "Must remain"


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["post", "put", "delete"])
async def test_todo_mutations_invalidate_user_cache(
    client: AsyncClient, redis_mock, method: str
):
    token = await get_auth_token(client, f"cache-{method}@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    cache_keys = [f"todos:user:cached:{method}"]

    async def cached_scan_iter(match=None):
        for key in cache_keys:
            yield key

    redis_mock.scan_iter = cached_scan_iter

    if method == "post":
        response = await client.post(
            "/api/v1/todos", json={"title": "Cached"}, headers=headers
        )
    else:
        create_response = await client.post(
            "/api/v1/todos", json={"title": "Cached"}, headers=headers
        )
        todo_id = create_response.json()["id"]
        if method == "put":
            response = await client.put(
                f"/api/v1/todos/{todo_id}",
                json={"title": "Updated"},
                headers=headers,
            )
        else:
            response = await client.delete(
                f"/api/v1/todos/{todo_id}", headers=headers
            )

    assert response.status_code in (201, 200, 204)
    redis_mock.delete_many.assert_called_with(cache_keys)


@pytest.mark.asyncio
async def test_list_todos_filters_by_status_and_tag(client: AsyncClient):
    token = await get_auth_token(client, "filters@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    tag_response = await client.post(
        "/api/v1/tags", json={"name": "Important"}, headers=headers
    )
    tag_id = tag_response.json()["id"]

    pending_response = await client.post(
        "/api/v1/todos", json={"title": "Pending matching"}, headers=headers
    )
    completed_response = await client.post(
        "/api/v1/todos", json={"title": "Completed matching"}, headers=headers
    )
    await client.put(
        f"/api/v1/todos/{completed_response.json()['id']}",
        json={"completed": True},
        headers=headers,
    )
    await client.post(
        f"/api/v1/todos/{pending_response.json()['id']}/tags",
        json={"tag_id": tag_id},
        headers=headers,
    )

    pending = await client.get(
        "/api/v1/todos", params={"status": "false"}, headers=headers
    )
    tagged = await client.get(
        "/api/v1/todos", params={"tag_id": tag_id}, headers=headers
    )

    assert pending.status_code == 200
    assert [item["title"] for item in pending.json()["items"]] == [
        "Pending matching"
    ]
    assert tagged.status_code == 200
    assert [item["title"] for item in tagged.json()["items"]] == [
        "Pending matching"
    ]
    assert tagged.json()["items"][0]["tags"] == [
        {"id": tag_id, "name": "Important", "color": None}
    ]


@pytest.mark.asyncio
async def test_bulk_status_rejects_mixed_ownership(client: AsyncClient):
    owner_token = await get_auth_token(client, "bulk-owner@example.com")
    other_token = await get_auth_token(client, "bulk-other@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}

    owner_todo = await client.post(
        "/api/v1/todos", json={"title": "Owner todo"}, headers=owner_headers
    )
    other_todo = await client.post(
        "/api/v1/todos", json={"title": "Other todo"}, headers=other_headers
    )

    response = await client.patch(
        "/api/v1/todos/bulk-status",
        json={
            "todo_ids": [owner_todo.json()["id"], other_todo.json()["id"]],
            "completed": True,
        },
        headers=owner_headers,
    )

    assert response.status_code == 404
    owner_read = await client.get(
        f"/api/v1/todos/{owner_todo.json()['id']}", headers=owner_headers
    )
    assert owner_read.json()["completed"] is False


@pytest.mark.asyncio
async def test_bulk_status_updates_owned_todos_and_invalidates_cache(
    client: AsyncClient, redis_mock
):
    token = await get_auth_token(client, "bulk-cache@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    cache_keys = ["todos:user:bulk-cache"]

    async def cached_scan_iter(match=None):
        for key in cache_keys:
            yield key

    redis_mock.scan_iter = cached_scan_iter
    todo_ids = []
    for title in ("First", "Second"):
        response = await client.post(
            "/api/v1/todos", json={"title": title}, headers=headers
        )
        todo_ids.append(response.json()["id"])
    redis_mock.delete_many.reset_mock()

    response = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": todo_ids, "completed": True},
        headers=headers,
    )

    assert response.status_code == 200
    assert {item["completed"] for item in response.json()} == {True}
    redis_mock.delete_many.assert_called_with(cache_keys)
