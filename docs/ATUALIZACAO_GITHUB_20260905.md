# Atualização pública de 5 de setembro de 2026

Esta publicação incorpora as correções científicas e empíricas já executadas localmente, e o manuscrito revisado, ao repositório que estava no commit 5559433. O estado local de trabalho foi preservado; a publicação foi preparada e verificada em outra cópia.

## Conteúdo

- Núcleo comum, escolha formal–informal contínua, calibração/ponte horária, contabilidade, GHH/CE e decomposição corrigidos.
- PNAD 2024T4 e RAIS 2022 verificadas, com fontes, pesos, universos e hipóteses documentados.
- Execução auditada fixada, comparativos, sensibilidades e testes.
- Manuscrito atual em `manuscript/`, com narrativa recuperada, figuras atualizadas no desenho original e Figura 4 em painéis A/B.
- Folha de rosto com Victor Rangel e Fernando Barros Jr; ORCID de Fernando 0000-0002-9073-7684. Declaração de IA sem a frase que atribuía etapas específicas a Victor.
- Original completo arquivado em ZIP com manifesto de hashes. Manuscritos históricos mantidos em `paper/` e identificados.

## Portabilidade e verificação

`reproduce.py` fornece o original arquivado ao executor existente, sem mudar os arquivos científicos cujo hash está fixado. Quatro scripts do manuscrito reconhecem a estrutura de diretórios da publicação. `.gitattributes` evita conversão de finais de linha, pois os manifestos verificam os bytes dos códigos. O modelo não foi alterado para reproduzir números antigos.

A verificação final está em `docs/VERIFICACAO_PUBLICACAO.json`. A reprodução econômica usa os agregados empíricos verificados já incluídos; o reprocessamento opcional dos microdados brutos é um comando separado e explícito. O ZIP PNAD de cerca de 210 MB não é versionado no Git; seu download oficial está documentado e seu arquivo local foi preservado.

A revisão editorial anterior da revista permanece registrada em `manuscript/CONFORMIDADE_REVISTA.md`; seus hashes e caminhos antigos identificam aquela etapa. Os manifestos BUILD_MANIFEST e ASSET_MANIFEST do manuscrito, e a verificação desta publicação, documentam o estado atual.
