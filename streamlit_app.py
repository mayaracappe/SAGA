import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Controle de Urgências", layout="wide")

# --- FUNÇÕES ---
def calcular_prazo(prioridade):
    agora = datetime.now()

    if "Imediato" in prioridade:
        return agora.replace(hour=16, minute=0, second=0, microsecond=0)

    elif "Urgente" in prioridade:
        return agora + timedelta(hours=48)

    elif "Alta" in prioridade:
        dias = 0
        prazo = agora
        while dias < 5:
            prazo += timedelta(days=1)
            if prazo.weekday() < 5:  # dias úteis
                dias += 1
        return prazo

    return agora

def prioridade_ordem(p):
    if "Imediato" in p: return 0
    if "Urgente" in p: return 1
    return 2

# --- BANCO TEMPORÁRIO ---
if 'db' not in st.session_state:
    st.session_state.db = []

# --- SIDEBAR ---
st.sidebar.header("Nova Urgência")

with st.sidebar.form("form"):
    cpf = st.text_input("CPF")

    tipo = st.selectbox("Tipo", [
        "Inscrição", "Especialização", "Transferência", "Outro"
    ])

    prioridade = st.selectbox("Prioridade", [
        "Imediato (até 16h)",
        "Urgente (48h)",
        "Alta (5 dias úteis)"
    ])

    motivo = st.radio("Motivo", [
        "Trabalho", "Pedido de Conselheiro", "Outro"
    ])

    detalhe = ""
    if motivo == "Trabalho":
        pdf = st.file_uploader("Anexar PDF", type="pdf")
        detalhe = "Comprovante anexado" if pdf else "Sem comprovante"

    elif motivo == "Pedido de Conselheiro":
        nome = st.text_input("Nome do Conselheiro")
        tipo_c = st.selectbox("Motivo", ["trabalho", "em atendimento", "particular"])
        detalhe = f"{nome} - {tipo_c}"

    else:
        detalhe = st.text_input("Especificar")

    quem = st.selectbox("Quem incluiu", [
        "Patrícia (Sede)",
        "Emmanuele",
        "Thiago (SIC)",
        "Outro"
    ])

    origem = quem

    if quem == "Emmanuele":
        sub = st.selectbox("Subseção", [
            "Cabo Frio", "Campos dos Goytacazes", "Campo Grande",
            "Niterói", "São Gonçalo", "Petrópolis",
            "Volta Redonda", "Nova Friburgo",
            "Nova Iguaçu", "Itaperuna"
        ])
        origem = f"Emmanuele - {sub}"

    if quem == "Outro":
        nome_o = st.text_input("Nome")
        local_o = st.text_input("Local")
        origem = f"{nome_o} - {local_o}"

    submit = st.form_submit_button("Cadastrar")

    if submit:
        prazo = calcular_prazo(prioridade)

        st.session_state.db.append({
            "id": int(time.time()),
            "cpf": cpf,
            "tipo": tipo,
            "prioridade": prioridade,
            "motivo": motivo,
            "detalhe": detalhe,
            "origem": origem,
            "status": "Em andamento",
            "prazo": prazo
        })

        if "Imediato" in prioridade:
            st.warning("🚨 NOVA DEMANDA IMEDIATA!")

# --- PAINEL ---
st.title("Controle de Atendimentos Urgentes")

if not st.session_state.db:
    st.info("Sem atendimentos")
else:
    df = pd.DataFrame(st.session_state.db)

    # --- DASHBOARD ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", len(df))
    col2.metric("Trabalho", len(df[df['motivo'] == 'Trabalho']))
    col3.metric("Conselheiro", len(df[df['motivo'] == 'Pedido de Conselheiro']))
    col4.metric("Outros", len(df[df['motivo'] == 'Outro']))

    st.divider()

    # --- ORDENAÇÃO ---
    df['ordem'] = df['prioridade'].apply(prioridade_ordem)
    df = df.sort_values(by=['ordem', 'prazo'])

    # --- LISTA ---
    for i, row in df.iterrows():
        tempo = row['prazo'] - datetime.now()

        if tempo.total_seconds() < 0:
            tempo_txt = "PRAZO ESTOURADO"
        else:
            tempo_txt = str(tempo).split('.')[0]

        if "Imediato" in row['prioridade']:
            st.error(f"⚠️ IMEDIATO: CPF {row['cpf']}")

        with st.expander(f"{row['prioridade']} | CPF {row['cpf']}"):
            c1, c2, c3 = st.columns([2,2,1])

            with c1:
                st.write("Tipo:", row['tipo'])
                st.write("Motivo:", row['motivo'], "-", row['detalhe'])
                st.write("Origem:", row['origem'])

            with c2:
                st.write("⏱️ Tempo restante:", tempo_txt)
                st.write("Prazo:", row['prazo'].strftime('%d/%m %H:%M'))

            with c3:
                status = st.selectbox(
                    "Status",
                    ["Em andamento", "Diligência", "Aguardando consulta", "Atendido"],
                    key=row['id']
                )

                if st.button("Salvar", key=f"btn{row['id']}"):
                    for item in st.session_state.db:
                        if item['id'] == row['id']:
                            item['status'] = status
                    st.rerun()

                if row['status'] == "Atendido":
                    if st.button("Excluir", key=f"del{row['id']}"):
                        st.session_state.db = [
                            x for x in st.session_state.db if x['id'] != row['id']
                        ]
                        st.rerun()

    st.divider()
    st.subheader("Resumo por motivo")
    st.bar_chart(df['motivo'].value_counts())
