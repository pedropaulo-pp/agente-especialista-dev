import streamlit as st
from google import genai
from google.genai import types
import sqlite3
import json
import uuid
import io
import contextlib

# *****************************************************************
# 1. CONFIGURAÇÃO DA CHAVE E CLIENTE
# *****************************************************************
try:
    CHAVE_API = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=CHAVE_API)
except Exception:
    st.error("Erro: A chave de API não pôde ser carregada do arquivo de segredos. Verifique o secrets.toml.")
    st.stop()


# *****************************************************************
# 1.5. GERENCIAMENTO DE HISTÓRICO (SQLite)
# *****************************************************************

DB_FILE = "piter_conversations.db"

def init_db():
    """Inicializa a conexão com o banco de dados e cria a tabela se não existir."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            history TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_conversation(session_id, title, history_list):
    """Salva ou atualiza a conversa no banco de dados."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Converte o histórico do Gemini para uma string JSON
    history_json = json.dumps([
        {"role": msg.role, "text": msg.parts[0].text} 
        for msg in history_list if msg.parts and msg.parts[0].text
    ])
    
    c.execute("""
        INSERT OR REPLACE INTO conversations (id, title, history)
        VALUES (?, ?, ?)
    """, (session_id, title, history_json))
    
    conn.commit()
    conn.close()

def load_all_conversations():
    """Carrega o ID e o título de todas as conversas (da mais recente para a mais antiga)."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, title FROM conversations ORDER BY rowid DESC")
    conversations = c.fetchall()
    conn.close()
    return conversations

def load_history(session_id):
    """Carrega o histórico completo de uma conversa específica."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT history FROM conversations WHERE id = ?", (session_id,))
    data = c.fetchone()
    conn.close()
    
    if data:
        history_dicts = json.loads(data[0])
        gemini_history = []
        for msg in history_dicts:
            # CORREÇÃO DO TYPE ERROR: Usando explicitamente o parâmetro 'text='
            part = types.Part.from_text(text=msg['text'])
            gemini_history.append(types.Content(role=msg['role'], parts=[part]))
        return gemini_history
    return []

# Inicializa o banco de dados antes de tudo
init_db()


# *****************************************************************
# 1.6. FERRAMENTA DE EXECUÇÃO DE CÓDIGO
# *****************************************************************

def executar_codigo(codigo: str) -> str:
    """
    Executa o código Python fornecido e retorna a saída ou o erro.
    
    Atenção: O código deve ser Python. Use 'print()' para exibir resultados.
    """
    try:
        local_scope = {}
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            exec(codigo, local_scope)
        
        output = stdout.getvalue()
        
        if output:
            return f"Saída do código:\n{output}"
        else:
            return "Código executado com sucesso, mas não houve saída (use print())."
            
    except Exception as e:
        return f"Erro durante a execução do código: {e}"


# *****************************************************************
# 2. PERSONALIDADE DO AGENTE (System Instruction)
# *****************************************************************
CONFIG_AGENTE = types.GenerateContentConfig(
    system_instruction="Você é Piter, um especialista em programação altamente qualificado. Você domina desenvolvimento Web (incluindo React, Vue, HTML, CSS, e JavaScript) e desenvolvimento Android (Kotlin e Java). Suas respostas devem ser precisas, didáticas, e incluir trechos de código relevantes. **Sempre se dirija ao usuário como 'Pedro'** no início de cada resposta. **Você tem acesso à ferramenta 'executar_codigo' para testar e validar snippets de Python.** Se o usuário enviar um arquivo, analise-o primeiro e depois responda à pergunta dele. Use Markdown para formatar o código.",
    # Registra a ferramenta
    tools=[executar_codigo]
)


# *****************************************************************
# 3. INTERFACE STREAMLIT E LÓGICA DE CHAT
# *****************************************************************

# Layout e Título (Com o ícone 🧠 na barra superior/aba)
st.set_page_config(
    page_title=" Piter - IA", 
    layout="wide", 
    initial_sidebar_state="collapsed", 
    page_icon="🧠" # <-- CORREÇÃO: Adicionando o ícone do Piter
)

# Funções de Controle de Sessão
def start_new_chat():
    """Cria uma nova sessão de chat e zera o ID/título."""
    st.session_state.current_session_id = str(uuid.uuid4())
    st.session_state.current_session_title = "Nova Conversa"
    st.session_state.chat_session = client.chats.create(
        model="gemini-2.5-flash",
        config=CONFIG_AGENTE,
        history=[] 
    )

def load_selected_chat(session_id, title):
    """Carrega o histórico de uma conversa salva."""
    history = load_history(session_id)
    st.session_state.current_session_id = session_id
    st.session_state.current_session_title = title
    
    # Recria a sessão de chat do Gemini com o histórico carregado
    st.session_state.chat_session = client.chats.create(
        model="gemini-2.5-flash",
        config=CONFIG_AGENTE,
        history=history 
    )


# CSS que funciona: Apenas esconde o menu do Streamlit
st.markdown("""
<style>
/* Esconde o menu de hambúrguer e o botão "Deploy" do Streamlit */
div.css-1l00lrh.e1tzin5v3 {
    visibility: hidden;
}
div.css-1l00lrh.e1tzin5v3::before {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


st.title("🧠 Olá, sou o Piter!") 
st.caption("Olá, Pedro Paulo, qual o objetivo de hoje ?")


# Inicializa variáveis de estado para o histórico
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = str(uuid.uuid4())
if "current_session_title" not in st.session_state:
    st.session_state.current_session_title = "Nova Conversa"


# Sidebar (Barra Lateral) e Interface de Histórico
with st.sidebar:
    st.title("Sobre Piter 🧠")
    st.markdown("Piter é um assistente de codificação baseado analise e criação.")
    st.markdown("**Foco:** Desenvolvimento Web e Android.")
    
    # --- Seção de Upload de Arquivos ---
    st.subheader("Análise de Arquivos")
    uploaded_file = st.file_uploader(
        "Selecione um arquivo (Imagem, PDF, Código, etc.)",
        type=None,
        key="sidebar_file_uploader" 
    )
    
    # --- Seção de Histórico de Conversas ---
    st.markdown("---")
    st.subheader("📝 Conversas Salvas")
    
    # Botão para Iniciar Nova Conversa
    if st.button("➕ Iniciar Nova Conversa", use_container_width=True):
        start_new_chat()
        st.rerun()

    # Exibe a lista de conversas salvas
    conversations = load_all_conversations()
    
    # Se houver conversas, exibe-as como botões
    if conversations:
        st.markdown(f"**Sessão Atual:** *{st.session_state.current_session_title}*")
        st.markdown("---")
        
        for conv_id, conv_title in conversations:
            if st.button(
                f"📃 {conv_title}", 
                key=f"load_{conv_id}", 
                use_container_width=True
            ):
                load_selected_chat(conv_id, conv_title)
                st.rerun()


# Inicializa ou Carrega a Sessão de Chat
if "chat_session" not in st.session_state:
    start_new_chat() # Garante que uma sessão vazia é iniciada se nenhuma for carregada


# Inicializa o estado do arquivo de upload
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
st.session_state.uploaded_file = uploaded_file


# Exibe o histórico de mensagens COM AVATARES PERSONALIZADOS
for message in st.session_state.chat_session.get_history():
    role = "user" if message.role == "user" else "assistant"
    
    if role == "user":
        avatar_icon = "👤" # CORREÇÃO: Usando o avatar de usuário consistente
    else:
        avatar_icon = "🧠"
    
    if message.parts and message.parts[0].text:
        message_content = message.parts[0].text
        with st.chat_message(role, avatar=avatar_icon):
            st.markdown(message_content)


# Captura de Entrada do Usuário
if prompt := st.chat_input("Pergunte ao Piter..."):
    
    # 1. Montar a lista de partes a serem enviadas (texto + arquivo)
    parts_to_send = [prompt]
    file_included = False
    
    if st.session_state.uploaded_file:
        file_bytes = st.session_state.uploaded_file.read()
        
        file_part = types.Part.from_bytes(
            data=file_bytes,
            mime_type=st.session_state.uploaded_file.type
        )
        parts_to_send.append(file_part)
        file_included = True
        
        st.session_state.uploaded_file = None

    # 2. Exibe a mensagem do usuário
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        if file_included:
            st.markdown("✅ *Arquivo incluído na análise.*")
            
    # 3. Processamento da Resposta da IA (Tool Use Logic)
    with st.chat_message("assistant", avatar="🧠"):
        with st.spinner("Piter está pensando..."):
            
            # Envia a primeira mensagem para o modelo
            response = st.session_state.chat_session.send_message(parts_to_send)
            
            # Loop para lidar com chamadas de ferramenta
            while response.function_calls:
                
                st.markdown(f"**Piter:** 🛠️ *Chamando ferramenta de execução de código...*")

                tool_results = []
                for call in response.function_calls:
                    if call.name == "executar_codigo":
                        code_to_execute = call.args["codigo"]
                        
                        st.code(code_to_execute, language="python")

                        # Chama a função Python localmente
                        result = executar_codigo(code_to_execute)
                        
                        # Adiciona o resultado para enviar de volta ao modelo
                        tool_results.append(types.Part.from_function_response(
                            name="executar_codigo",
                            response={"result": result}
                        ))
                
                # Envia o resultado da execução da ferramenta de volta ao modelo
                response = st.session_state.chat_session.send_message(tool_results)

            # 4. Exibe a resposta final do modelo (texto)
            try:
                st.markdown(response.text)
                
                # 5. LÓGICA DE SALVAMENTO (Salva após a resposta final da IA)
                history_list = st.session_state.chat_session.get_history()
                
                if st.session_state.current_session_title == "Nova Conversa":
                    first_message_text = prompt[:50] + ("..." if len(prompt) > 50 else "")
                    st.session_state.current_session_title = first_message_text
                
                save_conversation(
                    st.session_state.current_session_id, 
                    st.session_state.current_session_title, 
                    history_list
                )
                
            except Exception as e:
                st.error(f"Erro ao processar a resposta da API/Salvar: {e}")