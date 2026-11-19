from PyQt5 import QtWidgets,uic
from PyQt5.QtCore import QDate
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from sqlcipher3 import dbapi2 as sqlite3
import sys,os
import imprimir as pc

# ============================================================
# Configurar banco de dados
# ============================================================
conn = sqlite3.connect('ourives.db')
cursor = conn.cursor()
cursor.execute("PRAGMA key = 'P@s5w0rD.!2EfS';")
    
try:
#Abre e lê o arquivo .sql
    with open('ourives_db.sql', 'r', encoding='utf-8') as f:
        script_sql = f.read()
        
    # Executa todas as instruções do arquivo SQL de uma vez
    cursor.executescript(script_sql)
    conn.commit()
    print("Banco de dados SQLite configurado com sucesso!")
        
except FileNotFoundError:
    print("Erro: O arquivo 'schema.sql' não foi encontrado.")
except sqlite3.Error as e:
    print(f"Erro no SQLite: {e}")
finally:
    # Garante o fechamento da conexão
   conn.close()

# ============================================================
# Configuração dos botões de navegação
# ============================================================
def cliene_tab():
    tela.buscar_cliente_txt.textChanged.connect(Cliente.search)
    Cliente.search()
    
    tela.hud.setCurrentIndex(0)

def servico_tab():
    tela.buscar_servico_txt.textChanged.connect(Servico.search)
    Servico.search()

    tela.hud.setCurrentIndex(1)

def cad_cliente_tab():
    tela.cliente_cad_telefone_txt.setInputMask("(99)9999-9999; ") 
    tela.cliente_cad_cpf_txt.setInputMask("999.999.999-99; ") 
    tela.hud.setCurrentIndex(2)

def cad_serv_tab():
    tela.serv_cad_cpf_txt.setInputMask("999.999.999-99; ") 
    tela.serv_cad_saida_date_edit.setDate(QDate.currentDate())
    tela.hud.setCurrentIndex(3)

def att_serv():
    linha = tela.servico_table.currentRow()
        
    if linha == -1:
        QtWidgets.QMessageBox.warning(tela, "Atenção", "Selecione um Servico para editar")
        return
    else:  
        tela_servico_att.saida_date_edit.setDate(QDate.currentDate())
        tela_servico_att.show()

def att_serv_voltar():
    tela_servico_att.close()

def att_client():
    linha = tela.cliente_table.currentRow()
    
    if linha == -1:
        QtWidgets.QMessageBox.warning(tela, "Atenção", "Selecione um cliente para editar")
        return
    else:                
        tela_cliente_att.telefone_txt.setInputMask("(99)9999-9999; ") 
        tela_cliente_att.cpf_txt.setInputMask("999.999.999-99; ") 
        tela_cliente_att.show()

def att_cliente_voltar():
    tela_cliente_att.close()
# ============================================================
# Classes
# ============================================================
class Cliente():
    def __init__(self,nome,sobrenome,cpf,telefone,endereco):
        self.nome=nome
        self.sobrenome=sobrenome
        self.cpf=cpf
        self.telefone=telefone
        self.endereco=endereco

    def cadastrar():
        cadastrar=Cliente(tela.cliente_cad_nome_txt.text().strip(),
                          tela.cliente_cad_sobrenome_txt.text().strip(),
                          tela.cliente_cad_cpf_txt.text().strip(),
                          tela.cliente_cad_telefone_txt.text().strip(),
                          tela.cliente_cad_endereco_txt.text().strip())

        if cadastrar.nome=="" or len(cadastrar.cpf)!=14:
            QtWidgets.QMessageBox.warning(tela, "Atenção","Nome e CPF são obrigatórios!")
            return

        try:
            conn = sqlite3.connect('ourives.db')
            cursor = conn.cursor()
            cursor.execute("PRAGMA key = 'P@s5w0rD.!2EfS';")

            cursor.execute("SELECT cpf FROM cliente WHERE cpf = ?",(cadastrar.cpf,))

            if cursor.fetchall():
                QtWidgets.QMessageBox.warning(tela, "Atenção","CPF Já cadastrado!")
                return
            else:
                # 1️⃣ Inserir cliente
                cursor.execute("""
                    INSERT INTO cliente (nome, sobrenome, cpf, telefone, endereco)
                    VALUES (?,?,?,?,?)
                """, (cadastrar.nome ,cadastrar.sobrenome, cadastrar.cpf, cadastrar.telefone, cadastrar.endereco))


                conn.commit()
                
                QtWidgets.QMessageBox.warning(tela, "Atenção", "Cliente cadastrado com sucesso.")

        except Exception as e:
            QtWidgets.QMessageBox.warning(tela, "Atenção", f'Erro ao cadastrar {e}')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

        tela.cliente_cad_nome_txt.clear(),
        tela.cliente_cad_sobrenome_txt.clear(),
        tela.cliente_cad_cpf_txt.clear(),
        tela.cliente_cad_telefone_txt.clear(),
        tela.cliente_cad_endereco_txt.clear()

    def search():
        
        # Obtém o texto digitado na Line Edit
        busca = tela.buscar_cliente_txt.text().strip()
        
        # Conecta ao banco de dados ouves.db
        conexao = sqlite3.connect("ourives.db")
        cursor = conexao.cursor()
        cursor.execute("PRAGMA key = 'P@s5w0rD.!2EfS';")
        try:
            # Consulta SQL usando LIKE para filtrar pelo campo 'nome'
            # O uso de '%' permite que encontre o nome em qualquer parte do texto digitado
            query = """
                SELECT idCliente, nome, sobrenome, telefone 
                FROM cliente 
                WHERE nome LIKE ?
                ORDER BY nome ASC
            """
            cursor.execute(query, (f"%{busca}%",))
            dados = cursor.fetchall()
                    
            # Limpa as linhas atuais da tabela (mantendo o cabeçalho)
            tela.cliente_table.setRowCount(0)

            tela.cliente_table.setRowCount(len(dados))
            tela.cliente_table.setColumnCount(4)
            tela.cliente_table.setHorizontalHeaderLabels(["ID","NOME","SOBRENOME","TELEFONE"])

            for i in range(len(dados)):
                for j in range(len(dados[i])):
                    item = QtWidgets.QTableWidgetItem(str(dados[i][j]))                    
                    tela.cliente_table.setItem(i, j, item)

        except sqlite3.OperationalError:
            # Captura o erro de "tabela não existe" e ignora
            dados = []

        except Exception as e:
            QtWidgets.QMessageBox.warning(tela, "Atenção", f"Erro ao Listar {e}")
            conn.rollback()
        
        finally:
            cursor.close()
            conn.close()
      
    def imprimir():
        try:
            linha = tela.cliente_table.currentRow()
            idCliente= tela.cliente_table.item(linha, 0).text()
            pc.gerar_pdf_cliente(int(idCliente))
        except:
            QtWidgets.QMessageBox.warning(tela, "Atenção", "Selecione um Cliente na tabela para poder gerar o PDF")
            
    def editar():
        linha = tela.cliente_table.currentRow()
        idCliente= tela.cliente_table.item(linha, 0).text()
        att=Cliente(tela_cliente_att.nome_txt.text().strip(),
                    tela_cliente_att.sobrenome_txt.text().strip(),
                    tela_cliente_att.cpf_txt.text().strip(),
                    tela_cliente_att.telefone_txt.text().strip(),
                    tela_cliente_att.endereco_txt.text().strip()

        )
        
        if att.nome == "" or att.sobrenome == "" or att.endereco == "":
            QtWidgets.QMessageBox.warning(tela_cliente_att, "Atenção", "Por favor, preencha todos os campos obrigatórios.")
            return

        elif len(att.cpf) != 14 or len(att.telefone) != 13:
            QtWidgets.QMessageBox.warning(tela, "Atenção", "CPF ou Telefone com formato inválido.")
            return

        else:
            try:
                conn = sqlite3.connect('ourives.db')
                cursor = conn.cursor()
                cursor.execute("PRAGMA key = 'P@s5w0rD.!2EfS';")

                # Atualiza cliente
                cursor.execute("""
                    UPDATE cliente
                    SET Nome=?, sobrenome=?, cpf=?, telefone=?, endereco=?
                    WHERE idCliente=?
                """, (att.nome, att.sobrenome, att.cpf, att.telefone, att.endereco, idCliente))

                conn.commit()
                

                QtWidgets.QMessageBox.warning(tela_cliente_att, "Atenção", "Cliente Atualizado com sucesso")
                Cliente.search()

            except Exception as e:
                QtWidgets.QMessageBox.warning(tela_cliente_att, "Atenção", f"Erro ao atualizar {e}")
                conn.rollback()
            finally:
                cursor.close()
                conn.close()
                idCliente=-1

class Servico():
    def __init__(self,servico,descricao,valor,data_entrada,data_saida,idCliente):
        self.servico=servico
        self.descricao=descricao
        self.valor=valor
        self.data_entrada=data_entrada
        self.data_saida=data_saida
        self.idCliente=idCliente

    def cadastrar():
        cadastrar=Servico(tela.serv_cad_servico_txt.text(),
                          tela.serv_cad_descricao_txt.toPlainText(),
                          tela.serv_cad_valor_txt.text().replace(",","."),
                          datetime.today().strftime('%d-%m-%Y'),
                          tela.serv_cad_saida_date_edit.date().toString("dd-MM-yyyy"),
                          tela.serv_cad_cpf_txt.text())                      

        conn = sqlite3.connect('ourives.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA key = 'P@s5w0rD.!2EfS';")

        try:
            cursor.execute("""
                            SELECT c.idCliente
                            FROM cliente AS c
                            WHERE c.cpf=?
                            """,(cadastrar.idCliente,))
            resultado = cursor.fetchone()
             
        except:
            QtWidgets.QMessageBox.warning(tela, "Atenção","CPF não encontrado!")
            return
        id=resultado
        
        if id==None:
            
            QtWidgets.QMessageBox.warning(tela, "Atenção","CPF obrigatório!")
            return
        
        try:
            id=resultado[0]
            conn = sqlite3.connect('ourives.db')
            cursor = conn.cursor()
            cursor.execute("PRAGMA key = 'P@s5w0rD.!2EfS';")

            # 1️⃣ Inserir Serviço
            cursor.execute("""
                INSERT INTO pedido (servico,descricao,valor,data_entrada,data_saida,idCliente)
                VALUES (?,?,?,?,?,?)
            """, (cadastrar.servico,cadastrar.descricao,cadastrar.valor,cadastrar.data_entrada,cadastrar.data_saida,id))


            conn.commit()
            
            QtWidgets.QMessageBox.warning(tela, "Atenção", "Serviço cadastrado com sucesso.")

        except Exception as e:
            QtWidgets.QMessageBox.warning(tela, "Atenção", f'Erro ao cadastrar {e}')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

        tela.serv_cad_servico_txt.clear()
        tela.serv_cad_descricao_txt.clear()
        tela.serv_cad_valor_txt.clear()
        tela.serv_cad_saida_date_edit.setDate(QDate.currentDate())
        tela.serv_cad_cpf_txt.clear()

    def search():
        
        # Obtém o texto digitado na Line Edit
        busca = tela.buscar_servico_txt.text().strip()
        
        # Conecta ao banco de dados ouves.db
        conexao = sqlite3.connect("ourives.db")
        cursor = conexao.cursor()
        cursor.execute("PRAGMA key = 'P@s5w0rD.!2EfS';")

        try:
            # Consulta SQL usando LIKE para filtrar pelo campo 'nome'
            # O uso de '%' permite que encontre o nome em qualquer parte do texto digitado
            query = """
                SELECT s.idPedido, s.servico, c.nome, s.valor, s.data_entrada, s.data_saida
                FROM cliente AS c
                JOIN pedido AS s
                ON s.idCliente=c.idCliente
                WHERE c.nome LIKE ?
            """
            cursor.execute(query, (f"%{busca}%",))
            dados = cursor.fetchall()
                    
            # Limpa as linhas atuais da tabela (mantendo o cabeçalho)
            tela.servico_table.setRowCount(0)

            tela.servico_table.setRowCount(len(dados))
            tela.servico_table.setColumnCount(6)
            tela.servico_table.setHorizontalHeaderLabels(["ID","SERVIÇO","CLIENTE","VALOR","DATA ENTRADA","DATA SAIDA"])

            for i in range(len(dados)):
                for j in range(len(dados[i])):
                    item = QtWidgets.QTableWidgetItem(str(dados[i][j]))                    
                    tela.servico_table.setItem(i, j, item)

        except sqlite3.OperationalError:
            # Captura o erro de "tabela não existe" e ignora
            dados = []

        except Exception as e:
            QtWidgets.QMessageBox.warning(tela, "Atenção", f"Erro ao Listar {e}")
            conn.rollback()
        
        finally:
            cursor.close()
            conn.close()
    
    def atualizar():
        linha = tela.servico_table.currentRow()
         

        att=Servico(tela_servico_att.servico_txt.text().strip(),
                    tela_servico_att.descricao_txt.toPlainText().strip(),
                    tela_servico_att.valor_txt.text().strip(),
                    "",
                    tela_servico_att.saida_date_edit.date().toString("dd-MM-yyyy"),
                    tela.servico_table.item(linha, 0).text()

        )
        
        if att.servico == "" or att.descricao == "" or att.valor == "":
            QtWidgets.QMessageBox.warning(tela_servico_att, "Atenção", "Por favor, preencha todos os campos obrigatórios.")
            return

        else:
            try:
                conn = sqlite3.connect('ourives.db')
                cursor = conn.cursor()
                cursor.execute("PRAGMA key = 'P@s5w0rD.!2EfS';")

                # Atualiza Serviço
                cursor.execute("""
                    UPDATE pedido
                    SET servico=?, descricao=?, valor=?, data_saida=?
                    WHERE idPedido=?
                """, (att.servico, att.descricao, att.valor, att.data_saida, att.idCliente))

                conn.commit()
                

                QtWidgets.QMessageBox.warning(tela_cliente_att, "Atenção", "Cliente Atualizado com sucesso")
                Cliente.search()

            except Exception as e:
                QtWidgets.QMessageBox.warning(tela_cliente_att, "Atenção", f"Erro ao atualizar {e}")
                conn.rollback()
            finally:
                cursor.close()
                conn.close()
            idCliente=-1
            Servico.listar()

    def imprimir():
        try:
            linha = tela.servico_table.currentRow()
            id_pedido=tela.servico_table.item(linha, 0).text()
            pc.gerar_pdf_via_cliente(int(id_pedido))
        except:
            QtWidgets.QMessageBox.warning(tela, "Atenção", f"Selecione um Serviço na tabela para poder imprimir.")
    def imprimir_30():
        if  pc.gerar_relatorio_ultimos_30_dias()==False:
           QtWidgets.QMessageBox.warning(tela, "Atenção", f"Nenhum pedido encontrado nos últimos 30 dias.")
        else:
            pc.gerar_relatorio_ultimos_30_dias()
            
    
# ============================================================
# Bootstrap
# ============================================================
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
   
    #---------- Telas ----------
    tela = uic.loadUi("ui/main.ui")
    tela_cliente_att=uic.loadUi("ui/att_cliente.ui")
    tela_servico_att=uic.loadUi("ui/att_serv.ui")

    #---------- Botões ---------
    ##--------- Navegação ------
    tela.cliente_bt.clicked.connect(cliene_tab)
    tela.cad_cliente_bt.clicked.connect(cad_cliente_tab)
    tela.servicos_bt.clicked.connect(servico_tab)
    tela.cad_serv_bt.clicked.connect(cad_serv_tab)

    ##--------- Serviços ------
    tela.att_serv_bt.clicked.connect(att_serv)
    tela.print_serv_bt.clicked.connect(Servico.imprimir)
    tela.print_30days_bt.clicked.connect(Servico.imprimir_30)

    ##--------- Atualizar Serviços ------
    tela_servico_att.voltar_bt.clicked.connect(att_serv_voltar)
    tela_servico_att.att_bt.clicked.connect(Servico.atualizar)

    ##--------- Clientes ------
    tela.att_cad_cliente_bt.clicked.connect(att_client)
    tela.print_cad_cliente_bt.clicked.connect(Cliente.imprimir)
    

    ##--------- Atualizar Cliente ------
    tela_cliente_att.voltar_bt.clicked.connect(att_cliente_voltar)
    tela_cliente_att.att_bt.clicked.connect(Cliente.editar)

    ##--------- Cadastrar Cliente ------
    tela.cliente_cad_bt.clicked.connect(Cliente.cadastrar)
    

    ##--------- Cadastrar Serviços ------
    tela.serv_cad_bt.clicked.connect(Servico.cadastrar)

    #---------- Setup Tela Inicial ----------
    
    servico_tab()
    tela.show()
    sys.exit(app.exec())
