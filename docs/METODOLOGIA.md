# Metodologia e decisões de engenharia

## 1. Pergunta e objeto

Investigar a associação territorial entre continuidade do fornecimento e condições de renda na Região Metropolitana de Campinas (RMC), com contexto estadual e nacional. O estudo é observacional, ecológico e exploratório. Não identifica efeitos causais nem discriminação no atendimento.

A pergunta operacional é: **municípios com maior proporção de moradores de baixa renda estão associados a conjuntos elétricos com maior duração ou frequência de interrupções?** Ela não equivale a perguntar se pessoas pobres sofrem mais interrupções dentro de um mesmo município.

O objeto elétrico é a continuidade do serviço. Não são medidos tensão, harmônicos, afundamentos, qualidade comercial, acesso físico à rede nem comprometimento da renda com a conta de luz. Portanto, o projeto não calcula um índice completo de pobreza energética.

## 2. Recorte

- 20 municípios relacionados pela AGEMCAMP, com códigos confirmados na API de localidades do IBGE.
- Ano principal da associação: **2022**, alinhado ao Censo.
- Evolução: 2022–2024; **2024 é o retrato regional mais recente com séries completas na fotografia obtida**.
- 2025: análise suplementar, com identificação explícita das séries incompletas e das alterações de composição.
- Referência social fixa em julho de 2022, em reais nominais de 2022. Não corresponde à renda em 2024 ou 2025.
- A relação conjunto–município é uma fotografia de 09/09/2026. Sua aplicação a anos anteriores é uma aproximação territorial, sujeita a mudanças de rede; não constitui uma malha histórica validada.

## 3. Fontes e rastreabilidade

ANEEL: indicadores mensais DEC, FEC e NumCon; limites por conjunto e ano; relação IndQual Município. IBGE/SIDRA: tabelas 10295 e 10296 do Censo 2022, totais de sexo, cor ou raça e idade quando aplicável. A população dessas tabelas exclui pensionistas, empregados domésticos e parentes de empregados domésticos na condição especificada pelo IBGE; não é automaticamente a população residente total.

Cada aquisição registra URL, instante UTC, tamanho e SHA-256. `data/sources.json` registra as fontes obtidas. O arquivo `data/processed/extraction.json` registra o filtro do arquivo nacional, número de linhas lidas e hash do ZIP original. A amostra mensal incluída permite reproduzir a análise sem nova conexão. O ZIP nacional de origem não está incluído no pacote; pode ser readquirido.

## 4. Tratamento

1. Preservar CNPJ e códigos territoriais como texto; retirar espaços externos.
2. Converter decimal com vírgula para número, sem transformar ausência em zero.
3. Selecionar DEC, FEC e NumCon, meses 1–12, anos 2022–2025.
4. Rejeitar duplicações da chave `(CNPJ, conjunto, ano, mês, indicador)`.
5. Exigir os três indicadores nos 12 meses, NumCon positivo e valores finitos não negativos.
6. Excluir da anualização as séries incompletas. Manter seu diagnóstico em arquivo.
7. Excluir dos recortes territoriais os conjuntos sem vínculo na fotografia IndQual; registrar a quantidade excluída.
8. Rejeitar vínculo ambíguo: mesmo conjunto e ano com mais de um CNPJ.
9. Relacionar limites por CNPJ, conjunto e ano. Ausência de limite permanece ausente; não se presume cumprimento.

## 5. Reconstrução anual

Seja N_m o número de UCs do mês m e N̄ = (Σ N_m)/12. A reconstrução usa:

**DEC_a = (Σ DEC_m × N_m)/N̄; FEC_a = (Σ FEC_m × N_m)/N̄.**

O numerador do DEC representa a reconstrução de horas-consumidor a partir de valores mensais já arredondados; o denominador é a média mensal de consumidores. Se N_m for constante, a fórmula coincide com a soma dos indicadores mensais. A soma simples também é guardada para análise de sensibilidade.

Exemplo de verificação: onze meses com DEC = 1 h e N = 100; um mês com DEC = 4 h e N = 200. O numerador é 1.900 horas-consumidor e N̄ = 1.300/12. Resultado: 17,5385 h, diferente da soma simples de 15 h. Esse caso integra os testes.

Esta é uma reconstrução analítica, não um valor anual certificado. Arredondamento, revisões e diferenças de apuração podem produzir divergências. A razão reconstrução/limite é uma **triagem para conferência**, não um parecer de descumprimento, cálculo de compensação ou indicador DGC. Valores próximos de 1 exigem atenção especial ao arredondamento. Os componentes expurgados não foram incorporados ao DEC/FEC selecionados; isso limita a descrição da experiência total durante eventos extremos.

## 6. Compatibilização territorial

A base IndQual informa vínculos, mas não quantas UCs de cada conjunto pertencem a cada município. Não é defensável distribuir o número total de UCs de um conjunto igualmente entre cidades, nem ponderar por área ou população sem dados adicionais.

Por isso:

- As medições elétricas permanecem por conjunto.
- Para visualizar contexto municipal, calculamos a mediana não ponderada e a amplitude mínimo–máximo dos conjuntos associados.
- **Esse resumo não é DEC ou FEC municipal oficial, nem o valor experimentado pelo morador médio.**
- O grau de compartilhamento de um conjunto é contado na relação nacional, incluindo municípios fora da RMC.
- Um conjunto compartilhado pode aparecer em vários contextos municipais; não contamos essas aparições como novas medições elétricas independentes.
- A cobertura informada é proporção de conjuntos com série completa entre os que têm algum registro no ano; não é percentual de habitantes ou de UCs cobertos. Conjuntos totalmente ausentes do ano não entram nesse denominador.
- O mapa usa contornos municipais apenas para localizar esse contexto. Não representa fronteiras da rede, bairros ou alimentadores.

## 7. Variáveis sociais

Renda média e mediana vêm da tabela 10295. A proporção de baixa renda é calculada com a tabela 10296:

**100 × (moradores sem rendimento + até 1/4 SM + mais de 1/4 até 1/2 SM) / total do universo da tabela.**

As categorias são mutuamente exclusivas. O programa verifica o fechamento das classes com o total, tolerando apenas arredondamento de estimativas. A faixa é uma definição operacional deste estudo; não é prova de elegibilidade a benefício nem uma linha universal de pobreza. Supressões permanecem ausentes.

O Gini do Censo 2022 na tabela 10301 foi investigado, mas a API consultada não oferece o nível municipal. Não se atribui um Gini estadual a Campinas nem se substitui Gini pela razão média/mediana.

## 8. Associação e robustez

Calculamos Spearman entre variáveis sociais e resumos dos conjuntos associados. São estatísticas descritivas dos municípios analisados, sem p-valores: conjuntos compartilhados criam dependência entre observações, e 20 municípios oferecem suporte limitado para modelos com muitos controles.

Verificações incluídas:

- Renda média versus mediana e proporção de baixa renda.
- DEC versus FEC.
- Exclusão de todos os conjuntos que atendem mais de um município; registrar a redução de cobertura.
- Reconstrução ajustada por UCs versus soma mensal simples.
- Retirada de um município por vez; o intervalo resultante é de sensibilidade, **não intervalo de confiança**.
- Evolução estadual/nacional/regional com todos os conjuntos completos e com coorte fixa completa em 2022–2025.

As referências Brasil e São Paulo são medianas de conjuntos com vínculos e dados completos, não indicadores oficiais globais ponderados da ANEEL. Variações da cobertura podem alterar a amostra. Não há ajuste por clima, extensão/ruralidade da rede, vegetação, densidade ou investimento. Esses fatores podem confundir a associação.

## 9. Decisão pública

A versão atual fornece triagem territorial e aponta necessidades de informação. Não distribui orçamento automaticamente nem estabelece prioridade legal de manutenção. A análise evita um índice composto opaco: mostra separadamente condições sociais, indicadores elétricos, limites e qualidade da evidência. A seleção de ações demanda validação local e participação dos atingidos.

Antes de recomendar investimento localizado, obter histórico dos vínculos, distribuição de UCs por município e conjunto, interrupções e cargas críticas georreferenciadas, contexto climático e custos. Uma avaliação de impacto posterior pode comparar áreas tratadas e de controle com desenho temporal adequado; este estudo não executou essa avaliação.
