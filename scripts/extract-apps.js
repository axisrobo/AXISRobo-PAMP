const data = require('/Users/ruodongyang/Workplace/Business-Capability-Application-Mapping/src/data/default-data.json');

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
console.log('Total unique apps:', apps.length);

// Generate SQL: UPSERT (INSERT ... ON CONFLICT UPDATE)
const esc = (s) => (s || '').replace(/'/g, "''");

const sqls = apps.map(a => {
  return `INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
VALUES (gen_random_uuid(), '${esc(a.appId)}', '${esc(a.appName)}', '${esc(a.appDtOwner)}', '${esc(a.appStatus)}', '${esc(a.bizFunction)}', '${esc(a.appOwnership)}', '${esc(a.appSolutionOwner)}', '${esc(a.portfolioMgt)}', '${esc(a.appSolutionType)}', '${esc(a.appClassification)}', 'system', NOW())
ON CONFLICT (app_id) DO UPDATE SET
  app_name = EXCLUDED.app_name,
  app_it_owner = COALESCE(NULLIF(eam.project_app.app_it_owner, ''), EXCLUDED.app_it_owner),
  current_state = COALESCE(NULLIF(eam.project_app.current_state, ''), EXCLUDED.current_state),
  business_function = EXCLUDED.business_function,
  app_ownership = EXCLUDED.app_ownership,
  app_solution_owner = EXCLUDED.app_solution_owner,
  portfolio_mgt = EXCLUDED.portfolio_mgt,
  app_solution_type = EXCLUDED.app_solution_type,
  app_classification = EXCLUDED.app_classification,
  update_by = 'system',
  update_at = NOW();`;
});

// But wait, project_app primary key is 'id' not 'app_id'. Need a unique constraint on app_id first.
console.log('-- First ensure unique constraint on app_id');
console.log('CREATE UNIQUE INDEX IF NOT EXISTS idx_project_app_app_id ON eam.project_app (app_id);');
console.log('');

// Since ON CONFLICT needs a unique constraint, let's check if it exists.
// Alternative approach: use a CTE with upsert logic
for (const a of apps) {
  console.log(`INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), '${esc(a.appId)}', '${esc(a.appName)}', '${esc(a.appDtOwner)}', '${esc(a.appStatus)}', '${esc(a.bizFunction)}', '${esc(a.appOwnership)}', '${esc(a.appSolutionOwner)}', '${esc(a.portfolioMgt)}', '${esc(a.appSolutionType)}', '${esc(a.appClassification)}', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = '${esc(a.appId)}');`);
  console.log(`UPDATE eam.project_app SET app_name='${esc(a.appName)}', app_it_owner=COALESCE(NULLIF(app_it_owner,''), '${esc(a.appDtOwner)}'), current_state=COALESCE(NULLIF(current_state,''), '${esc(a.appStatus)}'), business_function='${esc(a.bizFunction)}', app_ownership='${esc(a.appOwnership)}', app_solution_owner='${esc(a.appSolutionOwner)}', portfolio_mgt='${esc(a.portfolioMgt)}', app_solution_type='${esc(a.appSolutionType)}', app_classification='${esc(a.appClassification)}', update_by='system', update_at=NOW() WHERE app_id='${esc(a.appId)}';`);
  console.log('');
}
