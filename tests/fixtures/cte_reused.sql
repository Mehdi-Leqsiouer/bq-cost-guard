WITH base AS (SELECT id FROM `proj.ds.users`) SELECT a.id FROM base AS a JOIN base AS b ON a.id = b.id
