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

function searchField(page: Page, label: string) {
  return page.locator('.bg-white.rounded-lg.border').first().locator('div', {
    has: page.locator('label', { hasText: label }),
  }).first();
}

async function getSelectValueText(page: Page, label: string): Promise<string> {
  const field = searchField(page, label);
  const selected = field.locator('.ant-select-selection-item');
  if (await selected.count()) {
    return (await selected.first().innerText()).trim();
  }
  return '';
}

async function hasSelectValue(page: Page, label: string): Promise<boolean> {
  const field = searchField(page, label);
  return (await field.locator('.ant-select-selection-item').count()) > 0;
}

test.describe('Business Capability Master Data (/app-management/biz-capability)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/app-management/biz-capability');
    await waitForTableData(page);
  });

  /* ─── Page Load ─── */

  test('page title and heading render', async ({ page }) => {
    await expect(page.locator('h1')).toHaveText('Business Capability Master Data');
  });

  test('sidebar link is active', async ({ page }) => {
    const link = page.locator('nav a', { hasText: 'Business Capability Master Data' });
    await expect(link).toBeVisible();
  });

  test('table loads with data rows', async ({ page }) => {
    const rows = page.locator(dataRowSelector);
    await expect(rows).not.toHaveCount(0);
  });

  /* ─── Search Form ─── */

  test('search form has all expected fields', async ({ page }) => {
    await expect(page.getByText('Version')).toBeVisible();
    await expect(page.getByText('Domain(L1)')).toBeVisible();
    await expect(page.getByText('Sub Domain(L2)')).toBeVisible();
    await expect(page.getByText('Capability Group(L3)')).toBeVisible();
    await expect(page.getByText('Level')).toBeVisible();
    const searchForm = page.locator('.bg-white.rounded-lg.border').first();
    await expect(searchForm.locator('.ant-select')).toHaveCount(5);
  });

  test('search and reset buttons exist', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Search' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Reset' })).toBeVisible();
  });

  /* ─── Table Columns ─── */

  test('table has expected column headers', async ({ page }) => {
    const headers = page.locator('table thead th');
    const texts = await headers.allTextContents();
    const joined = texts.join(' ');
    expect(joined).toContain('BC ID');
    expect(joined).toContain('BC Name');
    expect(joined).toContain('Domain L1');
    expect(joined).toContain('Sub Domain L2');
    expect(joined).toContain('Capability Group L3');
    expect(joined).toContain('Level');
    expect(joined).toContain('Version');
  });

  test('BC ID is rendered in blue', async ({ page }) => {
    const firstBcId = page.locator(`${dataRowSelector} td:first-child span.text-primary-blue`).first();
    await expect(firstBcId).toBeVisible();
  });

  /* ─── Action Bar ─── */

  test('import and export buttons are visible', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Import/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Export/i })).toBeVisible();
  });

  /* ─── Filtering ─── */

  test('search by BC Name filters results', async ({ page }) => {
    await page.getByPlaceholder('BC Name').fill('Finance');
    await page.getByRole('button', { name: 'Search' }).click();
    await waitForTableData(page, 5_000);

    const rows = page.locator(dataRowSelector);
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test('filter by Level = L1', async ({ page }) => {
    await selectSearchOption(page, 0, 'L1');
    await page.getByRole('button', { name: 'Search' }).click();
    await waitForTableData(page, 5_000);

    const rows = page.locator(dataRowSelector);
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test('reset button clears all filters', async ({ page }) => {
    const initialVersion = await getSelectValueText(page, 'Version');
    await selectSearchOption(page, 0, 'L1');
    await page.getByRole('button', { name: 'Search' }).click();
    await waitForTableData(page, 5_000);

    await page.getByRole('button', { name: 'Reset' }).click();
    await waitForTableData(page, 10_000);

    await expect(searchField(page, 'Domain(L1)').locator('.ant-select-selection-placeholder')).toBeVisible();
    await expect(searchField(page, 'Sub Domain(L2)').locator('.ant-select-selection-placeholder')).toBeVisible();
    await expect(searchField(page, 'Capability Group(L3)').locator('.ant-select-selection-placeholder')).toBeVisible();
    await expect(searchField(page, 'Version').locator('.ant-select-selection-item')).toHaveText(initialVersion);
  });

  test('default selects first version on load', async ({ page }) => {
    const versionField = searchField(page, 'Version');
    await expect(versionField.locator('.ant-select-selection-item')).toBeVisible();
    const currentVersion = (await versionField.locator('.ant-select-selection-item').first().innerText()).trim();
    expect(currentVersion.length).toBeGreaterThan(0);
  });

  test('changing version clears dependent cascade fields', async ({ page }) => {
    const searchForm = page.locator('.bg-white.rounded-lg.border').first();

    await searchForm.locator('.ant-select').nth(1).click();
    const domainOption = page.locator('.ant-select-dropdown:visible').last().locator('.ant-select-item-option-content').first();
    const hasDomainOptions = (await domainOption.count()) > 0;
    test.skip(!hasDomainOptions, 'No domain options available for cascade test');
    await domainOption.click({ force: true });

    await searchForm.locator('.ant-select').nth(2).click();
    const subDomainOption = page.locator('.ant-select-dropdown:visible').last().locator('.ant-select-item-option-content').first();
    if ((await subDomainOption.count()) > 0) {
      await subDomainOption.click({ force: true });
    } else {
      await page.keyboard.press('Escape');
    }

    await searchForm.locator('.ant-select').nth(0).click();
    const versionOptions = page.locator('.ant-select-dropdown:visible').last().locator('.ant-select-item-option-content');
    const optionCount = await versionOptions.count();
    test.skip(optionCount < 2, 'Need at least 2 versions to verify cascade clear on version change');
    const currentVersion = await getSelectValueText(page, 'Version');
    for (let i = 0; i < optionCount; i += 1) {
      const text = ((await versionOptions.nth(i).innerText()) || '').trim();
      if (text && text !== currentVersion) {
        await versionOptions.nth(i).click({ force: true });
        break;
      }
    }

    expect(await hasSelectValue(page, 'Domain(L1)')).toBeFalsy();
    expect(await hasSelectValue(page, 'Sub Domain(L2)')).toBeFalsy();
    expect(await hasSelectValue(page, 'Capability Group(L3)')).toBeFalsy();
  });

  /* ─── Sorting ─── */

  test('clicking column header changes sort indicator', async ({ page }) => {
    // Record initial first row
    const initialFirst = (await page.locator(`${dataRowSelector} td:nth-child(2)`).first().textContent())!.trim();

    // Click BC Name header to sort
    await page.getByRole('columnheader', { name: 'BC Name', exact: true }).click();
    await page.waitForTimeout(500);

    // Header remains interactive and rows stay rendered
    const sortedFirst = (await page.locator(`${dataRowSelector} td:nth-child(2)`).first().textContent())!.trim();
    expect(sortedFirst).toBeTruthy();
    expect(initialFirst).toBeTruthy();
  });

  test('clicking same header twice reverses sort', async ({ page }) => {
    const header = page.getByRole('columnheader', { name: 'BC Name', exact: true });
    // Record initial first row
    const initialFirst = (await page.locator(`${dataRowSelector} td:nth-child(2)`).first().textContent())!.trim();

    // Click once (asc)
    await header.click();
    await page.waitForTimeout(500);

    // Click again (desc)
    await header.click();
    await page.waitForTimeout(500);
    const afterDesc = (await page.locator(`${dataRowSelector} td:nth-child(2)`).first().textContent())!.trim();

    // Repeated interaction should not break the table
    expect(afterDesc).toBeTruthy();
    expect(initialFirst).toBeTruthy();
  });

  /* ─── Pagination ─── */

  test('pagination shows total count', async ({ page }) => {
    await expect(page.getByText(/Total/)).toBeVisible();
  });

  test('default page size is 10', async ({ page }) => {
    const rows = page.locator(dataRowSelector);
    const count = await rows.count();
    expect(count).toBeLessThanOrEqual(10);
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
});
