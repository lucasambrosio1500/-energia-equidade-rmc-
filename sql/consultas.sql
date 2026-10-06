-- Execute no SQLite, DB Browser for SQLite ou Python.
-- Os indicadores anuais são reconstruções, não certificação regulatória.

-- 1. Séries regionais que não permitem reconstrução anual completa.
SELECT set_id, set_name, agent, year, months_complete
FROM regional_sets WHERE complete = 0 ORDER BY year, set_name;

-- 2. Panorama municipal: os indicadores pertencem aos conjuntos associados.
SELECT municipality, year, income_mean, low_income_pct,
       n_sets, n_shared, set_coverage_pct, dec_median, dec_min, dec_max
FROM municipal_context WHERE year = 2024 ORDER BY low_income_pct DESC;

-- 3. Triagem técnica por conjunto; verificar arredondamento e dados de origem.
SELECT set_id, set_name, dec_h, dec_limit, dec_limit_ratio
FROM regional_sets WHERE year = 2024 AND complete = 1
  AND dec_limit_ratio > 1 ORDER BY dec_limit_ratio DESC;

-- 4. A mesma área elétrica pode atender cidades fora da RMC.
SELECT set_id, COUNT(DISTINCT municipality_id) AS municipios_associados
FROM crosswalk GROUP BY set_id HAVING COUNT(DISTINCT municipality_id) > 1;

-- 5. Evolução em coorte fixa de conjuntos (evita mudança de composição).
SELECT * FROM balanced_benchmarks ORDER BY scope, year;
