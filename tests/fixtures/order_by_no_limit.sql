WITH ranked AS (SELECT id FROM `proj.ds.users` ORDER BY id)
SELECT id FROM ranked
