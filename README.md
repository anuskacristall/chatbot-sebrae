# 🤖 Chatbot Inteligente Sebrae - RAG & Inteligência Artificial / AI RAG Chatbot

![Version](https://img.shields.io/badge/Vers%C3%A3o-v2.0-blue.svg)
![Status](https://img.shields.io/badge/Status-Conclu%C3%ADdo-brightgreen.svg)

---

### 🌐 Select Language / Selecione o Idioma

> **[ 🇧🇷 Português ](#-português)** &nbsp;&nbsp;|&nbsp;&nbsp; **[ 🇺🇸 English ](#-english)**

---

<a name="-português"></a>
## 🇧🇷 Português

Uma solução completa de **Assistente Virtual Inteligente** desenvolvida para o **Sebrae**, utilizando **RAG (Retrieval-Augmented Generation)** com a API da **OpenAI** e **FAISS** para busca vetorial semântica em base de conhecimento documental (PDFs oficiais).

### 🌟 Principais Funcionalidades

- 💬 **Interface de Atendimento Interativa**: Chat inteligente voltado para dúvidas de empreendedores e clientes do Sebrae.
- 📚 **Arquitetura RAG (Busca Vetorial)**: Consulta a documentos e Manuais em PDF utilizando indexação por embeddings e FAISS para garantir respostas precisas e contextualizadas.
- ⚙️ **Painel Administrativo Completo (`admin.html`)**:
  - Gerenciamento e upload dinâmico de novos documentos PDF.
  - Reindexação automática da base de conhecimento vetorial.
  - Gestão de usuários e permissões de acesso.
  - Monitoramento de feedbacks e dúvidas dos usuários.
- 🐳 **Ambiente Containerizado**: Suporte a **Docker** e **Docker Compose** para rápida implantação.

### 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3.10+, FastAPI, SQLite.
- **IA & RAG**: OpenAI API (GPT-4 / GPT-3.5-Turbo), FAISS (Facebook AI Similarity Search), LangChain / PyPDF2.
- **Frontend**: HTML5, CSS3 Moderno (Design System Sebrae), JavaScript (ES6+).
- **Infraestrutura**: Docker & Docker Compose.

### 🚀 Como Executar o Projeto Localmente

1. **Clonar o Repositório:**
   ```bash
   git clone https://github.com/anuskacristall/chatbot-sebrae.git
   cd chatbot-sebrae
   ```

2. **Configurar Variáveis de Ambiente:**
   Navegue até a pasta `backend` e duplique o arquivo `.env.example` para `.env`:
   ```bash
   cd backend
   cp .env.example .env
   ```
   Edite o arquivo `.env` inserindo sua chave da OpenAI:
   ```env
   OPENAI_API_KEY=sk-seu_token_openai_aqui
   ```

3. **Instalar Dependências e Executar o Backend:**
   ```bash
   pip install -r requirements.txt
   python app.py
   ```
   O servidor FastAPI estará rodando em `http://localhost:8000`.

4. **Acessar o Frontend:**
   Abra o arquivo `frontend/index.html` no seu navegador. Para acessar a área de administração, abra `frontend/admin.html`.

---

<a name="-english"></a>
## 🇺🇸 English

A complete **AI Virtual Assistant Solution** built for **Sebrae**, powered by **RAG (Retrieval-Augmented Generation)** with **OpenAI API** and **FAISS** vector search across official PDF document knowledge bases.

### 🌟 Key Features

- 💬 **Interactive Support Interface**: Intelligent chatbot answering entrepreneur questions with context-aware responses.
- 📚 **RAG Architecture (Vector Search)**: Queries PDF manuals and guides via embeddings index & FAISS to provide precise factual answers.
- ⚙️ **Full Administrative Dashboard (`admin.html`)**:
  - Dynamic upload and management of new PDF knowledge base documents.
  - Automatic re-indexing of vector databases.
  - User access control and permissions.
  - User feedback and query monitoring.
- 🐳 **Containerized Environment**: Docker & Docker Compose setup for fast setup and deployment.

### 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, SQLite.
- **AI & RAG Engine**: OpenAI API (GPT-4 / GPT-3.5-Turbo), FAISS (Facebook AI Similarity Search), LangChain / PyPDF2.
- **Frontend**: HTML5, Modern CSS3 (Sebrae Design System), JavaScript (ES6+).
- **DevOps**: Docker & Docker Compose.

### 🚀 How to Run Locally

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/anuskacristall/chatbot-sebrae.git
   cd chatbot-sebrae
   ```

2. **Set Environment Variables:**
   Navigate to the `backend` directory and copy `.env.example` to `.env`:
   ```bash
   cd backend
   cp .env.example .env
   ```
   Add your OpenAI API Key to `.env`:
   ```env
   OPENAI_API_KEY=sk-your_openai_token_here
   ```

3. **Install Dependencies & Start Backend:**
   ```bash
   pip install -r requirements.txt
   python app.py
   ```
   FastAPI server runs at `http://localhost:8000`.

4. **Open Frontend:**
   Open `frontend/index.html` in your browser. For admin access, open `frontend/admin.html`.

---

*Desenvolvido para apoio ao atendimento digital ao cliente. / Developed for digital customer support automation.*