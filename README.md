# 🤖 Chatbot Inteligente Sebrae - RAG & Inteligência Artificial

Uma solução completa de Assistente Virtual Inteligente desenvolvida para o **Sebrae**, utilizando **RAG (Retrieval-Augmented Generation)** com a API da **OpenAI** e **FAISS** para busca vetorial semântica em base de conhecimento documental (PDFs oficiais).

---

## 🌟 Principais Funcionalidades

- 💬 **Interface de Atendimento Interativa**: Chat inteligente voltado para dúvidas de empreendedores e clientes do Sebrae.
- 📚 **Arquitetura RAG (Busca Vetorial)**: Consulta a documentos e Manuais em PDF utilizando indexação por embeddings e FAISS para garantir respostas precisas e contextualizadas.
- ⚙️ **Painel Administrativo Completo (`admin.html`)**:
  - Gerenciamento e upload dinâmico de novos documentos PDF.
  - Reindexação automática da base de conhecimento vetorial.
  - Gestão de usuários e permissões de acesso.
  - Monitoramento de feedbacks e dúvidas dos usuários.
- 🐳 **Ambiente Containerizado**: Suporte a **Docker** e **Docker Compose** para rápida implantação.

---

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3.10+, FastAPI, SQLite.
- **IA & RAG**: OpenAI API (GPT-4 / GPT-3.5-Turbo), FAISS (Facebook AI Similarity Search), LangChain / PyPDF2.
- **Frontend**: HTML5, CSS3 Moderno (Design System Sebrae), JavaScript (ES6+).
- **Infraestrutura**: Docker & Docker Compose.

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────┐       ┌─────────────────┐       ┌──────────────────────┐
│  Cliente Web    │ ────> │  FastAPI Server │ ────> │  Engine RAG + FAISS  │
│  (Chat / Admin) │ <──── │   (REST API)    │ <──── │ + OpenAI Embeddings  │
└─────────────────┘       └─────────────────┘       └──────────────────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │ Banco de Dados  │
                          │     SQLite      │
                          └─────────────────┘
```

---

## 🚀 Como Executar o Projeto Localmente

### Pré-requisitos
- Python 3.10 ou superior
- Git
- Chave de API da OpenAI (`OPENAI_API_KEY`)

### 1. Clonar o Repositório
```bash
git clone https://github.com/SEU-USUARIO/chatbotsebrae.git
cd chatbotsebrae
```

### 2. Configurar Variáveis de Ambiente
Navegue até a pasta `backend` e duplique o arquivo `.env.example` para `.env`:
```bash
cd backend
cp .env.example .env
```
Edite o arquivo `.env` inserindo sua chave da OpenAI:
```env
OPENAI_API_KEY=sk-seu_token_openai_aqui
```

### 3. Instalar Dependências e Executar o Backend
```bash
pip install -r requirements.txt
python app.py
```
O servidor FastAPI estará rodando em `http://localhost:8000`.

### 4. Acessar o Frontend
Basta abrir o arquivo `frontend/index.html` no seu navegador ou utilizar uma extensão como o *Live Server* no VS Code. Para acessar a área de administração, abra `frontend/admin.html`.

---

## 🐳 Executando com Docker

Se preferir rodar com Docker Compose:
```bash
docker-compose up --build
```

---

## ✒️ Licença e Uso

Este projeto foi desenvolvido como parte de iniciativas do Sebrae para inovação em atendimento digital ao cliente.