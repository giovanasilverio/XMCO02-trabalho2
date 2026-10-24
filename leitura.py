from pathlib import Path
from math import isfinite


def ler_instancia(caminho):
    """Lê n, a matriz de demandas e a matriz de distâncias.

    Retorna 'n', 'demandas', 'distancias' e 'capacidades'.
    Capacidades são uma lista de n valores ou None quando ausentes.
    As matrizes são listas de listas com índices de 0 até n - 1:
    dados['demandas'][i][j] representa w_ij.
    dados['distancias'][i][j] representa d_ij.

    Preserva demandas assimétricas e demandas positivas na diagonal.
    Aceita um vetor opcional de capacidades após as matrizes.
    Ignora comentários iniciados por #, inclusive no fim das linhas.
    Parâmetros p, r e alpha devem ser definidos nos experimentos.

    Levanta ValueError para conteúdo inválido. Erros de acesso ao arquivo
    (como FileNotFoundError) são propagados normalmente.
    """
    caminho = Path(caminho)
    with caminho.open('r', encoding='utf-8-sig') as arquivo:
        valores = []
        for linha in arquivo:
            valores.extend(linha.split('#', 1)[0].split())

    if not valores:
        raise ValueError(f'O arquivo {caminho.name} está vazio.')

    try:
        n = int(valores[0])
    except ValueError as erro:
        raise ValueError('O primeiro valor deve ser um número inteiro de nós.') from erro

    if n <= 0:
        raise ValueError('O número de nós deve ser positivo.')

    quantidade_esperada = 1 + 2 * n * n
    if len(valores) not in (quantidade_esperada, quantidade_esperada + n):
        raise ValueError(
            f'{caminho.name}: esperados {2 * n * n} valores nas duas matrizes '
            f'{n}x{n}, opcionalmente seguidos por {n} capacidades; '
            f'encontrados {len(valores) - 1} valores após o número de nós.'
        )

    matrizes = []
    indice = 1

    for nome in ('demandas', 'distancias'):
        matriz = []
        for i in range(n):
            linha = []
            for j in range(n):
                texto = valores[indice]
                try:
                    valor = float(texto)
                except ValueError as erro:
                    raise ValueError(
                        f'{nome}[{i}][{j}]: valor inválido {texto!r}.'
                    ) from erro

                if not isfinite(valor) or valor < 0:
                    raise ValueError(
                        f'{nome}[{i}][{j}] deve ser finito e não negativo: {texto!r}.'
                    )

                linha.append(valor)
                indice += 1
            matriz.append(linha)
        matrizes.append(matriz)

    capacidades = None
    if len(valores) == quantidade_esperada + n:
        capacidades = []
        for k in range(n):
            texto = valores[indice + k]
            try:
                valor = float(texto)
            except ValueError as erro:
                raise ValueError(f'capacidades[{k}]: valor inválido {texto!r}.') from erro
            if not isfinite(valor) or valor < 0:
                raise ValueError(f'capacidades[{k}] deve ser finita e não negativa.')
            capacidades.append(valor)

    return {
        'n': n,
        'demandas': matrizes[0],
        'distancias': matrizes[1],
        'capacidades': capacidades,
    }


if __name__ == '__main__':
    caminho =  "dummy_instances/dummy/toy1.txt"
    dados = ler_instancia(caminho)
    print('Número de nós:', dados['n'])
    print('Demanda total:', sum(map(sum, dados['demandas'])))
    print('Capacidades:', dados['capacidades'])
