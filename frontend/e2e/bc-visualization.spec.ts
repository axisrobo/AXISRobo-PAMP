import { test, expect } from '@playwright/test';

test.describe('Business Capability Analysis (/app-management/bc-visualization)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/app-management/bc-visualization');
    // Wait for data to load — the info badge with counts appears once loaded
    await page.locator('.text-xs.text-text-secondary').filter({ hasText: /\d+ capabilities/ }).waitFor({ timeout: 15_000 });
  });

  /* ─── Page Load ─── */

  test('page title and heading render', async ({ page }) => {
    await expect(page.locator('h1')).toHaveText('Business Capability Analysis');
  });

  test('info badge shows summary stats', async ({ page }) => {
    // Format: "X capabilities · Y applications · Z mappings" in the info badge
    const badge = page.locator('.text-xs.text-text-secondary').filter({ hasText: /capabilities/ });
    await expect(badge).toBeVisible();
    const text = await badge.textContent();
    expect(text).toMatch(/\d+ capabilities/);
    expect(text).toMatch(/\d+ applications/);
    expect(text).toMatch(/\d+ mappings/);
  });

  test('three tabs are visible', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Capabilities' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Applications' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Capability Mindmap' })).toBeVisible();
  });

  test('default active tab is Capabilities', async ({ page }) => {
    const capTab = page.getByRole('button', { name: 'Capabilities' });
    await expect(capTab).toHaveClass(/text-primary-blue/);
  });

  /* ─── Capabilities Tab ─── */

  test('capabilities tab shows KPI cards', async ({ page }) => {
    await expect(page.getByText('Total Capabilities (L3)')).toBeVisible();
    await expect(page.getByText('Covered')).toBeVisible();
    await expect(page.getByText('Coverage Rate')).toBeVisible();
    await expect(page.getByText('Unique Applications')).toBeVisible();
  });

  test('capabilities tab shows legend section', async ({ page }) => {
    await expect(page.getByText('Portfolio', { exact: true })).toBeVisible();
    await expect(page.getByText('Invest')).toBeVisible();
    await expect(page.getByText('Migrate')).toBeVisible();
    await expect(page.getByText('N/A')).toBeVisible();
  });

  test('domain filter dropdown defaults to All Domains', async ({ page }) => {
    await expect(page.getByText('All Domains')).toBeVisible();
  });

  test('capability cards are rendered', async ({ page }) => {
    // There should be at least one domain group and capability card
    const capCards = page.locator('.rounded-xl.border');
    const count = await capCards.count();
    expect(count).toBeGreaterThan(0);
  });

  test('count text shows capabilities across domains', async ({ page }) => {
    await expect(page.getByText(/\d+ capabilities across \d+ domains/)).toBeVisible();
  });

  /* ─── Applications Tab ─── */

  test('clicking Applications tab switches view', async ({ page }) => {
    await page.getByRole('button', { name: 'Applications' }).click();
    await page.waitForTimeout(300);

    const appTab = page.getByRole('button', { name: 'Applications' });
    await expect(appTab).toHaveClass(/text-primary-blue/);
  });

  test('applications tab has search input', async ({ page }) => {
    await page.getByRole('button', { name: 'Applications' }).click();
    await page.waitForTimeout(300);

    await expect(page.getByPlaceholder('Search applications...')).toBeVisible();
  });

  test('applications tab has status filter', async ({ page }) => {
    await page.getByRole('button', { name: 'Applications' }).click();
    await page.waitForTimeout(300);

    await expect(page.getByText('All Statuses')).toBeVisible();
  });

  test('applications tab shows app cards', async ({ page }) => {
    await page.getByRole('button', { name: 'Applications' }).click();
    await page.waitForTimeout(300);

    // App cards have h3 headings
    const appCards = page.locator('h3.text-sm.font-semibold');
    const count = await appCards.count();
    expect(count).toBeGreaterThan(0);
  });

  test('applications tab shows count text', async ({ page }) => {
    await page.getByRole('button', { name: 'Applications' }).click();
    await page.waitForTimeout(300);

    await expect(page.locator('.text-xs.text-gray-500.whitespace-nowrap')).toHaveText(/\d+ of \d+/);
  });

  /* ─── Capability Mindmap Tab ─── */

  test('clicking Mindmap tab switches view', async ({ page }) => {
    await page.getByRole('button', { name: 'Capability Mindmap' }).click();
    await page.waitForTimeout(500);

    const mindmapTab = page.getByRole('button', { name: 'Capability Mindmap' });
    await expect(mindmapTab).toHaveClass(/text-primary-blue/);
  });

  test('mindmap has layout toggle buttons', async ({ page }) => {
    await page.getByRole('button', { name: 'Capability Mindmap' }).click();
    await page.waitForTimeout(500);

    await expect(page.getByRole('button', { name: /Radial/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Tree/ })).toBeVisible();
  });

  test('mindmap has zoom controls', async ({ page }) => {
    await page.getByRole('button', { name: 'Capability Mindmap' }).click();
    await page.waitForTimeout(500);

    // Zoom percentage display
    await expect(page.getByText(/\d+%/)).toBeVisible();
  });

  test('mindmap renders SVG canvas', async ({ page }) => {
    await page.getByRole('button', { name: 'Capability Mindmap' }).click();
    await page.waitForTimeout(500);

    const svg = page.locator('svg');
    await expect(svg.first()).toBeVisible();
  });

  test('mindmap has HUB center node', async ({ page }) => {
    await page.getByRole('button', { name: 'Capability Mindmap' }).click();
    await page.waitForTimeout(500);

    await expect(page.locator('svg text').filter({ hasText: 'HUB' })).toBeVisible();
  });
});
