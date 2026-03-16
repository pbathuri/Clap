-- Convenience views (extend as needed)
CREATE VIEW IF NOT EXISTS v_occupations_with_industry AS
SELECT o.*, i.title AS industry_title, i.taxonomy_system AS industry_taxonomy, iom.mapping_basis
FROM occupations o
LEFT JOIN industry_occupation_map iom ON o.occupation_id = iom.occupation_id
LEFT JOIN industries i ON iom.industry_id = i.industry_id;
