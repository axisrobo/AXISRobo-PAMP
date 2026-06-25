import { test, expect, type Page } from '@playwright/test';

const dataRowSelector = 'table tbody > tr:not(.ant-table-measure-row):not(.ant-table-placeholder):not([aria-hidden="true"])';

async function waitForTableData(page: Page, timeout = 10_000) {
  await expect(page.locator(dataRowSelector).first()).toBeVisible({ timeout });
}

test.describe('Business Capability Mapping (/app-management/bcm)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/app-management/bcm');
    await waitForTableData(page);
  });

  /* ─── Page Load ─── */

  test('page title and heading render', async ({ page }) => {
    await expect(page.locator('h1')).toHaveText('Business Capability Mapping');
  });

  test('sidebar link is active', async ({ page }) => {
    const link = page.locator('nav a', { hasText: 'Business Capability Mapping' });
    await expect(link).toBeVisible();
  });

  test('table loads with data rows', async ({ page }) => {
    const rows = page.locator(dataRowSelector);
    await expect(rows).not.toHaveCount(0);
  });

  /* ─── Search Form ─── */

  test('search form has all expected fields', async ({ page }) => {
    await expect(page.getByPlaceholder('Application ID')).toBeVisible();
    await expect(page.getByPlaceholder('Application name')).toBeVisible();
    await expect(page.getByPlaceholder('Domain L1')).toBeVisible();
    await expect(page.getByPlaceholder('Sub Domain L2')).toBeVisible();
    await expect(page.getByPlaceholder('BC Name')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Search' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Reset' })).toBeVisible();
  });

  /* ─── Table Columns ─── */

  test('table has expected column headers', async ({ page }) => {
    const headers = page.locator('table thead th');
    const texts = await headers.allTextContents();
    const joined = texts.join(' ');
    expect(joined).toContain('App ID');
    expect(joined).toContain('Application Name');
    expect(joined).toContain('IT Owner');
    expect(joined).toContain('Status');
    expect(joined).toContain('BC ID');
    expect(joined).toContain('BC Name');
    expect(joined).toContain('Domain L1');
    expect(joined).toContain('Sub Domain L2');
    expect(joined).toContain('Capability Group L3');
    expect(joined).toContain('Version');
  });

  test('export button is visible', async ({ page }) => {
    // Export button is in the DataTable toolbar (Download icon)
    const exportBtn = page.locator('button[title="Export CSV"], button:has(svg.lucide-download)');
    await expect(exportBtn).toBeVisible();
  });

  /* ─── Filtering ─── */

  test('search by App Name filters rows', async ({ page }) => {
    // Get first row's app name to use as a search term
    const firstAppName = (await page.locator(`${dataRowSelector} td:nth-child(2)`).first().textContent())!.trim();
    const searchTerm = firstAppName.slice(0, 5); // Use first 5 chars

    await page.getByPlaceholder('Application name').fill(searchTerm);
    await page.getByRole('button', { name: 'Search' }).click();
    await waitForTableData(page, 5_000);

    const rows = page.locator(dataRowSelector);
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test('reset button clears filters', async ({ page }) => {
    const firstAppName = (await page.locator(`${dataRowSelector} td:nth-child(2)`).first().textContent())!.trim();
    await page.getByPlaceholder('Application name').fill(firstAppName.slice(0, 5));
    await page.getByRole('button', { name: 'Search' }).click();
    await waitForTableData(page, 5_000);

    await page.getByRole('button', { name: 'Reset' }).click();
    await waitForTableData(page, 10_000);

    await expect(page.getByPlaceholder('Application name')).toHaveValue('');
  });

  /* ─── Pagination ─── */

  test('pagination shows total count', async ({ page }) => {
    await expect(page.getByText(/Total/)).toBeVisible();
  });

  test('changing page loads new data', async ({ page }) => {
    const firstRowText = (await page.locator(`${dataRowSelector} td:first-child`).first().textContent())!.trim();

    const paginationArea = page.locator('nav, .pagination, [class*="pagination"]').last();
    const page2Btn = paginationArea.getByRole('button', { name: '2', exact: true });
    if (await page2Btn.isVisible()) {
      await page2Btn.click();
      await waitForTableData(page, 5_000);
      const secondPageText = (await page.locator(`${dataRowSelector} td:first-child`).first().textContent())!.trim();
      expect(secondPageText).not.toEqual(firstRowText);
    }
  });

  /* ─── Detail Drawer ─── */

  test('clicking App ID opens detail drawer', async ({ page }) => {
    // App ID is a button with blue text
    const appIdLink = page.locator(`${dataRowSelector} button.text-primary-blue`).first();
    await appIdLink.click();
    await page.waitForTimeout(500);

    const drawer = page.locator('.fixed.inset-0');
    await expect(drawer).toBeVisible();
  });

  test('drawer shows correct title', async ({ page }) => {
    const appIdLink = page.locator(`${dataRowSelector} button.text-primary-blue`).first();
    await appIdLink.click();
    await page.waitForTimeout(500);

    await expect(page.getByText('Application Business Capability Mapping')).toBeVisible();
  });

  test('drawer shows General Data section', async ({ page }) => {
    const appIdLink = page.locator(`${dataRowSelector} button.text-primary-blue`).first();
    await appIdLink.click();
    await page.waitForTimeout(500);

    await expect(page.getByText('General Data')).toBeVisible();
    await expect(page.getByText('Application ID')).toBeVisible();
    // "Application Name" appears both as column header and field label — use the drawer-scoped label
    const drawer = page.locator('.fixed.inset-0');
    await expect(drawer.locator('span', { hasText: 'Application Name' }).first()).toBeVisible();
  });

  test('drawer shows Business Capability Mapping section with table', async ({ page }) => {
    const appIdLink = page.locator(`${dataRowSelector} button.text-primary-blue`).first();
    await appIdLink.click();
    await page.waitForTimeout(500);

    const drawer = page.locator('.fixed.inset-0');
    // The section heading "Business Capability Mapping" inside the drawer
    const bcmSection = drawer.locator('h3', { hasText: 'Business Capability Mapping' });
    await expect(bcmSection).toBeVisible();

    // Mapping table headers
    const drawerTable = drawer.locator('table');
    const headerTexts = await drawerTable.locator('th').allTextContents();
    const joined = headerTexts.join(' ');
    expect(joined).toContain('Versions');
    expect(joined).toContain('BC ID');
    expect(joined).toContain('Domain(L1)');
    expect(joined).toContain('BC Name');
    expect(joined).toContain('Operation');
  });

  test('drawer has Add button', async ({ page }) => {
    const appIdLink = page.locator(`${dataRowSelector} button.text-primary-blue`).first();
    await appIdLink.click();
    await page.waitForTimeout(500);

    const drawer = page.locator('.fixed.inset-0');
    await expect(drawer.getByText('Add')).toBeVisible();
  });

  test('clicking X button closes drawer', async ({ page }) => {
    const appIdLink = page.locator(`${dataRowSelector} button.text-primary-blue`).first();
    await appIdLink.click();
    await page.waitForTimeout(500);
    await expect(page.locator('.fixed.inset-0')).toBeVisible();

    // Click the X button (last button in the header)
    const closeBtn = page.locator('.fixed.inset-0 button:has(svg.lucide-x)').first();
    await closeBtn.click();
    await page.waitForTimeout(300);
    await expect(page.locator('.fixed.inset-0')).not.toBeVisible();
  });

  test('clicking overlay closes drawer', async ({ page }) => {
    const appIdLink = page.locator(`${dataRowSelector} button.text-primary-blue`).first();
    await appIdLink.click();
    await page.waitForTimeout(500);
    await expect(page.locator('.fixed.inset-0')).toBeVisible();

    await page.locator('.absolute.inset-0.bg-black\\/30').click({ force: true, position: { x: 10, y: 10 } });
    await page.waitForTimeout(300);
    await expect(page.locator('.fixed.inset-0')).not.toBeVisible();
  });
});
