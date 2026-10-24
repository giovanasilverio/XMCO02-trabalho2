"""Experimento 4: estrutura das soluções."""

import os

from crap_hmp import (
    carregar_instancia,
    resolver,
    exportar_dot,
    alocacao_efetiva
)

from exp3_alpha import configurar_capacidade



ARQUIVO = "dummy_instances/dummy/toy1.txt"
N_SUB = None

TEMPO_MAX = 120
SAIDA = "resultados"

# (nome, p, r, alpha, capacidade)
# None: sem capacidade.
# "arquivo": capacidades originais.
# Número: fator de folga para capacidade uniforme.
CASOS = [
    ("r1_a06_arquivo", 2, 1, 0.6, "arquivo"),
    ("r2_a06_arquivo", 2, 2, 0.6, "arquivo"),
    ("r2_a02_arquivo", 2, 2, 0.2, "arquivo"),
    ("r2_a06_folga12", 2, 2, 0.6, 1.2),
    ("r2_a06_livre",   2, 2, 0.6, None)
]


def matriz_txt(matriz, hubs, referencia=None):
    linhas = [
        "nó   " + "".join(f"{hub:>10}" for hub in hubs)
    ]

    for i, linha in enumerate(matriz):
        celulas = []

        for hub in hubs:
            valor = int(linha[hub] > 0.5)
            marca = " "

            if (
                referencia is not None
                and valor == 1
                and referencia[i][hub] == 0
            ):
                marca = "*"

            celulas.append(f"{valor:>9}{marca}")

        linhas.append(f"{i:>4} " + "".join(celulas))

    return "\n".join(linhas)


def relatorio(inst, res, rotulo, p, r, alpha):
    linhas = [
        f"=== {rotulo}: p={p}, r={r}, alpha={alpha} ===",
        (
            f"Instância: {os.path.basename(ARQUIVO)}; "
            f"n={inst['n']}; original={inst['n_original']}"
        ),
        (
            f"Status: {res['status']}; "
            f"solução: {res['sol_status']}"
        ),
        f"Tempo: {res['tempo_s']:.3f} segundos"
    ]

    if not res["tem_solucao"]:
        if res["status"] == "Infeasible":
            linhas.append("O solver declarou o cenário inviável.")
        else:
            linhas.append(
                "Nenhuma solução inteira disponível. "
                "Isso não comprova inviabilidade."
            )

        return "\n".join(linhas)

    linhas.extend([
        f"Custo: {res['custo']:.8f}",
        f"Hubs: {res['hubs']}",
        f"Ótimo comprovado: {res['otimo']}",
        f"Solução válida: {res['valida']}"
    ])

    if not res["valida"]:
        linhas.extend(res["erros_validacao"])
        return "\n".join(linhas)

    A = alocacao_efetiva(inst["n"], res)

    linhas.append(
        "\nMatriz z "
        "(* = alocação sem fluxo acima da tolerância):"
    )

    linhas.append(
        matriz_txt(res["z"], res["hubs"], referencia=A)
    )

    linhas.append(
        "\nAlocação efetivamente usada por frações > 1e-6:"
    )

    linhas.append(matriz_txt(A, res["hubs"]))

    linhas.append(
        "A diagonal efetiva só é marcada quando usada pelo fluxo. "
        "Os hubs são identificados separadamente."
    )

    linhas.append(
        "\nCargas: coleta + entrada de transferência. "
        "Quando k=l, o fluxo é contado uma única vez."
    )

    for hub, carga in res["carga_hubs"].items():
        if res["sem_capacidade"]:
            detalhe = "sem limite"
        else:
            capacidade = res["capacidades"][hub]

            if capacidade > 0:
                utilizacao = 100 * carga / capacidade

                detalhe = (
                    f"B={capacidade:.8f}; "
                    f"utilização={utilizacao:.2f}%"
                )
            else:
                detalhe = "B=0"

        linhas.append(
            f"Hub {hub}: carga={carga:.8f}; {detalhe}"
        )

    linhas.append(
        "\nRotas de demandas positivas "
        "(i -> k -> l -> j; fração x):"
    )

    rotas = {}

    for (i, j, k, l), fracao in sorted(res["x"].items()):
        if fracao > 1e-6:
            rotas.setdefault((i, j), []).append(
                (k, l, fracao)
            )

    for (i, j), lista in rotas.items():
        partes = []

        for k, l, fracao in lista:
            partes.append(
                f"{i}->{k}->{l}->{j}: x={fracao:.8f}"
            )

        linhas.append(
            f"w[{i},{j}]={inst['W'][i][j]:.8f}: "
            + " | ".join(partes)
        )

    divididos = sum(
        len(lista) > 1
        for lista in rotas.values()
    )

    linhas.append(
        f"Pares com fluxo dividido: {divididos} de {len(rotas)}"
    )

    return "\n".join(linhas)


def main():
    os.makedirs(SAIDA, exist_ok=True)

    inst = carregar_instancia(ARQUIVO, n_sub=N_SUB)

    caminho_txt = os.path.join(SAIDA, "exp4_estrutura.txt")

    with open(caminho_txt, "w", encoding="utf-8") as arquivo:
        for rotulo, p, r, alpha, folga in CASOS:
            B, sem_capacidade, _ = configurar_capacidade(
                inst, p, folga
            )

            res = resolver(
                inst,
                p=p,
                r=r,
                alpha=alpha,
                B=B,
                tempo_max=TEMPO_MAX,
                sem_capacidade=sem_capacidade
            )

            texto = relatorio(inst, res, rotulo, p, r, alpha)

            arquivo.write(texto + "\n\n")
            arquivo.flush()

            # As rotas completas ficam no relatório.
            print(texto.split("\nRotas")[0])
            print()

            if res["tem_solucao"] and res["valida"]:
                exportar_dot(
                    inst,
                    res,
                    os.path.join(
                        SAIDA,
                        "dot",
                        f"exp4_{rotulo}.dot"
                    )
                )

    print("Salvo em", caminho_txt)


if __name__ == "__main__":
    main()