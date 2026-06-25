Total unique apps: 43
-- First ensure unique constraint on app_id
CREATE UNIQUE INDEX IF NOT EXISTS idx_project_app_app_id ON eam.project_app (app_id);

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A003573', 'MSPO-LPS', 'guohui1', 'Active', 'Sales', 'CIO/CDTO', 'zhangyue8', 'Invest', 'SaaS', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A003573');
UPDATE eam.project_app SET app_name='MSPO-LPS', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'guohui1'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='zhangyue8', portfolio_mgt='Invest', app_solution_type='SaaS', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A003573';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A004606', 'NexBill', 'ssundar', 'Planned', 'Sales', 'CIO/CDTO', 'zwang12', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A004606');
UPDATE eam.project_app SET app_name='NexBill', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'ssundar'), current_state=COALESCE(NULLIF(current_state,''), 'Planned'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='zwang12', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A004606';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A002873', 'BRIM', 'wangzx9', 'Active', 'Sales', 'CIO/CDTO', 'jiangyong1', 'Invest', 'Package+Customization', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A002873');
UPDATE eam.project_app SET app_name='BRIM', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'wangzx9'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='jiangyong1', portfolio_mgt='Invest', app_solution_type='Package+Customization', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A002873';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A000593', 'RR', 'xusheng1', 'Active', 'Sales', 'CIO/CDTO', 'ttao1', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A000593');
UPDATE eam.project_app SET app_name='RR', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'xusheng1'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='ttao1', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A000593';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A002860', 'ESOT', 'ssundar', 'Active', 'Sales', 'CIO/CDTO', 'zwang12', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A002860');
UPDATE eam.project_app SET app_name='ESOT', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'ssundar'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='zwang12', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A002860';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A002856', 'OLMS', 'hujun11', 'Active', 'Service', 'CIO/CDTO', 'zwang12', 'Invest', 'Package', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A002856');
UPDATE eam.project_app SET app_name='OLMS', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'hujun11'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Service', app_ownership='CIO/CDTO', app_solution_owner='zwang12', portfolio_mgt='Invest', app_solution_type='Package', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A002856';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A004029', 'AIESA', 'huangli11', 'Planned', 'Service', 'CIO/CDTO', 'liuchen7', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A004029');
UPDATE eam.project_app SET app_name='AIESA', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'huangli11'), current_state=COALESCE(NULLIF(current_state,''), 'Planned'), business_function='Service', app_ownership='CIO/CDTO', app_solution_owner='liuchen7', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A004029';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A000550', 'D365 Sales B2B', 'cpreddy', 'Active', 'Sales', 'CIO/CDTO', 'wsiong', 'Invest', 'SaaS', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A000550');
UPDATE eam.project_app SET app_name='D365 Sales B2B', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'cpreddy'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='wsiong', portfolio_mgt='Invest', app_solution_type='SaaS', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A000550';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A000699', 'LKMS', 'csharpe', 'Active', 'Sales', 'CIO/CDTO', 'sunning2', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A000699');
UPDATE eam.project_app SET app_name='LKMS', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'csharpe'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='sunning2', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A000699';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A002197', 'D365 Sales B2C', 'kingb', 'Active', 'Sales', 'CIO/CDTO', 'llam4', 'Invest', 'SaaS', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A002197');
UPDATE eam.project_app SET app_name='D365 Sales B2C', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'kingb'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='llam4', portfolio_mgt='Invest', app_solution_type='SaaS', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A002197';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A004156', 'LKMS-NA', 'csharpe', 'Active', 'Sales', 'CIO/CDTO', 'hwong22', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A004156');
UPDATE eam.project_app SET app_name='LKMS-NA', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'csharpe'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='hwong22', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A004156';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A000103', 'RDD', 'lterpack', 'Active', 'Sales', 'CIO/CDTO', 'hwong22', 'Tolerate', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A000103');
UPDATE eam.project_app SET app_name='RDD', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'lterpack'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='hwong22', portfolio_mgt='Tolerate', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A000103';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A003537', 'THE SPHERE', 'mlu2', 'Active', 'Sales', 'CIO/CDTO', 'jtey', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A003537');
UPDATE eam.project_app SET app_name='THE SPHERE', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'mlu2'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='jtey', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A003537';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A002851', 'RoW C360', 'jhinson', 'Active', 'Sales', 'CIO/CDTO', 'chang2', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A002851');
UPDATE eam.project_app SET app_name='RoW C360', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'jhinson'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='chang2', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A002851';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A002281', 'Flash', 'lcutlip', 'Active', 'Sales', 'CIO/CDTO', 'liudz4', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A002281');
UPDATE eam.project_app SET app_name='Flash', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'lcutlip'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='liudz4', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A002281';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A003453', 'LI eCommerce LA', 'lcutlip', 'Active', 'Sales', 'CIO/CDTO', 'liudz4', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A003453');
UPDATE eam.project_app SET app_name='LI eCommerce LA', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'lcutlip'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='liudz4', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A003453';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A002862', 'LI eCommerce AP', 'lcutlip', 'Active', 'Sales', 'CIO/CDTO', 'liudz4', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A002862');
UPDATE eam.project_app SET app_name='LI eCommerce AP', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'lcutlip'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='liudz4', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A002862';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A002861', 'LI eCommerce US/CA', 'lcutlip', 'Active', 'Sales', 'CIO/CDTO', 'liudz4', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A002861');
UPDATE eam.project_app SET app_name='LI eCommerce US/CA', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'lcutlip'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='liudz4', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A002861';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A002864', 'LI eCommerce B2B', 'lcutlip', 'Active', 'Sales', 'CIO/CDTO', 'liudz4', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A002864');
UPDATE eam.project_app SET app_name='LI eCommerce B2B', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'lcutlip'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='liudz4', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A002864';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A002863', 'LI eCommerce EMEA', 'lcutlip', 'Active', 'Sales', 'CIO/CDTO', 'liudz4', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A002863');
UPDATE eam.project_app SET app_name='LI eCommerce EMEA', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'lcutlip'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='liudz4', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A002863';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A000432', 'LI eCommerce', 'lcutlip', 'Active', 'Sales', 'CIO/CDTO', 'liudz4', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A000432');
UPDATE eam.project_app SET app_name='LI eCommerce', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'lcutlip'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='liudz4', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A000432';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A002943', 'APPXITESRS', 'ssundar', 'Active', 'Sales', 'CIO/CDTO', 'zwang12', 'Invest', 'SaaS', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A002943');
UPDATE eam.project_app SET app_name='APPXITESRS', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'ssundar'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='zwang12', portfolio_mgt='Invest', app_solution_type='SaaS', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A002943';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A003177', 'TCCA', 'zwang1', 'Active', 'Sales', 'CIO/CDTO', 'lxue', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A003177');
UPDATE eam.project_app SET app_name='TCCA', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'zwang1'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='lxue', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A003177';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A000509', 'NECPCSECC', '', 'Active', 'Sales', 'CIO/CDTO', 'dryuzaki', 'Tolerate', 'Package', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A000509');
UPDATE eam.project_app SET app_name='NECPCSECC', app_it_owner=COALESCE(NULLIF(app_it_owner,''), ''), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='dryuzaki', portfolio_mgt='Tolerate', app_solution_type='Package', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A000509';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A000202', 'LCC', 'liying3', 'Active', 'Sales', 'CIO/CDTO', 'hwong22', 'Tolerate', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A000202');
UPDATE eam.project_app SET app_name='LCC', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'liying3'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='hwong22', portfolio_mgt='Tolerate', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A000202';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A003356', 'OWB', 'wilsonyip', 'Active', 'Sales', 'CIO/CDTO', 'jtey', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A003356');
UPDATE eam.project_app SET app_name='OWB', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'wilsonyip'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='jtey', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A003356';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A000760', 'Neogrid EDI', 'wangyhx', 'Active', 'Sales', 'CIO/CDTO', 'silmaravendemiatti', 'Tolerate', 'SaaS', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A000760');
UPDATE eam.project_app SET app_name='Neogrid EDI', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'wangyhx'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='silmaravendemiatti', portfolio_mgt='Tolerate', app_solution_type='SaaS', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A000760';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A000374', 'SOC-PRC', 'zhoufeng', 'Active', 'Sales', 'CIO/CDTO', 'wangjing70', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A000374');
UPDATE eam.project_app SET app_name='SOC-PRC', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'zhoufeng'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='wangjing70', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A000374';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A000291', 'DCSC', 'jbarrett', 'Active', 'Sales', 'CIO/CDTO', 'sunning2', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A000291');
UPDATE eam.project_app SET app_name='DCSC', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'jbarrett'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='sunning2', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A000291';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A002671', 'OLSC', 'seith', 'Active', 'Sales', 'CIO/CDTO', 'sunning2', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A002671');
UPDATE eam.project_app SET app_name='OLSC', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'seith'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='sunning2', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A002671';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A000394', 'Example Platform (EXP)', 'cpreddy', 'Active', 'Sales', 'CIO/CDTO', 'lxue', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A000394');
UPDATE eam.project_app SET app_name='Example Platform (EXP)', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'cpreddy'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='lxue', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A000394';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A000292', 'LSC 2.0', 'cpreddy', 'Active', 'Sales', 'CIO/CDTO', 'pyu7', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A000292');
UPDATE eam.project_app SET app_name='LSC 2.0', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'cpreddy'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='pyu7', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A000292';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A000109', 'Smartfind', 'cpreddy', 'Active', 'Sales', 'CIO/CDTO', 'hwong22', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A000109');
UPDATE eam.project_app SET app_name='Smartfind', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'cpreddy'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='hwong22', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A000109';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A000555', 'DPC', 'seith', 'Active', 'Sales', 'CIO/CDTO', 'hwong22', 'Migrate', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A000555');
UPDATE eam.project_app SET app_name='DPC', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'seith'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='hwong22', portfolio_mgt='Migrate', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A000555';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A000407', 'PPC', 'cpreddy', 'Active', 'Sales', 'CIO/CDTO', 'hwong22', 'Migrate', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A000407');
UPDATE eam.project_app SET app_name='PPC', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'cpreddy'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='hwong22', portfolio_mgt='Migrate', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A000407';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A002201', 'LPC', 'cpreddy', 'Active', 'Sales', 'CIO/CDTO', 'hwong22', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A002201');
UPDATE eam.project_app SET app_name='LPC', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'cpreddy'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='hwong22', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A002201';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A000395', 'Lead Widget for Partner Portal', 'songjy5', 'Planned', 'Sales', 'CIO/CDTO', 'sunyy13', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A000395');
UPDATE eam.project_app SET app_name='Lead Widget for Partner Portal', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'songjy5'), current_state=COALESCE(NULLIF(current_state,''), 'Planned'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='sunyy13', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A000395';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A000491', 'CREMET', '', 'Active', 'Sales', 'CIO/CDTO', 'dryuzaki', 'Tolerate', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A000491');
UPDATE eam.project_app SET app_name='CREMET', app_it_owner=COALESCE(NULLIF(app_it_owner,''), ''), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='dryuzaki', portfolio_mgt='Tolerate', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A000491';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A003553', 'CDM-ROWMS', 'bturner1', 'Active', 'Sales', 'CIO/CDTO', 'jinxl4', 'Invest', 'SaaS', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A003553');
UPDATE eam.project_app SET app_name='CDM-ROWMS', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'bturner1'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='jinxl4', portfolio_mgt='Invest', app_solution_type='SaaS', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A003553';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A003554', 'CDM-ROWSVC', 'yushuang3', 'Active', 'Service', 'CIO/CDTO', 'jinxl4', 'Invest', 'SaaS', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A003554');
UPDATE eam.project_app SET app_name='CDM-ROWSVC', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'yushuang3'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Service', app_ownership='CIO/CDTO', app_solution_owner='jinxl4', portfolio_mgt='Invest', app_solution_type='SaaS', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A003554';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A004151', 'EIM-NA', 'badstein', 'Active', 'Sales', 'CIO/CDTO', 'yhao2', 'Invest', 'Self-Development', 'Business Application', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A004151');
UPDATE eam.project_app SET app_name='EIM-NA', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'badstein'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Sales', app_ownership='CIO/CDTO', app_solution_owner='yhao2', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Business Application', update_by='system', update_at=NOW() WHERE app_id='A004151';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A003559', 'AxisArch', 'na', 'Active', 'IT Management Tool', 'CIO/CDTO', 'zhanghy25', 'Invest', 'Self-Development', 'IT Management Tool', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A003559');
UPDATE eam.project_app SET app_name='AxisArch', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'na'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='IT Management Tool', app_ownership='CIO/CDTO', app_solution_owner='zhanghy25', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='IT Management Tool', update_by='system', update_at=NOW() WHERE app_id='A003559';

INSERT INTO eam.project_app (id, app_id, app_name, app_it_owner, current_state, business_function, app_ownership, app_solution_owner, portfolio_mgt, app_solution_type, app_classification, create_by, create_at)
SELECT gen_random_uuid(), 'A002540', 'TechDP', 'na', 'Active', 'Development', 'CIO/CDTO', 'zhanghy25', 'Invest', 'Self-Development', 'Technical Platform', 'system', NOW()
WHERE NOT EXISTS (SELECT 1 FROM eam.project_app WHERE app_id = 'A002540');
UPDATE eam.project_app SET app_name='TechDP', app_it_owner=COALESCE(NULLIF(app_it_owner,''), 'na'), current_state=COALESCE(NULLIF(current_state,''), 'Active'), business_function='Development', app_ownership='CIO/CDTO', app_solution_owner='zhanghy25', portfolio_mgt='Invest', app_solution_type='Self-Development', app_classification='Technical Platform', update_by='system', update_at=NOW() WHERE app_id='A002540';

