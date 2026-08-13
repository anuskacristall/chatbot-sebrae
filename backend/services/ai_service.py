import warnings
warnings.filterwarnings("ignore", message=".*Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.*")

import os
import ssl
from openai import OpenAI
from dotenv import load_dotenv
from services.vector_store import buscar_informacao
import httpx

# Segurança para ambiente corporativo
ssl._create_default_https_context = ssl._create_unverified_context
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    api_key = "chave-nao-configurada"

client = OpenAI(
    api_key=api_key,
    http_client=httpx.Client(verify=False)
)

def gerar_resposta_chatbot(pergunta_usuario):
    # 1. Busca os textos relevantes no seu FAISS (Memória)
    trechos_relevantes = buscar_informacao(pergunta_usuario)
    
    # Transforma a lista de trechos em um único texto (faiss retorna dicionários)
    if isinstance(trechos_relevantes, list):
        contexto = "\n".join([item.get("texto", "") for item in trechos_relevantes if isinstance(item, dict)])
    else:
        contexto = str(trechos_relevantes)
    
    # 2. Monta o "Prompt" (Instrução para a IA) conforme suas Regras de Negócio (RN01, RN02)
    prompt_sistema = f"""
    Você é o Assistente Virtual do Sebrae Minas. Responda de forma empática e profissional.

    REGRAS DE OURO:
    1. Use APENAS as informações abaixo. Se não souber, diga: "Desculpe, não encontrei esse detalhe nos manuais, mas posso ajudar com outros temas de Educação Empreendedora!"
    2. SEMPRE que possível, organize a resposta em:
        - Uma breve introdução.
        - **Tópicos** (listas com marcadores) para facilitar a leitura.
        - Um fechamento prestativo.
    3. Use **negrito** em palavras-chave.

    CONTEXTO DOS MANUAIS:
    {contexto}
    """

    # 3. Chama a inteligência da OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Modelo rápido e barato para o MVP
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": pergunta_usuario}
            ],
            temperature=0.2 # Menos criatividade, mais precisão (conforme RN01)
        )

        return response.choices[0].message.content
    except Exception as e:
        print("[ERROR] OpenAI API call failed:", repr(e))
        import traceback; traceback.print_exc()
        raise

if __name__ == "__main__":
    # TESTE REAL: Faça uma pergunta sobre o conteúdo dos seus PDFs!
    pergunta = "O que é educação empreendedora?" 
    print(f"🤔 Pergunta: {pergunta}")
    print("🤖 Pensando...")
    print(f"\nRESPOSTA: {gerar_resposta_chatbot(pergunta)}")