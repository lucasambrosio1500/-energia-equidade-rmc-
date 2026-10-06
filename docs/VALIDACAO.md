# Registro de validação — 06/10/2026

## Executado

- 16 testes unitários passaram: cálculo conhecido com consumidores constantes, ajuste com consumidores variáveis, ausência mensal, ausência de indicador, chave duplicada, período inválido, valor negativo/não finito, consumidor zero, interrupção zero, vírgula decimal, correlação constante, retirada de uma observação e compartilhamento nacional.
- As 10 aquisições do manifesto principal tiveram hashes conferidos contra os bytes locais. Catálogos e demais metadados possuem seus próprios arquivos de origem.
- Os códigos dos 20 municípios foram confrontados com o cadastro do IBGE; a malha contém os 20 municípios.
- O banco SQLite contém as 11 tabelas esperadas. Os 20 contextos municipais de 2024 têm todas as séries observadas completas.
- O PDF tem 8 páginas. Capa, mapas/legenda, tabela dos municípios e gráfico/tabela de sensibilidade foram inspecionados visualmente. Todas as páginas tiveram conteúdo textual extraído para verificação de paginação.
- O HTML foi executado em ambiente DOM (jsdom): 20 regiões no mapa, 20 pontos na dispersão, quatro anos, quatro métricas, seleção municipal, aviso de série incompleta e exportação CSV passaram sem erros de script.

- O pacote ZIP foi extraído em outra pasta e executado offline. Os 11 CSVs analíticos foram regenerados com conteúdo idêntico; PDF e HTML também foram regenerados com sucesso.

## Limites da verificação

A validação de HTML foi funcional em DOM; não foi possível executar Chromium neste ambiente porque o binário não estava disponível e seu download não foi concluído. A renderização final em navegadores reais e em celular permanece uma verificação recomendada ao abrir o relatório. O PDF foi renderizado e inspecionado.

O workflow do GitHub está configurado para testar e reproduzir o projeto. O resultado de cada execução está disponível na [aba Actions do repositório](https://github.com/lucasambrosio1500/-energia-equidade-rmc-/actions). Não houve revisão externa, auditoria de origem junto às distribuidoras, validação de campo nem avaliação por órgão regulador. Testes do software não eliminam limitações das bases oficiais.

## Integridade e reprodução

O build verifica o hash do snapshot mensal antes de calcular. `MANIFEST.sha256` registra os arquivos do pacote, exceto o próprio manifesto. A reprodução offline utiliza o snapshot e as fontes auxiliares incluídos; o arquivo ZIP nacional de origem pode ser adquirido separadamente.

Antes de publicar uma nova edição com dados atualizados, rever datas, contagens, narrativas e comparabilidade territorial. A atualização dos cálculos não substitui a revisão da interpretação.
