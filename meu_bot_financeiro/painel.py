import sqlite3
from pathlib import Path
from datetime import date

import pandas as pd
import streamlit as st

# =====================================
# 1. CONFIGURACAO
# =====================================

st.set_page_config(
    page_title="Meu Financeiro",
    page_icon="💰",
    layout="wide"
)

BANCO = Path(__file__).resolve().parent / "financeiro.db"

CATEGORIAS_ENTRADA = [
    "Salário",
    "Serviços",
    "Vendas",
    "Investimentos",
    "Presente",
    "Outros"
]

CATEGORIAS_DESPESA = [
    "Alimentação",
    "Transporte",
    "Moradia",
    "Saúde",
    "Educação",
    "Lazer",
    "Contas",
    "Compras",
    "Outros"
]

st.title("💰 Meu Painel Financeiro")
st.caption("Controle suas entradas, despesas e categorias.")

# =====================================
# 2. VERIFICAR O BANCO EXISTENTE
# =====================================

if not BANCO.is_file():
    st.error(
        f"Banco não encontrado: {BANCO}\n\n"
        "Confira se financeiro.db está na pasta do painel."
    )
    st.stop()

conexao = sqlite3.connect(BANCO)

try:
    tabela = conexao.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'movimentacoes'
    """).fetchone()

    if tabela is None:
        st.error("Tabela movimentacoes não encontrada.")
        st.stop()

    colunas = {
        coluna[1]
        for coluna in conexao.execute(
            "PRAGMA table_info(movimentacoes)"
        ).fetchall()
    }

    # Adiciona categoria sem apagar os registros antigos
    if "categoria" not in colunas:
        conexao.execute("""
            ALTER TABLE movimentacoes
            ADD COLUMN categoria TEXT
            NOT NULL DEFAULT 'Não categorizado'
        """)
        conexao.commit()

finally:
    conexao.close()

# =====================================
# 3. CADASTRAR MOVIMENTACOES
# =====================================

st.subheader("➕ Nova movimentação")

tipo = st.selectbox(
    "Tipo de movimentação",
    ["entrada", "despesa"],
    format_func=lambda x: (
        "Entrada" if x == "entrada" else "Despesa"
    ),
    key="novo_tipo"
)

if tipo == "entrada":
    categorias = CATEGORIAS_ENTRADA
else:
    categorias = CATEGORIAS_DESPESA

categoria = st.selectbox(
    "Categoria",
    categorias,
    key="nova_categoria"
)

col1, col2 = st.columns(2)

with col1:
    valor = st.number_input(
        "Valor (R$)",
        min_value=0.01,
        value=10.00,
        step=10.00,
        format="%.2f",
        key="novo_valor"
    )

with col2:
    data_mov = st.date_input(
        "Data da movimentação",
        value=date.today(),
        key="nova_data"
    )

if st.button("Salvar movimentação", type="primary"):
    conexao = sqlite3.connect(BANCO)

    try:
        conexao.execute("""
            INSERT INTO movimentacoes
                (tipo, valor, data, categoria)
            VALUES (?, ?, ?, ?)
        """, (
            tipo,
            valor,
            data_mov.isoformat(),
            categoria
        ))

        conexao.commit()

    finally:
        conexao.close()

    st.success("Movimentação salva com sucesso!")
    st.rerun()

st.divider()

# =====================================
# 4. CARREGAR OS REGISTROS
# =====================================

conexao = sqlite3.connect(BANCO)

try:
    df = pd.read_sql_query("""
        SELECT id, tipo, valor, data, categoria
        FROM movimentacoes
        ORDER BY data DESC, id DESC
    """, conexao)

finally:
    conexao.close()

df["data"] = pd.to_datetime(
    df["data"],
    errors="coerce"
)

df["valor"] = pd.to_numeric(
    df["valor"],
    errors="coerce"
).fillna(0)

df["categoria"] = (
    df["categoria"]
    .fillna("Não categorizado")
    .replace("", "Não categorizado")
)

# =====================================
# 5. FILTRO MENSAL
# =====================================

st.subheader("📅 Resumo mensal")

meses = sorted(
    df["data"]
    .dropna()
    .dt.strftime("%Y-%m")
    .unique(),
    reverse=True
)

mes_atual = date.today().strftime("%Y-%m")

if mes_atual not in meses:
    meses.insert(0, mes_atual)

mes = st.selectbox(
    "Selecione o mês",
    meses
)

df_mes = df[
    df["data"].dt.strftime("%Y-%m") == mes
].copy()

# =====================================
# 6. INDICADORES FINANCEIROS
# =====================================

entradas = df_mes.loc[
    df_mes["tipo"] == "entrada", "valor"
].sum()

despesas = df_mes.loc[
    df_mes["tipo"] == "despesa", "valor"
].sum()

saldo = entradas - despesas

col1, col2, col3 = st.columns(3)

col1.metric(
    "Total de entradas",
    f"R$ {entradas:,.2f}"
)

col2.metric(
    "Total de despesas",
    f"R$ {despesas:,.2f}"
)

col3.metric(
    "Saldo do mês",
    f"R$ {saldo:,.2f}"
)

# =====================================
# 7. GRAFICO DE DESPESAS POR CATEGORIA
# =====================================

st.subheader("📊 Despesas por categoria")

despesas_categoria = df_mes[
    df_mes["tipo"] == "despesa"
].groupby("categoria")["valor"].sum().sort_values(
    ascending=False
)

if despesas_categoria.empty:
    st.info("Não há despesas registradas neste mês.")
else:
    grafico = despesas_categoria.rename(
        "Valor (R$)"
    ).to_frame()

    st.bar_chart(grafico)

# =====================================
# 8. FILTRO E HISTORICO
# =====================================

st.subheader("📋 Histórico de movimentações")

categorias_existentes = sorted(
    df_mes["categoria"].unique().tolist()
)

opcoes_filtro = ["Todas"] + categorias_existentes

categoria_filtro = st.selectbox(
    "Filtrar histórico por categoria",
    opcoes_filtro
)

historico = df_mes.copy()

if categoria_filtro != "Todas":
    historico = historico[
        historico["categoria"] == categoria_filtro
    ]

if historico.empty:
    st.info("Nenhuma movimentação encontrada.")
else:
    historico["data"] = historico["data"].dt.strftime(
        "%d/%m/%Y"
    )

    historico["tipo"] = historico["tipo"].str.capitalize()

    historico["valor"] = historico["valor"].map(
        lambda x: f"R$ {x:,.2f}"
    )

    historico = historico.rename(columns={
        "id": "ID",
        "data": "Data",
        "tipo": "Tipo",
        "valor": "Valor",
        "categoria": "Categoria"
    })

    st.dataframe(
        historico[
            ["ID", "Data", "Tipo", "Categoria", "Valor"]
        ],
        use_container_width=True,
        hide_index=True
    )

st.caption(
    "Os registros são armazenados no banco SQLite existente."
)

# =====================================
# 9. EDITAR E EXCLUIR MOVIMENTACOES
# =====================================

st.divider()
st.subheader("🛠️ Gerenciar movimentações")

conexao = sqlite3.connect(BANCO)

try:
    registros = pd.read_sql_query("""
        SELECT id, tipo, valor, data, categoria
        FROM movimentacoes
        ORDER BY id DESC
    """, conexao)
finally:
    conexao.close()

if registros.empty:
    st.info("Não existem movimentações para editar.")
else:
    opcoes = {
        int(row["id"]): (
            f'ID {int(row["id"])} | '
            f'{row["tipo"].capitalize()} | '
            f'R$ {row["valor"]:.2f} | '
            f'{row["categoria"]}'
        )
        for _, row in registros.iterrows()
    }

    id_selecionado = st.selectbox(
        "Selecione a movimentação",
        list(opcoes.keys()),
        format_func=lambda id: opcoes[id]
    )

    registro = registros[
        registros["id"] == id_selecionado
    ].iloc[0]

    categoria_antiga = registro["categoria"]
    tipo_antigo = registro["tipo"]
    valor_antigo = float(registro["valor"])

    try:
        data_antiga = pd.to_datetime(
            registro["data"]
        ).date()
    except (ValueError, TypeError):
        data_antiga = date.today()

    st.markdown("### Editar registro")

    with st.form("form_editar"):
        novo_tipo = st.selectbox(
            "Tipo",
            ["entrada", "despesa"],
            index=(
                0 if tipo_antigo == "entrada" else 1
            ),
            format_func=lambda x: (
                "Entrada" if x == "entrada" else "Despesa"
            )
        )

        if novo_tipo == "entrada":
            categorias_edicao = CATEGORIAS_ENTRADA.copy()
        else:
            categorias_edicao = CATEGORIAS_DESPESA.copy()

        if (
            categoria_antiga not in categorias_edicao
            and categoria_antiga != "Não categorizado"
        ):
            categorias_edicao.append(categoria_antiga)

        opcoes_edicao = (
            ["Não categorizado"] + categorias_edicao
            if categoria_antiga == "Não categorizado"
            else categorias_edicao
        )

        indice_categoria = (
            opcoes_edicao.index(categoria_antiga)
            if categoria_antiga in opcoes_edicao
            else 0
        )

        nova_categoria = st.selectbox(
            "Categoria",
            opcoes_edicao,
            index=indice_categoria
        )

        novo_valor = st.number_input(
            "Valor (R$)",
            min_value=0.01,
            value=max(valor_antigo, 0.01),
            step=10.0,
            format="%.2f"
        )

        nova_data = st.date_input(
            "Data",
            value=data_antiga
        )

        salvar_edicao = st.form_submit_button(
            "Salvar alterações"
        )

    if salvar_edicao:
        conexao = sqlite3.connect(BANCO)

        try:
            conexao.execute("""
                UPDATE movimentacoes
                SET tipo = ?,
                    valor = ?,
                    data = ?,
                    categoria = ?
                WHERE id = ?
            """, (
                novo_tipo,
                novo_valor,
                nova_data.isoformat(),
                nova_categoria,
                int(id_selecionado)
            ))

            conexao.commit()

        finally:
            conexao.close()

        st.success("Movimentação atualizada!")
        st.rerun()

    st.markdown("### Excluir registro")

    confirmar_exclusao = st.checkbox(
        f"Confirmo que desejo excluir o registro ID "
        f"{id_selecionado}"
    )

    if st.button(
        "Excluir movimentação",
        type="secondary",
        disabled=not confirmar_exclusao
    ):
        conexao = sqlite3.connect(BANCO)

        try:
            conexao.execute(
                "DELETE FROM movimentacoes WHERE id = ?",
                (int(id_selecionado),)
            )
            conexao.commit()

        finally:
            conexao.close()

        st.success("Movimentação excluída.")
        st.rerun()
