"""Modelo capacitado e auxiliares compartilhados pelos experimentos."""
from math import isfinite
from pathlib import Path
from time import perf_counter
import pulp
from leitura import ler_instancia
from validacao import validar_solucao


def carregar_instancia(caminho, n_sub=None):
    dados = ler_instancia(caminho)
    original = dados['n']
    if n_sub is not None:
        if type(n_sub) is not int or not 1 <= n_sub <= original:
            raise ValueError('n_sub deve ser inteiro entre 1 e o tamanho original.')
    n = original if n_sub is None else n_sub
    B = dados['capacidades']
    return {'n': n, 'W': [row[:n] for row in dados['demandas'][:n]],
            'D': [row[:n] for row in dados['distancias'][:n]],
            'B': None if B is None else B[:n], 'n_original': original,
            'arquivo': str(caminho)}


def capacidade_uniforme(inst, p, folga=1.0):
    if type(p) is not int or not 1 <= p <= inst['n']:
        raise ValueError('p inválido.')
    if not isfinite(folga) or folga <= 0:
        raise ValueError('folga deve ser finita e positiva.')
    # É uma parametrização experimental, não garantia de viabilidade.
    return folga * sum(map(sum, inst['W'])) / p


def resolver(inst, p, r, alpha=0.6, B=None, lam=1.0, delta=1.0,
             tempo_max=300, msg=False, sem_capacidade=False):
    inicio = perf_counter()
    n, W, D = inst['n'], inst['W'], inst['D']
    N = range(n)
    if type(p) is not int or not 1 <= p <= n:
        raise ValueError('p deve estar entre 1 e n.')
    if type(r) is not int or not 1 <= r <= p:
        raise ValueError('r deve estar entre 1 e p.')
    if not isfinite(alpha) or not 0 < alpha <= 1:
        raise ValueError('alpha deve estar em (0,1].')
    if any(not isfinite(v) or v < 0 for v in (lam, delta)):
        raise ValueError('lam e delta devem ser finitos e não negativos.')
    if tempo_max is not None and (not isfinite(tempo_max) or tempo_max <= 0):
        raise ValueError('tempo_max deve ser positivo ou None.')
    if sem_capacidade and B is not None:
        raise ValueError('Não informe B junto com sem_capacidade=True.')
    if not sem_capacidade:
        B = inst.get('B') if B is None else B
        if B is None:
            raise ValueError('Informe B: esta instância não tem capacidades. '
                             'Para comparação sem capacidade, use sem_capacidade=True.')
        if isinstance(B, (int, float)):
            B = [B] * n
        else:
            B = list(B)
        if len(B) != n or any(not isfinite(v) or v < 0 for v in B):
            raise ValueError('B deve conter n capacidades finitas e não negativas.')
    pares = [(i,j) for i in N for j in N if W[i][j] > 0]
    prob = pulp.LpProblem('CrApHMP', pulp.LpMinimize)
    z = [[pulp.LpVariable(f'z_{i}_{k}', cat='Binary') for k in N] for i in N]
    x = {(i,j,k,l): pulp.LpVariable(f'x_{i}_{j}_{k}_{l}', 0, 1)
         for i,j in pares for k in N for l in N}
    prob += pulp.lpSum(W[i][j] * (lam*D[i][k] + alpha*D[k][l] + delta*D[l][j])
                       * x[i,j,k,l] for i,j in pares for k in N for l in N), 'Custo'
    prob += pulp.lpSum(z[k][k] for k in N) == p, 'Numero_hubs'
    for i in N:
        for k in N:
            prob += z[i][k] <= z[k][k], f'Hub_aberto_{i}_{k}'
        # Limite inferior implícito em (7)-(8) na formulação completa.
        # Mantém a equivalência ao retirar pares de demanda zero, inclusive nós isolados.
        prob += pulp.lpSum(z[i]) >= 1, f'Alocacao_minima_{i}'
        prob += pulp.lpSum(z[i]) <= r, f'Alocacao_maxima_{i}'
    for i,j in pares:
        prob += pulp.lpSum(x[i,j,k,l] for k in N for l in N) == 1, f'Demanda_{i}_{j}'
        for k in N:
            prob += pulp.lpSum(x[i,j,k,l] for l in N) <= z[i][k], f'Origem_{i}_{j}_{k}'
        for l in N:
            prob += pulp.lpSum(x[i,j,k,l] for k in N) <= z[j][l], f'Destino_{i}_{j}_{l}'
    if not sem_capacidade:
        for k in N:
            prob += pulp.lpSum(W[i][j] * (
                pulp.lpSum(x[i,j,k,l] for l in N) +
                pulp.lpSum(x[i,j,l,k] for l in N if l != k))
                for i,j in pares) <= B[k]*z[k][k], f'Capacidade_{k}'
    tempo_construcao = perf_counter() - inicio
    t = perf_counter()
    prob.solve(pulp.PULP_CBC_CMD(msg=msg, timeLimit=tempo_max))
    tempo_solver = perf_counter() - t
    tem = prob.sol_status in (pulp.LpSolutionOptimal, pulp.LpSolutionIntegerFeasible)
    res = {'status': pulp.LpStatus[prob.status],
           'sol_status': pulp.LpSolution.get(prob.sol_status, str(prob.sol_status)),
           'tem_solucao': tem, 'otimo': prob.sol_status == pulp.LpSolutionOptimal,
           'custo': None, 'hubs': [], 'z': [], 'x': {}, 'carga_hubs': {},
           'capacidades': B, 'sem_capacidade': sem_capacidade,
           'tempo_s': tempo_construcao + tempo_solver,
           'tempo_construcao_s': tempo_construcao, 'tempo_solver_s': tempo_solver,
           'valida': None, 'erros_validacao': []}
    if not tem:
        return res
    res['z'] = [[v.value() for v in row] for row in z]
    # Preserva valores numéricos originais para validar, sem arredondar ou filtrar.
    res['x'] = {key: v.value() for key,v in x.items()}
    res['custo'] = sum(W[i][j]*(lam*D[i][k]+alpha*D[k][l]+delta*D[l][j])*f
                       for (i,j,k,l),f in res['x'].items())
    res['hubs'] = [k for k in N if res['z'][k][k] > 0.5]
    res['carga_hubs'] = {k: sum(W[i][j]*f*((a==k)+(b==k and a!=k))
                              for (i,j,a,b),f in res['x'].items()) for k in res['hubs']}
    # Instância sem B para que o validador não recupere capacidades no cenário livre.
    inst_validacao = dict(inst, B=None) if sem_capacidade else inst
    res['valida'], res['erros_validacao'] = validar_solucao(
        inst_validacao, res, p, r, B=B, alpha=alpha, lam=lam, delta=delta)
    return res


def alocacao_efetiva(n, res, tol=1e-6):
    A = [[0]*n for _ in range(n)]
    for (i,j,k,l),f in res['x'].items():
        if f > tol:
            A[i][k] = A[j][l] = 1
    return A


def exportar_dot(inst, res, caminho='solucao.dot', efetiva=True, tol=1e-6):
    if not res.get('tem_solucao') or not res.get('valida'):
        raise ValueError('É necessária uma solução validada para exportar.')
    A = alocacao_efetiva(inst['n'], res, tol) if efetiva else res['z']
    linhas = ['digraph G {', '  node [shape=circle];']
    for i in range(inst['n']):
        estilo = ' [style=filled, fillcolor=gray]' if i in res['hubs'] else ''
        linhas.append(f'  {i}{estilo};')
    for i in range(inst['n']):
        for k in range(inst['n']):
            if A[i][k] > 0.5 and i != k:
                linhas.append(f'  {i} -> {k} [style=dashed, color=gray, dir=none];')
    transf = {}
    for (i,j,k,l),f in res['x'].items():
        if k != l and f > tol:
            transf[k,l] = transf.get((k,l), 0.0) + inst['W'][i][j]*f
    for (k,l),v in transf.items():
        linhas.append(f'  {k} -> {l} [label="{v:.6g}", penwidth=2];')
    linhas.append('}')
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text('\n'.join(linhas), encoding='utf-8')


if __name__ == '__main__':
    ARQUIVO = "dummy_instances/dummy/toy1.txt"
    N_SUB = None
    P, R, ALPHA = 2, 1, 0.6
    B = None  # Usa capacidades do arquivo. Se ausentes, informe escalar ou lista.
    inst = carregar_instancia(ARQUIVO, N_SUB)
    res = resolver(inst, P, R, ALPHA, B=B, msg=True)
    print('Status:', res['status'], '| solução:', res['sol_status'])
    if res['tem_solucao']:
        print('Custo:', res['custo'], '| hubs:', res['hubs'])
        print('Ótimo comprovado:', res['otimo'], '| válida:', res['valida'])
        for erro in res['erros_validacao']:
            print('-', erro)
    else:
        if res['status'] == 'Infeasible':
            print('O solver declarou o cenário inviável.')
        else:
            print('Nenhuma solução inteira disponível; isso não prova inviabilidade.')
