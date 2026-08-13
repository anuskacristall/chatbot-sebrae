import ssl
import os
import io
import shutil
import pandas as pd
from fastapi import FastAPI, Depends, Header, HTTPException, File, UploadFile, BackgroundTasks
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse

from services.vector_store import buscar_informacao
from services.ai_service import gerar_resposta_chatbot
from services.database import (
    inicializar_banco,
    db_salvar_feedback,
    db_listar_feedbacks,
    db_registrar_usuario,
    db_obter_usuario,
    db_ativar_usuario,
    db_listar_usuarios,
    db_obter_admin,
    db_listar_documentos,
    db_registrar_documento,
    db_deletar_documento,
    db_upload_pdf_to_storage,
    db_delete_pdf_from_storage,
    db_download_all_pdfs_from_storage,
    db_upload_faiss_index,
    db_download_faiss_index
)
from services.auth import verificar_senha, gerar_hash_senha, criar_sessao, verificar_sessao, encerrar_sessao, obter_username_sessao
from services.data_loader import processar_base_conhecimento

# Ajuste para rede corporativa (SSL)
ssl._create_default_https_context = ssl._create_unverified_context

app = FastAPI()

# Inicializa o banco de dados SQLite no início do app
@app.on_event("startup")
def startup_event():
    inicializar_banco()

# Permissões de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELOS DE DADOS ---
class Mensagem(BaseModel):
    pergunta: str

class Feedback(BaseModel):
    reclamacao: str
    email: str = None
    data_hora: str

class LoginRequest(BaseModel):
    username: str
    password: str

class RegistrarUsuarioRequest(BaseModel):
    email: str
    password: str

class VerificarUsuarioRequest(BaseModel):
    email: str
    code: str

# --- CONFIGURAÇÃO DE ARQUIVOS ESTÁTICOS ---
# Direciona para a pasta onde os PDFs são salvos localmente
caminho_pdfs = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "pdfs"))
if not os.path.exists(caminho_pdfs):
    os.makedirs(caminho_pdfs, exist_ok=True)

app.mount("/pdfs", StaticFiles(directory=caminho_pdfs), name="pdfs")

# --- FUNÇÕES AUXILIARES DE AUTENTICAÇÃO ---
def obter_usuario_logado(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token de autorizacao ausente ou invalido")
    token = authorization.split(" ")[1]
    if not verificar_sessao(token, required_role='admin'):
        raise HTTPException(status_code=401, detail="Sessao expirada ou acesso nao autorizado")
    return token

def obter_usuario_chat_logado(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token de autorizacao ausente ou invalido")
    token = authorization.split(" ")[1]
    if not verificar_sessao(token):
        raise HTTPException(status_code=401, detail="Sessao expirada ou invalida")
    return token

# --- ROTAS DO SISTEMA ---

@app.get("/api/health")
def home():
    return {"status": "Chatbot do Sebrae está online!"}

@app.post("/chat")
def chat(dados: Mensagem, token: str = Depends(obter_usuario_chat_logado)):
    try:
        resposta = gerar_resposta_chatbot(dados.pergunta)
        # Tenta pegar a fonte real da primeira resposta do vector store
        # Caso ocorra algum erro ou esteja vazio, cai no padrão
        trechos = buscar_informacao(dados.pergunta)
        fonte = "Manual de Educação Empreendedora.pdf"
        if isinstance(trechos, list) and len(trechos) > 0:
            fonte = trechos[0].get("fonte", fonte)
        return {"resposta": resposta, "fonte": fonte}
    except Exception as e:
        print("[CHAT ERROR]", str(e))
        return {"resposta": "Desculpe, tive um problema ao processar sua pergunta. Verifique minhas configurações ou chave de API.", "fonte": "Sistema"}

@app.post("/feedback")
async def salvar_feedback(fb: Feedback, token: str = Depends(obter_usuario_chat_logado)):
    try:
        db_salvar_feedback(fb.data_hora, fb.reclamacao, fb.email)
        return {"status": "sucesso"}
    except Exception as e:
        print("[FEEDBACK ERROR]", str(e))
        raise HTTPException(status_code=500, detail="Erro ao salvar feedback no Supabase")

# --- ROTAS DE AUTENTICAÇÃO DE USUÁRIOS ---

@app.post("/api/auth/register")
def registrar_usuario(req: RegistrarUsuarioRequest):
    import datetime
    
    # Verifica se e-mail já existe
    if db_obter_usuario(req.email):
        raise HTTPException(status_code=400, detail="Este e-mail ja esta cadastrado.")
        
    hash_senha, salt = gerar_hash_senha(req.password)
    data_cadastro = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    
    db_registrar_usuario(req.email, hash_senha, salt, data_cadastro, 'pendente')
    
    return {"status": "pendente", "mensagem": "Usuario registrado. Use o codigo 123456 para confirmar."}

@app.post("/api/auth/verify")
def verificar_usuario(req: VerificarUsuarioRequest):
    if req.code != "123456":
        raise HTTPException(status_code=400, detail="Codigo de verificacao invalido.")
        
    usuario = db_obter_usuario(req.email)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado.")
        
    # Ativa o usuário no Supabase
    db_ativar_usuario(req.email)
    
    # Cria a sessão
    token = criar_sessao(req.email, role='usuario')
    return {"token": token, "email": req.email}

@app.post("/api/auth/login")
def login_usuario(req: RegistrarUsuarioRequest):
    usuario = db_obter_usuario(req.email)
    if not usuario:
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")
        
    if usuario["status"] == "pendente":
        raise HTTPException(status_code=403, detail="Esta conta ainda nao foi ativada. Por favor, confirme seu e-mail.")
        
    hash_senha = usuario["password_hash"]
    salt = usuario["salt"]
    
    if verificar_senha(req.password, hash_senha, salt):
        token = criar_sessao(req.email, role='usuario')
        return {"token": token, "email": req.email}
    else:
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")

# --- ROTAS ADMINISTRATIVAS ---

@app.post("/api/admin/login")
def admin_login(req: LoginRequest):
    usuario = db_obter_admin(req.username)
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario ou senha incorretos")
        
    hash_senha = usuario["password_hash"]
    salt = usuario["salt"]
    
    if verificar_senha(req.password, hash_senha, salt):
        token = criar_sessao(req.username)
        return {"token": token, "username": req.username}
    else:
        raise HTTPException(status_code=401, detail="Usuario ou senha incorretos")

@app.post("/api/admin/logout")
def admin_logout(token: str = Depends(obter_usuario_logado)):
    encerrar_sessao(token)
    return {"status": "sucesso"}

@app.get("/api/admin/feedbacks")
def admin_listar_feedbacks(token: str = Depends(obter_usuario_logado)):
    return db_listar_feedbacks()

@app.get("/api/admin/usuarios")
def admin_listar_usuarios(token: str = Depends(obter_usuario_logado)):
    return db_listar_usuarios()

@app.post("/api/admin/usuarios")
def admin_cadastrar_usuario(req: RegistrarUsuarioRequest, token: str = Depends(obter_usuario_logado)):
    import datetime
    
    # Verifica se e-mail já existe
    if db_obter_usuario(req.email):
        raise HTTPException(status_code=400, detail="Este e-mail ja esta cadastrado.")
        
    hash_senha, salt = gerar_hash_senha(req.password)
    data_cadastro = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Cadastra direto como ATIVO no Supabase
    db_registrar_usuario(req.email, hash_senha, salt, data_cadastro, 'ativo')
    
    return {"status": "sucesso", "mensagem": f"Usuario {req.email} cadastrado com sucesso!"}

@app.get("/api/admin/feedbacks/export")
def admin_exportar_feedbacks(token: str = Depends(obter_usuario_logado)):
    feedbacks = db_listar_feedbacks()
    if not feedbacks:
        df = pd.DataFrame(columns=["Data/Hora", "Reclamacao", "E-mail"])
    else:
        df = pd.DataFrame(feedbacks)
        df = df.rename(columns={
            "data_hora": "Data/Hora",
            "reclamacao": "Reclamacao",
            "email": "E-mail"
        })
        df = df[["Data/Hora", "Reclamacao", "E-mail"]]
        
    # Preenche e-mails nulos com "Não informado"
    df["E-mail"] = df["E-mail"].apply(lambda x: x if x else "Não informado")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Feedbacks')
        
        # Estilização
        workbook = writer.book
        worksheet = writer.sheets['Feedbacks']
        
        from openpyxl.styles import PatternFill, Font
        azul_sebrae = PatternFill(start_color='005696', end_color='005696', fill_type='solid')
        fonte_branca = Font(color='FFFFFF', bold=True)
        
        for cell in worksheet[1]:
            cell.fill = azul_sebrae
            cell.font = fonte_branca
            
    output.seek(0)
    
    headers = {
        'Content-Disposition': 'attachment; filename="feedbacks.xlsx"'
    }
    return StreamingResponse(
        output, 
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers=headers
    )

# --- GERENCIAMENTO DE PDFS ---

@app.get("/api/admin/pdfs")
def admin_listar_pdfs(token: str = Depends(obter_usuario_logado)):
    documentos = db_listar_documentos()
    lista = []
    for doc in documentos:
        lista.append({
            "nome": doc["nome_arquivo"],
            "tamanho": doc["status"] if doc["status"] else "Sincronizado"
        })
    return lista

@app.post("/api/admin/pdfs/upload")
async def admin_upload_pdf(file: UploadFile = File(...), token: str = Depends(obter_usuario_logado)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF sao permitidos.")
        
    try:
        conteudo = await file.read()
        tamanho = len(conteudo)
        tamanho_fmt = f"{tamanho / (1024*1024):.2f} MB" if tamanho > 1024*1024 else f"{tamanho / 1024:.2f} KB"
        
        # Envia direto ao Supabase Storage
        db_upload_pdf_to_storage(file.filename, conteudo)
        
        import datetime
        data_hoje = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # Registra no Supabase DB
        db_registrar_documento(file.filename, data_hoje, tamanho_fmt)
        
        return {"status": "sucesso", "arquivo": file.filename}
    except Exception as e:
        print("[UPLOAD ERROR]", str(e))
        raise HTTPException(status_code=500, detail="Erro ao salvar arquivo PDF no Supabase Storage")

@app.delete("/api/admin/pdfs/{filename}")
def admin_deletar_pdf(filename: str, token: str = Depends(obter_usuario_logado)):
    filename_limpo = os.path.basename(filename)
    
    try:
        # Exclui do Supabase Storage
        db_delete_pdf_from_storage(filename_limpo)
        
        # Exclui do banco
        db_deletar_documento(filename_limpo)
        return {"status": "sucesso"}
    except Exception as e:
        print("[DELETE DB ERROR]", str(e))
        raise HTTPException(status_code=500, detail="Erro ao excluir arquivo do banco de dados no Supabase")

# --- SINCRONIZAÇÃO DE BASE VETORIAL ---

sync_status = {"status": "idle", "mensagem": "Nenhuma sincronizacao ativa."}

def tarefa_sincronizacao():
    global sync_status
    import tempfile
    try:
        sync_status["status"] = "running"
        sync_status["mensagem"] = "Conectando ao Supabase Storage e baixando PDFs..."
        
        with tempfile.TemporaryDirectory() as temp_dir:
            pdfs_baixados = db_download_all_pdfs_from_storage(temp_dir)
            
            if not pdfs_baixados:
                sync_status["status"] = "success"
                sync_status["mensagem"] = "Nenhum PDF encontrado na nuvem para sincronizar."
                return
                
            sync_status["mensagem"] = f"Lendo {len(pdfs_baixados)} PDFs e gerando vetores na OpenAI..."
            processar_base_conhecimento(temp_dir)
            
            sync_status["mensagem"] = "Enviando indices de IA gerados para a nuvem..."
            from services.vector_store import PASTA_DB
            sucesso_envio = db_upload_faiss_index(PASTA_DB)
            
            if sucesso_envio:
                sync_status["status"] = "success"
                sync_status["mensagem"] = "Sincronizacao concluida com sucesso na nuvem!"
            else:
                raise Exception("Erro ao salvar indices do FAISS no Supabase Storage.")
    except Exception as e:
        sync_status["status"] = "error"
        sync_status["mensagem"] = f"Erro na sincronizacao: {str(e)}"

@app.post("/api/admin/pdfs/sync")
def admin_sincronizar_pdfs(background_tasks: BackgroundTasks, token: str = Depends(obter_usuario_logado)):
    global sync_status
    if sync_status["status"] == "running":
        return {"status": "ocupado", "mensagem": "Uma sincronizacao ja esta em andamento."}
    
    background_tasks.add_task(tarefa_sincronizacao)
    return {"status": "iniciado", "mensagem": "Sincronizacao iniciada em segundo plano."}

@app.get("/api/admin/pdfs/sync/status")
def admin_status_sincronizacao(token: str = Depends(obter_usuario_logado)):
    return sync_status

# --- CONFIGURAÇÃO DO FRONTEND ESTÁTICO ---
# Deve ser o último a ser montado para que as rotas da API tenham prioridade
caminho_frontend = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(caminho_frontend):
    app.mount("/", StaticFiles(directory=caminho_frontend, html=True), name="frontend")

# --- INICIALIZAÇÃO DO SERVIDOR ---
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)