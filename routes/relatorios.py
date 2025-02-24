from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import openpyxl
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils import get_column_letter
from io import BytesIO
from datetime import datetime
from models.user import User
from routes.auth import get_current_user
from config.database import get_database

router = APIRouter()

@router.get("/gerar-relatorio")
async def gerar_relatorio(current_user: User = Depends(get_current_user)):
    try:
        # Obter o banco de dados
        db = get_database()

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Relatório de Eventos"

        # Estilos
        header_font = Font(bold=True, color="FFFFFF", size=12)
        header_fill = PatternFill(start_color="007BFF", end_color="007BFF", fill_type="solid")
        
        event_font = Font(bold=True, size=11, color="000000")
        event_fill = PatternFill(start_color="E3F2FD", end_color="E3F2FD", fill_type="solid")
        
        subheader_font = Font(bold=True, size=10, color="000000")
        subheader_fill = PatternFill(start_color="F5F5F5", end_color="F5F5F5", fill_type="solid")

        # Título do relatório
        ws.merge_cells('A1:G1')
        title_cell = ws['A1']
        title_cell.value = "Relatório de Eventos - RSVP"
        title_cell.font = Font(bold=True, size=14, color="007BFF")
        title_cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Cabeçalhos
        headers = [
            "Nome do Evento", 
            "Data", 
            "Local", 
            "Nome do Convidado",
            "Email",
            "Telefone",
            "Status"
        ]

        row = 3  # Começamos na linha 3 por causa do título
        
        # Buscar eventos usando Motor AsyncIO corretamente
        eventos = await db.eventos.find().to_list(length=None)

        for evento in eventos:
            # Linha de separação entre eventos
            for col in range(1, 8):
                cell = ws.cell(row=row, column=col)
                cell.fill = event_fill
                cell.font = event_font
                if col == 1:
                    cell.value = f"Evento: {evento.get('nome', '')}"
                if col == 2:
                    cell.value = f"Data: {evento.get('data', '')}"
                if col == 3:
                    cell.value = f"Local: {evento.get('local', '')}"
            
            row += 1

            # Cabeçalhos da lista de convidados
            for col, header in enumerate(headers[3:], 4):  # Começamos do 4º cabeçalho
                cell = ws.cell(row=row, column=col)
                cell.value = header
                cell.font = subheader_font
                cell.fill = subheader_fill

            row += 1

            # Lista de convidados
            convidados = evento.get("convidados", [])
            if not convidados:
                cell = ws.cell(row=row, column=4)
                cell.value = "Nenhum convidado registrado"
                cell.font = Font(italic=True)
                row += 1
            else:
                for convidado in convidados:
                    ws.cell(row=row, column=4, value=convidado.get("nome", ""))
                    ws.cell(row=row, column=5, value=convidado.get("email", ""))
                    ws.cell(row=row, column=6, value=convidado.get("telefone", ""))
                    
                    # Estilizar o status
                    status_cell = ws.cell(row=row, column=7)
                    status_cell.value = convidado.get("status", "")
                    if status_cell.value.lower() == "confirmado":
                        status_cell.font = Font(color="008000")  # Verde
                    elif status_cell.value.lower() == "recusado":
                        status_cell.font = Font(color="FF0000")  # Vermelho
                    
                    row += 1

            # Espaço entre eventos
            row += 1

        # Ajustar largura das colunas
        for col in range(1, 8):  # Usar range de 1 a 7 (colunas de A a G)
            max_length = 0
            column = get_column_letter(col)
            for row_cells in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=col, max_col=col):
                for cell in row_cells:
                    try:
                        # Pule células mescladas
                        if not isinstance(cell, openpyxl.cell.cell.MergedCell):
                            max_length = max(max_length, len(str(cell.value or '')))
                    except:
                        pass
            ws.column_dimensions[column].width = max_length + 2

        # Bordas para todas as células preenchidas
        for row_cells in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=7):
            for cell in row_cells:
                if cell.value:
                    cell.border = Border(
                        left=Side(style='thin'),
                        right=Side(style='thin'),
                        top=Side(style='thin'),
                        bottom=Side(style='thin')
                    )

        # Salvar
        excel_file = BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)

        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                'Content-Disposition': f'attachment; filename="relatorio_eventos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
            }
        )

    except Exception as e:
        print(f"Erro na geração do relatório: {e}")
        raise HTTPException(status_code=500, detail=str(e))