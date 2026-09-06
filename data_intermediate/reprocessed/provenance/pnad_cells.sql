
WITH source AS (
 SELECT V1028 w, V2009 age, SAFE_CAST(VD4002 AS INT64) occupied,
 SAFE_CAST(VD4009 AS INT64) position, SAFE_CAST(V4019 AS INT64) cnpj,
 SAFE_CAST(V4017 AS INT64) partner, SAFE_CAST(V4018 AS INT64) size_category,
 V40183 size_exact_11_50, V4039 habitual, V4039C actual,
 VD4031 habitual_all_jobs, VD4035 actual_all_jobs, VD4016 income_monthly,
 SAFE_CAST(SUBSTR(LPAD(V4013,5,'0'),1,2) AS INT64) cnae2
 FROM `basedosdados.br_ibge_pnadc.microdados`
 WHERE ano=2024 AND trimestre=4
), classified AS (
 SELECT *, CASE WHEN cnae2 BETWEEN 1 AND 3 THEN 'agriculture'
 WHEN cnae2 BETWEEN 5 AND 43 THEN 'industry'
 WHEN cnae2 BETWEEN 45 AND 99 THEN 'services' ELSE 'unclassified' END sector,
 CASE WHEN position IN (2,4,10) THEN 1
 WHEN position IN (1,3,5,6,7) THEN 0
 WHEN position IN (8,9) AND cnpj=1 THEN 0
 WHEN position IN (8,9) AND cnpj=2 THEN 1 ELSE NULL END informal,
 CASE WHEN size_category IN (1,2) OR (size_category=3 AND size_exact_11_50<50) THEN 'le49'
 WHEN size_category=3 AND size_exact_11_50=50 THEN 'eq50'
 WHEN size_category=4 THEN 'ge51' ELSE 'unknown' END size_group
 FROM source WHERE age>=14 AND occupied=1
)
SELECT sector, position, cnpj, partner, informal, size_group, habitual,
 COUNT(*) sample_n, COUNTIF(w IS NULL OR w<=0) invalid_weight_n,
 SUM(IF(w>0,w,0)) occupied_weighted,
 COUNTIF(actual IS NULL) missing_actual_n,
 COUNTIF(habitual IS NULL) missing_habitual_n,
 COUNTIF(income_monthly IS NULL) missing_income_n,
 SUM(IF(w>0 AND actual BETWEEN 0 AND 120,w,0)) actual_weight,
 SUM(IF(w>0 AND actual BETWEEN 0 AND 120,w*actual,0)) actual_hours_sum,
 SUM(IF(w>0 AND habitual_all_jobs BETWEEN 1 AND 120,w,0)) habitual_all_weight,
 SUM(IF(w>0 AND habitual_all_jobs BETWEEN 1 AND 120,w*habitual_all_jobs,0)) habitual_all_sum,
 SUM(IF(w>0 AND actual_all_jobs BETWEEN 0 AND 120,w,0)) actual_all_weight,
 SUM(IF(w>0 AND actual_all_jobs BETWEEN 0 AND 120,w*actual_all_jobs,0)) actual_all_sum,
 SUM(IF(w>0 AND habitual BETWEEN 1 AND 120 AND income_monthly>0,w,0)) paid_weight,
 SUM(IF(w>0 AND habitual BETWEEN 1 AND 120 AND income_monthly>0,w*income_monthly,0)) paid_income_monthly,
 SUM(IF(w>0 AND habitual BETWEEN 1 AND 120 AND income_monthly>0,w*habitual,0)) paid_hours,
 SUM(IF(w>0 AND habitual BETWEEN 1 AND 120 AND income_monthly>0,w*income_monthly/(habitual*52.0/12.0),0)) paid_individual_hourly_sum
FROM classified GROUP BY sector,position,cnpj,partner,informal,size_group,habitual
ORDER BY sector,position,cnpj,partner,informal,size_group,habitual
