import os
import httpx
from langchain_community.vectorstores.faiss import FAISS
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv


# carrega a chave da OpenAI para podermos criar a busca
load_dotenv()

# onde vamos salvar a "memória" do chatbot
PASTA_DB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "db", "faiss_index"))

def salvar_no_banco(lista_de_textos, lista_de_fontes):
    
    # usa um cliente HTTPX customizado para ignorar checagem de certificado em rede corporativa
    http_client = httpx.Client(verify=False)
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY"),
        http_client=http_client,
    )
    metadados = [{"source": fonte} for fonte in lista_de_fontes]
    
    # cria o banco de dados FAISS a partir dos textos
    vector_db = FAISS.from_texts(lista_de_textos, embeddings, metadatas=metadados)
    
    # salva na pasta da estrutura do projeto
    vector_db.save_local(PASTA_DB)
    print(f"[DB] Banco de dados FAISS criado e salvo em: {PASTA_DB}")

def buscar_informacao(pergunta):
    
    # usa mesmo cliente HTTPX sem verificação SSL para buscas também
    http_client = httpx.Client(verify=False)
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY"),
        http_client=http_client,
    )
    
    # carrega o banco salvo anteriormente
    index_completo = os.path.exists(os.path.join(PASTA_DB, "index.faiss")) and os.path.exists(os.path.join(PASTA_DB, "index.pkl"))
    
    if not index_completo:
        print("[VECTOR STORE] Indice local nao encontrado. Tentando baixar do Supabase Storage...")
        from services.database import db_download_faiss_index
        sucesso_download = db_download_faiss_index(PASTA_DB)
        if not sucesso_download:
            print("[VECTOR STORE] Nao foi possivel obter o indice FAISS da nuvem. Retornando busca vazia.")
            return []
        
    vector_db = FAISS.load_local(PASTA_DB, embeddings, allow_dangerous_deserialization=True)
    
    # busca os 3 pedaços mais relevantes
    resultados = vector_db.similarity_search(pergunta, k=6)
    
    return [{"texto": res.page_content, "fonte": res.metadata['source']} for res in resultados]

# teste de salvamento e busca
if __name__ == "__main__":
    textos_exemplo = [
        "O Sebrae oferece cursos de finanças para MEI.",
        "A educação empreendedora foca em comportamento e inovação.",
        "O projeto chatbot está sendo desenvolvido pela Anuska."
    ]
    
    print("Criando banco de teste...")
    fontes_exemplo = ["manual1.pdf", "manual2.pdf", "manual3.pdf"]
    salvar_no_banco(textos_exemplo, fontes_exemplo)
    
    print("\nTestando busca...")
    resultado_busca = buscar_informacao("Quem está desenvolvendo o chatbot?")
    print(f"Resultado encontrado: {resultado_busca[0]}")