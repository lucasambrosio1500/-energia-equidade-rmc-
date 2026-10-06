# Guia para executar, compreender e apresentar

## Primeiro contato — sem programação

Abra `reports/Observatorio_Energia_Equidade.html` no navegador. Funciona sem instalação e sem enviar dados. Comece em 2024 e observe a cobertura. Alterne entre renda e continuidade, escolha um município e leia quantos conjuntos ele compartilha. Compare 2022, ano do Censo, com os demais anos sem tratar a renda como atualizada.

Leia o PDF em `reports/Relatorio_Tecnico_Energia_Equidade.pdf`, depois `docs/METODOLOGIA.md`. Consulte as tabelas em `data/processed/` no Excel, Power BI ou SQLite. O arquivo `sql/consultas.sql` contém consultas explicadas.

## Cinco pontos que você precisa dominar

1. DEC descreve duração equivalente e FEC frequência equivalente de interrupções. Não são indicadores de distorção harmônica ou tensão.
2. Um conjunto elétrico não é um município. Sem UCs por interseção geográfica, não calculamos um indicador municipal oficial.
3. Renda municipal não informa a renda dos consumidores que sofreram uma interrupção. Essa é a limitação ecológica.
4. Mês ausente não vale zero. Usar série incompleta pode produzir uma falsa melhora.
5. Uma correlação fraca ou instável é um resultado válido e não prova ausência de desigualdade dentro das cidades.

## Roteiro de estudo prático

- Abra um município e explique o valor mínimo, mediano e máximo dos seus conjuntos.
- Localize a tabela de conjuntos incompletos e explique por que foram excluídos.
- Rode as consultas SQL 1, 2 e 3; confira uma linha do resultado com o relatório.
- Refaça o exemplo de anualização da metodologia com uma calculadora.
- Compare a correlação com todos os vínculos e com conjuntos exclusivos; explique a perda de cobertura.
- Escolha uma frente de política pública e liste as informações que ainda precisaria coletar.

## Explicação de um minuto — adaptar à sua participação real

“O projeto investiga a relação entre continuidade do fornecimento de energia e condições socioeconômicas na Região Metropolitana de Campinas. Integra dados públicos da ANEEL e do Censo 2022, valida as séries mensais e compara os indicadores dos conjuntos elétricos com o contexto dos municípios. O principal cuidado é não confundir a área de um conjunto com os limites municipais. Os resultados servem para orientar investigações sobre confiabilidade, vulnerabilidade e serviços essenciais, sem transformar correlação em causalidade.”

## Perguntas de entrevista

**Por que estudar essa região?** Pela conexão com o território onde você vive e com sua experiência em indicadores e manutenção. Explicar sua motivação com suas próprias palavras.

**Você demonstrou que pessoas pobres ficam mais sem energia?** Não. A escala e a dependência dos dados não permitem essa afirmação individual. A análise testa associações territoriais e sua estabilidade.

**Por que não usou machine learning?** Uma amostra municipal pequena e parcialmente dependente pede análise transparente. A complexidade de um modelo não resolve limitações geográficas nem cria causalidade.

**Por que a última análise principal é 2024?** A fotografia obtida contém séries regionais incompletas em 2025. A versão suplementar mostra o efeito da exclusão; o recorte principal preserva a cobertura.

**O que faria para melhorar?** Obter a distribuição de consumidores por município e conjunto, histórico das fronteiras e dados de interrupções e cargas críticas. Realizar diagnóstico local e acrescentar variáveis de rede e clima.

**Você programou tudo?** Responder com precisão: a implementação foi produzida com assistência de IA. Sua participação em definição do problema, validação, análise ou adaptação deve refletir o que você efetivamente realizou. Não dizer que domina Python avançado se isso não for verdade.

## Currículo

Antes de incluir como experiência concluída, executar o relatório, conferir cálculos e conseguir explicar método, resultados e limitações. O material não comprova automaticamente competência individual em Python.

Título sugerido: **Energia e Equidade na Região Metropolitana de Campinas | Projeto pessoal**.

Depois da sua revisão, adaptar os tópicos à participação real:

- Análise exploratória de continuidade do fornecimento e condições socioeconômicas, integrando dados públicos da ANEEL e do IBGE para 20 municípios.
- Validação de séries temporais, consultas SQL e interpretação de indicadores para discussão de confiabilidade da infraestrutura e políticas públicas.

Não declarar atuação profissional como engenheiro responsável, parceria com Unicamp/ANEEL, publicação científica, impacto social medido, economia obtida ou implantação de política pública. Nada disso foi realizado por este projeto.
