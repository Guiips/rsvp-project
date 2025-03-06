// Carrega os dados do evento ao iniciar
document.addEventListener('DOMContentLoaded', function() {
    carregarDadosEvento();
    
    // Adiciona listeners para filtros
    document.getElementById('pesquisaConvidado').addEventListener('input', filtrarConvidados);
    document.getElementById('filtroStatus').addEventListener('change', filtrarConvidados);
    document.getElementById('filtroObservacoes').addEventListener('change', filtrarConvidados);
    
    // Listener para envio de emails
    document.getElementById('enviarEmails').addEventListener('click', enviarEmailsConvidados);
});

// Carrega os dados do evento
async function carregarDadosEvento() {
    try {
        const eventoId = getEventoId();
        const response = await fetch(`/api/eventos/${eventoId}`);
        await handleFetchError(response);
        const evento = await response.json();
        
        // Preenche os dados do evento
        preencherDadosEvento(evento);
        // Atualiza estatísticas
        atualizarEstatisticas(evento.convidados || []);
        // Carrega lista de convidados
        renderizarConvidados(evento.convidados || []);
        
    } catch (error) {
        console.error('Erro ao carregar dados do evento:', error);
        showAlert('Erro ao carregar dados do evento: ' + error.message, 'danger');
    }
}

// Preenche os dados básicos do evento
function preencherDadosEvento(evento) {
    document.getElementById('nomeEvento').textContent = evento.nome;
    document.getElementById('responsavel').textContent = evento.responsavel;
    document.getElementById('data').textContent = formatarData(evento.data);
    document.getElementById('hora').textContent = evento.hora;
    document.getElementById('local').textContent = evento.local;
    document.getElementById('categoria').textContent = evento.categoria;
    document.getElementById('descricao').textContent = evento.descricao || 'Sem descrição';
}

// Atualiza as estatísticas do evento
function atualizarEstatisticas(convidados) {
    const stats = convidados.reduce((acc, conv) => {
        acc.total++;
        acc[conv.status.toLowerCase()]++;
        return acc;
    }, { total: 0, confirmado: 0, recusado: 0, pendente: 0 });
    
    document.getElementById('totalConvidados').textContent = stats.total;
    document.getElementById('totalConfirmados').textContent = stats.confirmado;
    document.getElementById('totalRecusados').textContent = stats.recusado;
    document.getElementById('totalPendentes').textContent = stats.pendente;
}

// Renderiza a lista de convidados
function renderizarConvidados(convidados) {
    const tbody = document.getElementById('listaConvidados');
    tbody.innerHTML = '';
    
    if (convidados.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">Nenhum convidado cadastrado.</td>
            </tr>
        `;
        return;
    }
    
    convidados.forEach(convidado => {
        const row = document.createElement('tr');
        
        const obsHtml = convidado.observacoes ? 
            `<button class="btn btn-info btn-sm" onclick="mostrarObservacoes('${convidado.nome}', '${convidado.email}', '${convidado.status}', '${convidado.observacoes.replace(/'/g, "\\'")}')">
                <i class="bi bi-info-circle"></i> Ver
            </button>` : 
            '<span class="text-muted">-</span>';
        
        row.innerHTML = `
            <td>${convidado.nome}</td>
            <td>${convidado.email}</td>
            <td>${convidado.telefone || '-'}</td>
            <td><span class="badge ${getStatusClass(convidado.status)}">${convidado.status}</span></td>
            <td>${obsHtml}</td>
            <td>
                <button class="btn btn-primary btn-sm me-1" onclick="reenviarEmail('${convidado.email}', '${convidado.nome}')" title="Reenviar Email">
                    <i class="bi bi-envelope"></i>
                </button>
                <button class="btn btn-danger btn-sm" onclick="excluirConvidado('${convidado.email}')" title="Excluir">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
    
    // Inicializa tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Adiciona novo convidado
async function adicionarConvidado() {
    try {
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
        
        await handleFetchError(response);
        
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
        
        await handleFetchError(response);
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
        
        await handleFetchError(response);
        await carregarDadosEvento();
        showAlert('Convidado excluído com sucesso!');
        
    } catch (error) {
        console.error('Erro ao excluir convidado:', error);
        showAlert('Erro ao excluir convidado: ' + error.message, 'danger');
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
        const response = await fetch(`/api/eventos/${eventoId}/convidados/importar`, {
            method: 'POST',
            body: formData
        });
        
        await handleFetchError(response);
        const result = await response.json();
        
        // Fecha o modal e limpa o formulário
        const modal = bootstrap.Modal.getInstance(document.getElementById('importarConvidadosModal'));
        modal.hide();
        document.getElementById('formImportarConvidados').reset();
        
        // Recarrega os dados
        await carregarDadosEvento();
        showAlert(`${result.total_importados} convidados importados com sucesso!`);
        
    } catch (error) {
        console.error('Erro ao importar convidados:', error);
        showAlert('Erro ao importar convidados: ' + error.message, 'danger');
    }
}

// Enviar emails para todos os convidados
async function enviarEmailsConvidados() {
    try {
        const eventoId = getEventoId();
        const response = await fetch(`/api/eventos/${eventoId}/convidados/enviar-emails`, {
            method: 'POST'
        });
        
        await handleFetchError(response);
        showAlert('Emails enviados com sucesso!');
        
    } catch (error) {
        console.error('Erro ao enviar emails:', error);
        showAlert('Erro ao enviar emails: ' + error.message, 'danger');
    }
}

// Funções para download de relatórios
async function prepararDadosRelatorio() {
    const eventoId = getEventoId();
    const response = await fetch(`/api/eventos/${eventoId}`);
    const evento = await response.json();
    
    if (!evento.convidados || evento.convidados.length === 0) {
        throw new Error('Não há convidados para gerar o relatório.');
    }
    
    const dadosEvento = {
        nome: evento.nome,
        data: formatarData(evento.data),
        hora: evento.hora,
        local: evento.local,
        responsavel: evento.responsavel
    };
    
    const estatisticas = evento.convidados.reduce((acc, conv) => {
        acc[conv.status.toLowerCase()]++;
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
                convidado.nome,
                convidado.email,
                convidado.telefone || '',
                convidado.status,
                convidado.observacoes || ''
            ]);
        });
        
        csvLinhas.push(
            [''],
            ['Estatísticas:'],
            ['Confirmados:', dados.stats.confirmado],
            ['Recusados:', dados.stats.recusado],
            ['Pendentes:', dados.stats.pendente],
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
        switch(convidado.status.toLowerCase()) {
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

// Função para filtrar convidados
function filtrarConvidados() {
    const searchTerm = document.getElementById('pesquisaConvidado').value.toLowerCase();
    const statusFiltro = document.getElementById('filtroStatus').value.toLowerCase();
    const obsFiltro = document.getElementById('filtroObservacoes').value;
    
    const rows = document.querySelectorAll('#listaConvidados tr');
    
    rows.forEach(row => {
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
    return classes[status.toLowerCase()] || 'bg-secondary';
}

// Atualizar observações do convidado
async function atualizarObservacoes(email, observacoes) {
    try {
        const eventoId = getEventoId();
        const response = await fetch(`/api/eventos/${eventoId}/convidados/observacoes`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, observacoes })
        });
        
        await handleFetchError(response);
        await carregarDadosEvento();
        showAlert('Observações atualizadas com sucesso!');
        
    } catch (error) {
        console.error('Erro ao atualizar observações:', error);
        showAlert('Erro ao atualizar observações: ' + error.message, 'danger');
    }
}

// Inicialização de tooltips e handlers de eventos
document.addEventListener('DOMContentLoaded', function() {
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

// Função para mostrar progresso de envio de emails
function atualizarProgressoEnvio(progresso, total) {
    const porcentagem = (progresso / total) * 100;
    document.querySelector('.progress-bar').style.width = `${porcentagem}%`;
    document.querySelector('.progress-bar').setAttribute('aria-valuenow', porcentagem);
    document.getElementById('statusEnvioTexto').textContent = 
        `Enviando emails... ${progresso} de ${total} (${Math.round(porcentagem)}%)`;
}

// Função para resetar progresso de envio
function resetarProgressoEnvio() {
    document.querySelector('.progress-bar').style.width = '0%';
    document.querySelector('.progress-bar').setAttribute('aria-valuenow', 0);
    document.getElementById('statusEnvioTexto').textContent = 'Preparando envio...';
}

// Função para mostrar observações
function mostrarObservacoes(nome, email, status, observacoes) {
    // Adicione uma função para escapar caracteres especiais
    const escapeHtml = (unsafe) => {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    };

    Swal.fire({
        title: 'Observações do Convidado',
        html: `
            <div class="text-start">
                <p><strong>Nome:</strong> ${escapeHtml(nome)}</p>
                <p><strong>Email:</strong> ${escapeHtml(email)}</p>
                <p><strong>Status:</strong> ${escapeHtml(status)}</p>
                <hr>
                <p><strong>Observações:</strong></p>
                <p>${observacoes ? escapeHtml(observacoes) : 'Nenhuma observação disponível.'}</p>
            </div>
        `,
        icon: 'info',
        confirmButtonText: 'Fechar'
    });
}

// Na renderização dos convidados, ajuste a chamada do botão de observações
if (convidado.observacoes) {
    acoesTd.innerHTML += `
        <button onclick="mostrarObservacoes('${escapeHtml(convidado.nome)}', '${escapeHtml(convidado.email)}', '${escapeHtml(convidado.status)}', '${escapeHtml(convidado.observacoes)}')" 
                class="btn btn-sm btn-info btn-ver-observacoes">
            <i class="bi bi-eye"></i> Ver
        </button>
    `;
}

// Adicione uma função de escape no escopo global
function escapeHtml(unsafe) {
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