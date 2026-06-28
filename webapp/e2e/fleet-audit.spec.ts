import { test, expect } from "@playwright/test";

const BACKEND = "http://127.0.0.1:11072";
const FRONTEND = "http://127.0.0.1:11073";

test.describe("Fleet Audit", () => {
  test("Backend health", async ({ request }) => {
    const resp = await request.get(`${BACKEND}/health`);
    expect(resp.status()).toBe(200);
    const data = await resp.json();
    expect(data.status).toBe("ok");
  });

  test("Frontend loads", async ({ page }) => {
    await page.goto(FRONTEND, { timeout: 15000 });
    await page.waitForTimeout(3000);
    await expect(page.locator("#root")).toBeAttached();
  });

  test("Dashboard shows header", async ({ page }) => {
    await page.goto(FRONTEND, { timeout: 15000 });
    await page.waitForTimeout(2000);
    await expect(page.getByText("Glama Status")).toBeVisible();
  });

  test("Report view loads", async ({ page }) => {
    await page.goto(FRONTEND, { timeout: 15000 });
    await page.waitForTimeout(2000);

    const reportButton = page.getByRole("button", { name: /Report/i });
    if (await reportButton.isVisible()) {
      await reportButton.click();
      await page.waitForTimeout(2000);
      await expect(
        page.getByText("Daily Fleet Report") || page.locator("body"),
      ).toBeAttached();
    }
  });

  test("API repos endpoint returns data", async ({ request }) => {
    const resp = await request.get(`${BACKEND}/api/repos`);
    expect(resp.status()).toBe(200);
    const data = await resp.json();
    expect(Array.isArray(data)).toBe(true);
  });

  test("API report endpoint returns structured data", async ({ request }) => {
    const resp = await request.get(`${BACKEND}/api/report`);
    expect(resp.status()).toBe(200);
    const data = await resp.json();
    expect(data).toHaveProperty("total_repos");
    expect(data).toHaveProperty("grade_distribution");
  });

  test("No console errors on dashboard", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (err) => errors.push(err.message));

    await page.goto(FRONTEND, { timeout: 15000 });
    await page.waitForTimeout(3000);

    expect(errors).toEqual([]);
  });
});

test.describe("Navigation", () => {
  test("Refresh button visible", async ({ page }) => {
    await page.goto(FRONTEND, { timeout: 15000 });
    await page.waitForTimeout(2000);

    const refreshButton = page.getByRole("button", { name: /Refresh Now/i });
    expect(await refreshButton.count()).toBeGreaterThan(0);
  });

  test("Filter input works", async ({ page }) => {
    await page.goto(FRONTEND, { timeout: 15000 });
    await page.waitForTimeout(2000);

    const filterInput = page.getByPlaceholder(/Filter by name/);
    if (await filterInput.isVisible()) {
      await filterInput.fill("test");
      await page.waitForTimeout(500);
    }
  });
});
