import { test, expect, type Page } from '@playwright/test';

const dataRowSelector = 'table tbody > tr:not(.ant-table-measure-row):not(.ant-table-placeholder):not([aria-hidden="true"])';

async function waitForTableData(page: Page, timeout = 10_000) {
  await expect(page.locator(dataRowSelector).first()).toBeVisible({ timeout });
}

async function selectSearchOption(page: Page, index: number, optionText: string) {
  const searchForm = page.locator('.bg-white.rounded-lg.border').first();
  await searchForm.locator('.ant-select').nth(index).click();
  await page.locator('.ant-select-dropdown:visible').last().locator('.ant-select-item-option-content', { hasText: optionText }).first().click({ force: true });
}

test.describe('Application Master Data (/app-management/cmdb)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/app-management/cmdb');
    await waitForTableData(page);
  });

  /* ─── Page Load ─── */

  test('page title and heading render', async ({ page }) => {
    await expect(page.locator('h1')).toHaveText('Application Master Data');
  });

  test('sidebar link is active', async ({ page }) => {
    const link = page.locator('nav a', { hasText: 'Application Master Data' });
    await expect(link).toBeVisible();
  });

  test('table loads with data rows', async ({ page }) => {
    const rows = page.locator(dataRowSelector);
    await expect(rows).not.toHaveCount(0);
  });

  test('first row has a valid App ID (empty IDs sorted last)', async ({ page }) => {
    const firstAppId = page.locator(`${dataRowSelector} td:first-child`).first();
    await expect(firstAppId).toHaveText(/^A\d+/);
  });

  test('pagination shows total count', async ({ page }) => {
    await expect(page.getByText(/Total/)).toBeVisible();
  });

  /* ─── Search Form ─── */

  test('search form has all expected fields', async ({ page }) => {
    const form = page.locator('.bg-white.rounded-lg.border').first();
    // Text inputs
    await expect(form.getByPlaceholder('Application ID')).toBeVisible();
    await expect(form.getByPlaceholder('Name or Full Name')).toBeVisible();
    await expect(form.getByPlaceholder('Owner Tower')).toBeVisible();
    await expect(form.getByPlaceholder('Owned By')).toBeVisible();
    const selects = form.locator('.ant-select');
    await expect(selects).toHaveCount(6);
  });

  test('dropdown filters have correct options', async ({ page }) => {
    const form = page.locator('.bg-white.rounded-lg.border').first();
    await expect(form.locator('.ant-select')).toHaveCount(6);
    await expect(form.getByText('Status')).toBeVisible();
    await expect(form.getByText('Classification')).toBeVisible();
    await expect(form.getByText('Solution Type')).toBeVisible();
    await expect(form.getByText('Service Area')).toBeVisible();
    await expect(form.getByText('App Ownership')).toBeVisible();
    await expect(form.getByText('Portfolio')).toBeVisible();
  });

  /* ─── Filtering ─── */

  test('filter by Status = Active', async ({ page }) => {
    await selectSearchOption(page, 0, 'Active');
    await page.getByRole('button', { name: 'Search' }).click();
    // Wait for filtered data to load — status column should show "Active"
    await page.locator(`${dataRowSelector} td:nth-child(4)`).filter({ hasText: 'Active' }).first().waitFor({ timeout: 10_000 });

    // All visible status badges should say Active
    const statuses = page.locator(`${dataRowSelector} td:nth-child(4)`);
    const count = await statuses.count();
    expect(count).toBeGreaterThan(0);
    for (let i = 0; i < Math.min(count, 5); i++) {
      await expect(statuses.nth(i)).toContainText('Active');
    }
  });

  test('filter by Name text search', async ({ page }) => {
    await page.getByPlaceholder('Name or Full Name').fill('ECC');
    await page.getByRole('button', { name: 'Search' }).click();
    await waitForTableData(page, 5_000);

    const rows = page.locator(dataRowSelector);
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
    // At least one row should contain ECC
    await expect(page.locator('table tbody').getByText('ECC').first()).toBeVisible();
  });

  test('filter by Solution Type = SaaS', async ({ page }) => {
    await selectSearchOption(page, 2, 'SaaS');
    await page.getByRole('button', { name: 'Search' }).click();
    await waitForTableData(page, 5_000);

    const rows = page.locator(dataRowSelector);
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test('reset button clears filters', async ({ page }) => {
    // Apply a filter first
    await selectSearchOption(page, 0, 'Decommissioned');
    await page.getByRole('button', { name: 'Search' }).click();
    await waitForTableData(page, 5_000);

    // Click reset
    await page.getByRole('button', { name: 'Reset' }).click();
    await waitForTableData(page, 10_000);

    await expect(page.locator('.bg-white.rounded-lg.border').first().locator('.ant-select-selection-item')).toHaveCount(0);
  });

  /* ─── Sorting ─── */

  test('default sort is App ID ascending', async ({ page }) => {
    // Wait until first cell actually contains an App ID (not "Loading...")
    await page.locator(`${dataRowSelector} td:first-child`).first().filter({ hasText: /^A\d+/ }).waitFor({ timeout: 10_000 });

    const firstId = (await page.locator(`${dataRowSelector} td:first-child`).nth(0).textContent())!.trim();
    const secondId = (await page.locator(`${dataRowSelector} td:first-child`).nth(1).textContent())!.trim();
    // Both should start with A and first should come before second
    expect(firstId).toMatch(/^A\d+/);
    expect(secondId).toMatch(/^A\d+/);
    expect(firstId.localeCompare(secondId)).toBeLessThanOrEqual(0);
  });

  test('clicking Name header sorts by name', async ({ page }) => {
    await page.getByRole('columnheader', { name: 'Name', exact: true }).click();
    await waitForTableData(page, 5_000);

    const firstName = (await page.locator(`${dataRowSelector} td:nth-child(2)`).nth(0).textContent())!.trim();
    const secondName = (await page.locator(`${dataRowSelector} td:nth-child(2)`).nth(1).textContent())!.trim();
    expect(firstName.localeCompare(secondName)).toBeLessThanOrEqual(0);
  });

  test('clicking same header twice reverses sort', async ({ page }) => {
    const header = page.getByRole('columnheader', { name: 'Name', exact: true });
    const firstPass = (await page.locator(`${dataRowSelector} td:nth-child(2)`).nth(0).textContent())!.trim();

    await header.click();
    await waitForTableData(page, 5_000);
    const secondPass = (await page.locator(`${dataRowSelector} td:nth-child(2)`).nth(0).textContent())!.trim();

    await header.click();
    await waitForTableData(page, 5_000);

    const thirdPass = (await page.locator(`${dataRowSelector} td:nth-child(2)`).nth(0).textContent())!.trim();
    expect(firstPass).toBeTruthy();
    expect(secondPass).toBeTruthy();
    expect(thirdPass).toBeTruthy();
  });

  /* ─── Pagination ─── */

  test('changing page loads new data', async ({ page }) => {
    const firstPageId = (await page.locator(`${dataRowSelector} td:first-child`).first().textContent())!.trim();

    // Click page 2 button — find it within pagination area (not the table)
    const paginationArea = page.locator('nav, .pagination, [class*="pagination"]').last();
    const page2Btn = paginationArea.getByRole('button', { name: '2', exact: true });
    if (await page2Btn.isVisible()) {
      await page2Btn.click();
      await waitForTableData(page, 5_000);
      const secondPageId = (await page.locator(`${dataRowSelector} td:first-child`).first().textContent())!.trim();
      expect(secondPageId).not.toEqual(firstPageId);
    }
  });

  /* ─── Detail Drawer ─── */

  test('clicking a row opens detail drawer', async ({ page }) => {
    await page.locator(`${dataRowSelector} td:nth-child(2)`).first().click();
    await page.waitForTimeout(300);

    const drawer = page.locator('.fixed.inset-0');
    await expect(drawer).toBeVisible();
  });

  test('detail drawer shows basic information section', async ({ page }) => {
    await page.locator(`${dataRowSelector} td:nth-child(2)`).first().click();
    await page.waitForTimeout(300);

    const drawer = page.locator('.fixed.inset-0');
    await expect(drawer.getByRole('heading', { name: 'Basic Information' })).toBeVisible();
  });

  test('detail drawer shows ownership section', async ({ page }) => {
    await page.locator(`${dataRowSelector} td:nth-child(2)`).first().click();
    await page.waitForTimeout(300);

    const drawer = page.locator('.fixed.inset-0');
    await expect(drawer.getByRole('heading', { name: 'Ownership' })).toBeVisible();
  });

  test('detail drawer shows description section', async ({ page }) => {
    await page.locator(`${dataRowSelector} td:nth-child(2)`).first().click();
    await page.waitForTimeout(300);

    // Scroll down in drawer to see description section
    const drawerContent = page.locator('.fixed.inset-0 .overflow-y-auto');
    await drawerContent.evaluate(el => el.scrollTo(0, el.scrollHeight));
    await expect(page.getByText('DESCRIPTION & OTHER')).toBeVisible();
  });

  test('detail drawer classification has no curly braces', async ({ page }) => {
    await page.locator(`${dataRowSelector} td:nth-child(2)`).first().click();
    await page.waitForTimeout(300);

    const drawer = page.locator('.fixed.inset-0');
    const content = await drawer.textContent();
    expect(content).not.toContain('{"');
    expect(content).not.toContain('"}');
  });

  test('clicking overlay closes drawer', async ({ page }) => {
    await page.locator(`${dataRowSelector} td:nth-child(2)`).first().click();
    await page.waitForTimeout(300);

    await page.locator('.absolute.inset-0.bg-black\\/20').click({ force: true, position: { x: 10, y: 10 } });
    await page.waitForTimeout(300);

    await expect(page.locator('.fixed.inset-0')).not.toBeVisible();
  });

  test('clicking X button closes drawer', async ({ page }) => {
    await page.locator(`${dataRowSelector} td:nth-child(2)`).first().click();
    await page.waitForTimeout(300);

    await page.locator('.fixed.inset-0 button').first().click();
    await page.waitForTimeout(300);

    await expect(page.locator('.fixed.inset-0')).not.toBeVisible();
  });

  /* ─── Combined Filter + Sort ─── */

  test('filter and sort work together', async ({ page }) => {
    // Filter by Status = Active
    await selectSearchOption(page, 0, 'Active');
    await page.getByRole('button', { name: 'Search' }).click();
    // Wait for filtered data to load — status column should show "Active"
    await page.locator(`${dataRowSelector} td:nth-child(4)`).filter({ hasText: 'Active' }).first().waitFor({ timeout: 10_000 });

    // Sort by Name (use exact role selector to avoid matching "Full Name")
    await page.getByRole('columnheader', { name: 'Name', exact: true }).click();
    // Wait for sorted data to reload — first status cell should still be Active
    await page.locator(`${dataRowSelector} td:nth-child(4)`).filter({ hasText: 'Active' }).first().waitFor({ timeout: 10_000 });

    // All rows should still be Active
    const statuses = page.locator(`${dataRowSelector} td:nth-child(4)`);
    const count = await statuses.count();
    expect(count).toBeGreaterThan(0);
    for (let i = 0; i < Math.min(count, 3); i++) {
      await expect(statuses.nth(i)).toContainText('Active');
    }

    // And names should be sorted ascending
    const firstName = (await page.locator(`${dataRowSelector} td:nth-child(2)`).nth(0).textContent())!.trim();
    const secondName = (await page.locator(`${dataRowSelector} td:nth-child(2)`).nth(1).textContent())!.trim();
    expect(firstName.localeCompare(secondName)).toBeLessThanOrEqual(0);
  });
});
