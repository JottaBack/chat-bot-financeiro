
import csv
import sqlite3
from datetime import date, datetime
from pathlib import Path


def pedir_mes(formato="%m-%Y"):
    exemplo = "10-2026" if formato == "%m-%Y" else "2026-10"
    while True:
        mes_informado = input(f"Digite o mês no formato {exemplo}: ").strip()
        try:
            mes = datetime.strptime(mes_informado, formato)
            if len(mes_informado) == 7:
                return mes.strftime("%Y-%m")
        except ValueError:
            pass
        print(f"Mês inválido. Use o formato {exemplo}.")


def obter_resumo_mes(mes):
    cursor.execute("""
        SELECT tipo, SUM(valor)
        FROM movimentacoes
        WHERE substr(data, 1, 7) = ?
        GROUP BY tipo
    """, (mes,))
    resultados = dict(cursor.fetchall())
    entradas = resultados.get("entrada", 0) or 0
    despesas = resultados.get("despesa", 0) or 0
    return entradas, despesas, entradas - despesas


# Conectar ao banco de dados
CAMINHO_BANCO = Path(__file__).resolve().parent / "financeiro.db"
conexao = sqlite3.connect(CAMINHO_BANCO)
cursor = conexao.cursor()

# Criar a tabela, caso ela não exista
cursor.execute("""
    CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL,
        valor REAL NOT NULL,
        data DATE DEFAULT CURRENT_DATE
    )
""")

conexao.commit()

while True:
    print("\n=== BOT FINANCEIRO ===")
    print("1 - Registrar entrada")
    print("2 - Registrar despesa")
    print("3 - Ver resumo")
    print("4 - Sair")
    print("5 - Ver movimentações")
    print("6 - Ver relatório mensal")
    print("7 - Comparar meses")
    print("8 - Exportar relatório mensal para CSV")

    opcao = input("Escolha uma opção: ")

    if opcao in ("1", "2"):
        try:
            valor = float(
                input("Digite o valor: R$ ").replace(",", ".")
            )

            if valor <= 0:
                print("Digite um valor maior que zero.")
                continue

            tipo = "entrada" if opcao == "1" else "despesa"
            data_movimentacao = date.today().isoformat()

            cursor.execute(
                "INSERT INTO movimentacoes (tipo, valor, data) VALUES (?, ?, ?)",
                (tipo, valor, data_movimentacao)
            )
            conexao.commit()

            print("Movimentação salva com sucesso!")
            cursor.execute("""
                SELECT COALESCE(SUM(
                    CASE
                        WHEN tipo = 'entrada' THEN valor
                        WHEN tipo = 'despesa' THEN -valor
                        ELSE 0
                    END
                ), 0)
                FROM movimentacoes
            """)
            saldo_atual = cursor.fetchone()[0]
            print(f"Saldo atual: R$ {saldo_atual:.2f}")

        except ValueError:
            print("Valor inválido. Tente novamente.")

    elif opcao == "3":
        cursor.execute("""
            SELECT
                tipo,
                SUM(valor)
            FROM movimentacoes
            GROUP BY tipo
        """)

        resultados = dict(cursor.fetchall())

        entradas = resultados.get("entrada", 0) or 0
        despesas = resultados.get("despesa", 0) or 0
        saldo = entradas - despesas

        print("\n=== RESUMO FINANCEIRO ===")
        print(f"Total de entradas: R$ {entradas:.2f}")
        print(f"Total de despesas: R$ {despesas:.2f}")
        print(f"Saldo: R$ {saldo:.2f}")

    elif opcao == "5":
        cursor.execute("""
            SELECT tipo, valor, data
            FROM movimentacoes
            ORDER BY data DESC, id DESC
        """)
        movimentacoes = cursor.fetchall()

        print("\n=== MOVIMENTAÇÕES ===")
        if not movimentacoes:
            print("Nenhuma movimentação registrada.")
        else:
            for tipo, valor, data_registro in movimentacoes:
                data_formatada = datetime.strptime(
                    data_registro, "%Y-%m-%d"
                ).strftime("%d/%m/%Y")
                print(
                    f"{tipo.capitalize()}: R$ {valor:.2f} - "
                    f"Data: {data_formatada} (mês/ano: "
                    f"{data_registro[5:7]}/{data_registro[:4]})"
                )

    elif opcao == "6":
        mes = pedir_mes()
        entradas, despesas, saldo = obter_resumo_mes(mes)
        mes_exibicao = datetime.strptime(mes, "%Y-%m").strftime("%m-%Y")
        print(f"\n=== RELATÓRIO DE {mes_exibicao} ===")
        print(f"Total recebido: R$ {entradas:.2f}")
        print(f"Total gasto: R$ {despesas:.2f}")
        print(f"Saldo do mês: R$ {saldo:.2f}")

    elif opcao == "7":
        cursor.execute("""
            SELECT substr(data, 1, 7), tipo, SUM(valor)
            FROM movimentacoes
            GROUP BY substr(data, 1, 7), tipo
            ORDER BY substr(data, 1, 7)
        """)
        totais_por_mes = {}
        for mes, tipo, total in cursor.fetchall():
            totais_por_mes.setdefault(mes, {"entrada": 0, "despesa": 0})
            totais_por_mes[mes][tipo] = total

        print("\n=== COMPARAÇÃO ENTRE MESES ===")
        if not totais_por_mes:
            print("Nenhuma movimentação registrada.")
        else:
            for mes, totais in totais_por_mes.items():
                entradas = totais["entrada"]
                despesas = totais["despesa"]
                print(
                    f"{mes}: recebido R$ {entradas:.2f} | "
                    f"gasto R$ {despesas:.2f} | "
                    f"saldo R$ {entradas - despesas:.2f}"
                )

    elif opcao == "8":
        mes = pedir_mes("%Y-%m")
        cursor.execute("""
            SELECT data, tipo, valor
            FROM movimentacoes
            WHERE substr(data, 1, 7) = ?
            ORDER BY data, id
        """, (mes,))
        movimentacoes = cursor.fetchall()
        entradas, despesas, saldo = obter_resumo_mes(mes)
        nome_padrao = f"relatorio_financeiro_{mes}.csv"
        nome_arquivo = input(
            f"Nome do arquivo [{nome_padrao}]: "
        ).strip() or nome_padrao

        try:
            with open(nome_arquivo, "w", newline="", encoding="utf-8-sig") as arquivo:
                escritor = csv.writer(arquivo, delimiter=";")
                escritor.writerow(["Data", "Tipo", "Valor (R$)"])
                for data_registro, tipo, valor in movimentacoes:
                    escritor.writerow([data_registro, tipo, f"{valor:.2f}"])
                escritor.writerow([])
                escritor.writerow(["Resumo do mês", mes])
                escritor.writerow(["Total recebido", f"{entradas:.2f}"])
                escritor.writerow(["Total gasto", f"{despesas:.2f}"])
                escritor.writerow(["Saldo do mês", f"{saldo:.2f}"])
            print(f"Relatório exportado para: {nome_arquivo}")
        except OSError as erro:
            print(f"Não foi possível exportar o relatório: {erro}")

    elif opcao == "4":
        print("Até mais!")
        break

    else:
        print("Opção inválida!")

conexao.close()
