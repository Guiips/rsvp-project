// Funções globais úteis

// Formata data para exibição
function formatarData(data) {
    return moment(data).format('DD/MM/YYYY');
}

// Formata hora para exibição
function formatarHora(hora) {
    return moment(hora, 'HH:mm').format('HH:mm');
}

// Retorna a classe CSS baseada no status
function getStatusClass(status) {
    switch(status.toLowerCase()) {
        case 'confirmado':
            return 'bg-success';
        case 'recusado':
            return 'bg-danger';
        case 'pendente':
            return 'bg-warning';
        default:
            return 'bg-secondary';
    }
}

// Função para exibir mensagens de alerta
function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-remove após 5 segundos
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Função para tratar erros
async function handleFetchError(response) {
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erro ao processar requisição');
    }
    return response;
}

// Inicializa tooltips do Bootstrap
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Configuração do Moment.js
moment.locale('pt-br');