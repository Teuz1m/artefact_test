import streamlit as st
import requests
import os
from dotenv import load_dotenv


load_dotenv()


st.set_page_config(
    page_title="AI Assistant",
    page_icon="🤖",
    layout="wide"
)


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


if "messages" not in st.session_state:
    st.session_state.messages = []
if "tools_used" not in st.session_state:
    st.session_state.tools_used = []


st.title("🤖 AI Assistant - Desafio Técnico")
st.markdown(
    "Assistente de IA que decide qual melhor ferramenta a se usar para responder suas perguntas.")


with st.sidebar:
    st.header("⚙️ Informações")

    st.subheader("🛠️ Ferramentas Disponíveis")
    st.info("**Calculator**: Cálculos matemáticos seguros")
    st.info("**Weather API**: Consulta clima de cidades")

    if st.button("🗑️ Limpar Conversa"):
        st.session_state.messages = []
        st.session_state.tools_used = []
        st.rerun()

    st.divider()
    st.caption("Powered by LangChain + FastMCP")


st.subheader("💬 Conversa")


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant" and "tools_used" in message:
            if message["tools_used"]:
                st.caption(
                    f"🛠️ Tools usadas: {', '.join(message['tools_used'])}")

if prompt := st.chat_input("Digite sua pergunta..."):

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/v1/query",
                    json={"query": prompt},
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()

                    if data["success"]:

                        st.markdown(data["response"])

                        if data["intermediate_steps"]:
                            with st.expander("🔍 Ver detalhes do processamento"):
                                for step in data["intermediate_steps"]:
                                    st.write(f"**Tool**: {step['tool']}")
                                    st.write(f"**Input**: {step['input']}")
                                    st.write(f"**Output**: {step['output']}")
                                    st.divider()

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": data["response"],
                            "tools_used": data["tools_used"]
                        })
                        st.session_state.tools_used.extend(data["tools_used"])

                        if data["tools_used"]:
                            st.caption(
                                f"🛠️ Tools usadas: {', '.join(data['tools_used'])}")
                    else:
                        st.error(
                            f"Erro: {data.get('error', 'Erro desconhecido')}")
                else:
                    st.error(
                        f"Erro ao processar query (status: {response.status_code})")
            except requests.exceptions.Timeout:
                st.error("Timeout: O servidor demorou muito para responder")
            except requests.exceptions.ConnectionError:
                st.error(
                    f"Erro de conexão: Verifique se o backend está rodando em {BACKEND_URL}")
            except Exception as e:
                st.error(f"Erro: {str(e)}")


st.divider()
st.subheader("💡 Experimente perguntar:")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **Matemática:**
    - Quanto é 25 * 37?
    - Calcule 2 elevado a 10
    - (15 + 30) / 3
    - 128 vezes 46
    """)

with col2:
    st.markdown("""
    **Conhecimento Geral:**
    - Qual a capital do Brasil?
    - O que é inteligência artificial?
    - Explique o que é Python
    - Quem foi Albert Einstein?
    """)

with col3:
    st.markdown("""
    **Clima:**
    - Qual clima em São Paulo?
    - Qual a cor do céu em Floripa?
    - Previsão no tempo para o Rio de Janeiro
    - Está chovendo no Maranhao ?
    """)
