"""Tag and todo-tag API tests."""

import pytest
from httpx import AsyncClient


async def auth_token(client: AsyncClient, email: str) -> str:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_and_list_tag(client: AsyncClient):
    token = await auth_token(client, "tag-owner@example.com")

    create_response = await client.post(
        "/api/v1/tags",
        json={"name": "Work", "color": "#2563eb"},
        headers=headers(token),
    )

    assert create_response.status_code == 201
    tag = create_response.json()
    assert tag["name"] == "Work"
    assert tag["color"] == "#2563eb"
    assert "created_at" in tag
    assert "updated_at" in tag

    list_response = await client.get("/api/v1/tags", headers=headers(token))
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [tag["id"]]


@pytest.mark.asyncio
async def test_tag_names_are_unique_case_insensitively(client: AsyncClient):
    token = await auth_token(client, "tag-duplicate@example.com")
    auth = headers(token)

    first = await client.post("/api/v1/tags", json={"name": "Personal"}, headers=auth)
    duplicate = await client.post(
        "/api/v1/tags", json={"name": "pErSoNaL"}, headers=auth
    )

    assert first.status_code == 201
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_user_cannot_access_another_users_tag(client: AsyncClient):
    owner_token = await auth_token(client, "tag-owner-2@example.com")
    other_token = await auth_token(client, "tag-other@example.com")

    create_response = await client.post(
        "/api/v1/tags",
        json={"name": "Private"},
        headers=headers(owner_token),
    )
    tag_id = create_response.json()["id"]

    other_list = await client.get("/api/v1/tags", headers=headers(other_token))
    other_update = await client.patch(
        f"/api/v1/tags/{tag_id}",
        json={"name": "Stolen"},
        headers=headers(other_token),
    )
    other_delete = await client.delete(
        f"/api/v1/tags/{tag_id}", headers=headers(other_token)
    )

    assert other_list.status_code == 200
    assert other_list.json() == []
    assert other_update.status_code == 404
    assert other_delete.status_code == 404


@pytest.mark.asyncio
async def test_user_cannot_attach_another_users_tag(client: AsyncClient):
    owner_token = await auth_token(client, "tag-owner-3@example.com")
    other_token = await auth_token(client, "tag-other-2@example.com")

    tag_response = await client.post(
        "/api/v1/tags", json={"name": "Owner only"}, headers=headers(owner_token)
    )
    tag_id = tag_response.json()["id"]
    todo_response = await client.post(
        "/api/v1/todos", json={"title": "Other todo"}, headers=headers(other_token)
    )
    todo_id = todo_response.json()["id"]

    attach_response = await client.post(
        f"/api/v1/todos/{todo_id}/tags",
        json={"tag_id": tag_id},
        headers=headers(other_token),
    )

    assert attach_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_tag_removes_todo_tag_relation(client: AsyncClient):
    token = await auth_token(client, "tag-delete@example.com")
    auth = headers(token)

    tag_response = await client.post(
        "/api/v1/tags", json={"name": "Temporary"}, headers=auth
    )
    todo_response = await client.post(
        "/api/v1/todos", json={"title": "Tagged todo"}, headers=auth
    )
    tag_id = tag_response.json()["id"]
    todo_id = todo_response.json()["id"]

    attach_response = await client.post(
        f"/api/v1/todos/{todo_id}/tags",
        json={"tag_id": tag_id},
        headers=auth,
    )
    delete_response = await client.delete(f"/api/v1/tags/{tag_id}", headers=auth)
    todo_after_delete = await client.get(f"/api/v1/todos/{todo_id}", headers=auth)

    assert attach_response.status_code == 200
    assert delete_response.status_code == 204
    assert todo_after_delete.json()["tags"] == []


@pytest.mark.asyncio
async def test_tag_mapping_mutations_invalidate_todo_cache(client: AsyncClient, redis_mock):
    token = await auth_token(client, "tag-cache@example.com")
    auth = headers(token)
    cache_keys = ["todos:user:tag-cache"]

    async def cached_scan_iter(match=None):
        for key in cache_keys:
            yield key

    redis_mock.scan_iter = cached_scan_iter

    tag_response = await client.post("/api/v1/tags", json={"name": "Cached"}, headers=auth)
    todo_response = await client.post(
        "/api/v1/todos", json={"title": "Cached todo"}, headers=auth
    )
    tag_id = tag_response.json()["id"]
    todo_id = todo_response.json()["id"]
    redis_mock.delete_many.reset_mock()

    attach_response = await client.post(
        f"/api/v1/todos/{todo_id}/tags",
        json={"tag_id": tag_id},
        headers=auth,
    )
    assert attach_response.status_code == 200
    redis_mock.delete_many.assert_called_with(cache_keys)

    redis_mock.delete_many.reset_mock()
    detach_response = await client.delete(
        f"/api/v1/todos/{todo_id}/tags/{tag_id}", headers=auth
    )
    assert detach_response.status_code == 204
    redis_mock.delete_many.assert_called_with(cache_keys)
