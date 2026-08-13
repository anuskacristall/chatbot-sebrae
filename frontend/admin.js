const API_URL = window.location.protocol.startsWith('http') ? '' : 'http://localhost:8001';
let syncInterval = null;

// Verifica se o usuário já está logado ao carregar a página
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('admin_token');
    const username = localStorage.getItem('admin_username');
    
    if (token && username) {
        exibirDashboard(username);
    } else {
        exibirLogin();
    }
    
    // Configura Drag and Drop de arquivos
    const dropZone = document.getElementById('drop-zone');
    if (dropZone) {
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropZone.classList.add('highlight');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropZone.classList.remove('highlight');
            }, false);
        });

        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {
                uploadPDF(files[0]);
            }
        });
    }
});

// Controle de Telas (Login / Dashboard)
function exibirLogin() {
    document.getElementById('login-container').classList.remove('hidden');
    document.getElementById('admin-dashboard').classList.add('hidden');
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_username');
}

function exibirDashboard(username) {
    document.getElementById('login-container').classList.add('hidden');
    document.getElementById('admin-dashboard').classList.remove('hidden');
    document.getElementById('logged-user-name').innerText = username;
    
    // Inicia na aba de PDFs
    mudarAba('pdfs');
    
    // Monitora status de sincronização
    verificarStatusSync(true);
}

// Lógica de Login e Logout
async function realizarLogin() {
    const userIn = document.getElementById('username').value.trim();
    const passIn = document.getElementById('password').value;
    const errorMsg = document.getElementById('login-error');
    
    if (!userIn || !passIn) {
        errorMsg.innerText = "Por favor, preencha todos os campos.";
        errorMsg.classList.remove('hidden');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/admin/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: userIn, password: passIn })
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('admin_token', data.token);
            localStorage.setItem('admin_username', data.username);
            errorMsg.classList.add('hidden');
            exibirDashboard(data.username);
        } else {
            const err = await response.json();
            errorMsg.innerText = err.detail || "Erro de login.";
            errorMsg.classList.remove('hidden');
        }
    } catch (e) {
        errorMsg.innerText = "Erro ao conectar com o servidor do chatbot.";
        errorMsg.classList.remove('hidden');
    }
}

function realizarLogout() {
    const token = localStorage.getItem('admin_token');
    if (token) {
        fetch(`${API_URL}/api/admin/logout`, {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token }
        }).catch(err => console.log("Erro ao invalidar token no logout:", err));
    }
    
    if (syncInterval) {
        clearInterval(syncInterval);
        syncInterval = null;
    }
    
    exibirLogin();
}

// Navegação entre abas
function mudarAba(aba) {
    const tabPdfs = document.getElementById('tab-pdfs');
    const tabFeedbacks = document.getElementById('tab-feedbacks');
    const tabUsuarios = document.getElementById('tab-usuarios');
    const secPdfs = document.getElementById('conteudo-pdfs');
    const secFeedbacks = document.getElementById('conteudo-feedbacks');
    const secUsuarios = document.getElementById('conteudo-usuarios');
    
    // Reseta abas ativas e esconde conteúdos
    tabPdfs.classList.remove('active');
    tabFeedbacks.classList.remove('active');
    if (tabUsuarios) tabUsuarios.classList.remove('active');
    
    secPdfs.classList.add('hidden');
    secFeedbacks.classList.add('hidden');
    if (secUsuarios) secUsuarios.classList.add('hidden');
    
    if (aba === 'pdfs') {
        tabPdfs.classList.add('active');
        secPdfs.classList.remove('hidden');
        carregarPDFs();
    } else if (aba === 'feedbacks') {
        tabFeedbacks.classList.add('active');
        secFeedbacks.classList.remove('hidden');
        carregarFeedbacks();
    } else if (aba === 'usuarios') {
        if (tabUsuarios) tabUsuarios.classList.add('active');
        if (secUsuarios) secUsuarios.classList.remove('hidden');
        carregarUsuarios();
    }
}

// LÓGICA DE PDFS

async function carregarPDFs() {
    const token = localStorage.getItem('admin_token');
    const tbody = document.getElementById('tbody-pdfs');
    
    try {
        const res = await fetch(`${API_URL}/api/admin/pdfs`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        if (res.status === 401) {
            realizarLogout();
            return;
        }
        
        const arquivos = await res.json();
        tbody.innerHTML = '';
        document.getElementById('pdf-count').innerText = `${arquivos.length} arquivo(s)`;
        
        if (arquivos.length === 0) {
            tbody.innerHTML = `<tr><td colspan="3" class="empty-row">Nenhum PDF carregado na pasta do chatbot.</td></tr>`;
            return;
        }
        
        arquivos.forEach(arq => {
            tbody.innerHTML += `
                <tr>
                    <td><strong>${arq.nome}</strong></td>
                    <td>${arq.tamanho}</td>
                    <td style="text-align: right;">
                        <button onclick="deletarPDF('${arq.nome}')" class="btn-delete-row">Excluir</button>
                    </td>
                </tr>
            `;
        });
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="3" class="error-row">Erro ao listar arquivos da API.</td></tr>`;
    }
}

async function uploadPDF(file) {
    if (!file) return;
    if (!file.name.endsWith('.pdf')) {
        alert("Por favor, selecione apenas arquivos .pdf.");
        return;
    }
    
    const token = localStorage.getItem('admin_token');
    
    // Oculta o banner de sincronização anterior se houver novas ações
    const syncBox = document.getElementById('sync-status-box');
    if (syncBox) syncBox.classList.add('hidden');
    
    const statusMsg = document.getElementById('upload-status');
    statusMsg.className = 'status-msg info';
    statusMsg.innerText = 'Enviando arquivo...';
    statusMsg.classList.remove('hidden');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const res = await fetch(`${API_URL}/api/admin/pdfs/upload`, {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token },
            body: formData
        });
        
        if (res.ok) {
            statusMsg.className = 'status-msg success';
            statusMsg.innerText = `Sucesso! "${file.name}" carregado.`;
            carregarPDFs();
        } else {
            const err = await res.json();
            statusMsg.className = 'status-msg error';
            statusMsg.innerText = `Erro: ${err.detail || 'Falha no upload.'}`;
        }
    } catch (e) {
        statusMsg.className = 'status-msg error';
        statusMsg.innerText = 'Erro de conexao ao enviar arquivo.';
    }
    
    // Some após 4 segundos
    setTimeout(() => {
        statusMsg.classList.add('hidden');
    }, 4000);
}

async function deletarPDF(nome) {
    if (!confirm(`Tem certeza que deseja excluir "${nome}"? A base vetorial continuará respondendo sobre ele até que você clique em Sincronizar.`)) return;
    
    const token = localStorage.getItem('admin_token');
    
    // Oculta o banner de sincronização anterior
    const syncBox = document.getElementById('sync-status-box');
    if (syncBox) syncBox.classList.add('hidden');
    
    try {
        const res = await fetch(`${API_URL}/api/admin/pdfs/${encodeURIComponent(nome)}`, {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        if (res.ok) {
            carregarPDFs();
        } else {
            const err = await res.json();
            alert(`Erro ao excluir: ${err.detail}`);
        }
    } catch (e) {
        alert('Erro ao se conectar com o servidor para excluir.');
    }
}

// SINCRONIZAÇÃO DE IA (FAISS)

async function sincronizarBaseDados() {
    const token = localStorage.getItem('admin_token');
    const btn = document.getElementById('btn-sync-ia');
    
    btn.disabled = true;
    btn.innerText = 'Iniciando...';
    
    try {
        const res = await fetch(`${API_URL}/api/admin/pdfs/sync`, {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        const data = await res.json();
        
        if (res.ok) {
            verificarStatusSync(true);
        } else {
            alert(`Erro na sincronização: ${data.detail}`);
            btn.disabled = false;
            btn.innerText = 'Sincronizar Base de Dados';
        }
    } catch (e) {
        alert('Erro ao disparar sincronização no servidor.');
        btn.disabled = false;
        btn.innerText = 'Sincronizar Base de Dados';
    }
}

async function verificarStatusSync(forcarInicio = false) {
    const token = localStorage.getItem('admin_token');
    if (!token) return;
    
    try {
        const res = await fetch(`${API_URL}/api/admin/pdfs/sync/status`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        if (!res.ok) return;
        const info = await res.json();
        
        const btn = document.getElementById('btn-sync-ia');
        const syncBox = document.getElementById('sync-status-box');
        const syncTitle = document.getElementById('sync-state-title');
        const syncDesc = document.getElementById('sync-state-desc');
        const spinner = syncBox.querySelector('.spinner');
        
        if (info.status === 'running') {
            btn.disabled = true;
            btn.innerText = 'Sincronizando...';
            btn.classList.add('loading');
            
            if (spinner) spinner.style.display = 'block';
            syncBox.className = 'sync-status-banner running';
            syncBox.classList.remove('hidden');
            syncTitle.innerText = 'Sincronizando Base de Dados...';
            syncDesc.innerText = info.mensagem;
            
            // Inicia ou mantém o polling a cada 3 segundos
            if (!syncInterval) {
                syncInterval = setInterval(() => verificarStatusSync(), 3000);
            }
        } else {
            btn.disabled = false;
            btn.innerText = 'Sincronizar Base de Dados';
            btn.classList.remove('loading');
            
            if (spinner) spinner.style.display = 'none';
            
            if (info.status === 'success') {
                if (forcarInicio) {
                    syncBox.classList.add('hidden');
                } else {
                    syncBox.className = 'sync-status-banner success';
                    syncBox.classList.remove('hidden');
                    syncTitle.innerText = 'Concluído!';
                    syncDesc.innerText = info.mensagem;
                    
                    // Esconde automaticamente após 8 segundos para limpar a tela
                    setTimeout(() => {
                        syncBox.classList.add('hidden');
                    }, 8000);
                }
            } else if (info.status === 'error') {
                if (forcarInicio) {
                    syncBox.classList.add('hidden');
                } else {
                    syncBox.className = 'sync-status-banner error';
                    syncBox.classList.remove('hidden');
                    syncTitle.innerText = 'Falha na Sincronização';
                    syncDesc.innerText = info.mensagem;
                }
            } else {
                // idle
                syncBox.classList.add('hidden');
            }
            
            // Para o polling
            if (syncInterval) {
                clearInterval(syncInterval);
                syncInterval = null;
            }
        }
    } catch (e) {
        console.error("Erro ao verificar status de sincronização:", e);
    }
}

// LÓGICA DE FEEDBACKS

async function carregarFeedbacks() {
    const token = localStorage.getItem('admin_token');
    const tbody = document.getElementById('tbody-feedbacks');
    
    try {
        const res = await fetch(`${API_URL}/api/admin/feedbacks`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        if (res.status === 401) {
            realizarLogout();
            return;
        }
        
        const feedbacks = await res.json();
        tbody.innerHTML = '';
        
        if (feedbacks.length === 0) {
            tbody.innerHTML = `<tr><td colspan="3" class="empty-row">Nenhum feedback registrado no sistema até o momento.</td></tr>`;
            return;
        }
        
        feedbacks.forEach(fb => {
            tbody.innerHTML += `
                <tr>
                    <td class="date-cell">${fb.data_hora}</td>
                    <td class="feedback-text-cell">${fb.reclamacao}</td>
                    <td>${fb.email ? `<strong>${fb.email}</strong>` : '<span class="not-informed">Não informado</span>'}</td>
                </tr>
            `;
        });
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="3" class="error-row">Erro de conexao ao carregar feedbacks.</td></tr>`;
    }
}

async function exportarFeedbacksExcel() {
    const token = localStorage.getItem('admin_token');
    
    try {
        const res = await fetch(`${API_URL}/api/admin/feedbacks/export`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        if (res.status === 401) {
            realizarLogout();
            return;
        }
        
        if (!res.ok) {
            alert('Erro ao exportar feedbacks.');
            return;
        }
        
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `feedbacks_sebrae_${new Date().toISOString().slice(0,10)}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (e) {
        alert('Erro de conexao ao exportar arquivo.');
    }
}

async function carregarUsuarios() {
    const token = localStorage.getItem('admin_token');
    const tbody = document.getElementById('tbody-usuarios');
    if (!tbody) return;
    
    try {
        const res = await fetch(`${API_URL}/api/admin/usuarios`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        if (res.status === 401) {
            realizarLogout();
            return;
        }
        
        const usuarios = await res.json();
        tbody.innerHTML = '';
        
        if (usuarios.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="empty-row">Nenhum usuário cadastrado até o momento.</td></tr>`;
            return;
        }
        
        usuarios.forEach(user => {
            const statusClass = user.status === 'ativo' ? 'status-badge-ativo' : 'status-badge-pendente';
            tbody.innerHTML += `
                <tr>
                    <td><strong>${user.id}</strong></td>
                    <td>${user.email}</td>
                    <td class="date-cell">${user.data_cadastro}</td>
                    <td><span class="status-badge ${statusClass}">${user.status.toUpperCase()}</span></td>
                </tr>
            `;
        });
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="4" class="error-row">Erro de conexão ao carregar usuários.</td></tr>`;
    }
}

async function adicionarUsuario() {
    const token = localStorage.getItem('admin_token');
    const emailIn = document.getElementById('admin-add-email').value.trim();
    const senhaIn = document.getElementById('admin-add-senha').value.trim();
    const statusMsg = document.getElementById('admin-add-user-status');
    const btn = document.getElementById('btn-admin-add-user');
    
    if (!emailIn || !senhaIn) {
        alert("Preencha todos os campos.");
        return;
    }
    
    btn.disabled = true;
    btn.innerText = 'Cadastrando...';
    
    statusMsg.className = 'status-msg info';
    statusMsg.innerText = 'Processando cadastro...';
    statusMsg.classList.remove('hidden');
    
    try {
        const res = await fetch(`${API_URL}/api/admin/usuarios`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ email: emailIn, password: senhaIn })
        });
        
        const data = await res.json();
        
        if (res.ok) {
            statusMsg.className = 'status-msg success';
            statusMsg.innerText = `Sucesso: Usuário "${emailIn}" cadastrado e ativado!`;
            
            // Limpa o e-mail mas mantém a senha padrão
            document.getElementById('admin-add-email').value = '';
            
            // Recarrega a tabela de usuários
            carregarUsuarios();
        } else {
            statusMsg.className = 'status-msg error';
            statusMsg.innerText = `Erro: ${data.detail || 'Não foi possível cadastrar.'}`;
        }
    } catch (e) {
        statusMsg.className = 'status-msg error';
        statusMsg.innerText = 'Erro de conexão com o servidor.';
    } finally {
        btn.disabled = false;
        btn.innerText = 'Adicionar Usuário';
        
        // Some após 5 segundos
        setTimeout(() => {
            statusMsg.classList.add('hidden');
        }, 5000);
    }
}
