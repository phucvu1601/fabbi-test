# Technical Specification: Todo List Sharing & Collaboration

## 1. Overview & Objective

- **Feature Summary**:  
  Tính năng cho phép Chủ sở hữu (Owner) của một Danh sách công việc (Todo List) chia sẻ danh sách đó với những người dùng khác trong hệ thống dưới hai cấp độ phân quyền: **Đọc (Viewer)** hoặc **Chỉnh sửa (Editor)**. Chủ sở hữu có thể thay đổi quyền hoặc hủy truy cập (Revoke) của thành viên bất kỳ lúc nào.

- **Problem Statement**:  
  Hiện tại, danh sách công việc mang tính cá nhân đơn lẻ. Người dùng không thể hợp tác làm việc nhóm, phân chia công việc hoặc cho phép thành viên khác theo dõi tiến độ công việc chung.

- **Target Audience / Roles**:  
  - **Owner**: Người tạo ra Todo List. Có toàn quyền quản lý Todo List, phân quyền và thu hồi quyền chia sẻ.  
  - **Editor**: Người dùng được chia sẻ với quyền Chỉnh sửa. Có thể xem, tạo mới, chỉnh sửa và đánh dấu hoàn thành/xóa các công việc (Todo Items) trong Todo List.  
  - **Viewer**: Người dùng được chia sẻ với quyền Chỉ xem. Chỉ có thể xem danh sách công việc và trạng thái của chúng, không có quyền chỉnh sửa.

---

## 2. User Stories & Acceptance Criteria

### User Story 1: Chia sẻ Todo List với quyền cụ thể
- **As an** Owner của một Todo List  
- **I want to** chia sẻ danh sách công việc cho người dùng khác bằng Email và gán quyền (`VIEWER` hoặc `EDITOR`)  
- **So that** tôi có thể cộng tác hoặc cho phép người khác theo dõi tiến độ công việc  
- **Acceptance Criteria**:
  - [ ] Chủ sở hữu có thể nhập Email người nhận và chọn quyền (`VIEWER` hoặc `EDITOR`).
  - [ ] Hệ thống kiểm tra người nhận có tồn tại trong hệ thống hay không; nếu không tồn tại, trả về lỗi `404 Not Found`.
  - [ ] Nếu người nhận đã được chia sẻ trước đó, hệ thống không tạo bản ghi mới mà báo lỗi hoặc cập nhật trực tiếp (xem phần Edge Cases).
  - [ ] Người dùng không thể tự chia sẻ danh sách cho chính mình (`400 Bad Request`).

### User Story 2: Quản lý & Thu hồi quyền truy cập (Revoke Access)
- **As an** Owner của một Todo List  
- **I want to** xem danh sách những người đang được chia sẻ, thay đổi quyền của họ hoặc thu hồi quyền truy cập bất kỳ lúc nào  
- **So that** tôi kiểm soát hoàn toàn tính bảo mật và riêng tư của dữ liệu  
- **Acceptance Criteria**:
  - [ ] Owner có thể truy vấn danh sách tất cả collaborator kèm theo role tương ứng.
  - [ ] Owner có thể thay đổi role của một collaborator từ `VIEWER` sang `EDITOR` và ngược lại.
  - [ ] Owner có thể thu hồi quyền truy cập của bất kỳ collaborator nào. Khi thu hồi thành công, collaborator đó ngay lập tức không thể xem hoặc thao tác trên Todo List.

### User Story 3: Xem và Thao tác trên Todo List được chia sẻ
- **As a** Collaborator (`VIEWER` hoặc `EDITOR`)  
- **I want to** truy cập vào danh sách các Todo List được người khác chia sẻ với mình  
- **So that** tôi có thể theo dõi công việc (với vai trò Viewer) hoặc cùng cập nhật công việc (với vai trò Editor)  
- **Acceptance Criteria**:
  - [ ] User có thể lấy danh sách các Todo List mà mình sở hữu hoặc được chia sẻ.
  - [ ] `VIEWER` thực hiện các thao tác ghi (Tạo, Sửa, Xóa Todo Item) sẽ bị từ chối với lỗi `403 Forbidden`.
  - [ ] `EDITOR` có thể thêm mới Todo Item, sửa tiêu đề/mô tả/trạng thái và xóa Todo Item trong list đó.
  - [ ] `EDITOR` không có quyền chia sẻ danh sách đó cho người khác hoặc thu hồi quyền của người khác (`403 Forbidden`).

---

## 3. Scope

### In-Scope
- Phân quyền theo 3 vai trò cấp Todo List: `OWNER`, `EDITOR`, `VIEWER`.
- API chia sẻ, cập nhật quyền, thu hồi quyền, danh sách người được chia sẻ.
- Kiểm tra quyền truy cập chặt chẽ ở cấp độ API Middleware / Application Layer.
- Xử lý cache invalidation tức thì khi thu hồi quyền hoặc thay đổi phân quyền.
- Xử lý concurrency control khi có nhiều Editor cập nhật cùng lúc.

### Out-of-Scope (Dành cho các phiên bản sau)
- **Chưa hỗ trợ chia sẻ qua Public Link**: Chỉ hỗ trợ chia sẻ trực tiếp tới Email đã đăng ký trong hệ thống.
- **Chưa hỗ trợ phân quyền ở cấp độ từng Todo Item riêng lẻ**: Phân quyền áp dụng cho toàn bộ danh sách.
- **Chưa có hệ thống Lời mời (Pending Invitation / Accept / Decline)**: Khi Owner chia sẻ, quyền truy cập được cấp ngay lập tức cho người nhận.
- **Chưa hỗ trợ Notification / Email Thông báo**: Không gửi email/push notification khi được chia sẻ.
- **Chưa chuyển giao quyền sở hữu (Transfer Ownership)**: Owner không thể chuyển vai trò Owner cho user khác.

---

## 4. Database Design

### New Table: `todo_list_collaborators`

Bảng lưu trữ thông tin phân quyền chia sẻ giữa Todo List và User.

| Column | Type | Constraints / Attributes | Description |
|---|---|---|---|
| `id` | `UUID` / `BIGINT` | `PRIMARY KEY`, Default: `gen_random_uuid()` | Định danh bản ghi |
| `todo_list_id` | `UUID` / `BIGINT` | `NOT NULL`, `FOREIGN KEY` -> `todo_lists(id)` | ID của Todo List được chia sẻ |
| `user_id` | `UUID` / `BIGINT` | `NOT NULL`, `FOREIGN KEY` -> `users(id)` | ID của người dùng được chia sẻ |
| `role` | `VARCHAR(20)` | `NOT NULL`, Check: `role IN ('VIEWER', 'EDITOR')` | Quyền được cấp |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | `NOT NULL`, Default: `CURRENT_TIMESTAMP` | Thời điểm chia sẻ |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | `NOT NULL`, Default: `CURRENT_TIMESTAMP` | Thời điểm cập nhật quyền |

### Constraints & Indexes
1. **Unique Constraint**:  
   - `UNIQUE(todo_list_id, user_id)`: Đảm bảo một user chỉ có một bản ghi phân quyền trên một Todo List.
2. **Foreign Key Cascade Delete**:  
   - `todo_list_id` REFERENCES `todo_lists(id)` ON DELETE CASCADE: Khi một Todo List bị xóa, toàn bộ bản ghi chia sẻ liên quan tự động xóa.
   - `user_id` REFERENCES `users(id)` ON DELETE CASCADE: Khi một User bị xóa, các bản ghi chia sẻ liên quan tự động xóa.
3. **Indexes**:  
   - `CREATE INDEX idx_collaborators_user_id ON todo_list_collaborators(user_id);` (Tối ưu truy vấn tìm danh sách các todo_list mà user được chia sẻ).
   - `CREATE INDEX idx_collaborators_list_user ON todo_list_collaborators(todo_list_id, user_id);` (Tối ưu truy vấn kiểm tra quyền của user trên todo_list).

---

## 5. API Contracts & Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/todo-lists/{list_id}/shares` | Chia sẻ Todo List cho người dùng khác | Yes (Owner) |
| `GET` | `/api/v1/todo-lists/{list_id}/shares` | Lấy danh sách những người được chia sẻ | Yes (Owner) |
| `PUT` | `/api/v1/todo-lists/{list_id}/shares/{user_id}` | Cập nhật quyền của một collaborator | Yes (Owner) |
| `DELETE` | `/api/v1/todo-lists/{list_id}/shares/{user_id}` | Thu hồi quyền truy cập của collaborator | Yes (Owner) |
| `GET` | `/api/v1/todo-lists/shared-with-me` | Lấy danh sách các Todo List được chia sẻ cho tôi | Yes (Authenticated) |

---


### Request Schemas & Validation

#### 1. POST `/api/v1/todo-lists/{list_id}/shares`

**Request Body**:
```json
{
  "email": "user@example.com",
  "role": "EDITOR"
}

```

*Validation*:

* `email`: Định dạng Email hợp lệ, bắt buộc (`required`).
* `role`: Giá trị hợp lệ chỉ bao gồm `"VIEWER"` hoặc `"EDITOR"`.

**Success Response (`201 Created`)**:

```json
{
  "id": "c39a7b12-9e32-4d2a-8742-123456789abc",
  "todo_list_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "user_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "email": "user@example.com",
  "role": "EDITOR",
  "created_at": "2026-03-30T10:00:00Z"
}

```

#### 2. PUT `/api/v1/todo-lists/{list_id}/shares/{user_id}`

**Request Body**:

```json
{
  "role": "VIEWER"
}

```

**Success Response (`200 OK`)**:

```json
{
  "todo_list_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  "user_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "role": "VIEWER",
  "updated_at": "2026-03-30T10:15:00Z"
}

```

#### 3. DELETE `/api/v1/todo-lists/{list_id}/shares/{user_id}`

**Success Response (`204 No Content`)**

---

### Error Payloads & Status Codes

Cấu trúc Error Response chuẩn:

```json
{
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "Mô tả lỗi chi tiết cho người dùng",
    "details": []
  }
}

```

| HTTP Status | Error Code | Nguyên nhân |
| --- | --- | --- |
| `400 Bad Request` | `SELF_SHARING_NOT_ALLOWED` | Owner tự chia sẻ danh sách cho chính mình. |
| `400 Bad Request` | `INVALID_ROLE` | Giá trị `role` không hợp lệ (khác `VIEWER`/`EDITOR`). |
| `409 Conflict` | `COLLABORATOR_ALREADY_EXISTS` | User này đã được chia sẻ danh sách từ trước. |
| `403 Forbidden` | `NOT_LIST_OWNER` | Người thực hiện chia sẻ/thu hồi không phải là Owner của Todo List. |
| `403 Forbidden` | `INSUFFICIENT_PERMISSIONS` | Viewer thực hiện hành động sửa/xóa Todo Item. |
| `404 Not Found` | `USER_NOT_FOUND` | Email người nhận không tồn tại trong hệ thống. |
| `404 Not Found` | `LIST_NOT_FOUND` | `list_id` không tồn tại hoặc người dùng không có quyền truy cập. |

---

## 6. Business Logic & Security Considerations

### Authorization & Permission Matrix

| Thao tác / API | Owner | Editor | Viewer | Non-Collaborator |
| --- | --- | --- | --- | --- |
| Xem danh sách Todo List & Items | ✅ | ✅ | ✅ | ❌ (`404`/`403`) |
| Thêm / Sửa / Xóa Todo Item | ✅ | ✅ | ❌ (`403`) | ❌ (`403`) |
| Chia sẻ List / Thay đổi Role người khác | ✅ | ❌ (`403`) | ❌ (`403`) | ❌ (`403`) |
| Thu hồi quyền chia sẻ (Revoke) | ✅ | ❌ (`403`) | ❌ (`403`) | ❌ (`403`) |
| Xóa toàn bộ Todo List | ✅ | ❌ (`403`) | ❌ (`403`) | ❌ (`403`) |

### Business Logic Rules

1. **Self-Sharing Prevention**:
* Hệ thống so sánh `user_id` của email nhận với `owner_id` của Todo List. Nếu trùng khớp, ném ra lỗi `400 Bad Request` (`SELF_SHARING_NOT_ALLOWED`).


2. **Duplicate Invites**:
* Khi `POST` thêm collaborator đã tồn tại trong `todo_list_collaborators`, trả về `409 Conflict`. Trường hợp muốn đổi quyền, client bắt buộc dùng `PUT /api/v1/todo-lists/{list_id}/shares/{user_id}`.


3. **Revocation Logic**:
* Khi Owner xóa collaborator khỏi list, xóa ngay lập tức bản ghi tương ứng trong database và xóa Redis cache ngay trong cùng một Database Transaction / Cache Cleanup block.



### Edge Cases & Concurrent Operations

1. **Revoke/Downgrade trong lúc Collaborator đang thao tác**:
* *Kịch bản*: Owner thu hồi quyền (hoặc hạ xuống Viewer) của Editor A đúng thời điểm Editor A bấm Lưu một Todo Item.
* *Xử lý*: Mọi request ghi (POST/PUT/DELETE) bắt buộc kiểm tra quyền thực tế từ Cache/DB tại thời điểm API Gateway / Backend xử lý. Nếu Cache/DB đã bị gạt bỏ quyền, trả về `403 Forbidden` ngay lập tức.


2. **Concurrent Updates trên cùng một Todo Item**:
* *Kịch bản*: Hai Editors cùng sửa tiêu đề một Todo Item tại cùng một thời điểm.
* *Xử lý*: Sử dụng **Optimistic Locking** (bảng `todo_items` có trường `version` hoặc `updated_at`). Request nào đến sau với `version` cũ sẽ nhận về lỗi `409 Conflict` kèm thông báo dữ liệu đã thay đổi, yêu cầu client reload dữ liệu mới.



---

## 7. Caching & Invalidation Strategy

Để đảm bảo hiệu năng khi kiểm tra quyền truy cập trên mọi API, hệ thống sử dụng **Redis Cache** cho thông tin phân quyền.

### Redis Key Structure & TTL

* **Permission Key**: `todolist:{list_id}:permissions`
* **Data Type**: Hash Map
* **Schema**:
* Field: `{user_id}`
* Value: `OWNER` | `EDITOR` | `VIEWER`


* **TTL**: 1 hour (`3600s`) với chiến lược Lazy Loading (cache hit đọc luôn, cache miss đọc DB rồi ghi cache).



*Ví dụ cấu trúc Hash trong Redis*:

```text
Key: todolist:list_uuid_123:permissions
  ├── owner_user_uuid  : "OWNER"
  ├── editor_user_uuid : "EDITOR"
  └── viewer_user_uuid : "VIEWER"

```

### Cache Invalidation Strategy

Áp dụng chiến lược **Immediate Invalidation (Xóa cache ngay lập tức)** để đảm bảo tính bảo mật và cập nhật tức thì:

1. **Khi Owner chia sẻ thành công (`POST /shares`)**:
* Thêm direct field vào Hash Key: `HSET todolist:{list_id}:permissions {new_user_id} {role}` hoặc xóa key `DEL todolist:{list_id}:permissions`.


2. **Khi Owner thay đổi quyền (`PUT /shares/{user_id}`)**:
* Cập nhật field tương ứng trong Redis Hash Key hoặc thực hiện `DEL todolist:{list_id}:permissions`.


3. **Khi Owner thu hồi quyền (`DELETE /shares/{user_id}`)**:
* Xóa ngay lập tức field `{user_id}` khỏi Redis Hash Key: `HDEL todolist:{list_id}:permissions {user_id}`.
* Thực hiện xóa toàn bộ key `DEL todolist:{list_id}:permissions` để cưỡng chế load lại dữ liệu mới từ DB ở request tiếp theo.


4. **Khi Owner xóa Todo List (`DELETE /todo-lists/{list_id}`)**:
* Thực hiện `DEL todolist:{list_id}:permissions`.
