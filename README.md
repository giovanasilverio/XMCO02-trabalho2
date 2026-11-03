# CrApHMP — Métodos Exatos

Implementação do **Capacitated r-Allocation p-Hub Median Problem**, desenvolvida para a disciplina de Métodos Exatos da UNIFEI.

O modelo seleciona `p` hubs, permite até `r` alocações por nó e minimiza o custo de transporte, respeitando as capacidades dos hubs. Implementado em Python com PuLP e solver CBC.

## Estrutura

- `crap_hmp.py`: construção e resolução do modelo.
- `leitura.py`: leitura e verificação das instâncias.
- `validacao.py`: validação das soluções.
- `exp1_pr.py`: variação de `p` e `r`.
- `exp2_capacidade.py`: variação das capacidades.
- `exp3_alpha.py`: variação do desconto entre hubs.
- `exp4_estrutura.py`: análise das alocações e rotas.
- `resultados/`: resultados dos experimentos.
- `CAB25.txt`, `AP40.txt`, `AP80.txt` e `dummy_instances/`: instâncias disponíveis.
- `INSTANCES_README.txt`: informações sobre as instâncias.

## Execução

Instale as dependências:

```bash
pip install -r requirements.txt
```

Execute o experimento desejado na raiz do repositório:

```bash
python exp1_pr.py
python exp2_capacidade.py
python exp3_alpha.py
python exp4_estrutura.py
```

As instâncias e os parâmetros são configurados nos scripts. Os resultados permitem comparar custos, hubs selecionados, alocações e tempos de execução.

## Autores

- Bianca Salvador
- Giovana Silverio Pereira
- Luiz Augusto Silva
