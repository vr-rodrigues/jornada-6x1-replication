
SELECT tamanho_estabelecimento, vinculo_ativo_3112,
quantidade_horas_contratadas, COUNT(*) n_vinculos
FROM `basedosdados.br_me_rais.microdados_vinculos`
WHERE ano=2022
GROUP BY tamanho_estabelecimento,vinculo_ativo_3112,quantidade_horas_contratadas
ORDER BY tamanho_estabelecimento,vinculo_ativo_3112,quantidade_horas_contratadas
