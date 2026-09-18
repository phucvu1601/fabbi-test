# Manual Test Plan & Execution Report: Todo Application Security & Regression Scope

## 1. Scope & Objective
- **Mục tiêu kiểm thử:** Xác thực việc sửa đổi các lỗ hổng bảo mật (BOLA, Cross-account Cache Leakage) và kiểm tra hồi quy các chức năng cốt lõi của ứng dụng Todo.
- **Phạm vi kiểm thử:** Authentication, Todo CRUD, Authorization (BOLA), Redis/React Query Caching.

## 2. Test Environment & Prerequisites
- **Base URL Backend:** `http://localhost:8000`
- **Base URL Frontend:** `http://localhost:5173`
- **Pre-seeded Test Accounts:**
  - Account 1 (User A): `demo@test.com` / `Demo@123`
  - Account 2 (User B): `randallkimberly@example.com` / `Demo@123`

## 3. Test Cases Matrix (Cập nhật bổ sung)

| TC ID | Feature | Test Scenario | Test Steps | Expected Result | Priority | Status |
|---|---|---|---|---|---|---|
| **TC-01** | Auth | Login thành công | 1. Nhập email/pass User A<br>2. Bấm Login | Chuyển hướng vào `/todos`, lưu token vào LocalStorage | High / Blocker | **PASS** |
| **TC-02** | Auth | Login thất bại với mật khẩu sai | 1. Nhập email User A, pass sai<br>2. Bấm Login | Trả về thông báo "Incorrect password" (HTTP 401) | Medium / Security | **PASS** |
| **TC-03** | Security (BOLA) | User A không thể đọc/sửa/xóa Todo của User B | 1. User B tạo Todo ID `X`<br>2. User A gọi PUT/DELETE/GET `/todos/X` | Trả về HTTP 404/403, không sửa đổi dữ liệu | Critical | **PASS** |
| **TC-04** | Security (Cache Leak) | Chuyển tài khoản không lộ Cache cũ | 1. User A login, xem Todos<br>2. User A Logout<br>3. User B Login | UI xóa sạch cache User A, chỉ hiển thị Todos của User B | Critical | **PASS** |
| **TC-05** | Todo Logic | Single-field Update (Partial Update) | 1. Tạo Todo có `title` & `description`<br>2. Cập nhật chỉ `title` | `title` mới được lưu, `description` cũ không bị xóa/ghi đè `null` | High | **PASS** |
| **TC-06** | Todo Logic | Toggle `completed` từ true về false | 1. Check completed = true<br>2. Uncheck completed<br>3. Refresh trang | Trạng thái `completed` lưu chính xác là `false` trong DB | High | **PASS** |
| **TC-07** | Cache | Invalidate Cache khi Mutation | 1. Fetch `/todos` (Cache hit)<br>2. Tạo/Sửa/Xóa 1 Todo<br>3. Fetch lại `/todos` | Trả về dữ liệu mới nhất, Redis key cũ bị xóa | High | **PASS** |
| **TC-08** | Auth / Token | Tự động gia hạn Access Token khi hết hạn | 1. Chờ Access Token hết hạn (hoặc làm giả token hết hạn)<br>2. Thực hiện request gọi API `/todos` | Frontend tự động gọi API `/auth/refresh` bằng Refresh Token để lấy Access Token mới và retry request mượt mà | High | **FAIL** |
| **TC-09** | Auth / Security | Revoke Refresh Token khi người dùng Logout | 1. User A bấm Logout trên UI<br>2. Lấy Refresh Token cũ gọi trực tiếp endpoint `/auth/refresh` | Backend từ chối cấp Access Token mới (HTTP 401/40d Blacklisted/Revoked) | High | **FAIL** |

---

## 4. Execution Summary & Defect Tracking

- **Tổng số Test Cases:** 9
- **Passed:** 7/9 (77.8%)
- **Failed:** 2/9 (22.2%)
- **Tồn đọng (Known Issues):** Phát hiện 2 lỗi liên quan đến cơ chế Quản lý Token (Refresh Token Lifecycle):

### Danh sách Defect / Bug Tracking

| Bug ID | Title | Description / Impact | Severity | Status |
|---|---|---|---|---|
| **BUG-01** | Frontend chưa tích hợp luồng Refresh Token | Frontend nhận `refresh_token` từ response login nhưng lưu kho/không sử dụng. Khi `access_token` hết hạn (401), HTTP Interceptor không tự động gọi `/auth/refresh` mà bắt người dùng đăng nhập lại từ đầu. | High | **Open** |
| **BUG-02** | Backend không Revoke / Blacklist Refresh Token khi Logout | Khi người dùng thực hiện Logout, Backend chỉ trả về HTTP 200/Xóa Cookie/Token phía client mà không xóa/cho Refresh Token vào blacklist trên DB/Redis. Kẻ tấn công nếu chộp được `refresh_token` cũ vẫn có thể xin cấp `access_token` mới bình thường. | High | **Open** |

- **Ghi chú:** Bổ sung cơ chế Quản lý Token (Refresh Token Lifecycle)