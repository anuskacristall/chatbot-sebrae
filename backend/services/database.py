import os
import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# --- PATCH DE SSL BYPASS PARA REDE CORPORATIVA ---
import httpx
# Patch httpx Client
original_client_init = httpx.Client.__init__
def patched_client_init(self, *args, **kwargs):
    kwargs['verify'] = False
    original_client_init(self, *args, **kwargs)
httpx.Client.__init__ = patched_client_init

# Patch httpx AsyncClient
original_async_init = httpx.AsyncClient.__init__
def patched_async_init(self, *args, **kwargs):
    kwargs['verify'] = False
    original_async_init(self, *args, **kwargs)
httpx.AsyncClient.__init__ = patched_async_init
# ------------------------------------------------

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Inicializa o cliente Supabase
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    print("[SUPABASE] [ERROR] Chaves do Supabase não encontradas no arquivo .env!")

# --- FUNÇÕES DE INTERFACE DO BANCO DE DADOS (ABSTRAÇÃO) ---

def db_salvar_feedback(data_hora: str, reclamacao: str, email: str):
    """Salva um feedback enviado pelo usuário."""
    if not supabase:
        return None
    res = supabase.table("feedbacks").insert({
        "data_hora": data_hora,
        "reclamacao": reclamacao,
        "email": email
    }).execute()
    return res.data

def db_listar_feedbacks():
    """Retorna a lista de feedbacks ordenados por ID decrescente."""
    if not supabase:
        return []
    res = supabase.table("feedbacks").select("id, data_hora, reclamacao, email").order("id", desc=True).execute()
    return res.data

def db_registrar_usuario(email: str, password_hash: str, salt: str, data_cadastro: str, status: str):
    """Cadastra um novo usuário no banco."""
    if not supabase:
        return None
    res = supabase.table("usuarios_chat").insert({
        "email": email,
        "password_hash": password_hash,
        "salt": salt,
        "data_cadastro": data_cadastro,
        "status": status
    }).execute()
    return res.data

def db_obter_usuario(email: str):
    """Busca um usuário do chat por e-mail."""
    if not supabase:
        return None
    res = supabase.table("usuarios_chat").select("id, email, password_hash, salt, data_cadastro, status").eq("email", email).execute()
    return res.data[0] if res.data else None

def db_ativar_usuario(email: str):
    """Ativa o status de um usuário (torna 'ativo')."""
    if not supabase:
        return None
    res = supabase.table("usuarios_chat").update({"status": "ativo"}).eq("email", email).execute()
    return res.data

def db_listar_usuarios():
    """Lista todos os usuários cadastrados."""
    if not supabase:
        return []
    res = supabase.table("usuarios_chat").select("id, email, data_cadastro, status").order("id", desc=True).execute()
    return res.data

def db_obter_admin(username: str):
    """Busca dados de login de um administrador."""
    if not supabase:
        return None
    res = supabase.table("usuarios").select("id, username, password_hash, salt").eq("username", username).execute()
    return res.data[0] if res.data else None

def db_listar_documentos():
    """Lista metadados dos documentos em PDF cadastrados."""
    if not supabase:
        return []
    res = supabase.table("documentos").select("id, nome_arquivo, data_upload, status").order("id", desc=True).execute()
    return res.data

def db_registrar_documento(nome_arquivo: str, data_upload: str, tamanho_fmt: str):
    """Cadastra ou atualiza os metadados de um PDF."""
    if not supabase:
        return None
    res = supabase.table("documentos").upsert({
        "nome_arquivo": nome_arquivo,
        "data_upload": data_upload,
        "status": tamanho_fmt
    }, on_conflict="nome_arquivo").execute()
    return res.data

def db_deletar_documento(nome_arquivo: str):
    """Exclui os metadados de um documento."""
    if not supabase:
        return None
    res = supabase.table("documentos").delete().eq("nome_arquivo", nome_arquivo).execute()
    return res.data

# --- INICIALIZAÇÃO DE DADOS DE TESTE (CONEXÃO INICIAL) ---

def inicializar_banco():
    """Cria os usuários padrão no Supabase se não existirem."""
    if not supabase:
        print("[DB] Não foi possível inicializar: Supabase não conectado.")
        return
    
    # 1. Garante que a tabela 'usuarios' tenha o admin padrão
    try:
        res = supabase.table("usuarios").select("id").eq("username", "admin").execute()
        if not res.data:
            from services.auth import gerar_hash_senha
            hash_senha, salt = gerar_hash_senha("sebrae123")
            supabase.table("usuarios").insert({
                "username": "admin",
                "password_hash": hash_senha,
                "salt": salt
            }).execute()
            print("[DB] Administrador padrão criado no Supabase ('admin' / 'sebrae123')")
    except Exception as e:
        print("[DB] [ALERT] Erro ao verificar/criar administrador. Certifique-se de que a tabela 'usuarios' foi criada no Supabase SQL Editor.", str(e))

    # 2. Garante que os usuários de teste do chat existam
    usuarios_teste = ["gestor@sebrae.com.br", "consultor@sebrae.com.br"]
    for email_teste in usuarios_teste:
        try:
            res = supabase.table("usuarios_chat").select("id").eq("email", email_teste).execute()
            if not res.data:
                from services.auth import gerar_hash_senha
                hash_senha, salt = gerar_hash_senha("sebrae123")
                data_cadastro = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                supabase.table("usuarios_chat").insert({
                    "email": email_teste,
                    "password_hash": hash_senha,
                    "salt": salt,
                    "data_cadastro": data_cadastro,
                    "status": "ativo"
                }).execute()
                print(f"[DB] Usuário de teste criado no Supabase ({email_teste} / 'sebrae123')")
        except Exception as e:
            print(f"[DB] [ALERT] Erro ao verificar/criar usuário {email_teste} no Supabase.", str(e))
            
    # 3. Garante que o bucket de armazenamento exista no Supabase Storage
    inicializar_bucket()

# --- FUNÇÕES DE INTEGRAÇÃO COM SUPABASE STORAGE ---

def inicializar_bucket():
    """Garante que o bucket 'documentos' existe no Supabase."""
    if not supabase:
        return
    try:
        supabase.storage.create_bucket("documentos", options={"public": False})
        print("[STORAGE] Bucket 'documentos' verificado/criado com sucesso.")
    except Exception as e:
        # Se já existir, ele retorna erro de duplicidade que podemos ignorar
        pass

def db_upload_pdf_to_storage(nome_arquivo: str, bytes_arquivo: bytes):
    """Envia um arquivo PDF para a nuvem no bucket 'documentos'."""
    if not supabase:
        return None
    res = supabase.storage.from_("documentos").upload(
        path=nome_arquivo,
        file=bytes_arquivo,
        file_options={"upsert": "true", "content-type": "application/pdf"}
    )
    return res

def db_delete_pdf_from_storage(nome_arquivo: str):
    """Remove um PDF do bucket 'documentos'."""
    if not supabase:
        return None
    try:
        res = supabase.storage.from_("documentos").remove([nome_arquivo])
        return res
    except Exception as e:
        print(f"[STORAGE] Erro ao deletar o PDF {nome_arquivo} da nuvem: {e}")
        return None

def db_download_all_pdfs_from_storage(destino_dir: str):
    """Baixa todos os PDFs do bucket 'documentos' para uma pasta local temporária."""
    if not supabase:
        return []
    os.makedirs(destino_dir, exist_ok=True)
    
    # Lista arquivos no bucket documentos
    arquivos = supabase.storage.from_("documentos").list()
    arquivos_baixados = []
    
    for arq in arquivos:
        nome = arq["name"]
        # Ignora pastas ou o próprio índice FAISS se estiver no mesmo bucket
        if nome.endswith(".pdf"):
            try:
                caminho_local = os.path.join(destino_dir, nome)
                bytes_arq = supabase.storage.from_("documentos").download(nome)
                with open(caminho_local, "wb") as f:
                    f.write(bytes_arq)
                arquivos_baixados.append(nome)
                print(f"[STORAGE] PDF {nome} baixado da nuvem com sucesso.")
            except Exception as e:
                print(f"[STORAGE] Erro ao baixar o PDF {nome} da nuvem: {e}")
                
    return arquivos_baixados

def db_upload_faiss_index(pasta_origem: str):
    """Faz o upload dos arquivos index.faiss e index.pkl para o Supabase Storage."""
    if not supabase:
        return False
    
    arquivos = ["index.faiss", "index.pkl"]
    for nome in arquivos:
        caminho_local = os.path.join(pasta_origem, nome)
        if os.path.exists(caminho_local):
            try:
                with open(caminho_local, "rb") as f:
                    conteudo = f.read()
                
                caminho_remoto = f"faiss_index/{nome}"
                supabase.storage.from_("documentos").upload(
                    path=caminho_remoto,
                    file=conteudo,
                    file_options={"upsert": "true", "content-type": "application/octet-stream"}
                )
                print(f"[STORAGE] Índice {nome} enviado para a nuvem.")
            except Exception as e:
                print(f"[STORAGE] Erro ao enviar o índice {nome}: {e}")
                return False
    return True

def db_download_faiss_index(pasta_destino: str):
    """Baixa os arquivos index.faiss e index.pkl do Supabase Storage para uso local."""
    if not supabase:
        return False
    
    os.makedirs(pasta_destino, exist_ok=True)
    arquivos = ["index.faiss", "index.pkl"]
    
    # Verifica se os arquivos de índice existem na nuvem
    try:
        lista = supabase.storage.from_("documentos").list("faiss_index")
        arquivos_remotos = [item["name"] for item in lista]
    except Exception as e:
        print("[STORAGE] Erro ao listar arquivos do índice:", str(e))
        return False
    
    # Se algum arquivo estiver faltando, não prossegue
    for nome in arquivos:
        if nome not in arquivos_remotos:
            print(f"[STORAGE] Arquivo de índice {nome} não encontrado na nuvem.")
            return False
            
    for nome in arquivos:
        caminho_local = os.path.join(pasta_destino, nome)
        caminho_remoto = f"faiss_index/{nome}"
        try:
            bytes_arq = supabase.storage.from_("documentos").download(caminho_remoto)
            with open(caminho_local, "wb") as f:
                f.write(bytes_arq)
            print(f"[STORAGE] Índice {nome} baixado da nuvem com sucesso.")
        except Exception as e:
            print(f"[STORAGE] Erro ao baixar o índice {nome}: {e}")
            return False
            
    return True

if __name__ == "__main__":
    print("Inicializando chaves e acessos do Supabase...")
    inicializar_banco()
    print("Inicialização concluída.")
