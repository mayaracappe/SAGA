import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# Configurações da Página
st.set_page_config(page_title="Sistema SAGA", layout="wide")

# --- FUNÇÕES DE APOIO ---
def calcular_prazo(prioridade):
    agora = datetime.now()
    if "Imediato" in prioridade:
        # Hoje até as 16h
        prazo = agora.replace(hour=16, minute=0, second=0, microsecond=0)
        return prazo
    elif "Urgente" in prioridade:
        return agora + timedelta(hours=48)
    elif "Alta" in prioridade:
        # 5 dias úteis (simplificado para 7 dias corridos)
        return agora + timedelta(days=7)
    return agora

def cor_prioridade(prioridade):
    if "Imediato" in prioridade: return "#FF4B4B" # Vermelho
    if "Urgente" in prioridade: return "#FFA500"    # Laranja
    return "#1E90FF"                             # Azul

# --- BANCO DE DADOS TEMPORÁRIO ---
if 'db' not in st.session_state:
    st.session_state.db = []

# --- SIDEBAR: CADASTRO ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/950/950299.png", width=100)
st.sidebar.header("📝 Nova Urgência")

with st.sidebar.form("formulario", clear_on_submit=True):
    cpf = st.text_input("CPF do Solicitante")
    tipo = st.selectbox("Tipo de Requerimento", ["Inscrição", "Especialização", "Transferência", "Outro"])
    prioridade = st.selectbox("Nível de Prioridade", [
        "Imediato (mesmo dia até às 16h)", 
        "Urgente (48h)", 
        "Alta (5 dias úteis)"
    ])
    
    motivo = st.radio("Motivo da Urgência", ["Trabalho", "Pedido de Conselheiro", "Outro"])
    
    # Campos Condicionais do Motivo
    detalhe_motivo = ""
    comprovante = None
    if motivo == "Trabalho":
        comprovante = st.file_uploader("Anexar Comprovante (PDF)", type="pdf")
        detalhe_motivo = "PDF Anexado" if comprovante else "Sem anexo"
    elif motivo == "Pedido de Conselheiro":
        nome_c = st.text_input("Nome do Conselheiro")
        mot_c = st.selectbox("Motivo do pedido", ["trabalho", "em atendimento", "particular"])
        detalhe_motivo = f"Conselheiro: {nome_c} ({mot_c})"
    else:
        detalhe_motivo = st.text_input("Especifique o outro motivo")

    quem = st.selectbox("Quem incluiu", ["Patrícia (Sede)", "Matheus (Sede)", "Emmanuele", "Outro"])
    
    # Campos Condicionais de Quem Incluiu
    origem_final = quem
    if quem == "Emmanuele":
        sub = st.selectbox("Subseção", ["Cabo Frio", "Campos dos Goytacazes", "Campo Grande", "Niterói", "São Gonçalo", "Petrópolis", "Volta Redonda", "Nova Friburgo", "Nova Iguaçu", "Itaperuna"])
        origem_final = f"Emmanuele ({sub})"
    elif quem == "Outro":
        quem_outro = st.text_input("Quem?")
        onde_outro = st.text_input("Onde? (Sede ou Subseção)")
        origem_final = f"{quem_outro} - {onde_outro}"

    if st.form_submit_button("REGISTRAR URGÊNCIA"):
        prazo_calc = calcular_prazo(prioridade)
        nova_demanda = {
            "id": int(time.time()),
            "cpf": cpf,
            "tipo": tipo,
            "prioridade": prioridade,
            "motivo": motivo,
            "detalhe_motivo": detalhe_motivo,
            "origem": origem_final,
            "status": "Aguardando Consulta",
            "prazo": prazo_calc
        }
        st.session_state.db.append(nova_demanda)
        if "Imediato" in prioridade:
            st.toast("🚨 ALERTA: NOVA DEMANDA IMEDIATA!", icon="⚠️")

# --- PAINEL VISUAL ---
st.title("SAGA - Controle de Urgências")

if not st.session_state.db:
    st.info("Nenhum atendimento na fila.")
else:
    # --- DASHBOARD (QUANTITATIVO) ---
    df = pd.DataFrame(st.session_state.db)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", len(df))
    c2.metric("Trabalho", len(df[df['motivo'] == 'Trabalho']))
    c3.metric("Conselheiro", len(df[df['motivo'] == 'Pedido de Conselheiro']))
    c4.metric("Outros", len(df[df['motivo'] == 'Outro']))

    st.divider()

    # --- LISTA DE ATENDIMENTOS ---
    # Ordenação por prioridade: Imediato > Urgente > Alta
    ordem_map = {"Imediato (mesmo dia até às 16h)": 0, "Urgente (48h)": 1, "Alta (5 dias úteis)": 2}
    df['ordem'] = df['prioridade'].map(ordem_map)
    df = df.sort_values(by=['ordem', 'prazo'])

    for index, row in df.iterrows():
        # Lógica do Relógio
        tempo_restante = row['prazo'] - datetime.now()
        esgotado = tempo_restante.total_seconds() < 0
        
        # Pop-up visual para Imediatos
        if "Imediato" in row['prioridade'] and not esgotado:
            st.warning(f"⚠️ ATENÇÃO: Atendimento ID {row['id']} é IMEDIATO (Prazo até 16h)!")

        with st.expander(f"📌 {row['prioridade']} | CPF: {row['cpf']} | Status: {row['status']}", expanded=True):
            col_a, col_b, col_c = st.columns([2, 2, 1])
            
            with col_a:
                st.write(f"**Tipo:** {row['tipo']}")
                st.write(f"**Motivo:** {row['motivo']} - {row['detalhe_motivo']}")
                st.write(f"**Origem:** {row['origem']}")
            
            with col_b:
                cor = cor_prioridade(row['prioridade'])
                st.markdown(f"<h3 style='color:{cor}'>⏱️ {str(tempo_restante).split('.')[0]}</h3>", unsafe_allow_html=True)
                st.write(f"Prazo final: {row['prazo'].strftime('%d/%m/%Y %H:%M')}")
            
            with col_c:
                novo_status = st.selectbox("Alterar Status", ["Aguardando Consulta", "Diligência", "Atendido"], key=f"st_{row['id']}")
                
                # Botão para atualizar status no banco original
                if st.button("Salvar Status", key=f"btn_{row['id']}"):
                    for item in st.session_state.db:
                        if item['id'] == row['id']:
                            item['status'] = novo_status
                    st.rerun()

                # Opção de Excluir se Atendido
                if row['status'] == "Atendido":
                    if st.button("❌ Excluir Demanda", key=f"del_{row['id']}"):
                        st.session_state.db = [item for item in st.session_state.db if item['id'] != row['id']]
                        st.rerun()

    # Gráfico Quantitativo
    st.divider()
    st.subheader("📊 Resumo por Motivo")
    st.bar_chart(df['motivo'].value_counts())
