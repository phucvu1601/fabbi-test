import { test, expect, type BrowserContext, type Page } from "@playwright/test";

const API_URL =
  process.env.E2E_API_URL ?? "http://127.0.0.1:8000/api/v1";

const password = "Test@123456";

function uniqueEmail(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random()
    .toString(36)
    .slice(2, 8)}@example.com`;
}

async function registerUser(
  request: Parameters<typeof test>[0] extends never ? never : any,
  email: string,
) {
  const response = await request.post(`${API_URL}/auth/register`, {
    data: {
      email,
      password,
    },
  });

  expect(response.ok()).toBeTruthy();
}

async function login(page: Page, email: string) {
  await page.goto("/login");

  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign In" }).click();

  await expect(page).toHaveURL("/");
  await expect(page.getByRole("heading", { name: "Your todos" })).toBeVisible();
}

async function createTodo(page: Page, title: string) {
  await page.getByRole("button", { name: "Add todo" }).click();

  const dialog = page.getByRole("dialog");

  await expect(
    dialog.getByRole("heading", { name: "Create Todo" }),
  ).toBeVisible();

  await dialog.getByLabel("Title").fill(title);
  await dialog.getByRole("button", { name: "Create" }).click();

  await expect(dialog).toBeHidden();
  await expect(page.getByText(title, { exact: true })).toBeVisible();
}

test("Full User Journey: register, create, complete, verify, and logout", async ({
  page,
}) => {
  const email = uniqueEmail("journey");
  const todoTitle = `Journey todo ${Date.now()}`;

  await page.goto("/register");

  await page.getByLabel("Email", { exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page
    .getByLabel("Confirm Password", { exact: true })
    .fill(password);
  await page.getByRole("button", { name: "Create Account" }).click();

  await expect(page).toHaveURL("/");
  await expect(page.getByRole("heading", { name: "Your todos" })).toBeVisible();

  await createTodo(page, todoTitle);

  const checkbox = page.getByRole("checkbox");
  await expect(checkbox).toHaveCount(1);
  await expect(checkbox).not.toBeChecked();

  await checkbox.click();

  await expect(checkbox).toBeChecked();
  await expect(page.getByText(todoTitle, { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Log out" }).click();

  await expect(page).toHaveURL("/login");
  await expect(
    page.getByRole("heading", { name: "Welcome Back" }),
  ).toBeVisible();
});

test("Cross-User Data Isolation: private todos are not visible to another user", async ({
  browser,
  request,
}) => {
  const userA = uniqueEmail("user-a");
  const userB = uniqueEmail("user-b");
  const privateTodo = `Private todo ${Date.now()}`;

  await registerUser(request, userA);
  await registerUser(request, userB);

  const contextA = await browser.newContext();
  const contextB = await browser.newContext();

  try {
    const pageA = await contextA.newPage();
    await login(pageA, userA);
    await createTodo(pageA, privateTodo);

    await expect(pageA.getByText(privateTodo, { exact: true })).toBeVisible();

    const pageB = await contextB.newPage();
    await login(pageB, userB);

    await expect(pageB.getByText("No todos yet")).toBeVisible();
    await expect(
      pageB.getByText(privateTodo, { exact: true }),
    ).not.toBeVisible();
  } finally {
    await contextA.close();
    await contextB.close();
  }
});

test("Tags, filters, and bulk status actions work together", async ({ page }) => {
  const email = uniqueEmail("features");
  const todoTitle = `Tagged todo ${Date.now()}`;

  await page.goto("/register");
  await page.getByLabel("Email", { exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("Confirm Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Create Account" }).click();
  await expect(page).toHaveURL("/");

  await page.getByRole("button", { name: "Manage tags" }).click();
  const tagDialog = page.getByRole("dialog");
  await tagDialog.getByRole("button", { name: "Create tag" }).click();
  await expect(tagDialog.getByText("Tag name is required")).toBeVisible();
  await tagDialog.getByLabel("Name").fill("Project");
  await tagDialog.getByRole("button", { name: "Create tag" }).click();
  await expect(tagDialog.getByText("Project", { exact: true })).toBeVisible();
  await tagDialog.getByRole("button", { name: "Close" }).click();

  await page.getByRole("button", { name: "Add todo" }).click();
  const todoDialog = page.getByRole("dialog");
  await todoDialog.getByLabel("Title").fill(todoTitle);
  await todoDialog.getByRole("button", { name: "Project" }).click();
  await todoDialog.getByRole("button", { name: "Create" }).click();
  await expect(todoDialog).toBeHidden();
  await expect(page.getByText(todoTitle, { exact: true })).toBeVisible();

  const filterRequest = page.waitForRequest(
    (request) =>
      request.url().includes("/todos") &&
      request.url().includes("tag_id=") &&
      request.url().includes("page_size="),
  );
  await page.getByLabel("Filter by tag").selectOption({ label: "Project" });
  await filterRequest;
  await expect(page.getByText(todoTitle, { exact: true })).toBeVisible();

  await page
    .getByRole("button", {
      name: new RegExp(`Select ${todoTitle} for bulk actions`),
    })
    .click();
  await page.getByRole("button", { name: /Mark done \(1\)/ }).click();
  await expect(
    page.getByRole("checkbox", { name: `Mark ${todoTitle} active` }),
  ).toBeChecked();
});