import itertools
import pulp


def carregar_instancia(caminho, n_sub=None):
    with open(caminho) as f:
        tokens = f.read().split()
    n = int(tokens[0])
    vals = list(map(float, tokens[1:1 + 2 * n * n]))
    W = [vals[i * n:(i + 1) * n] for i in range(n)]
    D = [vals[n * n + i * n: n * n + (i + 1) * n] for i in range(n)]
    if n_sub and n_sub < n:
        n = n_sub
        W = [row[:n] for row in W[:n]]
        D = [row[:n] for row in D[:n]]
    return {"n": n, "W": W, "D": D}


def capacidade_uniforme(inst, p, folga=1.0):
    total = sum(map(sum, inst["W"]))
    return folga * total / p


def resolver(inst, p, r, alpha=0.6, B=None, lam=1.0, delta=1.0,
             tempo_max=300, msg=False):
    n, W, D = inst["n"], inst["W"], inst["D"]
    N = range(n)
    if B is not None and not isinstance(B, (list, tuple)):
        B = [B] * n

    pares = [(i, j) for i in N for j in N if W[i][j] > 0]

    prob = pulp.LpProblem("CrApHMP", pulp.LpMinimize)
    z = [[pulp.LpVariable(f"z_{i}_{k}", cat="Binary") for k in N] for i in N]
    x = {(i, j, k, l): pulp.LpVariable(f"x_{i}_{j}_{k}_{l}", 0, 1)
         for (i, j) in pares for k in N for l in N}

    def C(i, j, k, l):
        return lam * D[i][k] + alpha * D[k][l] + delta * D[l][j]

    # (3) objetivo
    prob += pulp.lpSum(W[i][j] * C(i, j, k, l) * x[i, j, k, l]
                       for (i, j) in pares for k in N for l in N)
    # (4)
    prob += pulp.lpSum(z[k][k] for k in N) == p
    # (5)
    for i in N:
        for k in N:
            prob += z[i][k] <= z[k][k]
    # (6)
    for i in N:
        prob += pulp.lpSum(z[i][k] for k in N) <= r
    for (i, j) in pares:
        # (7)
        prob += pulp.lpSum(x[i, j, k, l] for k in N for l in N) == 1
        # (8)
        for k in N:
            prob += pulp.lpSum(x[i, j, k, l] for l in N) <= z[i][k]
        # (9)
        for l in N:
            prob += pulp.lpSum(x[i, j, k, l] for k in N) <= z[j][l]
    # (10) capacidade
    if B is not None:
        for k in N:
            prob += pulp.lpSum(
                W[i][j] * (pulp.lpSum(x[i, j, k, l] for l in N) +
                           pulp.lpSum(x[i, j, l, k] for l in N if l != k))
                for (i, j) in pares) <= B[k] * z[k][k]

    solver = pulp.PULP_CBC_CMD(msg=msg, timeLimit=tempo_max)
    prob.solve(solver)
    status = pulp.LpStatus[prob.status]

    if prob.sol_status not in (pulp.LpSolutionOptimal, pulp.LpSolutionIntegerFeasible):
        return {"status": status,
                "sol_status": pulp.LpSolution.get(prob.sol_status, str(prob.sol_status)),
                "custo": None}

    hubs = [k for k in N if z[k][k].value() > 0.5]
    Z = [[int(round(z[i][k].value())) for k in N] for i in N]
    fluxos = {key: v.value() for key, v in x.items() if v.value() and v.value() > 1e-6}
    carga = {k: sum(W[i][j] * f * ((a == k) + (b == k and a != k))
                    for (i, j, a, b), f in fluxos.items()) for k in hubs}
    sol_status = pulp.LpSolution.get(prob.sol_status, str(prob.sol_status))
    return {"status": status, "sol_status": sol_status,
            "custo": pulp.value(prob.objective), "hubs": hubs,
            "z": Z, "x": fluxos, "carga_hubs": carga}


def alocacao_efetiva(n, res):
    A = [[0] * n for _ in range(n)]
    for (i, j, k, l), f in res["x"].items():
        A[i][k] = 1
        A[j][l] = 1
    for h in res["hubs"]:
        A[h][h] = 1
    return A


def exportar_dot(inst, res, caminho="solucao.dot", efetiva=True):
    n = inst["n"]
    aloc = alocacao_efetiva(n, res) if efetiva else res["z"]
    linhas = ["digraph G {", "  node [shape=circle];"]
    for h in res["hubs"]:
        linhas.append(f'  {h} [style=filled, fillcolor=gray];')
    for i in range(n):
        for k in range(n):
            if aloc[i][k] and i != k:
                linhas.append(f'  {i} -> {k} [style=dashed, color=gray, dir=none];')
    transf = {}
    for (i, j, k, l), f in res["x"].items():
        if k != l:
            transf[(k, l)] = transf.get((k, l), 0) + inst["W"][i][j] * f
    for (k, l), v in transf.items():
        linhas.append(f'  {k} -> {l} [label="{v:.0f}", penwidth=2];')
    linhas.append("}")
    with open(caminho, "w") as f:
        f.write("\n".join(linhas))


if __name__ == "__main__":
    inst = carregar_instancia("CAB25.txt", n_sub=8)
    for r in (1, 2, 3):
        res = resolver(inst, p=3, r=r, alpha=0.6)
        print(f"r={r}  custo={res['custo']:.1f}  hubs={res['hubs']}")
