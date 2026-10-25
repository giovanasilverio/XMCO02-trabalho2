"""Experimento 1: efeito do numero de alocaçoes r."""

import csv
import os

from crap_hmp import (
    carregar_instancia,
    resolver,
    alocacao_efetiva,
    exportar_dot,
)
from exp3_alpha import configurar_capacidade


ARQUIVO = "dummy_instances/dummy/toy1.txt"
N_SUB = None

# Compara alocaçao simples (r=1), intermediaria e multipla (r=p).
P_VALORES = [2, 3]
ALPHAS = [0.6]
FOLGAS = [None, "arquivo", 1.2, 2.0]
TEMPO_MAX = 120
SAIDA = "resultados"


def contar_estrutura(inst, res):
    A = alocacao_efetiva(inst["n"], res)
    nos_multi = sum(
        sum(A[i]) > 1
        for i in range(inst["n"])
        if i not in res["hubs"]
    )
    rotas_2hubs = sum(
        inst["W"][i][j] * fracao
        for (i, j, k, l), fracao in res["x"].items()
        if k != l
    )
    fluxo_total = sum(map(sum, inst["W"]))
    pct_2hubs = 100 * rotas_2hubs / fluxo_total if fluxo_total else 0.0
    return nos_multi, pct_2hubs


def main():
    os.makedirs(SAIDA, exist_ok=True)
    inst = carregar_instancia(ARQUIVO, n_sub=N_SUB)
    campos = [
        "instancia", "n_original", "n", "p", "r", "alpha",
        "cenario_capacidade", "capacidades", "status", "sol_status",
        "tem_solucao", "otimo", "valida", "custo", "hubs",
        "nos_multi_hub", "pct_fluxo_2hubs", "tempo_s", "erros_validacao",
    ]
    caminho_csv = os.path.join(SAIDA, "exp1_alocacao.csv")
    with open(caminho_csv, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        for folga in FOLGAS:
            for p in P_VALORES:
                for r in range(1, p + 1):
                    for alpha in ALPHAS:
                        B, sem_capacidade, rotulo = configurar_capacidade(inst, p, folga)
                        res = resolver(
                            inst, p=p, r=r, alpha=alpha, B=B,
                            tempo_max=TEMPO_MAX, sem_capacidade=sem_capacidade,
                        )
                        linha = dict.fromkeys(campos, "")
                        linha.update({
                            "instancia": os.path.basename(ARQUIVO),
                            "n_original": inst["n_original"], "n": inst["n"],
                            "p": p, "r": r, "alpha": alpha,
                            "cenario_capacidade": rotulo,
                            "capacidades": res["capacidades"],
                            "status": res["status"], "sol_status": res["sol_status"],
                            "tem_solucao": res["tem_solucao"], "otimo": res["otimo"],
                            "valida": res["valida"], "custo": res["custo"],
                            "tempo_s": res["tempo_s"],
                            "erros_validacao": "; ".join(res["erros_validacao"]),
                        })
                        if res["tem_solucao"] and res["valida"]:
                            nos_multi, pct_2hubs = contar_estrutura(inst, res)
                            linha.update({
                                "hubs": " ".join(map(str, res["hubs"])),
                                "nos_multi_hub": nos_multi,
                                "pct_fluxo_2hubs": pct_2hubs,
                            })
                            if r in (1, p):
                                exportar_dot(
                                    inst, res,
                                    os.path.join(SAIDA, "dot", f"exp1_p{p}_r{r}_{rotulo}.dot"),
                                )
                        escritor.writerow(linha)
                        arquivo.flush()
                        print(
                            f"p={p} r={r} alpha={alpha} capacidade={rotulo}: "
                            f"custo={res['custo']} [{res['sol_status']}] valida={res['valida']}"
                        )
    print("\nSalvo em", caminho_csv)


if __name__ == "__main__":
    main()

