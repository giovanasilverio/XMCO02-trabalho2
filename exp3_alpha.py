"""Experimento 3: efeito do desconto alpha."""

import csv
import os

from crap_hmp import (
    carregar_instancia,
    resolver,
    capacidade_uniforme,
    alocacao_efetiva,
    exportar_dot
)

ARQUIVO = "dummy_instances/dummy/toy1.txt"
N_SUB = None

ALPHAS = [0.2, 0.4, 0.6, 0.8, 1.0]
CONFIGS = [(2, 1), (2, 2)]  # (p, r)

# None: comparação sem capacidade.
# "arquivo": capacidades lidas da instância.
# Número: capacidade uniforme = folga * demanda_total / p.
FOLGAS = [None, "arquivo", 1.2, 2.0]

TEMPO_MAX = 120
SAIDA = "resultados"


def decompor_custo(inst, res, alpha, lam=1.0, delta=1.0):
    coleta = 0.0
    transferencia = 0.0
    distribuicao = 0.0

    for (i, j, k, l), fracao in res["x"].items():
        fluxo = inst["W"][i][j] * fracao

        coleta += fluxo * lam * inst["D"][i][k]
        transferencia += fluxo * alpha * inst["D"][k][l]
        distribuicao += fluxo * delta * inst["D"][l][j]

    return coleta, transferencia, distribuicao


def consolidacao(inst, res):
    total = 0.0
    dois_hubs = 0.0
    ligacoes = set()

    for (i, j, k, l), fracao in res["x"].items():
        fluxo = inst["W"][i][j] * fracao
        total += fluxo

        if k != l:
            dois_hubs += fluxo

            if fracao > 1e-6:
                ligacoes.add((k, l))

    percentual = dois_hubs / total if total > 0 else 0.0

    return percentual, len(ligacoes)


def configurar_capacidade(inst, p, folga):
    if folga is None:
        return None, True, "sem_capacidade"

    if folga == "arquivo":
        if inst["B"] is None:
            raise ValueError(
                "A instância não possui capacidades. "
                "Retire 'arquivo' de FOLGAS/CASOS "
                "e use uma folga numérica."
            )

        return inst["B"], False, "arquivo"

    capacidade = capacidade_uniforme(inst, p, folga)

    return capacidade, False, f"folga_{folga}"


def main():
    os.makedirs(SAIDA, exist_ok=True)

    inst = carregar_instancia(ARQUIVO, n_sub=N_SUB)

    campos = [
        "instancia",
        "n_original",
        "n",
        "p",
        "r",
        "alpha",
        "cenario_capacidade",
        "capacidades",
        "status",
        "sol_status",
        "tem_solucao",
        "otimo",
        "valida",
        "custo",
        "coleta",
        "transferencia",
        "distribuicao",
        "pct_fluxo_2hubs",
        "ligacoes_hub_hub",
        "hubs",
        "nos_multi_hub",
        "tempo_s",
        "erros_validacao"
    ]

    caminho_csv = os.path.join(SAIDA, "exp3_alpha.csv")

    with open(
        caminho_csv,
        "w",
        newline="",
        encoding="utf-8"
    ) as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()

        for folga in FOLGAS:
            for p, r in CONFIGS:
                B, sem_capacidade, rotulo = configurar_capacidade(
                    inst, p, folga
                )

                for alpha in ALPHAS:
                    res = resolver(
                        inst,
                        p=p,
                        r=r,
                        alpha=alpha,
                        B=B,
                        tempo_max=TEMPO_MAX,
                        sem_capacidade=sem_capacidade
                    )

                    linha = dict.fromkeys(campos, "")

                    linha.update({
                        "instancia": os.path.basename(ARQUIVO),
                        "n_original": inst["n_original"],
                        "n": inst["n"],
                        "p": p,
                        "r": r,
                        "alpha": alpha,
                        "cenario_capacidade": rotulo,
                        "capacidades": res["capacidades"],
                        "status": res["status"],
                        "sol_status": res["sol_status"],
                        "tem_solucao": res["tem_solucao"],
                        "otimo": res["otimo"],
                        "valida": res["valida"],
                        "custo": res["custo"],
                        "tempo_s": res["tempo_s"],
                        "erros_validacao": "; ".join(
                            res["erros_validacao"]
                        )
                    })

                    if res["tem_solucao"] and res["valida"]:
                        coleta, transferencia, distribuicao = (
                            decompor_custo(inst, res, alpha)
                        )

                        percentual, ligacoes = consolidacao(inst, res)

                        A = alocacao_efetiva(inst["n"], res)

                        nos_multi = sum(
                            sum(A[i]) > 1
                            for i in range(inst["n"])
                            if i not in res["hubs"]
                        )

                        linha.update({
                            "coleta": coleta,
                            "transferencia": transferencia,
                            "distribuicao": distribuicao,
                            "pct_fluxo_2hubs": 100 * percentual,
                            "ligacoes_hub_hub": ligacoes,
                            "hubs": " ".join(map(str, res["hubs"])),
                            "nos_multi_hub": nos_multi
                        })

                        if alpha in (min(ALPHAS), max(ALPHAS)):
                            nome_dot = (
                                f"exp3_p{p}_r{r}_"
                                f"a{alpha}_{rotulo}.dot"
                            )

                            exportar_dot(
                                inst,
                                res,
                                os.path.join(SAIDA, "dot", nome_dot)
                            )

                    # Registra também cenários sem solução ou inválidos.
                    escritor.writerow(linha)
                    arquivo.flush()

                    print(
                        f"p={p} r={r} alpha={alpha} "
                        f"capacidade={rotulo}: "
                        f"custo={res['custo']} "
                        f"[{res['sol_status']}] "
                        f"válida={res['valida']}"
                    )

    print("\nSalvo em", caminho_csv)


if __name__ == "__main__":
    main()