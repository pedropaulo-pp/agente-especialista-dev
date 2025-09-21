import streamlit as st
from google import genai
from google.genai import types

# *****************************************************************
# 1. CONFIGURAÇÃO DA CHAVE E CLIENTE
# *****************************************************************
# Sua chave de API.
CHAVE_API = "AIzaSyANH52j0F88PczHNkKwJwyFDyQYAzoMo_U" 

try:
    # Cria o cliente, usando a chave de API fornecida.
    client = genai.Client(api_key=CHAVE_API)
except Exception:
    st.error("Erro: A chave de API não pôde ser carregada ou é inválida. Verifique o código.")
    st.stop()


# *****************************************************************
# 2. PERSONALIDADE DO AGENTE (System Instruction)
# *****************************************************************
# Define a configuração do agente como Especialista em Web e Android.
CONFIG_AGENTE = types.GenerateContentConfig(
    system_instruction="Você é um especialista em programação altamente qualificado. Você domina desenvolvimento Web (incluindo React, Vue, HTML, CSS, e JavaScript) e desenvolvimento Android (Kotlin e Java). Suas respostas devem ser precisas, didáticas, e incluir trechos de código relevantes. Use Markdown para formatar o código."
)


# *****************************************************************
# 3. INTERFACE STREAMLIT E LÓGICA DE CHAT
# *****************************************************************
st.set_page_config(page_title="Agente Especialista em Programação")
st.title("🤖 Especialista Dev (Web & Android)")
st.caption("Converse com um especialista em Kotlin, React, Python, etc.")

# Inicializa a sessão de chat (COM MEMÓRIA)
# Usa st.session_state (corrigido!) para manter o estado.
if "chat_session" not in st.session_state:
    st.session_state.chat_session = client.chats.create(
        model="gemini-2.5-flash",
        config=CONFIG_AGENTE
    )

# Exibe o histórico de mensagens (BLOCO CORRIGIDO!)
# Acessa st.session_state.chat_session
for message in st.session_state.chat_session.get_history():
    # Mapeia a 'role' do Gemini para o Streamlit
    role = "user" if message.role == "user" else "assistant"
    
    # Acessa o texto através da lista 'parts'
    if message.parts and message.parts[0].text:
        message_content = message.parts[0].text
        with st.chat_message(role):
            st.markdown(message_content)


# Captura de Entrada do Usuário
if prompt := st.chat_input("Pergunte sobre código..."):
    
    # 1. Exibe a mensagem do usuário imediatamente
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # 2. Envia o prompt para a IA e exibe a resposta
    with st.chat_message("assistant"):
        with st.spinner("O Especialista está consultando a documentação..."):
            try:
                # Acessa st.session_state.chat_session (corrigido!)
                response = st.session_state.chat_session.send_message(prompt)
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Erro de comunicação com a API: {e}")