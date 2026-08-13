import os
import ssl
import certifi
import urllib3
import warnings

# Hide noisy LangChain Pydantic warning on Python 3.14
warnings.filterwarnings(
    "ignore",
    message=r".*Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.*",
    category=UserWarning,
    module=r"langchain_core\\_api\\deprecation"
)

# Disable SSL warnings 
urllib3.disable_warnings()

# Fix SSL certificate verification - MUST be before any other imports
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''
ssl.verify_mode = ssl.CERT_NONE
ssl._create_default_https_context = ssl._create_unverified_context

# Monkey patch requests to disable SSL verification
import requests
original_get = requests.get
def patched_get(url, *args, **kwargs):
    kwargs.setdefault('verify', False)
    return original_get(url, *args, **kwargs)
requests.get = patched_get

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Carrega a sua chave do arquivo .env
load_dotenv()

def gerar_embeddings_da_lista(lista_de_textos):
    """
    Pega os pedaços de texto e pede para a OpenAI transformar em números (vetores).
    """
    # Usamos o modelo 'text-embedding-3-small' por ser o mais barato e eficiente [cite: 44]
    modelo_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # Isso envia os textos para a API e recebe os vetores de volta
    vetores = modelo_embeddings.embed_documents(lista_de_textos)
    return vetores

def criar_pedacos_de_texto(texto_bruto):
    """
    Divide o texto em blocos de 500 caracteres conforme o MVP[cite: 124].
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len
    )
    return text_splitter.split_text(texto_bruto)

# Teste Real com a sua Chave
if __name__ == "__main__":
    texto_exemplo = "O Sebrae fomenta a cultura empreendedora no Brasil."
    chunks = criar_pedacos_de_texto(texto_exemplo)
    
    try:
        resultado = gerar_embeddings_da_lista(chunks)
        print(f"✅ Sucesso! A OpenAI transformou seu texto em um vetor de {len(resultado[0])} números.")
    except Exception as e:
        print(f"❌ Erro de conexão ou chave: {e}")