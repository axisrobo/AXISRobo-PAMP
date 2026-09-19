#!/usr/bin/env node
// Generate idempotent upsert SQL for pamp.project_app from an application
// mapping JSON export.
//
// Usage:
//   node scripts/data/extract-apps.js <default-data.json> > scripts/data/upsert-apps.sql
//
// The input is expected to be an array of rows with fields such as appId,
// appName, appOwnership, appSolutionOwner, appDtOwner, portfolioMgt,
// appSolutionType, appClassification, appStatus, and bizFunction.

const fs = require('fs');

const inputPath = process.argv[2];
if (!inputPath) {
  console.error('usage: node scripts/data/extract-apps.js <default-data.json>');
  process.exit(1);
}

const data = JSON.parse(fs.readFileSync(inputPath, 'utf8'));

const appMap = {};
for (const row of data) {
  if (!appMap[row.appId]) {
    appMap[row.appId] = {
      appId: row.appId,
      appName: row.appName || '',
      appOwnership: row.appOwnership || '',
      appSolutionOwner: row.appSolutionOwner || '',
      appDtOwner: row.appDtOwner || '',
      portfolioMgt: row.portfolioMgt || '',
      appSolutionType: row.appSolutionType || '',
      appClassification: row.appClassification || '',
      appStatus: row.appStatus || '',
      bizFunction: row.bizFunction || '',
    };
  }
}

const apps = Object.values(appMap);
console.log(`-- Total unique apps: ${apps.length}`);

const esc = (s) => (s || '').replace(/'/g, "''");

console.log('-- Ensure a unique constraint on app_id for the upsert.');
console.log('CREATE UNIQUE INDEX IF NOT EXISTS idx_project_app_app_id ON pamp.project_app (app_id);');
console.log('');

for (const a of apps) {
  console.log(`INSERT INTO pamp.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), '${esc(a.appId)}', '${esc(a.appName)}', '${esc(a.appDtOwner)}', '${esc(a.appStatus)}', '${esc(a.bizFunction)}', '${esc(a.appOwnership)}', '${esc(a.appSolutionOwner)}', '${esc(a.portfolioMgt)}', '${esc(a.appSolutionType)}', '${esc(a.appClassification)}', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM pamp.project_app WHERE app_id = '${esc(a.appId)}');`);
  console.log(`UPDATE pamp.project_app SET app_name='${esc(a.appName)}', app_it_owner=COALESCE(NULLIF(app_it_owner,''), '${esc(a.appDtOwner)}'), current_state=COALESCE(NULLIF(current_state,''), '${esc(a.appStatus)}'), business_function='${esc(a.bizFunction)}', app_ownership='${esc(a.appOwnership)}', app_solution_owner='${esc(a.appSolutionOwner)}', portfolio_mgt='${esc(a.portfolioMgt)}', app_solution_type='${esc(a.appSolutionType)}', app_classification='${esc(a.appClassification)}', update_by='system', update_at=NOW() WHERE app_id='${esc(a.appId)}';`);
  console.log('');
}
