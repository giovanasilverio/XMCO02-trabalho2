"""Experimento 2: efeito do aperto das capacidades dos hubs."""

import csv
import os

from crap_hmp import (
    carregar_instancia,
    resolver,
    capacidade_uniforme,
    alocacao_efetiva,
    exportar_dot,
)


ARQUIVO = "dummy_instances/dummy/toy1.txt"
N_SUB = None

P = 2
R = 2
ALPHA = 0.6

# Valores relativos a demanda total / P.
# Folga alta representa capacidade mais relaxada; baixa, capacidade apertada.
FOLGAS = [2.0, 1.5, 1.2, 1.0, 0.8, 0.6]
INCLUIR_SEM_CAPACIDADE = True
TEMPO_MAX = 120
SAIDA = "resultados"


def main():
    os.makedirs(SAIDA, exist_ok=True)
    inst = carregar_instancia(ARQUIVO, n_sub=N_SUB)
    cenarios = []
    if INCLUIR_SEM_CAPACIDADE:
        cenarios.append(("sem_capacidade", None, True))
    if inst["B"] is not None:
        cenarios.append(("capacidades_arquivo", inst["B"], False))
    cenarios.extend(
        (f"folga_{folga}", capacidade_uniforme(inst, P, folga), False)
        for folga in FOLGAS
    )

    campos = [
        "instancia", "n_original", "n", "p", "r", "alpha",
        "cenario_capacidade", "capacidades", "status", "sol_status",
        "tem_solucao", "otimo", "valida", "custo", "hubs",
        "cargas_hubs", "utilizacao_hubs_pct", "utilizacao_max_pct", "hubs_com_capacidade_ativa",
        "nos_multi_hub", "tempo_s", "erros_validacao",
    ]
    caminho_csv = os.path.join(SAIDA, "exp2_capacidade2.csv")
    with open(caminho_csv, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        for rotulo, B, sem_capacidade in cenarios:
            res = resolver(
                inst, p=P, r=R, alpha=ALPHA, B=B,
                tempo_max=TEMPO_MAX, sem_capacidade=sem_capacidade,
            )
            linha = dict.fromkeys(campos, "")
            linha.update({
                "instancia": os.path.basename(ARQUIVO),
                "n_original": inst["n_original"], "n": inst["n"],
                "p": P, "r": R, "alpha": ALPHA,
                "cenario_capacidade": rotulo,
                "capacidades": res["capacidades"],
                "status": res["status"], "sol_status": res["sol_status"],
                "tem_solucao": res["tem_solucao"], "otimo": res["otimo"],
                "valida": res["valida"], "custo": res["custo"],
                "tempo_s": res["tempo_s"],
                "erros_validacao": "; ".join(res["erros_validacao"]),
            })
            if res["tem_solucao"] and res["valida"]:
                A = alocacao_efetiva(inst["n"], res)
                cargas = res["carga_hubs"]
                capacidades = res["capacidades"]
                utilizacoes = {
                    k: (100 * cargas[k] / capacidades[k]
                        if capacidades is not None and capacidades[k] > 0 else None)
                    for k in res["hubs"]
                }
                ativos = [
                    k for k in res["hubs"]
                    if capacidades is not None and capacidades[k] > 0
                    and cargas[k] >= capacidades[k] - 1e-6 * max(1.0, abs(capacidades[k]))
                ]
                nos_multi = sum(
                    sum(A[i]) > 1
                    for i in range(inst["n"])
                    if i not in res["hubs"]
                )
                linha.update({
                    "hubs": " ".join(map(str, res["hubs"])),
                    "cargas_hubs": "; ".join(
                        f"{k}:{cargas[k]:.8f}" for k in res["hubs"]
                    ),
                    "utilizacao_hubs_pct": "; ".join(
                        f"{k}:{v:.2f}%" for k, v in utilizacoes.items()
                        if v is not None
                    ),
                    "utilizacao_max_pct": (
                        max((v for v in utilizacoes.values() if v is not None), default="")
                    ),
                    "hubs_com_capacidade_ativa": " ".join(map(str, ativos)),
                    "nos_multi_hub": nos_multi,
                })
                exportar_dot(
                    inst, res,
                    os.path.join(SAIDA, "dot", f"exp2_capacidade2_{rotulo}.dot"),
                )
            escritor.writerow(linha)
            arquivo.flush()
            print(
                f"capacidade={rotulo}: custo={res['custo']} "
                f"[{res['sol_status']}] valida={res['valida']}"
            )
    print("\nSalvo em", caminho_csv)


if __name__ == "__main__":
    main()

