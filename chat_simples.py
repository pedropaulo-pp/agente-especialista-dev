import os
from google import genai
from google.genai import types

# *****************************************************************
# 1. CONFIGURAÇÃO DA CHAVE
# *****************************************************************
# Sua chave de API está definida diretamente aqui para garantir a execução imediata.
# AVISO: Em projetos profissionais, NUNCA deixe a chave diretamente no código!
CHAVE_API = "AIzaSyANH52j0F88PczHNkKwJwyFDyQYAzoMo_U" 

# 2. CONEXÃO COM A API
try:
    # Cria o cliente, usando a chave de API fornecida.
    client = genai.Client(api_key=CHAVE_API)
except Exception as e:
    print(f"ERRO CRÍTICO NA CONEXÃO. Verifique a chave de API e sua instalação do Python.")
    print(f"Detalhes do erro: {e}")
    exit()

# 3. INSTRUÇÃO DE SISTEMA (Personalidade do Agente)
# Define o agente como um especialista em Web e Android.
config = types.GenerateContentConfig(
    system_instruction="Você é um especialista em programação altamente qualificado. Você domina desenvolvimento Web (incluindo React, Vue, HTML, CSS, e JavaScript) e desenvolvimento Android (Kotlin e Java). Suas respostas devem ser precisas, didáticas, e incluir trechos de código relevantes para o contexto do usuário. Seja direto e objetivo."
)

# 4. INICIA A SESSÃO DE CHAT (com a nova personalidade e memória)
chat = client.chats.create(
    model="gemini-2.5-flash",
    config=config
)

print("🤖 Agente Especialista em Programação (Web & Android) iniciado!")
print("Pode perguntar sobre Kotlin, React, ou qualquer linguagem.")
print("-" * 60)

# 5. LOOP PRINCIPAL DE CONVERSA
while True:
    user_input = input("Você: ")

    if user_input.lower() == 'sair':
        print("Até logo! Agente encerrado.")
        break

    try:
        # Envia a mensagem do usuário para o modelo e recebe a resposta.
        response = chat.send_message(user_input)
        print(f"IA: {response.text}")

    except Exception as e:
        print(f"\n--- ERRO AO ENVIAR MENSAGEM ---")
        print(f"Ocorreu um erro durante a comunicação com a API: {e}")
        break