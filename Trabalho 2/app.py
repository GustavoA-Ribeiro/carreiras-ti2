import streamlit as st
import pandas as pd
import json

# -------------------------------------------------------------
# FASE 1 & 2: CARREGAMENTO DE CONHECIMENTO E MOTOR DE INFERÊNCIA
# -------------------------------------------------------------

@st.cache_data
def carregar_base_conhecimento():
    """Lê o arquivo JSON dinamicamente (Desacoplamento)"""
    with open("regras_carreiras.json", "r", encoding="utf-8") as file:
        return json.load(file)

def calcular_compatibilidade(respostas, base_dados):
    """
    Motor de Inferência Ponderado:
    Multiplica as respostas (1-5) pelos pesos das regras para cada trilha.
    Calcula a aderência em formato de percentagem (%).
    """
    trilhas = base_dados["trilhas"]
    resultados = []

    for nome_trilha, dados_trilha in trilhas.items():
        pesos = dados_trilha["pesos"]
        pontuacao_maxima_possivel = sum(peso * 5 for peso in pesos.values())
        pontuacao_usuario = sum(pesos[key] * respostas[key] for key in pesos.keys())
        
        # Compatibilidade Percentual
        percentual = (pontuacao_usuario / pontuacao_maxima_possivel) * 100
        resultados.append({"Trilha": nome_trilha, "Compatibilidade (%)": round(percentual, 1)})
    
    # Ordenar do maior para o menor e devolver
    df_resultados = pd.DataFrame(resultados).sort_values(by="Compatibilidade (%)", ascending=False)
    return df_resultados.reset_index(drop=True)

def analisar_gaps(nivel_atual, trilha_recomendada, base_dados):
    """Identifica lacunas de competências para atingir o nível Júnior."""
    dados_trilha = base_dados["trilhas"][trilha_recomendada]
    roadmap = dados_trilha["roadmap"]
    
    gaps = []
    if nivel_atual == "Iniciante (Conceitos Básicos)":
        gaps.append("Falta aprofundamento prático nas tecnologias base da área.")
        gaps.append("Necessidade de construir o primeiro projeto aplicável.")
    elif nivel_atual == "Intermediário (Projetos Académicos)":
        gaps.append("Falta experiência de integração de sistemas e deploy em produção.")
    
    return roadmap, gaps

# -------------------------------------------------------------
# FASE 4: INTERFACE WEB EM ETAPAS (WIZARD)
# -------------------------------------------------------------

def main():
    st.set_page_config(page_title="Consultor Avançado de Carreiras", page_icon="🧭", layout="wide")
    
    # Gestão de Estado para as etapas (Wizard)
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'respostas' not in st.session_state:
        st.session_state.respostas = {}
    
    base_conhecimento = carregar_base_conhecimento()
    
    st.title("🧭 Consultor Avançado de Carreiras em TI")
    st.markdown("Sistema Especialista Ponderado com Análise de Gaps e Roadmap.")
    st.progress(st.session_state.step / 3)

    # --- PASSO 1: PERFIL E OBJETIVOS ---
    if st.session_state.step == 1:
        st.header("Passo 1: Perfil Pessoal")
        
        st.session_state.nome = st.text_input("Qual o seu nome?")
        st.session_state.nivel_atual = st.selectbox(
            "Qual o seu nível de conhecimento geral em TI?",
            ["Iniciante (Conceitos Básicos)", "Intermediário (Projetos Académicos)", "Avançado (Já atuo no mercado)"]
        )
        
        if st.button("Próximo Passo ➡️"):
            if st.session_state.nome:
                st.session_state.step = 2
                st.rerun()
            else:
                st.warning("Por favor, introduza o seu nome para continuar.")

    # --- PASSO 2: AFINIDADES TÉCNICAS (LIKERT) ---
    elif st.session_state.step == 2:
        st.header("Passo 2: Afinidades Técnicas")
        st.write("Avalie o seu grau de afinidade com cada área de **1 (Nenhuma Afinidade)** a **5 (Muita Afinidade)**.")
        
        for pergunta in base_conhecimento["perguntas_afinidade"]:
            st.session_state.respostas[pergunta["id"]] = st.slider(
                pergunta["texto"], min_value=1, max_value=5, value=3
            )
        
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("⬅️ Voltar"):
                st.session_state.step = 1
                st.rerun()
        with col2:
            if st.button("Gerar Diagnóstico 🚀"):
                st.session_state.step = 3
                st.rerun()

    # --- PASSO 3: RESULTADOS, RANKING E ROADMAP ---
    elif st.session_state.step == 3:
        st.header("Passo 3: Resultados e Plano de Ação")
        
        # Calcular Compatibilidade
        ranking = calcular_compatibilidade(st.session_state.respostas, base_conhecimento)
        top_3 = ranking.head(3)
        trilha_vencedora = top_3.iloc[0]["Trilha"]
        
        st.subheader(f"Olá, {st.session_state.nome}! Aqui está o seu Top 3 de Compatibilidade:")
        
        # Exibir Gráfico de Barras com a compatibilidade (%)
        st.bar_chart(data=ranking.set_index("Trilha")["Compatibilidade (%)"])
        
        st.table(top_3.style.format({"Compatibilidade (%)": "{:.1f}%"}))
        
        st.divider()
        
        # Módulo de Recomendação de Gaps e Roadmap
        st.header(f"🎯 Foco Principal: {trilha_vencedora}")
        
        roadmap, gaps = analisar_gaps(st.session_state.nivel_atual, trilha_vencedora, base_conhecimento)
        
        col_gaps, col_road = st.columns(2)
        
        with col_gaps:
            st.subheader("⚠️ Análise de Gaps (Skill Gaps)")
            if gaps:
                for gap in gaps:
                    st.warning(gap)
            else:
                st.success("O seu nível atual requer apenas especialização direcionada.")
                
            st.write("**Tecnologias que precisa de dominar:**")
            for tech in roadmap["tecnologias"]:
                st.markdown(f"- {tech}")
                
        with col_road:
            st.subheader("🗺️ Roadmap Personalizado")
            st.info(f"**Certificações Recomendadas:**\n{', '.join(roadmap['certificacoes'])}")
            st.success(f"**Projeto de Portfólio Sugerido:**\n{roadmap['portfolio']}")
            
        if st.button("🔄 Refazer Teste"):
            st.session_state.step = 1
            st.session_state.respostas = {}
            st.rerun()

if __name__ == "__main__":
    main()