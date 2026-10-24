"""Verificação independente de viabilidade; não comprova otimalidade."""
from math import isfinite


def validar_solucao(inst, res, p, r, B=None, alpha=0.6,
                    lam=1.0, delta=1.0, tol=1e-6):
    n, W, D = inst['n'], inst['W'], inst['D']
    N = range(n)
    erros = []
    if res.get('custo') is None:
        return False, ['Nenhuma solução inteira disponível.']
    Z, X = res['z'], res['x']
    if len(Z) != n or any(len(row) != n for row in Z):
        return False, ['Dimensões incorretas de z.']
    if B is None:
        B = inst.get('B')
    if B is not None and isinstance(B, (int, float)):
        B = [B] * n
    if B is not None and (len(B) != n or any(not isfinite(v) or v < 0 for v in B)):
        return False, ['Capacidades inválidas.']
    for i in N:
        for k in N:
            v = Z[i][k]
            if v is None or not isfinite(v):
                erros.append(f'z[{i},{k}] não possui valor finito.')
            elif min(abs(v), abs(v - 1)) > tol:
                erros.append(f'z[{i},{k}] não é binária: {v}.')
    for chave, v in X.items():
        if (not isinstance(chave, tuple) or len(chave) != 4
                or any(not isinstance(t, int) or t not in N for t in chave)):
            erros.append(f'Índice de x inválido: {chave}.')
        elif v is None or not isfinite(v) or v < -tol or v > 1 + tol:
            erros.append(f'x{chave} fora de [0,1] ou sem valor finito.')
    if erros:
        return False, erros
    if abs(sum(Z[k][k] for k in N) - p) > tol:
        erros.append('Quantidade de hubs diferente de p.')
    for i in N:
        soma = sum(Z[i])
        if soma < 1 - tol or soma > r + tol:
            erros.append(f'Nó {i}: quantidade de alocações fora de [1,r].')
        for k in N:
            if Z[i][k] > Z[k][k] + tol:
                erros.append(f'Nó {i} alocado ao hub fechado {k}.')
    totais, saidas, entradas = {}, {}, {}
    cargas = [0.0] * n
    custo = 0.0
    for (i,j,k,l), f in X.items():
        totais[i,j] = totais.get((i,j), 0.0) + f
        saidas[i,j,k] = saidas.get((i,j,k), 0.0) + f
        entradas[i,j,l] = entradas.get((i,j,l), 0.0) + f
        fluxo = W[i][j] * f
        cargas[k] += fluxo
        if l != k:
            cargas[l] += fluxo
        custo += fluxo * (lam * D[i][k] + alpha * D[k][l] + delta * D[l][j])
    # Pares com demanda zero são omitidos no modelo reduzido.
    # A alocação mínima de cada nó permite completar suas rotas sem custo/carga.
    for i in N:
        for j in N:
            if W[i][j] <= 0:
                continue
            if abs(totais.get((i,j), 0.0) - 1) > tol:
                erros.append(f'Par ({i},{j}): frações não somam 1.')
            for k in N:
                if saidas.get((i,j,k), 0.0) > Z[i][k] + tol:
                    erros.append(f'Par ({i},{j}): vínculo da origem com {k} violado.')
                if entradas.get((i,j,k), 0.0) > Z[j][k] + tol:
                    erros.append(f'Par ({i},{j}): vínculo do destino com {k} violado.')
    if B is not None:
        for k in N:
            limite = B[k] * Z[k][k]
            if cargas[k] > limite + tol * max(1.0, abs(limite)):
                erros.append(f'Hub {k}: carga {cargas[k]} excede {limite}.')
    if abs(custo - res['custo']) > tol * max(1.0, abs(custo), abs(res['custo'])):
        erros.append('Custo informado difere do custo recalculado.')
    return not erros, erros
