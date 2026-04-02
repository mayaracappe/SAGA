import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# Configuração visual
st.set_page_config(page_title="Controle de Urgências", layout="wide")

# Arquivo de dados (Simples para teste, ideal seria banco de dados para produção)
DB_FILE = "dados.csv"

def carregar_dados():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["ID", "CPF", "Tipo", "Prioridade", "Motivo", "Detalhe", "Origem", "Status", "Prazo"])

def salvar_dados(df):
    df.to_csv(DB_FILE, index=False)

# --- ESTILO ---
st.markdown("""
    <style>
    .card-imediato { background-color: #ff4b4b; color: white; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 10px solid #800000; }
    .card-urgente { background-color: #ffa500; color: white; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    .card-alta { background-color: #1e90ff; color: white; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: CADASTRO ---
st.sidebar.header("🆕 Nova Urgência")
with st.sidebar.form("form"):
    cpf = st.text_input("CPF do Solicitante")
    tipo = st.selectbox("Tipo", ["Inscrição", "Especialização", "Transferência", "Outro"])
    prioridade = st.selectbox("Prioridade", ["Imediato (Hoje 16h)", "Urgente (48h)", "Alta (5 dias)"])
    motivo = st.selectbox("Motivo", ["Trabalho", "Pedido de Conselheiro", "Outro"])
    
    detalhe = ""
    if motivo == "Trabalho":
        arq = st.file_uploader("Anexar Comprovante")
        detalhe = "Comprovante anexado" if arq else "Sem anexo"
    elif motivo == "Pedido de Conselheiro":
        n = st.text_input("Nome Conselheiro")
        m = st.selectbox("Motivo pedido", ["Trabalho", "Em atendimento", "Particular"])
        detalhe = f"{n} ({m})"
    else:
        detalhe = st.text_input("Especifique")
        
    origem_lista = st.selectbox("Quem incluiu", ["Patrícia", "Emmanuele", "Thiago", "Outro"])
    sub = ""
    if origem_lista == "Emmanuele":
        sub = st.selectbox("Subseção", ["Cabo Frio", "Campos", "Campo Grande", "Niterói", "São Gonçalo", "Petrópolis", "Volta Redonda", "Friburgo", "Nova Iguaçu", "Itaperuna"])
    
    if st.form_submit_button("SALVAR"):
        df = carregar_dados()
        agora = datetime.now()
        
        # Lógica de Prazo
        if "Imediato" in prioridade:
            prazo = agora.replace(hour=16, minute=0, second=0)
        elif "Urgente" in prioridade:
            prazo = agora + timedelta(hours=48)
        else:
            prazo = agora + timedelta(days=5)

        novo = pd.DataFrame([{
            "ID": len(df)+1, "CPF": cpf, "Tipo": tipo, "Prioridade": prioridade,
            "Motivo": motivo, "Detalhe": detalhe, "Origem": f"{origem_lista} {sub}",
            "Status": "Aguardando", "Prazo": prazo.strftime("%d/%m/%Y %H:%M")
        }])
        salvar_dados(pd.concat([df, novo]))
        st.success("Registrado!")
        if "Imediato" in prioridade: st.toast("🚨 PRIORIDADE IMEDIATA!")

# --- PAINEL PRINCIPAL ---
st.title("⚖️ Gestão de Atendimentos Urgentes")

df = carregar_dados()

if not df.empty:
    # Filtros e Status
    st.subheader("Fila de Atendimento")
    
    # Ordenação (Imediato primeiro)
    df['sort_order'] = df['Prioridade'].map({"Imediato (Hoje 16h)": 0, "Urgente (48h)": 1, "Alta (5 dias)": 2})
    df = df.sort_values('sort_order').drop('sort_order', axis=1)

    for i, row in df.iterrows():
        if row['Status'] == "Atendido": continue
        
        classe = "card-imediato" if "Imediato" in row['Prioridade'] else ("card-urgente" if "Urgente" in row['Prioridade'] else "card-alta")
        
        # Calcular tempo restante
        try:
            prazo_dt = datetime.strptime(row['Prazo'], "%d/%m/%Y %H:%M")
            restante = prazo_dt - datetime.now()
            tempo_str = f"{restante.days}d {restante.seconds//3600}h" if restante.total_seconds() > 0 else "PRAZO ESGOTADO"
        except:
            tempo_str = "Erro no prazo"

        st.markdown(f"""
            <div class="{classe}">
                <h3>{row['Prioridade']} - CPF: {row['CPF']}</h3>
                <p><b>Tipo:</b> {row['Tipo']} | <b>Motivo:</b> {row['Motivo']} ({row['Detalhe']})</p>
                <p><b>Origem:</b> {row['Origem']} | <b>⏱️ Resta:</b> {tempo_str} | <b>Prazo:</b> {row['Prazo']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([2,1,1])
        novo_st = c1.selectbox("Status", ["Aguardando", "Diligência", "Aguardando Consulta", "Atendido"], key=f"st{i}", index=["Aguardando", "Diligência", "Aguardando Consulta", "Atendido"].index(row['Status']))
        if c2.button("Atualizar", key=f"btn{i}"):
            df.at[i, 'Status'] = novo_st
            salvar_dados(df)
            st.rerun()
        if row['Status'] == "Atendido" or c3.button("Excluir", key=f"del{i}"):
            salvar_dados(df.drop(i))
            st.rerun()

    # --- INDICADORES ---
    st.divider()
    st.subheader("📊 Quantitativo por Motivo")
    st.bar_chart(df['Motivo'].value_counts())

else:
    st.info("Nenhuma demanda cadastrada.")
