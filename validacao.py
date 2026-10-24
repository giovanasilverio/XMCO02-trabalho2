from math import isfinite

TOL = 1e-6


def validar_solucao(dados, resultado, p, r, capacidades=None):
    """
    resultado = {
        "z": {(i, k): valor, ...},
        "x": {(i, j, k, l): valor, ...}
    }

    Os índices vão de 0 até n - 1.
    Retorna: (valido, lista_de_erros).
    Verifica viabilidade, não garante otimalidade.
    """
    n = dados["n"]
    demandas = dados["demandas"]
    nos = range(n)
    erros = []

    if not isinstance(p, int) or not 1 <= p <= n:
        return False, ["p deve ser inteiro e estar entre 1 e n."]

    if not isinstance(r, int) or not 1 <= r <= p:
        return False, ["r deve ser inteiro e estar entre 1 e p."]

    if capacidades is None:
        capacidades = dados.get("capacidades")

    if capacidades is None:
        return False, ["As capacidades precisam ser informadas."]

    if len(capacidades) != n:
        return False, [f"Devem existir {n} capacidades."]

    for k in nos:
        valor = capacidades[k]
        if not isinstance(valor, (int, float)):
            erros.append(f"Capacidade do nó {k} não é numérica.")
        elif not isfinite(valor) or valor < 0:
            erros.append(f"Capacidade do nó {k} é inválida.")

    if erros:
        return False, erros

    z = resultado.get("z")
    x = resultado.get("x")

    if not isinstance(z, dict) or not isinstance(x, dict):
        return False, ["O resultado deve conter os dicionários z e x."]

    # Verifica índices e valores antes de realizar as somas.
    for nome, variaveis, tamanho in (("z", z, 2), ("x", x, 4)):
        for chave, valor in variaveis.items():
            if (
                not isinstance(chave, tuple)
                or len(chave) != tamanho
                or any(
                    not isinstance(indice, int) or indice not in nos
                    for indice in chave
                )
            ):
                erros.append(f"Índice inválido em {nome}: {chave}.")
                continue

            if not isinstance(valor, (int, float)):
                erros.append(f"{nome}{chave} não possui valor numérico.")
            elif not isfinite(valor):
                erros.append(f"{nome}{chave} possui valor não finito.")

    if erros:
        return False, erros

    # (11): z deve ser binária.
    for chave, valor in z.items():
        if min(abs(valor), abs(valor - 1)) > TOL:
            erros.append(f"z{chave} = {valor} não é binária.")

    # (12): x deve estar entre 0 e 1.
    for chave, valor in x.items():
        if valor < -TOL or valor > 1 + TOL:
            erros.append(f"x{chave} = {valor} está fora de [0, 1].")

    # (4): exatamente p hubs abertos.
    total_hubs = sum(z.get((k, k), 0.0) for k in nos)

    if abs(total_hubs - p) > TOL:
        erros.append(
            f"Quantidade de hubs incorreta: {total_hubs}; esperado: {p}."
        )

    # (5): um nó só pode ser alocado a um hub aberto.
    for i in nos:
        for k in nos:
            if z.get((i, k), 0.0) > z.get((k, k), 0.0) + TOL:
                erros.append(
                    f"Nó {i} alocado ao nó {k}, que não está aberto como hub."
                )

    # (6): cada nó pode ser alocado a no máximo r hubs.
    for i in nos:
        total = sum(z.get((i, k), 0.0) for k in nos)

        if total > r + TOL:
            erros.append(
                f"Nó {i} possui {total} alocações; limite: {r}."
            )

    # Acumula os fluxos para verificar (7), (8), (9) e (10).
    total_rotas = {}
    saidas = {}
    entradas = {}
    cargas = [0.0] * n

    for (i, j, k, l), valor in x.items():
        total_rotas[(i, j)] = total_rotas.get((i, j), 0.0) + valor
        saidas[(i, j, k)] = saidas.get((i, j, k), 0.0) + valor
        entradas[(i, j, l)] = entradas.get((i, j, l), 0.0) + valor

        fluxo = demandas[i][j] * valor
        cargas[k] += fluxo

        # Se os dois hubs forem iguais, conta o fluxo apenas uma vez.
        if l != k:
            cargas[l] += fluxo

    for i in nos:
        for j in nos:
            # (7): todo o fluxo deve ser roteado.
            total = total_rotas.get((i, j), 0.0)

            if abs(total - 1.0) > TOL:
                erros.append(
                    f"Par ({i}, {j}): soma das frações = {total}; esperado: 1."
                )

            for k in nos:
                # (8): primeiro hub deve estar ligado à origem.
                if (
                    saidas.get((i, j, k), 0.0)
                    > z.get((i, k), 0.0) + TOL
                ):
                    erros.append(
                        f"Par ({i}, {j}): saída pelo hub {k} "
                        f"viola a alocação da origem."
                    )

                # (9): segundo hub deve estar ligado ao destino.
                if (
                    entradas.get((i, j, k), 0.0)
                    > z.get((j, k), 0.0) + TOL
                ):
                    erros.append(
                        f"Par ({i}, {j}): chegada pelo hub {k} "
                        f"viola a alocação do destino."
                    )

    # (10): capacidade de cada hub.
    for k in nos:
        limite = capacidades[k] * z.get((k, k), 0.0)

        if cargas[k] > limite + TOL:
            erros.append(
                f"Hub {k}: carga {cargas[k]:.6f} "
                f"excede o limite {limite:.6f}."
            )

    return len(erros) == 0, erros