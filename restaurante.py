import mysql.connector
import google.generativeai as genai # Importar Gemini
from tkinter import *
from tkinter import ttk, messagebox
import customtkinter
from CTkMessagebox import CTkMessagebox
from datetime import datetime
from twilio.rest import Client
import os # Para gerenciar chave de API (opcional, mas recomendado)

# Imports para o gráfico
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use("TkAgg") # Define o backend do Matplotlib para Tkinter

# ==================== Configurações ====================
# Chave da API Gemini - Mantenha segura!

#gemini_api_key = "CHAVE NO PDF" # Chave fornecida pelo usuário / ESTA COMENTADO POIS O GITHUB NÃO PERMITE COLOCAR CHAVES (DESCOMENTE ESSA LINHA DE CÓDIGO E COLOQUE A CHAVE QUE ESTA NO PDF)

# Configura a biblioteca Gemini
gemini_model = None
gemini_chat = None
try:
    genai.configure(api_key=gemini_api_key)
    nome_modelo_para_usar = "models/gemini-1.5-flash-latest"
    print(f"Inicializando o modelo: {nome_modelo_para_usar}...")
    gemini_model = genai.GenerativeModel(nome_modelo_para_usar)
    gemini_chat = gemini_model.start_chat(history=[])
    print(f"Modelo {nome_modelo_para_usar} inicializado com sucesso.")
except Exception as e:
    error_message = f"Falha ao configurar ou inicializar a API Gemini com o modelo {nome_modelo_para_usar}: {e}\nVerifique sua chave de API e conexão."
    print(f"ERRO: {error_message}")
    messagebox.showerror("Erro Gemini API", error_message)

# Configurações Twilio
#account_sid = "CHAVE NO PDF"                        # ESTA COMENTADO POIS O GITHUB NÃO PERMITE COLOCAR CHAVES (DESCOMENTE ESSA LINHA DE CÓDIGO E COLOQUE A CHAVE QUE ESTA NO PDF)
#auth_token = "CHAVE NO PDF"                        
#twilio_number = "CHAVE NO PDF"                      # ESTA COMENTADO POIS O GITHUB NÃO PERMITE COLOCAR CHAVES (DESCOMENTE ESSA LINHA DE CÓDIGO E COLOQUE A CHAVE QUE ESTA NO PDF)
#client_twilio = Client(account_sid, auth_token)

# ==================== Funções de Banco ====================
def conecta_bd():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="restaurante",
            connect_timeout=5
        )
    except mysql.connector.Error as err:
        messagebox.showerror("Erro Conexão DB", f"Não foi possível conectar ao banco: {err}")
        return None

# ==================== Atualiza Comboboxes ====================
def atualizar_comboboxes_pedido():
    conn = conecta_bd()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT nome FROM clientes ORDER BY nome")
        clientes = [row[0] for row in cursor.fetchall()]
        combobox_cliente_pedido["values"] = [""] + clientes

        cursor.execute("SELECT nome FROM pratos ORDER BY nome")
        pratos = [row[0] for row in cursor.fetchall()]
        combobox_prato_pedido["values"] = [""] + pratos
    except mysql.connector.Error as err:
        messagebox.showerror("Erro DB", f"Erro ao carregar clientes/pratos: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# ==================== Enviar SMS ====================
def enviar_sms(telefone_cliente, mensagem):
    if not telefone_cliente:
        print("Telefone do cliente não fornecido para SMS.")
        return
    if not telefone_cliente.startswith("+"):
        telefone_cliente = "+55" + telefone_cliente
    try:
        print(f"Enviando SMS para {telefone_cliente}: {mensagem}")
        message = client_twilio.messages.create(body=mensagem, from_=twilio_number, to=telefone_cliente)
        print(f"SMS SID: {message.sid}, Status: {message.status}")
    except Exception as e:
        try:
            CTkMessagebox(title="Erro SMS", message=f"Falha ao enviar SMS para {telefone_cliente}: {str(e)}", icon="cancel")
        except NameError:
            messagebox.showerror("Erro SMS", f"Falha ao enviar SMS para {telefone_cliente}: {str(e)}")
        print(f"Erro ao enviar SMS: {str(e)}")

# ==================== CRUD Clientes ====================
def cadastrar_cliente():
    nome = entry_nome_cliente.get().strip()
    telefone = entry_telefone_cliente.get().strip()
    email = entry_email_cliente.get().strip()
    if not nome:
        CTkMessagebox(title="Atenção", message="Nome é obrigatório!", icon="warning")
        return
    conn = conecta_bd()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO clientes (nome, telefone, email) VALUES (%s, %s, %s)", (nome, telefone, email))
        conn.commit()
        CTkMessagebox(title="Sucesso", message="Cliente cadastrado com sucesso!", icon="check")
    except mysql.connector.Error as err:
        CTkMessagebox(title="Erro DB", message=f"Erro ao cadastrar cliente: {err}", icon="cancel")
    except Exception as e:
        CTkMessagebox(title="Erro", message=f"Erro inesperado: {str(e)}", icon="cancel")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    listar_clientes()
    atualizar_comboboxes_pedido()
    limpar_campos_cliente()

def listar_clientes():
    for item in tree_clientes.get_children():
        tree_clientes.delete(item)
    conn = conecta_bd()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM clientes ORDER BY nome")
        dados = cursor.fetchall()
        for row in dados:
            tree_clientes.insert("", END, values=row)
    except mysql.connector.Error as err:
        CTkMessagebox(title="Erro DB", message=f"Erro ao listar clientes: {err}", icon="cancel")
    except Exception as e:
        CTkMessagebox(title="Erro", message=f"Erro inesperado ao listar clientes: {str(e)}", icon="cancel")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def on_cliente_select(event=None):
    limpar_campos_cliente()
    selecionado = tree_clientes.focus()
    if not selecionado:
        return
    valores = tree_clientes.item(selecionado, "values")
    if valores:
        entry_nome_cliente.insert(0, valores[1])
        entry_telefone_cliente.insert(0, valores[2])
        entry_email_cliente.insert(0, valores[3])

def excluir_cliente():
    selecionado = tree_clientes.focus()
    if not selecionado:
        CTkMessagebox(title="Atenção", message="Selecione um cliente para excluir!", icon="warning")
        return
    valores = tree_clientes.item(selecionado, "values")
    id_cliente = valores[0]
    nome_cliente = valores[1]
    msg = CTkMessagebox(title="Confirmação", message=f"Deseja realmente excluir o cliente \"{nome_cliente}\"?", icon="question", option_1="Não", option_2="Sim")
    if msg.get() == "Sim":
        conn = conecta_bd()
        if not conn:
            return
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM pedidos WHERE id_cliente = %s", (id_cliente,))
            if cursor.fetchone()[0] > 0:
                CTkMessagebox(title="Erro", message="Não é possível excluir cliente com pedidos registrados.", icon="cancel")
                return
            cursor.execute("DELETE FROM clientes WHERE id = %s", (id_cliente,))
            conn.commit()
            CTkMessagebox(title="Sucesso", message="Cliente excluído com sucesso!", icon="check")
        except mysql.connector.Error as err:
            CTkMessagebox(title="Erro DB", message=f"Erro ao excluir cliente: {err}", icon="cancel")
        except Exception as e:
            CTkMessagebox(title="Erro", message=f"Erro inesperado: {str(e)}", icon="cancel")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
        listar_clientes()
        atualizar_comboboxes_pedido()
        limpar_campos_cliente()

def limpar_campos_cliente():
    entry_nome_cliente.delete(0, END)
    entry_telefone_cliente.delete(0, END)
    entry_email_cliente.delete(0, END)
    selecionado = tree_clientes.focus()
    if selecionado:
        tree_clientes.selection_remove(selecionado)

def alterar_cliente():
    selecionado = tree_clientes.focus()
    if not selecionado:
        CTkMessagebox(title="Atenção", message="Selecione um cliente para alterar!", icon="warning")
        return
    id_cliente = tree_clientes.item(selecionado, "values")[0]
    nome = entry_nome_cliente.get().strip()
    telefone = entry_telefone_cliente.get().strip()
    email = entry_email_cliente.get().strip()
    if not nome:
        CTkMessagebox(title="Atenção", message="Nome é obrigatório!", icon="warning")
        return
    conn = conecta_bd()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE clientes SET nome = %s, telefone = %s, email = %s WHERE id = %s", (nome, telefone, email, id_cliente))
        conn.commit()
        CTkMessagebox(title="Sucesso", message="Cliente alterado com sucesso!", icon="check")
    except mysql.connector.Error as err:
        CTkMessagebox(title="Erro DB", message=f"Erro ao alterar cliente: {err}", icon="cancel")
    except Exception as e:
        CTkMessagebox(title="Erro", message=f"Erro inesperado: {str(e)}", icon="cancel")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    listar_clientes()
    atualizar_comboboxes_pedido()
    limpar_campos_cliente()

# ==================== CRUD Pratos ====================
def cadastrar_prato():
    nome = entry_nome_prato.get().strip()
    descricao = entry_descricao_prato.get("1.0", END).strip()
    preco_str = entry_preco_prato.get().strip()
    if not nome or not preco_str:
        CTkMessagebox(title="Atenção", message="Nome e Preço são obrigatórios!", icon="warning")
        return
    try:
        preco = float(preco_str.replace(",", "."))
    except ValueError:
        CTkMessagebox(title="Erro", message="Preço deve ser um número válido! Use ponto ou vírgula.", icon="cancel")
        return
    conn = conecta_bd()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO pratos (nome, descricao, preco) VALUES (%s, %s, %s)", (nome, descricao, preco))
        conn.commit()
        CTkMessagebox(title="Sucesso", message="Prato cadastrado com sucesso!", icon="check")
    except mysql.connector.Error as err:
        CTkMessagebox(title="Erro DB", message=f"Erro ao cadastrar prato: {err}", icon="cancel")
    except Exception as e:
        CTkMessagebox(title="Erro", message=f"Erro inesperado: {str(e)}", icon="cancel")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    listar_pratos()
    atualizar_comboboxes_pedido()
    limpar_campos_prato()

def listar_pratos():
    for item in tree_pratos.get_children():
        tree_pratos.delete(item)
    conn = conecta_bd()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, nome, descricao, FORMAT(preco, 2, 'de_DE') FROM pratos ORDER BY nome")
        dados = cursor.fetchall()
        for row in dados:
            tree_pratos.insert("", END, values=row)
    except mysql.connector.Error as err:
        CTkMessagebox(title="Erro DB", message=f"Erro ao listar pratos: {err}", icon="cancel")
    except Exception as e:
        CTkMessagebox(title="Erro", message=f"Erro inesperado ao listar pratos: {str(e)}", icon="cancel")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def on_prato_select(event=None):
    limpar_campos_prato()
    selecionado = tree_pratos.focus()
    if not selecionado:
        return
    valores = tree_pratos.item(selecionado, "values")
    if valores:
        entry_nome_prato.insert(0, valores[1])
        entry_descricao_prato.insert("1.0", valores[2])
        entry_preco_prato.insert(0, valores[3])

def excluir_prato():
    selecionado = tree_pratos.focus()
    if not selecionado:
        CTkMessagebox(title="Atenção", message="Selecione um prato para excluir!", icon="warning")
        return
    valores = tree_pratos.item(selecionado, "values")
    id_prato = valores[0]
    nome_prato = valores[1]
    msg = CTkMessagebox(title="Confirmação", message=f"Deseja realmente excluir o prato \"{nome_prato}\"?", icon="question", option_1="Não", option_2="Sim")
    if msg.get() == "Sim":
        conn = conecta_bd()
        if not conn:
            return
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM pedidos WHERE id_prato = %s", (id_prato,))
            if cursor.fetchone()[0] > 0:
                CTkMessagebox(title="Erro", message="Não é possível excluir prato presente em pedidos.", icon="cancel")
                return
            cursor.execute("DELETE FROM pratos WHERE id = %s", (id_prato,))
            conn.commit()
            CTkMessagebox(title="Sucesso", message="Prato excluído com sucesso!", icon="check")
        except mysql.connector.Error as err:
            CTkMessagebox(title="Erro DB", message=f"Erro ao excluir prato: {err}", icon="cancel")
        except Exception as e:
            CTkMessagebox(title="Erro", message=f"Erro inesperado: {str(e)}", icon="cancel")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
        listar_pratos()
        atualizar_comboboxes_pedido()
        limpar_campos_prato()

def limpar_campos_prato():
    entry_nome_prato.delete(0, END)
    entry_descricao_prato.delete("1.0", END)
    entry_preco_prato.delete(0, END)
    selecionado = tree_pratos.focus()
    if selecionado:
        tree_pratos.selection_remove(selecionado)

def alterar_prato():
    selecionado = tree_pratos.focus()
    if not selecionado:
        CTkMessagebox(title="Atenção", message="Selecione um prato para alterar!", icon="warning")
        return
    id_prato = tree_pratos.item(selecionado, "values")[0]
    nome = entry_nome_prato.get().strip()
    descricao = entry_descricao_prato.get("1.0", END).strip()
    preco_str = entry_preco_prato.get().strip()
    if not nome or not preco_str:
        CTkMessagebox(title="Atenção", message="Nome e Preço são obrigatórios!", icon="warning")
        return
    try:
        preco = float(preco_str.replace(",", "."))
    except ValueError:
        CTkMessagebox(title="Erro", message="Preço deve ser um número válido! Use ponto ou vírgula.", icon="cancel")
        return
    conn = conecta_bd()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE pratos SET nome = %s, descricao = %s, preco = %s WHERE id = %s", (nome, descricao, preco, id_prato))
        conn.commit()
        CTkMessagebox(title="Sucesso", message="Prato alterado com sucesso!", icon="check")
    except mysql.connector.Error as err:
        CTkMessagebox(title="Erro DB", message=f"Erro ao alterar prato: {err}", icon="cancel")
    except Exception as e:
        CTkMessagebox(title="Erro", message=f"Erro inesperado: {str(e)}", icon="cancel")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    listar_pratos()
    atualizar_comboboxes_pedido()
    limpar_campos_prato()

# ==================== CRUD Pedidos ====================
def cadastrar_pedido():
    cliente_nome = combobox_cliente_pedido.get().strip()
    prato_nome = combobox_prato_pedido.get().strip()
    quantidade_str = entry_quantidade_pedido.get().strip()
    data_pedido = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not cliente_nome or not prato_nome or not quantidade_str:
        CTkMessagebox(title="Atenção", message="Cliente, Prato e Quantidade são obrigatórios!", icon="warning")
        return
    try:
        quantidade = int(quantidade_str)
        if quantidade <= 0:
            raise ValueError("Quantidade deve ser positiva")
    except ValueError as e:
        CTkMessagebox(title="Erro", message=f"Quantidade inválida: {e}", icon="cancel")
        return
    id_cliente = None
    id_prato = None
    telefone_cliente = None
    conn = conecta_bd()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, telefone FROM clientes WHERE nome = %s", (cliente_nome,))
        cliente_data = cursor.fetchone()
        if not cliente_data:
            CTkMessagebox(title="Erro", message=f"Cliente '{cliente_nome}' não encontrado!", icon="cancel")
            return
        id_cliente, telefone_cliente = cliente_data
        cursor.execute("SELECT id FROM pratos WHERE nome = %s", (prato_nome,))
        prato_data = cursor.fetchone()
        if not prato_data:
            CTkMessagebox(title="Erro", message=f"Prato '{prato_nome}' não encontrado!", icon="cancel")
            return
        id_prato = prato_data[0]
        cursor.execute("INSERT INTO pedidos (id_cliente, id_prato, quantidade, data_pedido) VALUES (%s, %s, %s, %s)", (id_cliente, id_prato, quantidade, data_pedido))
        conn.commit()
        if telefone_cliente:
            mensagem_sms = f"Olá {cliente_nome}, seu pedido de {quantidade}x {prato_nome} foi registrado em {data_pedido}. Obrigado!"
            enviar_sms(telefone_cliente, mensagem_sms)
        else:
            print(f"Cliente {cliente_nome} não possui telefone cadastrado para envio de SMS.")
        CTkMessagebox(title="Sucesso", message="Pedido cadastrado com sucesso!", icon="check")
    except mysql.connector.Error as err:
        CTkMessagebox(title="Erro DB", message=f"Erro ao cadastrar pedido: {err}", icon="cancel")
    except Exception as e:
        CTkMessagebox(title="Erro", message=f"Erro inesperado: {str(e)}", icon="cancel")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    listar_pedidos()
    limpar_campos_pedido()

def listar_pedidos():
    for item in tree_pedidos.get_children():
        tree_pedidos.delete(item)
    conn = conecta_bd()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT pedidos.id, clientes.nome, pratos.nome, pedidos.quantidade, DATE_FORMAT(pedidos.data_pedido, '%d/%m/%Y %H:%i:%s')
            FROM pedidos
            JOIN clientes ON pedidos.id_cliente = clientes.id
            JOIN pratos ON pedidos.id_prato = pratos.id
            ORDER BY pedidos.data_pedido DESC
        """)
        dados = cursor.fetchall()
        for row in dados:
            tree_pedidos.insert("", END, values=row)
    except mysql.connector.Error as err:
        CTkMessagebox(title="Erro DB", message=f"Erro ao listar pedidos: {err}", icon="cancel")
    except Exception as e:
        CTkMessagebox(title="Erro", message=f"Erro inesperado ao listar pedidos: {str(e)}", icon="cancel")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def excluir_pedido():
    selecionado = tree_pedidos.focus()
    if not selecionado:
        CTkMessagebox(title="Atenção", message="Selecione um pedido para excluir!", icon="warning")
        return
    valores = tree_pedidos.item(selecionado, "values")
    id_pedido = valores[0]
    cliente_nome = valores[1]
    prato_nome = valores[2]
    msg = CTkMessagebox(title="Confirmação", message=f"Deseja realmente excluir o pedido {id_pedido} ({cliente_nome} - {prato_nome})?", icon="question", option_1="Não", option_2="Sim")
    if msg.get() == "Sim":
        conn = conecta_bd()
        if not conn:
            return
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM pedidos WHERE id = %s", (id_pedido,))
            conn.commit()
            CTkMessagebox(title="Sucesso", message="Pedido excluído com sucesso!", icon="check")
        except mysql.connector.Error as err:
            CTkMessagebox(title="Erro DB", message=f"Erro ao excluir pedido: {err}", icon="cancel")
        except Exception as e:
            CTkMessagebox(title="Erro", message=f"Erro inesperado: {str(e)}", icon="cancel")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
        listar_pedidos()

def limpar_campos_pedido():
    combobox_cliente_pedido.set("")
    combobox_prato_pedido.set("")
    entry_quantidade_pedido.delete(0, END)
    selecionado = tree_pedidos.focus()
    if selecionado:
        tree_pedidos.selection_remove(selecionado)

# ==================== Gemini Chat Bot ====================
def enviar_mensagem_chat():
    if not gemini_model or not gemini_chat:
        CTkMessagebox(title="Erro Gemini", message="API Gemini não inicializada corretamente. Verifique a chave e a configuração inicial.", icon="cancel")
        return
    texto_usuario = txt_chat_usuario.get("1.0", END).strip()
    if not texto_usuario:
        CTkMessagebox(title="Atenção", message="Digite uma mensagem para enviar ao bot.", icon="warning")
        return
    txt_chat_bot.configure(state=NORMAL)
    txt_chat_bot.insert(END, f"Você: {texto_usuario}\n")
    txt_chat_bot.see(END)
    txt_chat_usuario.delete("1.0", END)
    txt_chat_bot.configure(state=DISABLED)
    janela.update_idletasks()
    txt_chat_bot.configure(state=NORMAL)
    pensando_msg = "Bot: Pensando...\n"
    txt_chat_bot.insert(END, pensando_msg)
    txt_chat_bot.see(END)
    txt_chat_bot.configure(state=DISABLED)
    janela.update_idletasks()
    texto_resposta = ""
    try:
        resposta = gemini_chat.send_message(texto_usuario)
        texto_resposta = resposta.text
    except Exception as e:
        texto_resposta = f"Erro ao obter resposta do Gemini: {str(e)}"
        print(f"Erro Gemini API: {str(e)}")
    txt_chat_bot.configure(state=NORMAL)
    start_index = txt_chat_bot.search(pensando_msg.strip(), "1.0", END, backwards=True)
    if start_index:
        end_index = f"{start_index}+{len(pensando_msg)}c"
        txt_chat_bot.delete(start_index, end_index)
    txt_chat_bot.insert(END, f"Bot: {texto_resposta}\n\n")
    txt_chat_bot.see(END)
    txt_chat_bot.configure(state=DISABLED)

# ==================== Análise de Pratos (Gráfico) ====================
# Variável global para o canvas do gráfico, para poder limpar depois
canvas_grafico = None

def gerar_grafico_pratos_mais_pedidos():
    global canvas_grafico
    conn = conecta_bd()
    if not conn:
        CTkMessagebox(title="Erro DB", message="Não foi possível conectar ao banco para gerar o gráfico.", icon="cancel")
        return
    
    try:
        # Consulta SQL para somar quantidades por prato
        query = """
            SELECT pratos.nome, SUM(pedidos.quantidade) as total_pedido
            FROM pedidos
            JOIN pratos ON pedidos.id_prato = pratos.id
            GROUP BY pratos.nome
            ORDER BY total_pedido DESC
        """
        # Usar Pandas para ler diretamente do SQL e facilitar a manipulação
        df_pratos = pd.read_sql(query, conn)

        if df_pratos.empty:
            CTkMessagebox(title="Info", message="Não há dados de pedidos para gerar o gráfico.", icon="info")
            return

        # Limpa o frame do gráfico se já existir um canvas
        for widget in frame_grafico_analise.winfo_children():
            widget.destroy()
        
        # Cria a figura e o eixo do Matplotlib
        # Ajusta o tamanho da figura se necessário
        fig, ax = plt.subplots(figsize=(10, 5)) 
        
        # Cria o gráfico de barras
        bars = ax.bar(df_pratos['nome'], df_pratos['total_pedido'], color='skyblue')
        
        # Adiciona títulos e legendas em português
        ax.set_title('Quantidade Total Pedida por Prato')
        ax.set_xlabel('Prato')
        ax.set_ylabel('Quantidade Total Pedida')
        
        # Rotaciona os nomes dos pratos no eixo X se forem muitos
        plt.xticks(rotation=45, ha='right') 
        
        # Adiciona os valores em cima das barras
        ax.bar_label(bars, fmt='%d')

        # Ajusta o layout para não cortar legendas
        plt.tight_layout()

        # Cria o canvas do Tkinter para incorporar o gráfico Matplotlib
        canvas_grafico = FigureCanvasTkAgg(fig, master=frame_grafico_analise)
        canvas_grafico.draw()
        
        # Adiciona o widget do canvas ao frame
        canvas_grafico.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)

    except mysql.connector.Error as err:
        CTkMessagebox(title="Erro DB", message=f"Erro ao buscar dados para o gráfico: {err}", icon="cancel")
    except Exception as e:
        CTkMessagebox(title="Erro Gráfico", message=f"Erro inesperado ao gerar gráfico: {str(e)}", icon="cancel")
    finally:
        if conn and conn.is_connected():
            conn.close()

# ==================== Configurações da Interface ====================
customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

janela = customtkinter.CTk()
janela.title("Sistema de Restaurante com Gemini Chat e Análise")
janela.geometry("1100x750")

window_width = 1100
window_height = 750
screen_width = janela.winfo_screenwidth()
screen_height = janela.winfo_screenheight()
center_x = int(screen_width/2 - window_width / 2)
center_y = int(screen_height/2 - window_height / 2)
janela.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", background="#2b2b2b", foreground="white", rowheight=25, fieldbackground="#2b2b2b")
style.map("Treeview", background=[("selected", "#003366")])
style.configure("Treeview.Heading", background="#202020", foreground="white", font=("Arial", 10, "bold"))
style.configure("TCombobox", fieldbackground="#333333", background="#444444", foreground="white", arrowcolor="white", selectbackground="#003366", selectforeground="white")
style.map("TCombobox", fieldbackground=[("readonly", "#333333")], selectbackground=[("readonly", "#003366")], selectforeground=[("readonly", "white")])

tabControl = customtkinter.CTkTabview(janela, width=window_width-40, height=window_height-40)
tabControl.pack(expand=True, fill="both", padx=10, pady=10)

tab_clientes = tabControl.add("Clientes")
tab_pratos = tabControl.add("Pratos")
tab_pedidos = tabControl.add("Pedidos")
tab_chatbot = tabControl.add("ChatBot Gemini")
tab_analise = tabControl.add("Análise de Pratos") # Nova aba

# ================== GUI Clientes ==================
frame_form_clientes = customtkinter.CTkFrame(tab_clientes)
frame_form_clientes.pack(pady=10, padx=10, fill="x")
customtkinter.CTkLabel(frame_form_clientes, text="Nome:").grid(row=0, column=0, padx=(10,5), pady=5, sticky="w")
entry_nome_cliente = customtkinter.CTkEntry(frame_form_clientes, width=350)
entry_nome_cliente.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
customtkinter.CTkLabel(frame_form_clientes, text="Telefone:").grid(row=1, column=0, padx=(10,5), pady=5, sticky="w")
entry_telefone_cliente = customtkinter.CTkEntry(frame_form_clientes, width=200)
entry_telefone_cliente.grid(row=1, column=1, padx=5, pady=5, sticky="w")
customtkinter.CTkLabel(frame_form_clientes, text="Email:").grid(row=2, column=0, padx=(10,5), pady=5, sticky="w")
entry_email_cliente = customtkinter.CTkEntry(frame_form_clientes, width=350)
entry_email_cliente.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
frame_form_clientes.grid_columnconfigure(1, weight=1)
frame_botoes_clientes = customtkinter.CTkFrame(tab_clientes)
frame_botoes_clientes.pack(pady=5, padx=10, fill="x")
btn_cadastrar_cliente = customtkinter.CTkButton(frame_botoes_clientes, text="Cadastrar", command=cadastrar_cliente)
btn_cadastrar_cliente.pack(side=LEFT, padx=5, pady=5)
btn_alterar_cliente = customtkinter.CTkButton(frame_botoes_clientes, text="Alterar Selecionado", command=alterar_cliente)
btn_alterar_cliente.pack(side=LEFT, padx=5, pady=5)
btn_excluir_cliente = customtkinter.CTkButton(frame_botoes_clientes, text="Excluir Selecionado", command=excluir_cliente, fg_color="#D32F2F", hover_color="#B71C1C")
btn_excluir_cliente.pack(side=LEFT, padx=5, pady=5)
btn_limpar_cliente = customtkinter.CTkButton(frame_botoes_clientes, text="Limpar Campos", command=limpar_campos_cliente, fg_color="#555555", hover_color="#444444")
btn_limpar_cliente.pack(side=LEFT, padx=5, pady=5)
frame_tree_clientes = customtkinter.CTkFrame(tab_clientes)
frame_tree_clientes.pack(pady=10, padx=10, fill="both", expand=True)
tree_clientes = ttk.Treeview(frame_tree_clientes, columns=("ID", "Nome", "Telefone", "Email"), show="headings")
tree_clientes.heading("ID", text="ID")
tree_clientes.heading("Nome", text="Nome")
tree_clientes.heading("Telefone", text="Telefone")
tree_clientes.heading("Email", text="Email")
tree_clientes.column("ID", width=50, anchor="center")
tree_clientes.column("Nome", width=300)
tree_clientes.column("Telefone", width=150, anchor="center")
tree_clientes.column("Email", width=300)
tree_clientes.pack(side=LEFT, fill="both", expand=True)
scrollbar_clientes = customtkinter.CTkScrollbar(frame_tree_clientes, command=tree_clientes.yview)
scrollbar_clientes.pack(side=RIGHT, fill="y")
tree_clientes.configure(yscrollcommand=scrollbar_clientes.set)
tree_clientes.bind("<<TreeviewSelect>>", on_cliente_select)

# ================== GUI Pratos ==================
frame_form_pratos = customtkinter.CTkFrame(tab_pratos)
frame_form_pratos.pack(pady=10, padx=10, fill="x")
customtkinter.CTkLabel(frame_form_pratos, text="Nome:").grid(row=0, column=0, padx=(10,5), pady=5, sticky="w")
entry_nome_prato = customtkinter.CTkEntry(frame_form_pratos, width=350)
entry_nome_prato.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
customtkinter.CTkLabel(frame_form_pratos, text="Descrição:").grid(row=1, column=0, padx=(10,5), pady=(5,0), sticky="nw")
entry_descricao_prato = customtkinter.CTkTextbox(frame_form_pratos, width=350, height=80, wrap="word")
entry_descricao_prato.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
customtkinter.CTkLabel(frame_form_pratos, text="Preço (R$):", anchor="w").grid(row=2, column=0, padx=(10,5), pady=5, sticky="w")
entry_preco_prato = customtkinter.CTkEntry(frame_form_pratos, width=150)
entry_preco_prato.grid(row=2, column=1, padx=5, pady=5, sticky="w")
frame_form_pratos.grid_columnconfigure(1, weight=1)
frame_botoes_pratos = customtkinter.CTkFrame(tab_pratos)
frame_botoes_pratos.pack(pady=5, padx=10, fill="x")
btn_cadastrar_prato = customtkinter.CTkButton(frame_botoes_pratos, text="Cadastrar", command=cadastrar_prato)
btn_cadastrar_prato.pack(side=LEFT, padx=5, pady=5)
btn_alterar_prato = customtkinter.CTkButton(frame_botoes_pratos, text="Alterar Selecionado", command=alterar_prato)
btn_alterar_prato.pack(side=LEFT, padx=5, pady=5)
btn_excluir_prato = customtkinter.CTkButton(frame_botoes_pratos, text="Excluir Selecionado", command=excluir_prato, fg_color="#D32F2F", hover_color="#B71C1C")
btn_excluir_prato.pack(side=LEFT, padx=5, pady=5)
btn_limpar_prato = customtkinter.CTkButton(frame_botoes_pratos, text="Limpar Campos", command=limpar_campos_prato, fg_color="#555555", hover_color="#444444")
btn_limpar_prato.pack(side=LEFT, padx=5, pady=5)
frame_tree_pratos = customtkinter.CTkFrame(tab_pratos)
frame_tree_pratos.pack(pady=10, padx=10, fill="both", expand=True)
tree_pratos = ttk.Treeview(frame_tree_pratos, columns=("ID", "Nome", "Descrição", "Preço"), show="headings")
tree_pratos.heading("ID", text="ID")
tree_pratos.heading("Nome", text="Nome")
tree_pratos.heading("Descrição", text="Descrição")
tree_pratos.heading("Preço", text="Preço (R$)")
tree_pratos.column("ID", width=50, anchor="center")
tree_pratos.column("Nome", width=250)
tree_pratos.column("Descrição", width=400)
tree_pratos.column("Preço", width=100, anchor="e")
tree_pratos.pack(side=LEFT, fill="both", expand=True)
scrollbar_pratos = customtkinter.CTkScrollbar(frame_tree_pratos, command=tree_pratos.yview)
scrollbar_pratos.pack(side=RIGHT, fill="y")
tree_pratos.configure(yscrollcommand=scrollbar_pratos.set)
tree_pratos.bind("<<TreeviewSelect>>", on_prato_select)

# ================== GUI Pedidos ==================
frame_form_pedidos = customtkinter.CTkFrame(tab_pedidos)
frame_form_pedidos.pack(pady=10, padx=10, fill="x")
customtkinter.CTkLabel(frame_form_pedidos, text="Cliente:").grid(row=0, column=0, padx=(10,5), pady=5, sticky="w")
combobox_cliente_pedido = ttk.Combobox(frame_form_pedidos, state="readonly", width=45)
combobox_cliente_pedido.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
customtkinter.CTkLabel(frame_form_pedidos, text="Prato:").grid(row=1, column=0, padx=(10,5), pady=5, sticky="w")
combobox_prato_pedido = ttk.Combobox(frame_form_pedidos, state="readonly", width=45)
combobox_prato_pedido.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
customtkinter.CTkLabel(frame_form_pedidos, text="Quantidade:").grid(row=2, column=0, padx=(10,5), pady=5, sticky="w")
entry_quantidade_pedido = customtkinter.CTkEntry(frame_form_pedidos, width=100)
entry_quantidade_pedido.grid(row=2, column=1, padx=5, pady=5, sticky="w")
frame_form_pedidos.grid_columnconfigure(1, weight=1)
frame_botoes_pedidos = customtkinter.CTkFrame(tab_pedidos)
frame_botoes_pedidos.pack(pady=5, padx=10, fill="x")
btn_cadastrar_pedido = customtkinter.CTkButton(frame_botoes_pedidos, text="Cadastrar Pedido", command=cadastrar_pedido)
btn_cadastrar_pedido.pack(side=LEFT, padx=5, pady=5)
btn_excluir_pedido = customtkinter.CTkButton(frame_botoes_pedidos, text="Excluir Selecionado", command=excluir_pedido, fg_color="#D32F2F", hover_color="#B71C1C")
btn_excluir_pedido.pack(side=LEFT, padx=5, pady=5)
btn_limpar_pedido = customtkinter.CTkButton(frame_botoes_pedidos, text="Limpar Campos", command=limpar_campos_pedido, fg_color="#555555", hover_color="#444444")
btn_limpar_pedido.pack(side=LEFT, padx=5, pady=5)
frame_tree_pedidos = customtkinter.CTkFrame(tab_pedidos)
frame_tree_pedidos.pack(pady=10, padx=10, fill="both", expand=True)
tree_pedidos = ttk.Treeview(frame_tree_pedidos, columns=("ID", "Cliente", "Prato", "Qtd", "Data"), show="headings")
tree_pedidos.heading("ID", text="ID")
tree_pedidos.heading("Cliente", text="Cliente")
tree_pedidos.heading("Prato", text="Prato")
tree_pedidos.heading("Qtd", text="Qtd")
tree_pedidos.heading("Data", text="Data e Hora")
tree_pedidos.column("ID", width=50, anchor="center")
tree_pedidos.column("Cliente", width=250)
tree_pedidos.column("Prato", width=250)
tree_pedidos.column("Qtd", width=50, anchor="center")
tree_pedidos.column("Data", width=150, anchor="center")
tree_pedidos.pack(side=LEFT, fill="both", expand=True)
scrollbar_pedidos = customtkinter.CTkScrollbar(frame_tree_pedidos, command=tree_pedidos.yview)
scrollbar_pedidos.pack(side=RIGHT, fill="y")
tree_pedidos.configure(yscrollcommand=scrollbar_pedidos.set)

# ================== GUI Chatbot ==================
frame_chat = customtkinter.CTkFrame(tab_chatbot)
frame_chat.pack(pady=10, padx=10, fill="both", expand=True)
frame_chat.grid_rowconfigure(0, weight=1)
frame_chat.grid_columnconfigure(0, weight=1)
txt_chat_bot = customtkinter.CTkTextbox(frame_chat, state=DISABLED, wrap="word")
txt_chat_bot.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
scrollbar_chat = customtkinter.CTkScrollbar(frame_chat, command=txt_chat_bot.yview)
scrollbar_chat.grid(row=0, column=1, padx=(0,5), pady=5, sticky="ns")
txt_chat_bot.configure(yscrollcommand=scrollbar_chat.set)
frame_entrada_chat = customtkinter.CTkFrame(tab_chatbot)
frame_entrada_chat.pack(pady=(0,10), padx=10, fill="x")
frame_entrada_chat.grid_columnconfigure(0, weight=1)
txt_chat_usuario = customtkinter.CTkTextbox(frame_entrada_chat, height=80, wrap="word")
txt_chat_usuario.grid(row=0, column=0, padx=(5,0), pady=5, sticky="ew")
btn_enviar_chat = customtkinter.CTkButton(frame_entrada_chat, text="Enviar", command=enviar_mensagem_chat, width=80)
btn_enviar_chat.grid(row=0, column=1, padx=5, pady=5, sticky="e")
def enviar_com_enter(event):
    enviar_mensagem_chat()
    return "break"
txt_chat_usuario.bind("<Return>", enviar_com_enter)
txt_chat_usuario.bind("<KP_Enter>", enviar_com_enter)

# ================== GUI Análise ==================
# Frame principal para a aba de análise
frame_analise = customtkinter.CTkFrame(tab_analise)
frame_analise.pack(pady=10, padx=10, fill="both", expand=True)

# Frame para o botão
frame_botao_analise = customtkinter.CTkFrame(frame_analise)
frame_botao_analise.pack(pady=10, padx=10, fill="x")

btn_gerar_grafico = customtkinter.CTkButton(frame_botao_analise, text="Gerar Gráfico de Pratos Mais Pedidos", command=gerar_grafico_pratos_mais_pedidos)
btn_gerar_grafico.pack(pady=5)

# Frame onde o gráfico será exibido
frame_grafico_analise = customtkinter.CTkFrame(frame_analise, fg_color="#2b2b2b") # Frame para o canvas do gráfico
frame_grafico_analise.pack(pady=10, padx=10, fill="both", expand=True)

# ==================== Inicialização ====================
def inicializar_dados():
    try:
        listar_clientes()
        listar_pratos()
        listar_pedidos()
        atualizar_comboboxes_pedido()
    except mysql.connector.Error as err:
        CTkMessagebox(title="Erro Inicial DB", message=f"Não foi possível conectar ao banco ou carregar dados iniciais: {err}\nVerifique se o servidor MySQL está rodando e as credenciais/database estão corretas.", icon="cancel")
    except Exception as e:
         CTkMessagebox(title="Erro Inicial", message=f"Ocorreu um erro inesperado na inicialização: {e}", icon="cancel")

janela.after(100, inicializar_dados)
janela.mainloop()

