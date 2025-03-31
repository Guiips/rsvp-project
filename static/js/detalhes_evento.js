// Carrega os dados do evento ao iniciar
document.addEventListener('DOMContentLoaded', function() {
    carregarDadosEvento();
    
    // Adiciona listeners para filtros
    document.getElementById('pesquisaConvidado').addEventListener('input', filtrarConvidados);
    document.getElementById('filtroStatus').addEventListener('change', filtrarConvidados);
    document.getElementById('filtroObservacoes').addEventListener('change', filtrarConvidados);
    
    // Listener para envio de emails
    document.getElementById('enviarEmails').addEventListener('click', function(e) {
        e.preventDefault();
        preVisualizarEmail();
    });
    
    // Inicializa tooltips do Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Handler para auto-salvar em textareas
    document.querySelectorAll('textarea[data-autosave]').forEach(textarea => {
        let timeout;
        textarea.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                const email = this.dataset.email;
                const observacoes = this.value;
                atualizarObservacoes(email, observacoes);
            }, 1000);
        });
    });
});

// Carrega os dados do evento
async function carregarDadosEvento() {
    try {
        const eventoId = getEventoId();
        console.log("Carregando dados do evento:", eventoId);
        
        const response = await fetch(`/api/eventos/${eventoId}`);
        
        // Verificação de erro na resposta
        if (!response.ok) {
            const text = await response.text();
            console.error('Resposta não-OK:', text);
            throw new Error(`Erro ${response.status}: ${response.statusText}`);
        }
        
        // Verificação do tipo de conteúdo
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('Resposta não-JSON:', text);
            throw new Error('Resposta não é JSON');
        }
        
        const evento = await response.json();
        console.log("Dados do evento carregados:", evento);
        
        // Preenche os dados do evento
        preencherDadosEvento(evento);
        
        // Atualiza estatísticas
        const convidados = evento.convidados || [];
        console.log("Total de convidados:", convidados.length);
        atualizarEstatisticas(convidados);
        
        // Renderiza a lista de convidados
        renderizarConvidados(convidados);
        
    } catch (error) {
        console.error('Erro ao carregar dados do evento:', error);
        showAlert('Erro ao carregar dados do evento: ' + error.message, 'danger');
    }
}

// Preenche os dados básicos do evento
function preencherDadosEvento(evento) {
    document.getElementById('nomeEvento').textContent = evento.nome || 'Sem nome';
    document.getElementById('responsavel').textContent = evento.responsavel || 'Não informado';
    document.getElementById('data').textContent = formatarData(evento.data) || 'Não informada';
    document.getElementById('hora').textContent = evento.hora || 'Não informada';
    document.getElementById('local').textContent = evento.local || 'Não informado';
    document.getElementById('categoria').textContent = evento.categoria || 'Não informada';
    document.getElementById('descricao').textContent = evento.descricao || 'Sem descrição';
}

// Atualiza as estatísticas do evento
function atualizarEstatisticas(convidados) {
    const stats = convidados.reduce((acc, conv) => {
        acc.total++;
        const status = (conv.status || 'pendente').toLowerCase();
        acc[status] = (acc[status] || 0) + 1;
        return acc;
    }, { total: 0 });
    
    document.getElementById('totalConvidados').textContent = stats.total || 0;
    document.getElementById('totalConfirmados').textContent = stats.confirmado || 0;
    document.getElementById('totalRecusados').textContent = stats.recusado || 0;
    document.getElementById('totalPendentes').textContent = stats.pendente || 0;
}

// Renderiza a lista de convidados
function renderizarConvidados(convidados) {
    const tbody = document.getElementById('listaConvidados');
    tbody.innerHTML = '';
    
    if (!convidados || convidados.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">Nenhum convidado cadastrado.</td>
            </tr>
        `;
        return;
    }
    
    convidados.forEach(convidado => {
        // Função para escapar caracteres especiais
        const escapeHtml = (unsafe) => {
            if (!unsafe) return '';
            return unsafe
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        };
        
        const row = document.createElement('tr');
        
        // Verificação segura para observações
        const obsHtml = convidado.observacoes ? 
            `<button class="btn btn-info btn-sm" onclick="mostrarObservacoes('${escapeHtml(convidado.nome)}', '${escapeHtml(convidado.email)}', '${escapeHtml(convidado.status)}', '${escapeHtml(convidado.observacoes)}')">
                <i class="bi bi-info-circle"></i> Ver
            </button>` : 
            '<span class="text-muted">-</span>';
        
        row.innerHTML = `
            <td>${escapeHtml(convidado.nome)}</td>
            <td>${escapeHtml(convidado.email)}</td>
            <td>${convidado.telefone ? escapeHtml(convidado.telefone) : '-'}</td>
            <td><span class="badge ${getStatusClass(convidado.status)}">${escapeHtml(convidado.status)}</span></td>
            <td>${obsHtml}</td>
            <td>
                <button class="btn btn-primary btn-sm me-1" onclick="reenviarEmail('${escapeHtml(convidado.email)}', '${escapeHtml(convidado.nome)}')" title="Reenviar Email">
                    <i class="bi bi-envelope"></i>
                </button>
                <button class="btn btn-danger btn-sm" onclick="excluirConvidado('${escapeHtml(convidado.email)}')" title="Excluir">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// Função para mostrar observações
function mostrarObservacoes(nome, email, status, observacoes) {
    Swal.fire({
        title: 'Observações do Convidado',
        html: `
            <div class="text-start">
                <p><strong>Nome:</strong> ${nome}</p>
                <p><strong>Email:</strong> ${email}</p>
                <p><strong>Status:</strong> ${status}</p>
                <hr>
                <p><strong>Observações:</strong></p>
                <p>${observacoes ? observacoes : 'Nenhuma observação disponível.'}</p>
            </div>
        `,
        icon: 'info',
        confirmButtonText: 'Fechar'
    });
}

// Função para mostrar o email antes de enviar
function preVisualizarEmail() {
    // Busca dados do evento
    const eventoNome = document.getElementById('nomeEvento').textContent;
    const eventoData = document.getElementById('data').textContent;
    const eventoHora = document.getElementById('hora').textContent;
    const eventoLocal = document.getElementById('local').textContent;
    const eventoDescricao = document.getElementById('descricao').textContent || eventoNome;
    const eventoResponsavel = document.getElementById('responsavel').textContent;
    
    // Template comprovadamente compatível com Gmail
    const emailPadrao = `
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <title>Convite para ${eventoNome}</title>
</head>
<body style="margin:0; padding:0; font-family:Arial, Helvetica, sans-serif;">
  <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#f7f7f7;">
    <tr>
      <td align="center">
        <table border="0" cellpadding="0" cellspacing="0" width="600" style="background-color:#ffffff; border:1px solid #e0e0e0;">
          <!-- Cabeçalho -->
          <tr>
            <td align="center" bgcolor="#1976D2" style="padding:20px;">
              <h1 style="color:#ffffff; margin:0; font-size:24px; font-weight:bold;">Convite Oficial</h1>
            </td>
          </tr>
          
          <!-- Conteúdo -->
          <tr>
            <td style="padding:30px 20px;">
              <p style="margin-top:0;">Bom dia, Dr(a). [Nome do Convidado],</p>
              
              <p style="margin-bottom:15px;">Meu nome é ${eventoResponsavel} e falo em nome da <strong>${eventoNome}</strong>.</p>
              
              <p style="margin-bottom:15px;">É com grande satisfação que oficializamos o convite para o <strong>${eventoDescricao}</strong>.</p>
              
              <!-- Detalhes do evento -->
              <table border="0" cellpadding="10" cellspacing="0" width="100%" style="background-color:#f5f5f5; margin:20px 0; border-left:4px solid #1976D2;">
                <tr>
                  <td width="100"><strong>Data:</strong></td>
                  <td>${eventoData}</td>
                </tr>
                <tr>
                  <td width="100"><strong>Horário:</strong></td>
                  <td>${eventoHora}</td>
                </tr>
                <tr>
                  <td width="100"><strong>Local:</strong></td>
                  <td>${eventoLocal}</td>
                </tr>
              </table>
              
              <p style="margin-bottom:25px;">Por gentileza, gostaríamos de saber se podemos confirmar sua presença.</p>
              
              <!-- Botões -->
              <table border="0" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center">
                    <table border="0" cellpadding="0" cellspacing="0">
                      <tr>
                        <td bgcolor="#4CAF50" style="padding:12px 18px; border-radius:4px;">
                          <a href="[Link de Confirmação]" target="_blank" style="color:#ffffff; text-decoration:none; display:inline-block; font-weight:bold;">Confirmar Presença</a>
                        </td>
                        <td width="20">&nbsp;</td>
                        <td bgcolor="#f44336" style="padding:12px 18px; border-radius:4px;">
                          <a href="[Link de Recusa]" target="_blank" style="color:#ffffff; text-decoration:none; display:inline-block; font-weight:bold;">Não Poderei Comparecer</a>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
              
              <p style="margin-top:30px;">Atenciosamente,<br />
              ${eventoResponsavel}<br />
              ${eventoNome}</p>
            </td>
          </tr>
          
          <!-- Rodapé -->
          <tr>
            <td bgcolor="#f5f5f5" style="padding:15px; text-align:center; color:#757575; font-size:12px;">
              <p style="margin:0;">Este é um e-mail automático. Por favor, não responda diretamente a esta mensagem.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
    `;
    
    // O restante do código permanece o mesmo
    Swal.fire({
        title: 'Visualizar Email',
        html: `
            <div class="form-group">
                <label for="assuntoEmail">Assunto:</label>
                <input id="assuntoEmail" class="form-control" value="Convite para ${eventoNome}">
            </div>
            <div class="form-group mt-3">
                <label for="corpoEmail">Conteúdo do Email:</label>
                <textarea id="corpoEmail" class="form-control" style="height: 300px;">${emailPadrao}</textarea>
            </div>
            <div class="alert alert-info mt-3">
                <small>[Nome do Convidado], [Link de Confirmação] e [Link de Recusa] serão substituídos automaticamente para cada convidado.</small>
            </div>
        `,
        width: 800,
        showCancelButton: true,
        confirmButtonText: 'Enviar Emails',
        cancelButtonText: 'Cancelar',
        preConfirm: () => {
            return {
                assunto: document.getElementById('assuntoEmail').value,
                corpo: document.getElementById('corpoEmail').value
            };
        }
    }).then((result) => {
        if (result.isConfirmed) {
            enviarEmailsPersonalizados(result.value.assunto, result.value.corpo);
        }
    });
}

// Função para enviar emails personalizados
async function enviarEmailsPersonalizados(assunto, corpo) {
    try {
        const eventoId = getEventoId();
        
        // Mostra um indicador de carregamento
        Swal.fire({
            title: 'Enviando emails...',
            html: 'Por favor, aguarde enquanto os emails são enviados.',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });
        
        // Faz a requisição para enviar os emails
        const response = await fetch(`/api/eventos/${eventoId}/convidados/enviar-emails-template`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                assunto: assunto,
                corpo: corpo
            }),
            // Evita seguir redirecionamentos automaticamente
            redirect: 'error'
        });
        
        // Verifica se a resposta é um redirecionamento
        if (response.status === 303 || response.redirected) {
            throw new Error("Redirecionamento detectado. Você pode não estar autenticado.");
        }
        
        // Verifica o tipo de conteúdo da resposta
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('Resposta não é JSON:', text);
            throw new Error('Resposta do servidor não está no formato JSON esperado');
        }
        
        if (!response.ok) {
            throw new Error(`Erro ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Mostra o resultado
        Swal.fire({
            title: 'Emails Enviados',
            html: `${result.total_enviados} emails foram enviados com sucesso!<br>
                   ${result.total_erros > 0 ? `${result.total_erros} emails não puderam ser enviados.` : ''}`,
            icon: 'success'
        });
        
    } catch (error) {
        console.error('Erro ao enviar emails:', error);
        Swal.fire({
            title: 'Erro',
            text: 'Ocorreu um erro ao enviar os emails: ' + error.message,
            icon: 'error'
        });
    }
}

// Importar lista de convidados
async function importarConvidados() {
    const fileInput = document.getElementById('arquivoConvidados');
    const file = fileInput.files[0];
    
    if (!file) {
        showAlert('Por favor, selecione um arquivo.', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const eventoId = getEventoId();
        // URL com parâmetro para não enviar emails
        const response = await fetch(`/api/eventos/${eventoId}/convidados/importar?enviar_emails=false`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Erro ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Fecha o modal do formulário
        const modal = bootstrap.Modal.getInstance(document.getElementById('importarConvidadosModal'));
        modal.hide();
        document.getElementById('formImportarConvidados').reset();
        
        // Monta a mensagem de sucesso com detalhes dos convidados
        let mensagem = `${result.total_importados} convidados importados com sucesso!`;
        
        if (result.registros_completos) {
            mensagem += ` (${result.registros_completos} com dados completos`;
        }
        
        if (result.registros_incompletos) {
            mensagem += `, ${result.registros_incompletos} com dados incompletos)`;
        }
        
        if (result.convidados && result.convidados.length > 0) {
            mensagem += '<br><br>Convidados importados (primeiros 5):<br>';
            const convidadosExemplo = result.convidados.slice(0, 5);
            
            convidadosExemplo.forEach(convidado => {
                mensagem += `- ${convidado.nome} (${convidado.email})<br>`;
            });
            
            if (result.convidados.length > 5) {
                mensagem += `... e mais ${result.convidados.length - 5} convidados.`;
            }
        }
        
        // Mostra o modal de sucesso e quando o usuário clicar em OK, recarrega a página
        Swal.fire({
            title: 'Sucesso!',
            html: mensagem,
            icon: 'success',
            confirmButtonText: 'OK'
        }).then(() => {
            // Recarrega a página completamente para garantir que os dados sejam atualizados
            window.location.reload();
        });
        
    } catch (error) {
        console.error('Erro ao importar convidados:', error);
        showAlert('Erro ao importar convidados: ' + error.message, 'danger');
    }
}

// Adiciona novo convidado
async function adicionarConvidado() {
    try {
        if (!validarFormularioConvidado()) {
            return;
        }
        
        const eventoId = getEventoId();
        const nome = document.getElementById('nomeConvidado').value;
        const email = document.getElementById('emailConvidado').value;
        const telefone = document.getElementById('telefoneConvidado').value;
        const observacoes = document.getElementById('observacoesConvidado').value;
        
        const response = await fetch(`/api/eventos/${eventoId}/convidados`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ nome, email, telefone, observacoes })
        });
        
        if (!response.ok) {
            throw new Error(`Erro ${response.status}: ${response.statusText}`);
        }
        
        // Fecha o modal e limpa o formulário
        const modal = bootstrap.Modal.getInstance(document.getElementById('addConvidadoModal'));
        modal.hide();
        document.getElementById('formAddConvidado').reset();
        
        // Recarrega os dados
        await carregarDadosEvento();
        showAlert('Convidado adicionado com sucesso!');
        
    } catch (error) {
        console.error('Erro ao adicionar convidado:', error);
        showAlert('Erro ao adicionar convidado: ' + error.message, 'danger');
    }
}

// Reenviar email para um convidado
async function reenviarEmail(email, nome) {
    try {
        const eventoId = getEventoId();
        const response = await fetch(`/api/eventos/${eventoId}/convidados/enviar-email`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, nome })
        });
        
        if (!response.ok) {
            throw new Error(`Erro ${response.status}: ${response.statusText}`);
        }
        
        showAlert(`Email reenviado para ${nome}`);
        
    } catch (error) {
        console.error('Erro ao reenviar email:', error);
        showAlert('Erro ao reenviar email: ' + error.message, 'danger');
    }
}

// Excluir convidado
async function excluirConvidado(email) {
    if (!confirm('Tem certeza que deseja excluir este convidado?')) {
        return;
    }
    
    try {
        const eventoId = getEventoId();
        const response = await fetch(`/api/eventos/${eventoId}/convidados/excluir`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email })
        });
        
        if (!response.ok) {
            throw new Error(`Erro ${response.status}: ${response.statusText}`);
        }
        
        await carregarDadosEvento();
        showAlert('Convidado excluído com sucesso!');
        
    } catch (error) {
        console.error('Erro ao excluir convidado:', error);
        showAlert('Erro ao excluir convidado: ' + error.message, 'danger');
    }
}

// Enviar emails para todos os convidados
async function enviarEmailsConvidados() {
    try {
        const eventoId = getEventoId();
        const response = await fetch(`/api/eventos/${eventoId}/convidados/enviar-emails`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`Erro ${response.status}: ${response.statusText}`);
        }
        
        showAlert('Emails enviados com sucesso!');
        
    } catch (error) {
        console.error('Erro ao enviar emails:', error);
        showAlert('Erro ao enviar emails: ' + error.message, 'danger');
    }
}

// Função para filtrar convidados
function filtrarConvidados() {
    const searchTerm = document.getElementById('pesquisaConvidado').value.toLowerCase();
    const statusFiltro = document.getElementById('filtroStatus').value.toLowerCase();
    const obsFiltro = document.getElementById('filtroObservacoes').value;
    
    const rows = document.querySelectorAll('#listaConvidados tr');
    
    rows.forEach(row => {
        if (row.cells.length < 4) return; // Ignora linhas inválidas
        
        const nome = row.cells[0].textContent.toLowerCase();
        const email = row.cells[1].textContent.toLowerCase();
        const status = row.cells[3].textContent.toLowerCase();
        const temObs = row.cells[4].textContent.trim() !== '-';
        
        const matchSearch = nome.includes(searchTerm) || email.includes(searchTerm);
        const matchStatus = !statusFiltro || status === statusFiltro;
        const matchObs = !obsFiltro || 
            (obsFiltro === 'com' && temObs) || 
            (obsFiltro === 'sem' && !temObs);
        
        row.style.display = matchSearch && matchStatus && matchObs ? '' : 'none';
    });
}

// Função para obter o ID do evento da URL
function getEventoId() {
    const path = window.location.pathname;
    return path.split('/').pop();
}

// Função para obter a classe CSS do status
function getStatusClass(status) {
    const classes = {
        'confirmado': 'bg-success',
        'recusado': 'bg-danger',
        'pendente': 'bg-warning'
    };
    return classes[(status || 'pendente').toLowerCase()] || 'bg-secondary';
}

// Atualizar observações do convidado
async function atualizarObservacoes(email, observacoes) {
    try {
        const eventoId = getEventoId();
        const response = await fetch(`/api/eventos/${eventoId}/convidados/observacoes`, {
            method: 'POST', // Alterado para POST para corresponder ao backend
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, observacoes })
        });
        
        if (!response.ok) {
            throw new Error(`Erro ${response.status}: ${response.statusText}`);
        }
        
        await carregarDadosEvento();
        showAlert('Observações atualizadas com sucesso!');
        
    } catch (error) {
        console.error('Erro ao atualizar observações:', error);
        showAlert('Erro ao atualizar observações: ' + error.message, 'danger');
    }
}

// Função para mostrar progresso de envio de emails
function atualizarProgressoEnvio(progresso, total) {
    const porcentagem = (progresso / total) * 100;
    const progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
        progressBar.style.width = `${porcentagem}%`;
        progressBar.setAttribute('aria-valuenow', porcentagem);
    }
    const statusText = document.getElementById('statusEnvioTexto');
    if (statusText) {
        statusText.textContent = `Enviando emails... ${progresso} de ${total} (${Math.round(porcentagem)}%)`;
    }
}

// Função para resetar progresso de envio
function resetarProgressoEnvio() {
    const progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
        progressBar.style.width = '0%';
        progressBar.setAttribute('aria-valuenow', 0);
    }
    const statusText = document.getElementById('statusEnvioTexto');
    if (statusText) {
        statusText.textContent = 'Preparando envio...';
    }
}

// Função para formatar data
function formatarData(dataStr) {
    if (!dataStr) return '';
    
    try {
        // Se for string no formato ISO, converte para DD/MM/YYYY
        if (dataStr.includes('-')) {
            const [ano, mes, dia] = dataStr.split('-');
            return `${dia}/${mes}/${ano}`;
        }
        return dataStr;
    } catch (e) {
        return dataStr;
    }
}

// Alerta usando SweetAlert
function showAlert(message, type = 'success', allowHtml = false) {
    Swal.fire({
        title: type === 'success' ? 'Sucesso!' : 'Atenção!',
        html: allowHtml ? message : undefined,
        text: !allowHtml ? message : undefined,
        icon: type,
        confirmButtonText: 'OK'
    });
}

// Função para escapar HTML
function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Função para validar formulário de novo convidado
function validarFormularioConvidado() {
    const nome = document.getElementById('nomeConvidado').value.trim();
    const email = document.getElementById('emailConvidado').value.trim();
    
    if (!nome) {
        showAlert('O nome do convidado é obrigatório', 'warning');
        return false;
    }
    
    if (!email) {
        showAlert('O email do convidado é obrigatório', 'warning');
        return false;
    }
    
    if (!email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
        showAlert('Por favor, insira um email válido', 'warning');
        return false;
    }
    
    return true;
}

// Funções para download de relatórios
async function prepararDadosRelatorio() {
    const eventoId = getEventoId();
    const response = await fetch(`/api/eventos/${eventoId}`);
    
    if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
    }
    
    const evento = await response.json();
    
    if (!evento.convidados || evento.convidados.length === 0) {
        throw new Error('Não há convidados para gerar o relatório.');
    }
    
    const dadosEvento = {
        nome: evento.nome || 'Sem nome',
        data: formatarData(evento.data) || 'Sem data',
        hora: evento.hora || 'Sem horário',
        local: evento.local || 'Sem local',
        responsavel: evento.responsavel || 'Sem responsável'
    };
    
    const estatisticas = evento.convidados.reduce((acc, conv) => {
        const status = (conv.status || 'pendente').toLowerCase();
        acc[status] = (acc[status] || 0) + 1;
        return acc;
    }, { confirmado: 0, recusado: 0, pendente: 0 });
    
    return {
        evento: dadosEvento,
        convidados: evento.convidados,
        stats: estatisticas
    };
}

// Download CSV
async function baixarRelatorioCSV() {
    try {
        const dados = await prepararDadosRelatorio();
        
        const csvLinhas = [
            ['Relatório de Convidados'],
            [''],
            ['Evento:', dados.evento.nome],
            ['Data:', dados.evento.data],
            ['Hora:', dados.evento.hora],
            ['Local:', dados.evento.local],
            ['Responsável:', dados.evento.responsavel],
            [''],
            ['Lista de Convidados:'],
            ['Nome', 'Email', 'Telefone', 'Status', 'Observações']
        ];
        
        dados.convidados.forEach(convidado => {
            csvLinhas.push([
                convidado.nome || 'Sem nome',
                convidado.email || 'Sem email',
                convidado.telefone || '',
                convidado.status || 'pendente',
                convidado.observacoes || ''
            ]);
        });
        
        csvLinhas.push(
            [''],
            ['Estatísticas:'],
            ['Confirmados:', dados.stats.confirmado || 0],
            ['Recusados:', dados.stats.recusado || 0],
            ['Pendentes:', dados.stats.pendente || 0],
            ['Total:', dados.convidados.length]
        );
        
        const csv = csvLinhas.map(linha => 
            linha.map(celula => `"${celula}"`).join(',')
        ).join('\n');
        
        const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `relatorio_${dados.evento.nome}_${formatarData(new Date())}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showAlert('Relatório CSV baixado com sucesso!');
        
    } catch (error) {
        console.error('Erro ao gerar CSV:', error);
        showAlert(error.message || 'Erro ao gerar relatório CSV', 'danger');
    }
}

// Download Excel
async function baixarRelatorioExcel() {
    console.log('Iniciando processo de download do Excel');
    
    try {
        // Verificar se a biblioteca ExcelJS está carregada
        if (typeof ExcelJS === 'undefined') {
            console.error('Biblioteca ExcelJS não carregada!');
            showAlert('Erro: Biblioteca Excel não encontrada', 'danger');
            return;
        }

        // Preparar dados do relatório
        const dados = await prepararDadosRelatorio();
        console.log('Dados preparados:', dados);
        
        const dadosEvento = {
            nome: dados.evento.nome,
            data: dados.evento.data,
            hora: dados.evento.hora,
            local: dados.evento.local,
            responsavel: dados.evento.responsavel
        };

        console.log('Dados do Evento:', dadosEvento);
        console.log('Convidados:', dados.convidados);

        // Chamar função de geração de Excel
        await gerarRelatorioExcelComEstilo(dadosEvento, dados.convidados);
        
        showAlert('Relatório Excel baixado com sucesso!');
        
    } catch (error) {
        console.error('Erro completo ao gerar Excel:', error);
        showAlert('Erro ao gerar relatório Excel: ' + error.message, 'danger');
    }
}

async function gerarRelatorioExcelComEstilo(dadosEvento, convidados) {
    console.log('Iniciando geração do relatório Excel com ExcelJS');
    
    // Criar workbook
    const workbook = new ExcelJS.Workbook();
    workbook.creator = 'Sistema RSVP';
    workbook.lastModifiedBy = 'Sistema RSVP';
    workbook.created = new Date();
    workbook.modified = new Date();
    
    // Adicionar planilha
    const worksheet = workbook.addWorksheet('Relatório de Convidados');
    
    // Definir largura das colunas
    worksheet.columns = [
        { header: 'Nome', key: 'nome', width: 30 },
        { header: 'Email', key: 'email', width: 40 },
        { header: 'Telefone', key: 'telefone', width: 20 },
        { header: 'Status', key: 'status', width: 15 },
        { header: 'Observações', key: 'observacoes', width: 50 }
    ];
    
    // Adicionar título do relatório
    worksheet.mergeCells('A1:E1');
    const tituloCell = worksheet.getCell('A1');
    tituloCell.value = 'Relatório Detalhado de Evento';
    tituloCell.font = { 
        size: 16, 
        bold: true, 
        color: { argb: 'FF1F4E79' } 
    };
    tituloCell.alignment = { 
        horizontal: 'center', 
        vertical: 'middle' 
    };
    tituloCell.fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: 'FFF2F2F2' }
    };
    worksheet.getRow(1).height = 30;
    
    // Adicionar informações do evento
    worksheet.mergeCells('A3:B3');
    worksheet.getCell('A3').value = 'Evento:';
    worksheet.getCell('A3').font = { bold: true };
    worksheet.getCell('C3').value = dadosEvento.nome;
    worksheet.mergeCells('C3:E3');
    
    worksheet.mergeCells('A4:B4');
    worksheet.getCell('A4').value = 'Data:';
    worksheet.getCell('A4').font = { bold: true };
    worksheet.getCell('C4').value = dadosEvento.data;
    worksheet.mergeCells('C4:E4');
    
    worksheet.mergeCells('A5:B5');
    worksheet.getCell('A5').value = 'Hora:';
    worksheet.getCell('A5').font = { bold: true };
    worksheet.getCell('C5').value = dadosEvento.hora;
    worksheet.mergeCells('C5:E5');
    
    worksheet.mergeCells('A6:B6');
    worksheet.getCell('A6').value = 'Local:';
    worksheet.getCell('A6').font = { bold: true };
    worksheet.getCell('C6').value = dadosEvento.local;
    worksheet.mergeCells('C6:E6');
    
    worksheet.mergeCells('A7:B7');
    worksheet.getCell('A7').value = 'Responsável:';
    worksheet.getCell('A7').font = { bold: true };
    worksheet.getCell('C7').value = dadosEvento.responsavel;
    worksheet.mergeCells('C7:E7');
    
    // Adicionar estatísticas
    worksheet.mergeCells('A9:E9');
    const estatisticasTitulo = worksheet.getCell('A9');
    estatisticasTitulo.value = 'Estatísticas de Participação';
    estatisticasTitulo.font = { 
        size: 14, 
        bold: true,
        color: { argb: 'FF1F4E79' } 
    };
    estatisticasTitulo.alignment = { horizontal: 'left' };
    estatisticasTitulo.fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: 'FFF2F2F2' }
    };
    
    worksheet.mergeCells('A10:B10');
    worksheet.getCell('A10').value = 'Total de Convidados:';
    worksheet.getCell('A10').font = { bold: true };
    worksheet.getCell('C10').value = convidados.length;
    
    worksheet.mergeCells('A11:B11');
    worksheet.getCell('A11').value = 'Confirmados:';
    worksheet.getCell('A11').font = { bold: true };
    worksheet.getCell('A11').font.color = { argb: 'FF006100' };
    worksheet.getCell('C11').value = convidados.filter(c => c.status === 'confirmado').length;
    
    worksheet.mergeCells('A12:B12');
    worksheet.getCell('A12').value = 'Recusados:';
    worksheet.getCell('A12').font = { bold: true };
    worksheet.getCell('A12').font.color = { argb: 'FF9C0006' };
    worksheet.getCell('C12').value = convidados.filter(c => c.status === 'recusado').length;
    
    worksheet.mergeCells('A13:B13');
    worksheet.getCell('A13').value = 'Pendentes:';
    worksheet.getCell('A13').font = { bold: true };
    worksheet.getCell('A13').font.color = { argb: 'FF9C6500' };
    worksheet.getCell('C13').value = convidados.filter(c => c.status === 'pendente').length;
    
    // Adicionar cabeçalho da tabela na linha 15
    const headerRow = worksheet.getRow(15);
    headerRow.values = ['Nome', 'Email', 'Telefone', 'Status', 'Observações'];
    headerRow.font = { bold: true };
    headerRow.alignment = { horizontal: 'center' };
    headerRow.fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: 'FFD9D9D9' }
    };
    headerRow.height = 20;
    
    // Adicionar borda ao cabeçalho
    headerRow.eachCell((cell) => {
        cell.border = {
            top: { style: 'thin' },
            left: { style: 'thin' },
            bottom: { style: 'thin' },
            right: { style: 'thin' }
        };
    });
    
    // Adicionar dados dos convidados
    convidados.forEach((convidado, index) => {
        const rowIndex = index + 16; // Começa na linha 16 (após o cabeçalho)
        const row = worksheet.getRow(rowIndex);
        
        row.values = [
            convidado.nome || 'Sem nome',
            convidado.email || 'Sem email',
            convidado.telefone || 'Não informado',
            convidado.status || 'Sem status',
            convidado.observacoes || 'Sem observações'
        ];
        
        // Aplicar cores baseadas no status
        let fillColor;
        switch((convidado.status || 'pendente').toLowerCase()) {
            case 'confirmado':
                fillColor = 'FFE6F3E6'; // Verde claro
                break;
            case 'pendente':
                fillColor = 'FFFFF2CC'; // Amarelo claro
                break;
            case 'recusado':
                fillColor = 'FFF2DCDB'; // Vermelho claro
                break;
            default:
                fillColor = 'FFFFFFFF'; // Branco
        }
        
        // Aplicar estilo a cada célula da linha
        row.eachCell((cell) => {
            cell.fill = {
                type: 'pattern',
                pattern: 'solid',
                fgColor: { argb: fillColor }
            };
            cell.border = {
                top: { style: 'thin' },
                left: { style: 'thin' },
                bottom: { style: 'thin' },
                right: { style: 'thin' }
            };
            cell.alignment = { 
                vertical: 'middle',
                horizontal: cell.col === 4 ? 'center' : 'left' // Status centralizado, resto à esquerda
            };
        });
    });
    
    // Gerar e baixar o arquivo
    const buffer = await workbook.xlsx.writeBuffer();
    const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `Relatorio_Evento_${dadosEvento.nome}_${new Date().toISOString().split('T')[0]}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    console.log('Relatório Excel gerado com sucesso!');
}