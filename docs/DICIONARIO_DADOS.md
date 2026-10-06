# Dicionário das tabelas analíticas

Todos os CSVs processados usam UTF-8, vírgula como separador e ponto decimal. Identificadores são texto. Ausência numérica é célula vazia, não zero.

| Tabela | Unidade de observação | Campos principais |
|---|---|---|
| `regional_monthly` | CNPJ × conjunto × ano × mês × indicador | `value`: DEC em h/UC, FEC em interrupções/UC ou NumCon em UCs |
| `annual_sets` | CNPJ × conjunto × ano | `complete`, `months_complete`, `dec_h`, `fec_n`, `uc_mean`, `uc_ratio`, limites e razões |
| `regional_sets` | Mesma unidade, conjuntos associados à RMC | Inclui conjuntos que também atendem cidades externas |
| `municipal_context` | Município × ano elétrico | Medianas/amplitudes de conjuntos associados, renda de 2022, baixa renda, compartilhamento e cobertura |
| `municipal_exclusive` | Município × ano elétrico | Resumo apenas dos conjuntos ligados exclusivamente a um município na relação nacional |
| `regional_links` | Município × conjunto × ano completo | Relação expandida para auditoria; não somar como se as linhas fossem conjuntos independentes |
| `crosswalk` | Conjunto × município | Todos os municípios, inclusive externos, ligados aos conjuntos cadastrados da RMC |
| `income` | Território: município, SP ou Brasil | `income_mean`, `income_median`: R$/pessoa/mês nominais de 2022; `low_income_pct`: % do universo SIDRA |
| `benchmarks` | Escopo × ano | Medianas não ponderadas de conjuntos completos; amostra pode variar |
| `balanced_benchmarks` | Escopo × ano | Mesmas estatísticas em coorte completa nos quatro anos |
| `sensitivity` | Cenário × ano | `n`, `rho`, `loo_min`, `loo_max`: correlação e sensibilidade à retirada de um município |

`set_id` é o identificador de conjunto; `cnpj` preserva zeros iniciais. Não fazer associação por nome de município ou conjunto. `set_coverage_pct` conta conjuntos, não UCs ou pessoas. `n_shared` conta conjuntos com mais de um município em toda a base nacional. `income_population` é a população específica do universo da tabela de renda, não a população total do município.

`dec_sum` e `fec_sum` são somas mensais sem ajuste; `dec_h` e `fec_n` usam a reconstrução com NumCon. `uc_ratio` é a razão entre maior e menor número mensal de UCs, usada como diagnóstico de mudanças de cadastro. Ausência de limite invalida apenas a razão; não apaga uma série elétrica completa.

O banco `energia_equidade.sqlite` contém as mesmas tabelas. Não há dados pessoais individualizados. O arquivo `rmc.geojson` vem da API de malhas do IBGE e representa municípios, não redes elétricas; sua referência geográfica foi obtida no momento da consulta, sem assumir que é uma malha histórica de 2022.
