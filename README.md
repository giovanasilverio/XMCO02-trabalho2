

## Execução

Instale a dependência:

```bash
python -m pip install -r requirements.txt
```

Execute os arquivos:

```bash
python leitura.py
python crap_hmp.py
python exp1_pr.py
python exp2_capacidade.py
python exp3_alpha.py
python exp4_estrutura.py
```

Os caminhos usam a pasta do próprio código. Troque ARQUIVO, N_SUB, CONFIGS,
ALPHAS, FOLGAS ou CASOS manualmente no início dos experimentos. O exemplo
individual fica no final de crap_hmp.py. Não existe argumento obrigatório
na linha de comando.

## Arquivos

- leitura.py: n, demandas, distâncias e capacidades opcionais; comentários #.
- validacao.py: verifica valores originais, alocações, fluxos, capacidades e custo.
- crap_hmp.py: adaptador de leitura, modelo, solução e exportação .dot.
- exp1_pr2.py: compara valores de r para diferentes p e cenarios de capacidade; CSV incremental e grafos .dot.
- exp2_capacidade2.py: compara folgas de capacidade; CSV incremental em exp2_capacidade2.csv com cargas e utilizacao por hub, alem de grafos .dot.
- exp3_alpha.py: comparação de alpha com capacidades do arquivo, capacidades
  uniformes e referência explicitamente sem capacidade; CSV incremental.
- exp4_estrutura.py: alocações, cargas, rotas e grafos; relatório incremental.
- instancias/: os onze arquivos fornecidos, preservados sem alterações.

Use estes cinco módulos juntos. O novo validacao.py recebe inst com W, D, B
 e z como matriz; substitui a versão anterior que esperava outros formatos.
O formato original do leitura.py continua n/demandas/distancias/capacidades;
carregar_instancia faz a conversão para W/D/B.

## Capacidades

resolver(..., B=None) usa as capacidades do arquivo. Quando elas não existem,
informe B como número (mesma capacidade para todos) ou lista de n valores.
A ausência de B causa erro, evitando resolver sem capacidade por acidente.
Somente sem_capacidade=True desativa a restrição, para comparação experimental.

Nos experimentos, None significa cenário sem capacidade; 'arquivo' usa B
original; um número cria B = folga * demanda_total / p para cada candidato.
Essa fórmula não garante viabilidade: fluxos que usam dois hubs consomem
capacidade em ambos. Os padrões usam toy8, que tem capacidades.
Para CAB/AP e toy7, remova os cenários 'arquivo' e escolha folgas numéricas.
A linha final do toy7 está comentada com # e é ignorada; não foi descomentada.

## Formulação e interpretação

As restrições (8) e (9) usam <=. A carga segue (10), contando uma vez os
fluxos com k=l. Demandas positivas i=j das AP são preservadas.

São criadas variáveis x apenas para demandas positivas. Cada nó deve ter
pelo menos uma alocação, condição implícita na formulação completa. Assim,
os pares de demanda zero podem receber rotas sem custo ou carga entre hubs
alocados, sem alterar a solução. O validador segue essa mesma convenção.

Todos os índices vão de 0 até n-1. z e x preservam valores originais para
validação. Tolerâncias e arredondamentos de apresentação não alteram os dados.
Uma alocação z=1 sem fluxo é permitida. A matriz efetiva marca somente ligações
com fração superior a 1e-6, sem forçar a diagonal dos hubs.

Um resultado viável não é necessariamente ótimo. Compare custos como ótimos
somente quando otimo=True; sol_status diferencia soluções inteiras encontradas
sem prova de otimalidade. Uma tentativa sem solução não prova inviabilidade.

N_SUB seleciona os primeiros nós e elimina as demandas externas ao subconjunto.
Identifique os resultados como instâncias reduzidas. O modelo de quatro índices
continua grande: AP80 pode gerar cerca de 41 milhões de variáveis x. Comece pelos
toy ou subconjuntos pequenos. O limite de tempo se aplica ao solver, não à montagem.

Os arquivos .dot podem ser abertos em um visualizador Graphviz. O grafo agrega
transferências entre hubs; o relatório contém as rotas completas de demanda positiva.

Os experimentos 3 e 4 não substituem estudos específicos de variação de p/r e
aperto das capacidades, caso essas partes estejam com outro integrante.
