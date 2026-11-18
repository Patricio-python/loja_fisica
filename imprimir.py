import sqlite3
import os
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def gerar_pdf_cliente(id_cliente):
    
    # 1. Conectar ao Banco de Dados e buscar as informações
    conn = sqlite3.connect('ourives.db') 
    cursor = conn.cursor()
    
    # Buscar dados do cliente
    cursor.execute("SELECT nome, sobrenome, cpf, telefone, endereco FROM cliente WHERE idCliente = ?", (id_cliente,))
    cliente = cursor.fetchone()
    
    if not cliente:
        print(f"Erro: Cliente com ID {id_cliente} não foi encontrado.")
        conn.close()
        return

    else:    
        nome, sobrenome, cpf, telefone, endereco = cliente
        nome_completo = f"{nome} {sobrenome}"
        
        # Buscar pedidos deste cliente
        cursor.execute("SELECT idPedido, servico, descricao, valor, data_entrada, data_saida FROM pedido WHERE idCliente = ?", (id_cliente,))
        pedidos = cursor.fetchall()
        conn.close()

        if not os.path.exists("Relatório de Clientes"):
            os.makedirs("Relatório de Clientes")
        # 2. Configurar o arquivo PDF
        nome_arquivo = f"relatorio_cliente_{nome_completo}.pdf"
        caminho_completo = os.path.join("Relatório de Clientes", nome_arquivo)

        doc = SimpleDocTemplate(caminho_completo, pagesize=letter,
                                rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        
        # Estilos de texto
        styles = getSampleStyleSheet()
        
        # Estilos customizados para deixar o relatório elegante
        style_titulo = ParagraphStyle(
            'TituloCustom',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor("#1A365D"), # Azul escuro profissional
            spaceAfter=15
        )
        
        style_subtitulo = ParagraphStyle(
            'SubtituloCustom',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor("#2B6CB0"),
            spaceBefore=12,
            spaceAfter=8
        )
        
        style_texto = styles['Normal']
        style_texto.fontSize = 11
        style_texto.leading = 14
        
        # Elementos que vão compor o PDF
        elementos = []
        
        # Título do Relatório
        elementos.append(Paragraph("<b>DADOS DO CLIENTE</b>", style_titulo))
        elementos.append(Spacer(1, 10))
        
        # Seção: Dados Cadastrais
        elementos.append(Paragraph("Dados Cadastrais", style_subtitulo))
        
        dados_cliente_html = f"""
        <b>ID:</b> {id_cliente}<br/>
        <b>Nome:</b> {nome_completo}<br/>
        <b>CPF:</b> {cpf}<br/>
        <b>Telefone:</b> {telefone}<br/>
        <b>Endereço:</b> {endereco}
        """
        elementos.append(Paragraph(dados_cliente_html, style_texto))
        elementos.append(Spacer(1, 20))
        
        # Seção: Histórico de Pedidos
        elementos.append(Paragraph("Histórico de Pedidos / Serviços", style_subtitulo))
        
        if not pedidos:
            elementos.append(Paragraph("<i>Nenhum pedido encontrado para este cliente.</i>", style_texto))
        else:
            # Montar a tabela de pedidos
            # Cabeçalho da tabela
            dados_tabela = [["Nº Pedido", "Serviço", "Descrição", "Entrada", "Saída", "Valor"]]
            
            # Inserir as linhas de pedidos
            soma_total = 0.0
            for p in pedidos:
                id_ped, serv, desc, valor, dt_ent, dt_sai = p
                soma_total += valor
                # Formata o valor para R$ e garante que descrições longas não quebrem o layout
                desc_formatada = Paragraph(desc if desc else "-", style_texto)
                dados_tabela.append([
                    str(id_ped),
                    serv,
                    desc_formatada,
                    str(dt_ent),
                    str(dt_sai),
                    f"R$ {valor:.2f}"
                ])
            dados_tabela.append(["", "", "", "", "TOTAL GERAL", f"R$ {soma_total:.2f}"])    

            # Configuração visual e larguras das colunas da tabela
            tabela_pedidos = Table(dados_tabela, colWidths=[60, 100, 160, 65, 75, 75])
            tabela_pedidos.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")), # Cor do cabeçalho
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F7FAFC")), # Cor das linhas
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")), # Linhas divisórias pratas
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]), # Linhas alternadas
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            elementos.append(tabela_pedidos)
            
        # 3. Construir o documento PDF
        doc.build(elementos)
        print(f"PDF gerado com sucesso: {nome_arquivo}")
        
        # Opcional: Abre o PDF automaticamente após criado (funciona em Windows/Mac/Linux)
        os.startfile(caminho_completo) if hasattr(os, 'startfile') else os.system(f'xdg-open {nome_arquivo}')

def gerar_pdf_via_cliente(id_pedido_busca, pasta_saida='Via Pedidos'):
    """
    Busca um pedido pelo idPedido no banco de dados SQLite e gera um PDF formatado da Via do Cliente.
    """
    # Conexão com o banco de dados fornecido
    conn = sqlite3.connect('ourives.db')
    cursor = conn.cursor()
    
    # Query relacionando a tabela pedido com a tabela cliente
    cursor.execute('''
        SELECT p.idPedido, p.servico, p.descricao, p.valor, p.data_entrada, p.data_saida,
               c.nome, c.sobrenome, c.telefone
        FROM pedido p
        JOIN cliente c ON p.idCliente = c.idCliente
        WHERE p.idPedido = ?
    ''', (id_pedido_busca,))
    
    row = cursor.fetchone()
    conn.close()
    
    # Validação caso o ID do pedido não exista
    if not row:
        print(f"Pedido com ID {id_pedido_busca} não encontrado.")
        return False
        
    # Desestruturação dos dados recuperados
    idPedido, servico, descricao, valor, data_entrada, data_saida, nome, sobrenome, telefone = row
    nome_completo = f"{nome} {sobrenome}"
    
    # Garantir que a pasta de destino exista
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)
        
    caminho_pdf = os.path.join(pasta_saida, f"via_cliente_pedido_{idPedido}.pdf")
    nome_arquivo=f"via_cliente_pedido_{idPedido}.pdf"

    # Configuração do documento PDF
    doc = SimpleDocTemplate(caminho_pdf, pagesize=letter, title=f"Via do Cliente - Pedido {idPedido}")
    story = []
    styles = getSampleStyleSheet()
    
    # Estilização customizada
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#1A365D"),
        alignment=1, # Centralizado
        spaceAfter=20
    )
    
    header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=12,
        spaceAfter=6
    )
    
    body_style = styles['Normal']
    
    # Montagem do conteúdo (Story)
    story.append(Paragraph("<b>COMPROVANTE DE SERVIÇO</b>", title_style))
    story.append(Paragraph("<i>Via do Cliente</i>", ParagraphStyle('Sub', parent=body_style, alignment=1, fontSize=10, spaceAfter=20)))
    story.append(Spacer(1, 15))
    
    # Tabela 1: Dados do Cliente
    story.append(Paragraph("<b>Dados do Cliente</b>", header_style))
    dados_cliente = [
        [Paragraph(f"<b>Nome Completo:</b> {nome_completo}", body_style)],
        [Paragraph(f"<b>Telefone:</b> {telefone}", body_style)]
    ]
    t_cliente = Table(dados_cliente, colWidths=[450])
    t_cliente.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(t_cliente)
    story.append(Spacer(1, 15))
    
    # Tabela 2: Detalhes do Pedido / Serviço
    story.append(Paragraph("<b>Detalhes do Serviço</b>", header_style))
    dados_pedido = [
        [Paragraph(f"<b>Número do Serviço (ID):</b> {idPedido}", body_style), Paragraph(f"<b>Valor:</b> R$ {valor:,.2f}", body_style)],
        [Paragraph(f"<b>Serviço:</b> {servico}", body_style), Paragraph(f"<b>Data de Entrada:</b> {data_entrada}", body_style)],
        [Paragraph(f"<b>Descrição:</b> {descricao}", body_style), Paragraph(f"<b>Data de Saída:</b> {data_saida}", body_style)]
    ]
    t_pedido = Table(dados_pedido, colWidths=[250, 200])
    t_pedido.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.white),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('VALIGN', (0,0), (-1,-1), 'TOP')
    ]))
    story.append(t_pedido)
    
    # Construção final do arquivo PDF
    doc.build(story)
    print(f"PDF gerado com sucesso em: {caminho_pdf}")
    
    # Opcional: Abre o PDF automaticamente após criado (funciona em Windows/Mac/Linux)
    os.startfile(caminho_pdf) if hasattr(os, 'startfile') else os.system(f'xdg-open {nome_arquivo}')

def gerar_relatorio_ultimos_30_dias(pasta_saida='Relatorio 30 Dias'):
    """
    Busca os pedidos dos últimos 30 dias ordenados por data de entrada, 
    calcula a somatória dos valores e gera um relatório em PDF.
    """
    # Conexão com o banco de dados
    conn = sqlite3.connect("ourives.db")
    cursor = conn.cursor()
    
    # 1. Definir o intervalo de datas (Últimos 30 dias a partir de hoje)
    hoje = datetime.now()
    data_limite = hoje - timedelta(days=30)
    
    # Formato esperado no banco: 'DD-MM-YYYY'
    # Esta query reconstrói a string 'DD-MM-YYYY' em 'YYYY-MM-DD' para fazer o filtro e a ordenação corretos
    query = '''
        SELECT p.servico, (c.nome || ' ' || c.sobrenome) AS nome_cliente, 
               p.data_entrada, p.data_saida, p.valor
        FROM pedido p
        JOIN cliente c ON p.idCliente = c.idCliente
        WHERE 
            (SUBSTR(p.data_entrada, 7, 4) || '-' || SUBSTR(p.data_entrada, 4, 2) || '-' || SUBSTR(p.data_entrada, 1, 2)) 
            BETWEEN ? AND ?
        ORDER BY 
            SUBSTR(p.data_entrada, 7, 4) ASC, 
            SUBSTR(p.data_entrada, 4, 2) ASC, 
            SUBSTR(p.data_entrada, 1, 2) ASC
    '''
    
    # Executa a busca passando as datas limítrofes no formato ISO (YYYY-MM-DD)
    str_limite = data_limite.strftime('%Y-%m-%d')
    str_hoje = hoje.strftime('%Y-%m-%d')
    
    cursor.execute(query, (str_limite, str_hoje))
    pedidos = cursor.fetchall()
    conn.close()
    
    # Validação caso não existam pedidos no período
    if not pedidos:
        
        return False
        
    # Garantir pasta de saída existente
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)
        
    caminho_pdf = os.path.join(pasta_saida, f"relatorio_pedidos_{ hoje.strftime('%m-%Y')}.pdf")
    nome_arquivo=f"relatorio_pedidos_{ hoje.strftime('%m-%Y')}.pdf"
    
    # Configuração do PDF
    doc = SimpleDocTemplate(caminho_pdf, pagesize=letter, leftMargin=30, rightMargin=30)
    story = []
    styles = getSampleStyleSheet()
    
    # Estilos customizados
    title_style = ParagraphStyle(
        'RepTitle', parent=styles['Heading1'], fontSize=20, leading=24,
        textColor=colors.HexColor("#1A365D"), alignment=1, spaceAfter=5
    )
    subtitle_style = ParagraphStyle(
        'RepSub', parent=styles['Normal'], fontSize=10, textColor=colors.gray,
        alignment=1, spaceAfter=20
    )
    th_style = ParagraphStyle('TH', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold', textColor=colors.white)
    td_style = ParagraphStyle('TD', parent=styles['Normal'], fontSize=9, leading=12)
    td_bold = ParagraphStyle('TDBold', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold', alignment=2)
    
    # Cabeçalho do documento
    story.append(Paragraph("<b>RELATÓRIO DE PEDIDOS</b>", title_style))
    story.append(Paragraph(f"Período: {data_limite.strftime('%d/%m/%Y')} até {hoje.strftime('%d/%m/%Y')}", subtitle_style))
    
    # Estrutura da Tabela de Dados
    # Cabeçalhos: Serviço, Cliente, Entrada, Saída, Valor
    tabela_dados = [[
        Paragraph("Serviço", th_style),
        Paragraph("Cliente", th_style),
        Paragraph("Dt. Entrada", th_style),
        Paragraph("Dt. Saída", th_style),
        Paragraph("Valor", th_style)
    ]]
    
    total_acumulado = 0.0
    
    # Loop para preencher as linhas e somar os valores
    for servico, nome_cliente, data_entrada, data_saida, valor in pedidos:
        total_acumulado += valor
        tabela_dados.append([
            Paragraph(servico, td_style),
            Paragraph(nome_cliente, td_style),
            Paragraph(data_entrada, td_style),
            Paragraph(data_saida, td_style),
            Paragraph(f"R$ {valor:,.2f}", td_style)
        ])
    
    # Linha final com a somatória total
    tabela_dados.append([
        Paragraph("<b>TOTAL GERAL:</b>", td_bold), "", "", "", 
        Paragraph(f"<b>R$ {total_acumulado:,.2f}</b>", td_bold)
    ])
    
    # Configuração visual e larguras das colunas da tabela
    # Largura total disponível ~552 pt (612 - 60 de margens)
    t_relatorio = Table(tabela_dados, colWidths=[130, 150, 90, 90, 92])
    
    estilo_tabela = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")), # Cor azul do cabeçalho
        ('ALIGN', (0,0), (-1,0), 'LEFT'),
        ('PADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-2), 0.5, colors.HexColor("#CBD5E0")), # Grade fina interna
        ('SPAN', (0, -1), (3, -1)), # Mescla as 4 primeiras colunas do totalizador
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#EDF2F7")), # Fundo cinza claro para o totalizador
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.HexColor("#2B6CB0")), # Linha mais grossa sobre o total
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ])
    
    t_relatorio.setStyle(estilo_tabela)
    story.append(t_relatorio)
    
    # Geração do arquivo físico
    doc.build(story)
    print(f"Relatório gerado com sucesso em: {caminho_pdf}")
    os.startfile(caminho_pdf) if hasattr(os, 'startfile') else os.system(f'xdg-open {nome_arquivo}')
    return True