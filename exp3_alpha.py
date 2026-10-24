import csv
import os
import time

from crap_hmp import (carregar_instancia, resolver, exportar_dot, alocacao_efetiva,
                      capacidade_uniforme)


ARQUIVO = "instancias/CAB25.txt"
N_SUB = 10
ALPHAS = [0.2, 0.4, 0.6, 0.8, 1.0]
CONFIGS = [(3, 1), (3, 2), (3, 3), (2, 2)]   # (p, r)
FOLGAS = [None]
TEMPO_MAX = 120
SAIDA = "resultados"


def checar_instancia(inst):
    D, n = inst["D"], inst["n"]
    diag_ok = all(abs(D[i][i]) < 1e-9 for i in range(n))
    sim_ok = all(abs(D[i][j] - D[j][i]) < 1e-6 for i in range(n) for j in range(n))
    if not (diag_ok and sim_ok):
        print("AVISO: D nao e simetrica/diagonal zero -> confira se W e D estao trocadas "
              "no carregar_instancia.")


def decompor_custo(inst, res, alpha):
    W, D = inst["W"], inst["D"]
    col = tra = dis = 0.0
    for (i, j, k, l), f in res["x"].items():
        col += W[i][j] * f * D[i][k]
        tra += W[i][j] * f * alpha * D[k][l]
        dis += W[i][j] * f * D[l][j]
    return col, tra, dis


def consolidacao(inst, res):
    W = inst["W"]
    total = dois = 0.0
    ligacoes = set()
    for (i, j, k, l), f in res["x"].items():
        v = W[i][j] * f
        total += v
        if k != l:
            dois += v
            ligacoes.add((k, l))
    return (dois / total if total else 0.0), len(ligacoes)


def main():
    os.makedirs(os.path.join(SAIDA, "dot"), exist_ok=True)
    inst = carregar_instancia(ARQUIVO, n_sub=N_SUB)
    checar_instancia(inst)
    n = inst["n"]
    linhas = []
    for folga in FOLGAS:
        for (p, r) in CONFIGS:
            B = None if folga is None else capacidade_uniforme(inst, p, folga)
            for a in ALPHAS:
                t = time.time()
                res = resolver(inst, p=p, r=r, alpha=a, B=B, tempo_max=TEMPO_MAX)
                dt = time.time() - t
                if res["custo"] is None:
                    print(f"p={p} r={r} a={a} folga={folga}: {res['status']}")
                    continue
                col, tra, dis = decompor_custo(inst, res, a)
                if abs(col + tra + dis - res["custo"]) > 1e-3 * max(1, res["custo"]):
                    print(f"  AVISO: decomposicao ({col+tra+dis:.1f}) != custo "
                          f"({res['custo']:.1f})")
                pct2, n_lig = consolidacao(inst, res)
                A = alocacao_efetiva(n, res)
                n_multi = sum(1 for i in range(n)
                              if i not in res["hubs"] and sum(A[i]) > 1)
                linhas.append({
                    "instancia": ARQUIVO, "n": n, "p": p, "r": r, "alpha": a,
                    "capacidade": "sem" if folga is None else f"folga {folga}",
                    "custo": round(res["custo"]), "coleta": round(col),
                    "transferencia": round(tra), "distribuicao": round(dis),
                    "pct_fluxo_2hubs": round(100 * pct2, 1), "ligacoes_hub_hub": n_lig,
                    "hubs": " ".join(map(str, res["hubs"])), "nos_multi_hub": n_multi,
                    "tempo_s": round(dt, 1), "status": res["sol_status"]})
                print(f"p={p} r={r} alpha={a} cap={folga}: custo={res['custo']:.0f} "
                      f"hubs={res['hubs']} 2hubs={pct2:.0%} lig={n_lig} "
                      f"multi={n_multi} [{res['sol_status']}] ({dt:.1f}s)")
                if a in (min(ALPHAS), max(ALPHAS)):
                    sufixo = "" if folga is None else f"_cap{folga}"
                    exportar_dot(inst, res, os.path.join(
                        SAIDA, "dot", f"p{p}_r{r}_a{a}{sufixo}.dot"))

    if not linhas:
        print("Nenhuma solucao obtida.")
        return
    with open(os.path.join(SAIDA, "exp3_alpha.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)
    print("\nSalvo em", os.path.join(SAIDA, "exp3_alpha.csv"))


if __name__ == "__main__":
    main()
