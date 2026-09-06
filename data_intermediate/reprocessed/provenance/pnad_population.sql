
SELECT ano,trimestre,COUNT(*) sample_n,
COUNTIF(V2009>=14) working_age_sample_n,
SUM(IF(V1028>0,V1028,0)) population_weighted,
SUM(IF(V2009>=14 AND V1028>0,V1028,0)) working_age_weighted,
COUNTIF(V1028 IS NULL OR V1028<=0) invalid_weight_n
FROM `basedosdados.br_ibge_pnadc.microdados`
WHERE ano=2024 AND trimestre=4 GROUP BY ano,trimestre
