
# Bot de controle financeiro

entradas = []
despesas = []

while True:
    print("\n=== BOT FINANCEIRO ===")
    print("1 - Registrar entrada")
    print("2 - Registrar despesa")
    print("3 - Ver resumo")
    print("4 - Sair")

    opcao = input("Escolha uma opção: ")

    if opcao == "1":
        valor = float(input("Valor recebido: R$ "))
        entradas.append(valor)
        print("Entrada registrada!")

    elif opcao == "2":
        valor = float(input("Valor da despesa: R$ "))
        despesas.append(valor)
        print("Despesa registrada!")

    elif opcao == "3":
        total_entradas = sum(entradas)
        total_despesas = sum(despesas)
        saldo = total_entradas - total_despesas

        print("\n=== RESUMO FINANCEIRO ===")
        print(f"Total recebido: R$ {total_entradas:.2f}")
        print(f"Total de despesas: R$ {total_despesas:.2f}")
        print(f"Saldo atual: R$ {saldo:.2f}")

    elif opcao == "4":
        print("Bot encerrado!")
        break

    else:
        print("Opção inválida!")
