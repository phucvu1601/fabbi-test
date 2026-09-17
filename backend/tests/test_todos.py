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
