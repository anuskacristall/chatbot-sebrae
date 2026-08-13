const API_URL = window.location.protocol.startsWith('http') ? '' : 'http://localhost:8001';

let originalModalContent = null;
let feedbackCloseTimeout = null; // Timer para fechar modal após envio (evita reabertura indevida)

// Inicialização segura
document.addEventListener('DOMContentLoaded', () => {
    // Configura o envio com a tecla Enter
    const userInput = document.getElementById('user-input');
    if (userInput) {
        userInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') enviarPergunta();
        });
    }
});

async function enviarPergunta() {
    const input = document.getElementById('user-input');
    const chatWindow = document.getElementById('chat-window');
    const pergunta = input.value.trim();

    if (!pergunta) return;

    // 1. Adiciona a pergunta do usuário na tela (lado direito)
    chatWindow.innerHTML += `
        <div class="user-msg-container">
            <div class="user-msg">${pergunta}</div>
        </div>`;
    
    input.value = '';
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // 2. Cria o balão do bot com as bolinhas animadas
    const botContainerId = 'bot-' + Date.now();
    chatWindow.innerHTML += `
        <div class="bot-msg-container" id="${botContainerId}">
            <div class="bot-msg">
                <div class="typing">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            </div>
        </div>`;
    chatWindow.scrollTop = chatWindow.scrollHeight;

    try {
        const token = localStorage.getItem('usuario_token');
        // 3. Faz a chamada para o seu backend Python com Token de Sessão
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ pergunta: pergunta })
        });

        if (response.status === 401) {
            realizarLogoutChat();
            return;
        }

        const data = await response.json();
        const botContainer = document.getElementById(botContainerId);
        
        // 4. Substitui as bolinhas pelo texto final
        // Em vez de .innerText, use .innerHTML + o tradutor marked
    botContainer.querySelector('.bot-msg').innerHTML = marked.parse(data.resposta);

        // 5. LOG TÉCNICO (F12): Mostra a fonte apenas no console para você conferir
        if (data.fonte) {
            console.log(`[DEBUG SEBRAE] Fonte da resposta: ${data.fonte}`);
        }

    } catch (error) {
        // Trata erro de conexão (caso o Python esteja desligado)
        const botContainer = document.getElementById(botContainerId);
        botContainer.querySelector('.bot-msg').innerHTML = '<span style="color:red">Erro de conexão. Verifique o backend.</span>';
    }

    // Garante que o chat role para baixo no final
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// Abre e fecha o modal
function toggleFeedback() {
    const modal = document.getElementById('feedback-modal');
    if (!modal) return;
    
    const modalContent = modal.querySelector('.modal-content');
    if (!originalModalContent && modalContent) {
        originalModalContent = modalContent.innerHTML;
    }
    
    const isOpening = modal.classList.contains('hidden');

    // Se alguma ação async foi agendada, cancela para não reabrir de forma inesperada
    if (feedbackCloseTimeout) {
        clearTimeout(feedbackCloseTimeout);
        feedbackCloseTimeout = null;
    }

    if (isOpening && originalModalContent && modalContent) {
        // Reset to original form when opening
        modalContent.innerHTML = originalModalContent;

        // Reconecta o handler de enviar (recriado ao resetar o HTML)
        const btnEnviar = modal.querySelector('.btn-send');
        if (btnEnviar) btnEnviar.onclick = enviarFeedback;
        const btnCancelar = modal.querySelector('.btn-cancel');
        if (btnCancelar) btnCancelar.onclick = toggleFeedback;
    }

    modal.classList.toggle('hidden');
}

// Função para enviar os dados para o Backend
async function enviarFeedback() {
    const texto = document.getElementById('feedback-text').value;
    const email = document.getElementById('feedback-email').value;
    const modalContent = document.querySelector('.modal-content'); // Pega a caixinha branca

    if (!texto) {
        alert("Por favor, descreva o que você não encontrou.");
        return;
    }

    try {
        const token = localStorage.getItem('usuario_token');
        const response = await fetch(`${API_URL}/feedback`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ 
                reclamacao: texto, 
                email: email,
                data_hora: new Date().toLocaleString('pt-BR')
            })
        });

        if (response.status === 401) {
            realizarLogoutChat();
            return;
        }

        if (response.ok) {
            // Substitui o conteúdo do formulário por uma mensagem de sucesso
            modalContent.innerHTML = `
                <div style="padding: 20px;">
                    <h2 style="color: #28a745;">✓ Enviado!</h2>
                    <p style="margin-top: 15px;">Obrigado por ajudar o Sebrae a melhorar.</p>
                    <button onclick="toggleFeedback()" style="margin-top: 20px; padding: 10px 20px; cursor: pointer; background: #005696; color: white; border: none; border-radius: 5px;">Fechar</button>
                </div>
            `;
            
            // Fecha automaticamente depois de 3 segundos
            if (feedbackCloseTimeout) {
                clearTimeout(feedbackCloseTimeout);
            }
            feedbackCloseTimeout = setTimeout(() => {
                toggleFeedback();
                feedbackCloseTimeout = null;
            }, 3000);
        }
    } catch (error) {
        alert("Erro ao conectar com o servidor.");
    }
}

// --- CONTROLE DE AUTENTICAÇÃO DO USUÁRIO (CHAT) ---

let activeLoginTab = 'entrar';

document.addEventListener('DOMContentLoaded', () => {
    verificarAutenticacaoChat();
});

function verificarAutenticacaoChat() {
    const token = localStorage.getItem('usuario_token');
    const email = localStorage.getItem('usuario_email');
    const overlay = document.getElementById('login-overlay');
    const btnLogout = document.getElementById('btn-logout-chat');
    
    if (token && email) {
        if (overlay) overlay.classList.add('hidden');
        if (btnLogout) btnLogout.classList.remove('hidden');
    } else {
        if (overlay) overlay.classList.remove('hidden');
        if (btnLogout) btnLogout.classList.add('hidden');
        resetarFormulariosLogin();
    }
}

function alternarLoginTab(tab) {
    activeLoginTab = tab;
    
    const tabEntrar = document.getElementById('tab-entrar');
    const tabCadastrar = document.getElementById('tab-cadastrar');
    const formEntrar = document.getElementById('form-entrar');
    const formCadastrar = document.getElementById('form-cadastrar');
    const formVerificar = document.getElementById('form-verificar');
    
    // Oculta status msg
    const statusMsg = document.getElementById('login-status-msg');
    if (statusMsg) statusMsg.classList.add('hidden');
    
    if (tab === 'entrar') {
        if (tabEntrar) tabEntrar.classList.add('active');
        if (tabCadastrar) tabCadastrar.classList.remove('active');
        if (formEntrar) formEntrar.classList.remove('hidden');
        if (formCadastrar) formCadastrar.classList.add('hidden');
        if (formVerificar) formVerificar.classList.add('hidden');
    } else if (tab === 'cadastrar') {
        if (tabEntrar) tabEntrar.classList.remove('active');
        if (tabCadastrar) tabCadastrar.classList.add('active');
        if (formEntrar) formEntrar.classList.add('hidden');
        if (formCadastrar) formCadastrar.classList.remove('hidden');
        if (formVerificar) formVerificar.classList.add('hidden');
    }
}

function resetarFormulariosLogin() {
    const loginEmail = document.getElementById('login-email');
    const loginSenha = document.getElementById('login-senha');
    const cadastroEmail = document.getElementById('cadastro-email');
    const cadastroSenha = document.getElementById('cadastro-senha');
    const verificarCodigoEl = document.getElementById('verificar-codigo');
    
    if (loginEmail) loginEmail.value = '';
    if (loginSenha) loginSenha.value = '';
    if (cadastroEmail) cadastroEmail.value = '';
    if (cadastroSenha) cadastroSenha.value = '';
    if (verificarCodigoEl) verificarCodigoEl.value = '';
    alternarLoginTab('entrar');
}

function mostrarStatusMsg(texto, tipo) {
    const statusMsg = document.getElementById('login-status-msg');
    if (statusMsg) {
        statusMsg.innerText = texto;
        statusMsg.className = `login-status-msg ${tipo}`;
        statusMsg.classList.remove('hidden');
    }
}

async function logarUsuario() {
    const email = document.getElementById('login-email').value.trim();
    const senha = document.getElementById('login-senha').value;
    
    if (!email || !senha) {
        mostrarStatusMsg("Preencha todos os campos.", "error");
        return;
    }
    
    const btn = document.getElementById('btn-submit-login');
    btn.disabled = true;
    btn.innerText = 'Entrando...';
    
    try {
        const response = await fetch(`${API_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email, password: senha })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            localStorage.setItem('usuario_token', data.token);
            localStorage.setItem('usuario_email', data.email);
            verificarAutenticacaoChat();
        } else {
            mostrarStatusMsg(data.detail || "Erro ao realizar login.", "error");
        }
    } catch (e) {
        mostrarStatusMsg("Erro de conexão com o servidor.", "error");
    } finally {
        btn.disabled = false;
        btn.innerText = 'Entrar';
    }
}

async function cadastrarUsuario() {
    const email = document.getElementById('cadastro-email').value.trim();
    const senha = document.getElementById('cadastro-senha').value;
    
    if (!email || !senha) {
        mostrarStatusMsg("Preencha todos os campos.", "error");
        return;
    }
    
    const btn = document.getElementById('btn-submit-cadastro');
    btn.disabled = true;
    btn.innerText = 'Cadastrando...';
    
    try {
        const response = await fetch(`${API_URL}/api/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email, password: senha })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('form-cadastrar').classList.add('hidden');
            document.getElementById('form-verificar').classList.remove('hidden');
            mostrarStatusMsg(data.mensagem || "Cadastro inicial realizado. Digite o código de ativação.", "success");
        } else {
            mostrarStatusMsg(data.detail || "Erro ao realizar cadastro.", "error");
        }
    } catch (e) {
        mostrarStatusMsg("Erro de conexão com o servidor.", "error");
    } finally {
        btn.disabled = false;
        btn.innerText = 'Cadastrar';
    }
}

async function verificarCodigo() {
    const email = document.getElementById('cadastro-email').value.trim();
    const codigo = document.getElementById('verificar-codigo').value.trim();
    
    if (!codigo) {
        mostrarStatusMsg("Digite o código de verificação.", "error");
        return;
    }
    
    const btn = document.getElementById('btn-submit-verificar');
    btn.disabled = true;
    btn.innerText = 'Verificando...';
    
    try {
        const response = await fetch(`${API_URL}/api/auth/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email, code: codigo })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            localStorage.setItem('usuario_token', data.token);
            localStorage.setItem('usuario_email', data.email);
            verificarAutenticacaoChat();
        } else {
            mostrarStatusMsg(data.detail || "Código de verificação incorreto.", "error");
        }
    } catch (e) {
        mostrarStatusMsg("Erro de conexão com o servidor.", "error");
    } finally {
        btn.disabled = false;
        btn.innerText = 'Confirmar Código';
    }
}

function voltarParaCadastro() {
    document.getElementById('form-verificar').classList.add('hidden');
    document.getElementById('form-cadastrar').classList.remove('hidden');
    const statusMsg = document.getElementById('login-status-msg');
    if (statusMsg) statusMsg.classList.add('hidden');
}

function realizarLogoutChat() {
    localStorage.removeItem('usuario_token');
    localStorage.removeItem('usuario_email');
    verificarAutenticacaoChat();
}


