import os
import ssl
# Esse comando "desliga" a verificação de certificado SSL para o script atual
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
    getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context
    
from services.pdf_reader import extrair_texto_pdf
from services.embeddings import criar_pedacos_de_texto
from services.vector_store import salvar_no_banco

# Resolve o problema de conexão SSL no ambiente corporativo
ssl._create_default_https_context = ssl._create_unverified_context

def processar_base_conhecimento(pasta_pdfs=None):
    """
    Realiza o fluxo completo: PDF -> Texto -> Chunks -> Vetores -> FAISS
    """
    if not pasta_pdfs:
        raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        pasta_pdfs = os.path.join(raiz_projeto, "data", "pdfs")
        if not os.path.exists(pasta_pdfs):
            os.makedirs(pasta_pdfs, exist_ok=True)
        
    todos_os_textos = []
    fontes_por_texto = []
    
    print("[LOADER] Iniciando processamento da base de conhecimento...")
    
    # 1. Localiza os PDFs
    arquivos = [f for f in os.listdir(pasta_pdfs) if f.endswith('.pdf')]
    
    if not arquivos:
        print("[LOADER] [INFO] Nenhum PDF encontrado em backend/data/pdfs/")
        return

    for arquivo in arquivos:
        caminho = os.path.join(pasta_pdfs, arquivo)
        print(f"[LOADER] Lendo: {arquivo}...")
        
        # 2. Extrai o texto (conforme seu RF05)
        resultado_pdf = extrair_texto_pdf(caminho)
        
        if resultado_pdf and isinstance(resultado_pdf, dict) and resultado_pdf.get("texto"):
            # 3. Faz o Chunking (conforme planejado no seu documento)
            pedacos = criar_pedacos_de_texto(resultado_pdf["texto"])
            todos_os_textos.extend(pedacos)
            fontes_por_texto.extend([resultado_pdf.get("fonte", "desconhecido")] * len(pedacos))
            print(f"[LOADER] {len(pedacos)} pedacos gerados para {arquivo}")
        else:
            print(f"[LOADER] [WARN] Ignorado: nao foi possivel extrair texto de {arquivo}")

    # 4. Salva tudo no FAISS (Gera Embeddings via OpenAI)
    if todos_os_textos:
        if len(todos_os_textos) != len(fontes_por_texto):
            print("[LOADER] [WARN] Inconsistencia detectada: numero de textos e fontes nao corresponde. Ajustando...")
            fontes_por_texto = ["desconhecido"] * len(todos_os_textos)

        print(f"\n[LOADER] Enviando {len(todos_os_textos)} blocos para a OpenAI e salvando no FAISS...")
        salvar_no_banco(todos_os_textos, fontes_por_texto)
        print("\n[LOADER] BASE DE CONHECIMENTO PRONTA PARA USO!")

if __name__ == "__main__":
    processar_base_conhecimento()