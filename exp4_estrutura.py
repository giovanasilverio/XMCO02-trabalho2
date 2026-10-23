import os

from crap_hmp import (carregar_instancia, resolver, exportar_dot, alocacao_efetiva,
                      capacidade_uniforme)

ARQUIVO = "instancias/CAB25.txt"
N_SUB = 10
TEMPO_MAX = 120
SAIDA = "resultados"

CASOS = [
    ("r1_a0.6",       3, 1, 0.6, None),
    ("r3_a0.6",       3, 3, 0.6, None),
    ("r3_a0.2",       3, 3, 0.2, None),
    ("r3_a0.6_cap",   3, 3, 0.6, 1.2),
]

USAR_NOMES = False
NOMES_CAB = ["Atlanta", "Baltimore", "Boston", "Chicago", "Cincinnati", "Cleveland",
             "Dallas", "Denver", "Detroit", "Houston", "KansasCity", "LosAngeles",
             "Memphis", "Miami", "Minneapolis", "NewOrleans", "NewYork", "Philadelphia",
             "Phoenix", "Pittsburgh", "StLouis", "SanFrancisco", "Seattle", "Tampa",
             "Washington"]


def nome(i):
    return NOMES_CAB[i] if USAR_NOMES else str(i)


def matriz_txt(M, Z_ref, hubs, n):
    cab = "     " + "".join(f"{nome(h):>8}" for h in hubs)
    linhas = [cab]
    for i in range(n):
        cel = ""
        for h in hubs:
            v = M[i][h]
            marca = "*" if (Z_ref is not None and v == 1 and Z_ref[i][h] == 0) else " "
            cel += f"{v:>7}{marca}"
        linhas.append(f"{nome(i):>4} {cel}")
    return "\n".join(linhas)


def relatorio(inst, res, rotulo, p, r, alpha, B):
    n, W = inst["n"], inst["W"]
    out = []
    cap = "sem capacidade" if B is None else f"B = {B:.0f}"
    out.append(f"=== {rotulo}: p={p} r={r} alpha={alpha} ({cap}) ===")
    out.append(f"custo = {res['custo']:.1f}   hubs = {[nome(h) for h in res['hubs']]}   "
               f"status = {res['sol_status']}")

    A = alocacao_efetiva(n, res)
    out.append("\nMatriz z devolvida pelo solver (colunas = hubs; * = alocacao sem fluxo):")
    out.append(matriz_txt(res["z"], A, res["hubs"], n))

    fantasmas = [(i, k) for i in range(n) for k in res["hubs"]
                 if res["z"][i][k] == 1 and A[i][k] == 0]
    out.append("\nAlocacao efetiva (usada pelo fluxo):")
    out.append(matriz_txt(A, None, res["hubs"], n))
    out.append(f"1s de z sem fluxo (fantasmas): "
               f"{[(nome(i), nome(k)) for i, k in fantasmas] or 'nenhum'}")

    out.append("\nCarga por hub (coleta + entrada de transferencia, como na restricao 10):")
    for h, c in res["carga_hubs"].items():
        uso = "" if B is None else f"  ({100 * c / B:.0f}% de B)"
        out.append(f"  hub {nome(h)}: {c:.0f}{uso}")

    out.append("\nRotas (i -> k -> l -> j : fracao do fluxo w_ij):")
    rotas = {}
    for (i, j, k, l), f in sorted(res["x"].items()):
        rotas.setdefault((i, j), []).append((k, l, f))
    n_div = 0
    for (i, j), lst in rotas.items():
        if len(lst) > 1:
            n_div += 1
        partes = []
        for k, l, f in lst:
            nos = [i, k, l, j]
            nos = [v for t, v in enumerate(nos) if t == 0 or v != nos[t - 1]]  # tira repetidos
            caminho = "->".join(nome(v) for v in nos)
            partes.append(f"{caminho} ({f:.2f})")
        out.append(f"  w={W[i][j]:>8.0f}  " + " | ".join(partes))
    out.append(f"Pares com fluxo dividido entre rotas: {n_div} de {len(rotas)}")
    return "\n".join(out)


def main():
    os.makedirs(os.path.join(SAIDA, "dot"), exist_ok=True)
    inst = carregar_instancia(ARQUIVO, n_sub=N_SUB)
    blocos = []
    for rotulo, p, r, alpha, folga in CASOS:
        B = None if folga is None else capacidade_uniforme(inst, p, folga)
        res = resolver(inst, p=p, r=r, alpha=alpha, B=B, tempo_max=TEMPO_MAX)
        if res["custo"] is None:
            msg = f"=== {rotulo}: sem solucao ({res['status']}) ==="
            print(msg)
            blocos.append(msg)
            continue
        txt = relatorio(inst, res, rotulo, p, r, alpha, B)
        blocos.append(txt)
        print(txt.split("\nRotas")[0])
        print("  (rotas completas no arquivo .txt)\n")
        exportar_dot(inst, res, os.path.join(SAIDA, "dot", f"exp4_{rotulo}.dot"))

    caminho = os.path.join(SAIDA, "exp4_estrutura.txt")
    with open(caminho, "w") as f:
        f.write("\n\n".join(blocos))
    print("Salvo em", caminho, "e", os.path.join(SAIDA, "dot"))


if __name__ == "__main__":
    main()
