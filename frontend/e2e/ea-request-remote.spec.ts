import fs from 'fs';
import path from 'path';

import { expect, test, type Page } from '@playwright/test';

const createRoute = '/ea-review/request/create';
const confluenceUrl = process.env.EA_CONFLUENCE_URL || 'https://confluence.example.com';
const featureDir = path.resolve(process.cwd(), '../test-data/uat/features/ea-request');
const sampleDataDir = path.resolve(process.cwd(), '../test-data/uat/sample-data/ea-request');
const assetDir = path.resolve(process.cwd(), '../test-data/uat/asset');
const sampleJsonPath = path.join(sampleDataDir, 'sample.json');
const appDiagram = path.join(assetDir, 'app-diagram', 'App_archietcture_tempate.png');
const techDiagram = path.join(assetDir, 'tech-diagram', 'EA_TAT_01.drawio.png');

type SampleData = {
  'Project ID': string;
  'Project Name'?: string;
  'Review Scope'?: string;
  'Request Description'?: string;
};

function loadSampleData(): SampleData {
  const raw = fs.readFileSync(sampleJsonPath, 'utf8');
  const normalized = raw.replace(/[“”]/g, '"').replace(/[‘’]/g, "'");
  return JSON.parse(normalized) as SampleData;
}

const sampleData = loadSampleData();
const projectId = process.env.EA_PROJECT_ID || sampleData['Project ID'];
const reviewScope = sampleData['Review Scope'] || 'All';
const requestDescription = sampleData['Request Description'] || '';

async function ensureCreatePage(page: Page) {
  if (!page.url().includes(createRoute)) {
    await page.goto(createRoute, { waitUntil: 'domcontentloaded' });
  }

  await expect(page.getByText('Create A Request')).toBeVisible({ timeout: 60_000 });
  await expect(page.getByText('01. Create an EA Review request for a project')).toBeVisible({ timeout: 60_000 });
}

async function waitForManualLogin(page: Page) {
  console.log('Manual login required. Complete Keycloak login in the opened browser window.');

  const createBanner = page.getByText('Create A Request');
  const homeCreateButton = page.getByRole('link', { name: 'Create A Request' }).or(page.getByRole('button', { name: 'Create A Request' }));

  await expect(createBanner.or(homeCreateButton)).toBeVisible({ timeout: 5 * 60 * 1000 });

  if (!page.url().includes(createRoute) && (await homeCreateButton.first().isVisible().catch(() => false))) {
    await homeCreateButton.first().click();
  }
}

async function selectProject(page: Page) {
  const projectField = page.locator('.ant-card').filter({
    has: page.getByRole('heading', { name: 'Select a MSPO project or create project' }),
  }).first();
  const projectCombobox = projectField.getByRole('combobox').first();

  await expect(projectCombobox).toBeVisible({ timeout: 30_000 });
  await projectCombobox.click();

  const matchingOption = page
    .getByRole('option')
    .filter({ hasText: projectId })
    .first();

  await expect(matchingOption).toBeVisible({ timeout: 20_000 });
  const optionText = (await matchingOption.textContent())?.trim() || '<unknown project>';
  await matchingOption.click();
  console.log(`Selected project: ${optionText}`);
}

async function fillStepOneDetails(page: Page) {
  if (reviewScope === 'Part of Project') {
    await page.getByRole('radio', { name: 'Part of Project' }).check();
    await page.getByPlaceholder('All contents of the project or WS Name or Phase Name').fill('UAT Phase 1');
  } else {
    await page.getByRole('radio', { name: 'All' }).check();
  }

  if (requestDescription) {
    const descriptionCard = page.locator('.ant-card').filter({
      has: page.getByRole('heading', { name: 'Describe review scope' }),
    }).first();
    await descriptionCard.locator('textarea').fill(requestDescription);
  }
}

async function uploadDiagram(page: Page, sectionTitle: string, filePath: string, expectedFileText: string) {
  const section = page.locator('.ant-card').filter({
    has: page.getByRole('heading', { name: sectionTitle }),
  }).first();

  await expect(section).toBeVisible({ timeout: 30_000 });
  await section.locator('input[type="file"]').setInputFiles(filePath);
  await expect(section.getByText(expectedFileText, { exact: false })).toBeVisible({ timeout: 60_000 });
}

async function captureFailureArtifacts(page: Page, reason: string) {
  const safeReason = reason.replace(/[^a-z0-9-_]+/gi, '-').toLowerCase();
  const artifactDir = path.resolve(process.cwd(), 'test-results', 'ea-request-remote');
  fs.mkdirSync(artifactDir, { recursive: true });

  const screenshotPath = path.join(artifactDir, `${safeReason}.png`);
  const domPath = path.join(artifactDir, `${safeReason}.html`);

  await page.screenshot({ path: screenshotPath, fullPage: true });
  fs.writeFileSync(domPath, await page.content(), 'utf8');

  console.log(`Captured screenshot: ${screenshotPath}`);
  console.log(`Captured DOM: ${domPath}`);

  const alertTexts = await page.locator('[role="alert"], .ant-alert, .ant-message-notice, .ant-modal').allTextContents();
  console.log(`Visible alert/modal text: ${alertTexts.join(' | ')}`);
}

test('remote UAT creates an EA request with provided diagrams', async ({ page }) => {
  test.setTimeout(10 * 60 * 1000);

  console.log(`Loaded Project ID from sample.json: ${projectId}`);
  console.log(`Using app diagram: ${appDiagram}`);
  console.log(`Using tech diagram: ${techDiagram}`);

  await page.goto(createRoute, { waitUntil: 'domcontentloaded' });

  await ensureCreatePage(page);

  const selectFromMspoButton = page.getByRole('button', { name: 'Select from MSPO' });
  if (await selectFromMspoButton.isVisible()) {
    await selectFromMspoButton.click();
  }

  await selectProject(page);
  await fillStepOneDetails(page);

  await page.getByRole('button', { name: 'Save & Next Step' }).click();
  await expect(page.getByText('02. Provide Architecture Design')).toBeVisible({ timeout: 30_000 });

  await page.getByRole('radio', { name: 'I am from DT/IT' }).check();

  const organizationCard = page.locator('.ant-card').filter({
    has: page.getByText("What's your organization?"),
  }).first();
  await organizationCard.getByRole('textbox').fill(confluenceUrl);

  await uploadDiagram(page, 'Application Architecture Diagram', appDiagram, 'App_archietcture_tempate');
  await uploadDiagram(page, 'Technical Architecture Diagram', techDiagram, 'EA_TAT_01');

  const submitButton = page.getByRole('button', { name: 'Confirm to Submit & Next Step' });
  await expect(submitButton).toBeEnabled({ timeout: 60_000 });
  await submitButton.click();

  const submitModal = page.getByRole('dialog').filter({ has: page.getByText('Confirm to Submit', { exact: true }) }).first();
  await expect(submitModal).toBeVisible({ timeout: 15_000 });
  await submitModal.getByRole('button', { name: 'Yes' }).click();

  const queueMessage = 'This request is in queue, please wait for the EA team to process it.';
  try {
    await expect(page.getByText(queueMessage)).toBeVisible({ timeout: 60_000 });
  } catch (error) {
    await captureFailureArtifacts(page, 'missing-in-queue-message');
    throw error;
  }

  await expect(page.getByText('EA Review Process')).toBeVisible({ timeout: 60_000 });
  await expect(page.locator('input[value="Submitted"]')).toBeVisible({ timeout: 60_000 });

  const finalUrl = page.url();
  const requestReference = new URL(finalUrl).searchParams.get('id') || finalUrl;
  console.log(`EA request creation completed. Final URL: ${finalUrl}`);
  console.log(`Feature source: ${path.join(featureDir, 'ea-request-creation.feature')}`);
  console.log(`Recorded request reference: ${requestReference}`);
  console.log(`Recorded request reference at: ${new Date().toISOString()}`);
});