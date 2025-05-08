import tkinter as tk
from tkinter import filedialog , messagebox
import json
import os
import random

import threading
from pynput.mouse import Listener
import pyautogui
import time
#from queue import Queue
import pygetwindow as gw
from concurrent.futures import ThreadPoolExecutor
import sys
from datetime import datetime

# GERAR O .EXE
# pyinstaller --noconsole --onefile --icon=img.ico --add-data "img.ico;." --name CLICK-DINAMICO CLICK-DINAMICO.py

def caminho_recurso(relativo):
    """Retorna o caminho absoluto para o recurso, seja em .py ou em .exe"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relativo)
    return os.path.join(os.path.abspath("."), relativo)

 


data_limite = datetime(3025, 5, 15)
data_atual = datetime.now()

if data_atual > data_limite:
    print("Este sistema expirou. Entre em contato com o desenvolvedor.")
    sys.exit()  # Encerra o programa

tempo_movimento = 0.01  # quanto menor, mais rápido
intervalo_entre_cliques = 0.2  # ajustável


window_mapping = {}
NOME_DO_ARQUIVO = ''
CAMINHO_DO_ARQUIVO = ''
is_paused = False
sensors = []

thread_listener = None 

#click_queue = Queue()

executor = ThreadPoolExecutor(max_workers=5)

FREIO_DE_MAO = False
stop_threads = False

## falta apenas 1 coisa. as vezes se voce coloca masi de 1 sensor, o click acontece fora de ordem.. ( clica 2x no mesmo lugar)
## DESCONSIDERAR O CLIC QUANDO CLICA NO COMPOENTE
##
##




def ativar_janela(sensor_id):
    try:
        window_title = sensor_id.split('_')[0]  # Pega parte do título da janela
        windows = gw.getWindowsWithTitle(window_title)
        if windows:
            windows[0].activate()  # Ativa a janela correta
           # print("SLEEP B")

            time.sleep(0.1)  # Pequeno delay para garantir que a ativação ocorreu
    except Exception as e:
        print(f"Erro ao ativar janela: {e}")




def realizar_click_slave(tag, tagCompleta):
    acoes = ['_BUY_', '_SELL_', '_DEL_']

    pontos = []

    for window in window_mapping:
        window.window.update_idletasks()
        sensor_id = window.window_tag
        
        if f"TAG{tag}" in sensor_id and "SLAVE" in sensor_id:
            for acao in acoes:
                if acao in sensor_id and acao in tagCompleta:
                    
                    try:
                        x, y = window.window.winfo_x(), window.window.winfo_y()
                        pontos.append((x+30,y+30))
                    except Exception as e:
                        print(f"realizar_click_slave: {e}")


    for x, y in pontos:
        pyautogui.moveTo(x , y , duration=tempo_movimento)
        pyautogui.click(x=x ,y= y , interval= intervalo_entre_cliques )
        print(f"Realizando click em [ {x} {y} ]")
        time.sleep(intervalo_entre_cliques)


def verificar_clique(cx, cy):
    for window in window_mapping:
        try:
            x, y = window.window.winfo_x(), window.window.winfo_y()
            largura, altura = window.window.winfo_width(), window.window.winfo_height()
            sensor_id = window.window_tag

            if x <= cx <= x + largura and y <= cy <= y + altura:
            #  print(f"\n\nClique detectado dentro da janela {sensor_id} em ({cx}, {cy})")
                
                if 'MASTER_' in sensor_id:
                    pos_indexTAG = sensor_id.find('_TAG')
                    if pos_indexTAG != -1:
                        pos_index_underscore = sensor_id.find('_', pos_indexTAG + 4)
                        if pos_index_underscore != -1:
                            tag = sensor_id[pos_indexTAG + 4:pos_index_underscore]
                            print("\n\n~~~~~ TAG ENCONTRADA  "+sensor_id+" | "+str(datetime.now()))
                            time.sleep(0.5)
                            realizar_click_slave(tag, sensor_id)
        except Exception as e:
            print(f"verificar_clique: {e}")

def on_click(x, y, button, pressed):
    if pressed:
        verificar_clique(x, y)

def start_mouse_listener():
    global thread_listener, stop_threads

    stop_threads = False
    thread_listener = Listener(on_click=on_click)
    thread_listener.start()
    print("\n\n\n   ~~~~~~~~~~ Iniciando listener do mouse.")

   # processing_thread = threading.Thread(target=processar_cliques)
   # processing_thread.daemon = True
   # processing_thread.start()






class CustomWindowClick:
    def __init__(self, colorBack, window_tag, colorBorder, withBorder, x_position, y_position):


        self.window = tk.Toplevel()
        # Remove a barra de título da janela
        self.window.overrideredirect(True)
        # Coloca a janela em primeiro plano
        self.window.attributes('-topmost', True)
        # Define a cor de fundo transparente como verde
        self.window.attributes('-transparentcolor', '#00FF00')

        # Define um atributo personalizado para identificar a janela
        self.window_tag = window_tag

        # Variável para rastrear a cor atual da janela
        self.current_color = "#ff1493"  # Cor inicial (rosa)
        
        self.is_dragging_enabled = True  
        self.is_dragging = False  # Inicialmente, o movimento está habilitado
        self.is_paused = False  # Inicialmente, movimento está permitido
        self.can_drag = True  # Variável para controlar se o movimento é permitido

        # Obtenha as dimensões da tela
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        # Calcule as coordenadas para centralizar a janela
        window_width = 60
        window_height = 60
        if x_position is None or y_position is None:
            x_position = (screen_width - window_width) // 2
            y_position = (screen_height - window_height) // 2

        self.window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.border_color = colorBorder 
        self.canvas = tk.Canvas(
            self.window,
            width=window_width,
            height=window_height,
            bg=self.current_color,  # Cor de fundo do quadrado
            highlightbackground=colorBorder,  # Cor da borda
            highlightthickness=withBorder  # Espessura da borda
        )
        self.canvas.pack()

        # Desenha um círculo vermelho com um buraco no meio
        circle_x = 15  # Posição X do círculo
        circle_y = 15  # Posição Y do círculo
        circle_size = 30  # Tamanho do círculo (altura e largura iguais)
        self.inner_circle = self.canvas.create_oval(
            circle_x, circle_y, circle_x + circle_size, circle_y + circle_size, fill="#00FF00", outline="black")

        sensors.append(self)

        # Definir eventos de mouse para permitir arrastar a janela
        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_drag_end)

        # Adiciona a nova janela Tkinter à lista de janelas abertas
        window_mapping[self] = self.window
        self.set_window_color(colorBack)

        # Adiciona eventos para esconder e mostrar com hover
        if 'MASTER_' in window_tag:
            self.window.bind("<Enter>", self._esconder_ao_hover)
            #self.window.bind("<Leave>", self._mostrar_ao_sair)


    def _esconder_ao_hover(self, event):
        global is_paused
        if is_paused:
            threading.Thread(target=self._aguardar_e_mostrar, daemon=True).start()

    def _aguardar_e_mostrar(self):
        self.window.withdraw()
        time.sleep(1)
        self.window.deiconify()

    def on_drag_start(self, event):
        global is_dragging, start_x, start_y
        if not self.is_paused:  # Permitir arrastar apenas se não estiver pausado
            is_dragging = True
            start_x, start_y = event.x, event.y

    def on_drag(self, event):
        global mouse_x, mouse_y
        if not self.is_paused:  # Permitir arrastar apenas se não estiver pausado
            self.is_dragging = True
            if is_dragging:
                deltax = event.x - start_x
                deltay = event.y - start_y
                self.window.geometry(f"+{self.window.winfo_x() + deltax}+{self.window.winfo_y() + deltay}")
                mouse_x, mouse_y = event.x, event.y

    def on_drag_end(self, event):
        
        global is_dragging
        is_dragging = False
        sensor_id = self.window_tag
      #  print("sensor_id        "+str(sensor_id))

        pos_indexTAG = sensor_id.find('_TAG')

        if pos_indexTAG != -1:
            # Encontrar o próximo "_" após "_TAG"
            pos_index_underscore = sensor_id.find('_', pos_indexTAG + 4)

            # Extrair o valor entre "_TAG" e o próximo "_"
            tag = sensor_id[pos_indexTAG + 4 : pos_index_underscore]
            entry_nome_sensor.delete(0, tk.END)
            entry_nome_sensor.insert(0, tag)

        def close_window():
            window_mapping.pop(self)
            self.window.destroy()

        self.window.protocol("WM_DELETE_WINDOW", close_window)

    def destroy(self):
        self.window.destroy()  #

    def set_window_color(self, color):
        self.current_color = color
        self.canvas.configure(bg=color)

    def disable_dragging(self):
        """Desabilita a movimentação do sensor"""
        self.is_paused = True  # Bloqueia o movimento ao pausar
        #print(f"Movimento do sensor {self.window_tag} bloqueado.")

    def enable_dragging(self):
        """Habilita a movimentação do sensor"""
        self.is_paused = False  # Libera o movimento
        #print(f"Movimento do sensor {self.window_tag} liberado.")

def create_circle_window(colorBackground, tagSensor,colorBorder,withBorder,x_position,y_position):
    CustomWindowClick(colorBackground, tagSensor,colorBorder,withBorder,x_position,y_position)



def gerar_cor_sortida():
    return f"#{random.randint(0, 0xFFFFFF):06x}"

def procurar_arquivo():
    global NOME_DO_ARQUIVO ,CAMINHO_DO_ARQUIVO
    filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
    if filename:
        entry_nome_arquivo.delete(0, tk.END)
        nome_arquivo = os.path.splitext(os.path.basename(filename))[0]
        NOME_DO_ARQUIVO = nome_arquivo  
        CAMINHO_DO_ARQUIVO = filename
        entry_nome_arquivo.insert(0, NOME_DO_ARQUIVO)

        with open(filename, "r", encoding="utf-8") as f:
            dados = json.load(f)
            for item in dados:
                nomeCompmente = item['nome_componente']
                tipo = ''
                # Verificando o tipo de sensor com base no nome do componente
                if 'BUY' in nomeCompmente:
                    tipo = 'BUY'
                elif 'SELL' in nomeCompmente:
                    tipo = 'SELL'
                else:
                    tipo = 'DEL'
                
                pos_x = item['posicao_x']
                pos_y = item['posicao_y']
                codigoCor = str(item['corQuadrado'])
                nomeSensor = nomeCompmente
                # Definindo a espessura da linha com base no tipo
                espessuraLinha = 5
                if 'MASTER' in nomeCompmente:
                    espessuraLinha = 10

                create_circle_window(
                    "#0066ff" if tipo == "BUY" else "#ff3300" if tipo == "SELL" else "#999999",
                    nomeSensor, 
                    codigoCor, 
                    espessuraLinha, 
                    pos_x, 
                    pos_y
                )

    else:
        NOME_DO_ARQUIVO = None

def salvar_posicao_sensores():
    global CAMINHO_DO_ARQUIVO

    if entry_nome_arquivo.get() == '' or entry_nome_sensor.get() == '' :
        messagebox.showinfo("Aviso", "Selecione( ou crie ) o nome do arquivo e o nome do sensor")
        return


    print("Posição dos sensores salva!")

    sensores = []
    for window in window_mapping:
        # Verifique se a janela ainda existe
        if hasattr(window, 'window') and window.window.winfo_exists():
            window.window.update_idletasks()
            sensor_id = window.window_tag
            x = window.window.winfo_x()
            y = window.window.winfo_y()
            cor_atual = window.border_color

            # Criar um dicionário com as informações do sensor
            sensor_info = {
                "nome_componente": sensor_id,
                "posicao_x": x,
                "posicao_y": y,
                "corQuadrado": cor_atual
            }
            sensores.append(sensor_info)

    nomeArquivoStr = entry_nome_arquivo.get() + ".json"

    # Verifica se o arquivo já existe
    if os.path.exists(nomeArquivoStr):
        try:
            with open(nomeArquivoStr, "r", encoding="utf-8") as arquivo:
                dados_existentes = json.load(arquivo)

            # Atualiza os dados existentes
            sensores_dict = {s["nome_componente"]: s for s in dados_existentes}

            for sensor in sensores:
                sensores_dict[sensor["nome_componente"]] = sensor  # Atualiza ou adiciona novo sensor

            sensores = list(sensores_dict.values())  # Converte novamente para lista

        except json.JSONDecodeError:
            print("Erro ao carregar JSON existente. Criando um novo.")

    # Salva os dados atualizados no arquivo
    with open(nomeArquivoStr, "w", encoding="utf-8") as arquivo:
        json.dump(sensores, arquivo, indent=4)

    CAMINHO_DO_ARQUIVO = os.path.abspath(nomeArquivoStr)

    print(f"Dados dos sensores salvos em {nomeArquivoStr}")

def extrair_maior_numero(dados,tagName):
    numMaior = 0  # Inicializa o maior número encontrado

    for item in dados:
        nomeComponete = item['nome_componente']
        
        # Verifica se a tag especificada está no nome do componente
        if tagName in nomeComponete:
            pos_indexPOS = nomeComponete.rfind('_POS')
            
            if pos_indexPOS != -1: 
                # Extrai a parte após '_POS' e tenta converter em número
                try:
                    parte_pos = int(nomeComponete[pos_indexPOS + 4:])
                    if parte_pos > numMaior:
                        numMaior = parte_pos  # Atualiza o maior número encontrado
                except ValueError:
                    print(f"Erro: Não foi possível converter '{nomeComponete[pos_indexPOS + 4:]}' para número.")
    
    return numMaior  # Retorna o maior número encontrado

def extrair_cod_cor(tagFind):
    codCor = None
    for window in window_mapping:
        window.window.update_idletasks() 
        sensor_id = window.window_tag
      #  print(sensor_id)
     #   print(tagFind)
        if "_TAG"+tagFind+"_" in sensor_id :
            codCor = window.border_color
            break
    return codCor

def extrair_tag(dados, tagParaProcurar):
    for item in dados:
        nome_componente = item['nome_componente']
        
        # Verifica se a tag está presente no nome_componente
        if tagParaProcurar in nome_componente:
            # Encontrar a posição de "_TAG"
            pos_indexTAG = nome_componente.find('_TAG')

            if pos_indexTAG != -1:
                # Encontrar o próximo "_" após "_TAG"
                pos_index_underscore = nome_componente.find('_', pos_indexTAG + 4)

                if pos_index_underscore != -1:
                    # Extrair o valor entre "_TAG" e o próximo "_"
                    tag = nome_componente[pos_indexTAG + 4 : pos_index_underscore]
                    print(f"Tag extraída: {tag}")
                    return tag
    return None  # Se não encontrar a tag no nome_componente

def add_um_novo_sensor():
    global NOME_DO_ARQUIVO

    if entry_nome_arquivo.get() == '' or entry_nome_sensor.get() == '' :
        messagebox.showinfo("Aviso", "Selecione( ou crie ) o nome do arquivo e o nome do sensor")
        return

    codigoCor = gerar_cor_sortida()
    pos_x, pos_y = 200 + 1 * 10, 200 + 1 * 10
    tipo = 'BUY'
    nomeSensor = "MASTER_TAG"+entry_nome_sensor.get()+"_"+tipo+"_POS"+str("0") 
    create_circle_window("#0066ff" if tipo == "BUY" else "#ff3300" if tipo == "SELL" else "#999999",
                            nomeSensor, codigoCor, 10, pos_x, pos_y)

    pos_x, pos_y = 200 + 2 * 10, 200 + 2 * 10
    tipo = 'SELL'
    nomeSensor = "MASTER_TAG"+entry_nome_sensor.get()+"_"+tipo+"_POS"+str("0")
    create_circle_window("#0066ff" if tipo == "BUY" else "#ff3300" if tipo == "SELL" else "#999999",
                            nomeSensor, codigoCor, 10, pos_x, pos_y)

    pos_x, pos_y = 200 + 3 * 10, 200 + 3 * 10
    tipo = 'DEL'
    nomeSensor = "MASTER_TAG"+entry_nome_sensor.get()+"_"+tipo+"_POS"+str("0")
    create_circle_window("#0066ff" if tipo == "BUY" else "#ff3300" if tipo == "SELL" else "#999999",
                            nomeSensor, codigoCor, 10, pos_x, pos_y)








    pos_x, pos_y = 200 + 4 * 10, 200 + 4 * 10
    tipo = 'BUY'
    nomeSensor = "SLAVE_TAG"+entry_nome_sensor.get()+"_"+tipo+"_POS"+str("1") 
    create_circle_window("#0066ff" if tipo == "BUY" else "#ff3300" if tipo == "SELL" else "#999999",
                            nomeSensor, codigoCor, 5, pos_x, pos_y)

    pos_x, pos_y = 200 + 5 * 10, 200 + 5 * 10
    tipo = 'SELL'
    nomeSensor = "SLAVE_TAG"+entry_nome_sensor.get()+"_"+tipo+"_POS"+str("1")
    create_circle_window("#0066ff" if tipo == "BUY" else "#ff3300" if tipo == "SELL" else "#999999",
                            nomeSensor, codigoCor, 5, pos_x, pos_y)

    pos_x, pos_y = 200 + 6 * 10, 200 + 6 * 10
    tipo = 'DEL'
    nomeSensor = "SLAVE_TAG"+entry_nome_sensor.get()+"_"+tipo+"_POS"+str("1")
    create_circle_window("#0066ff" if tipo == "BUY" else "#ff3300" if tipo == "SELL" else "#999999",
                            nomeSensor, codigoCor, 5, pos_x, pos_y)




    sensores = []
    for window in window_mapping:
        window.window.update_idletasks() 
        sensor_id = window.window_tag
        x = window.window.winfo_x()
        y = window.window.winfo_y()
        cor_atual = window.border_color

        sensor_info = {
            "nome_componente": sensor_id,
            "posicao_x": x,
            "posicao_y": y,
            "corQuadrado": cor_atual
        }

        sensores.append(sensor_info)


    nomeArquivo = entry_nome_arquivo.get()
    with open(str(nomeArquivo)+".json", "w", encoding="utf-8") as arquivo:
        json.dump(sensores, arquivo, indent=4)
    NOME_DO_ARQUIVO = nomeArquivo


def conferir_cor_no_arquivo_salvo(codigoCor,tag):
    global CAMINHO_DO_ARQUIVO

    requestCor = codigoCor
    with open(CAMINHO_DO_ARQUIVO, "r", encoding="utf-8") as f:
        dados = json.load(f)

        for item in dados:
            if "_TAG"+tag+"_" in item['nome_componente']:
                if item['corQuadrado'] == codigoCor:
                    requestCor = codigoCor
                    break
                else:
                    requestCor = item['corQuadrado']
                    break

    return requestCor
def adicionar_sensor():
    global NOME_DO_ARQUIVO

    if entry_nome_arquivo.get() == '' or entry_nome_sensor.get() == '' :
        messagebox.showinfo("Aviso", "Selecione( ou crie ) o nome do arquivo e o nome do sensor")
        return

    #salvar_posicao_sensores()

    if NOME_DO_ARQUIVO:
        arquivos = os.listdir()  # Lista os arquivos no diretório atual
        arquivos_json = [arquivo for arquivo in arquivos if arquivo.endswith(".json")]
        
        salvar_posicao_sensores()

        for arquivo in arquivos_json:
            if NOME_DO_ARQUIVO in arquivo:

                try:
                    with open(CAMINHO_DO_ARQUIVO, "r", encoding="utf-8") as f:
                        dados = json.load(f)
                        tagNomeSensor = entry_nome_sensor.get()
                        tag = extrair_tag(dados,tagNomeSensor)

                        if tag:
                            numMaior = extrair_maior_numero(dados,tag)
                                     
                            codigoCor = extrair_cod_cor(tag)
                            codCorConferido = conferir_cor_no_arquivo_salvo(codigoCor,tag)
                            if codigoCor != codCorConferido:
                                codigoCor = codCorConferido
                            #confere no arquivo json

                            pos_x, pos_y = 200 + 4 * 10, 200 + 4 * 10
                            tipo = 'BUY'
                            nomeSensor = "SLAVE_TAG"+tag+"_"+tipo+"_POS"+str(numMaior+1) 
                            create_circle_window("#0066ff" if tipo == "BUY" else "#ff3300" if tipo == "SELL" else "#999999",
                                                    nomeSensor, codigoCor, 5, pos_x, pos_y)

                            pos_x, pos_y = 200 + 5 * 10, 200 + 5 * 10
                            tipo = 'SELL'
                            nomeSensor = "SLAVE_TAG"+tag+"_"+tipo+"_POS"+str(numMaior+1)
                            create_circle_window("#0066ff" if tipo == "BUY" else "#ff3300" if tipo == "SELL" else "#999999",
                                                    nomeSensor, codigoCor, 5, pos_x, pos_y)

                            pos_x, pos_y = 200 + 6 * 10, 200 + 6 * 10
                            tipo = 'DEL'
                            nomeSensor = "SLAVE_TAG"+tag+"_"+tipo+"_POS"+str(numMaior+1)
                            create_circle_window("#0066ff" if tipo == "BUY" else "#ff3300" if tipo == "SELL" else "#999999",
                                                    nomeSensor, codigoCor, 5, pos_x, pos_y)
                            

                            salvar_posicao_sensores()
                            break

                        else:
                            add_um_novo_sensor()
                            salvar_posicao_sensores()

                except Exception as e:
                    salvar_posicao_sensores()
                    print(f"1 Erro ao abrir o arquivo: {e}")

    else:
        add_um_novo_sensor()
        salvar_posicao_sensores()


def remover_sensor():
    global NOME_DO_ARQUIVO
    if entry_nome_arquivo.get() == '' or entry_nome_sensor.get() == '' :
        messagebox.showinfo("Aviso", "Selecione( ou crie ) o nome do arquivo e o nome do sensor")
        return

    #salvar_posicao_sensores()
    if NOME_DO_ARQUIVO:
        arquivos = os.listdir()  # Lista os arquivos no diretório atual
        arquivos_json = [arquivo for arquivo in arquivos if arquivo.endswith(".json")]
    #    print("arquivos "+str(arquivos))
   #     print("teste "+str(CAMINHO_DO_ARQUIVO))
        for arquivo in arquivos_json:
            if NOME_DO_ARQUIVO in arquivo:
                try:
                    with open(CAMINHO_DO_ARQUIVO, "r", encoding="utf-8") as f:
                        dados = json.load(f)
                        tagNomeSensor = entry_nome_sensor.get()
                        tag = extrair_tag(dados,tagNomeSensor)

                        if tag:
                            numMaior = extrair_maior_numero(dados,tag)

                        # Lista de tags a serem removidas
                        tags_para_remover = [
                            f"SLAVE_TAG{tag}_BUY_POS{numMaior}",
                            f"SLAVE_TAG{tag}_SELL_POS{numMaior}",
                            f"SLAVE_TAG{tag}_DEL_POS{numMaior}",
                        ]

                        # Filtrar os sensores, removendo os que têm as tags especificadas
                        dados_atualizados = [
                            sensor for sensor in dados if sensor["nome_componente"] in tags_para_remover
                        ]

                        if len(dados_atualizados) == 0:
                            tags_para_remover = [
                                f"MASTER_TAG{tag}_BUY_POS0",
                                f"MASTER_TAG{tag}_SELL_POS0",
                                f"MASTER_TAG{tag}_DEL_POS0",
                            ]
                            dados_atualizados = [
                                sensor for sensor in dados if sensor["nome_componente"] in tags_para_remover
                            ]

                        dados_atualizados2 = [
                            sensor for sensor in dados if sensor["nome_componente"] not in tags_para_remover
                        ]
                        # Reescrevendo o arquivo JSON com os dados atualizados
                        with open(arquivo, "w", encoding="utf-8") as f:
                            json.dump(dados_atualizados2, f, indent=4)


                        print(dados_atualizados)
                        print(f"Sensores removidos e {arquivo} atualizado.")

                        for window in window_mapping:
                            for item in dados_atualizados:
                                sensor_id = window.window_tag
                                if sensor_id in item['nome_componente']:
                              #      print("sensor_id  >  "+str(sensor_id))
                                    window.destroy()
                                    window.window.update_idletasks() 

                except Exception as e:
                    print(f"2 Erro ao abrir o arquivo: {e}")


# Criando a janela principal
root = tk.Tk()
root.title("Gerenciador de Sensores")
root.geometry("400x300")
root.iconbitmap(caminho_recurso("img.ico"))


# Linha 1
frame1 = tk.Frame(root)
frame1.pack(fill=tk.X, padx=10, pady=5)
tk.Label(frame1, text="Carregar Sensores:").pack(side=tk.LEFT)
btn_procurar = tk.Button(frame1, text="Procurar", command=procurar_arquivo)
btn_procurar.pack(side=tk.RIGHT)

# Linha 2
frame2 = tk.Frame(root)
frame2.pack(fill=tk.X, padx=10, pady=5)
tk.Label(frame2, text="Nome Arquivo:").pack(side=tk.LEFT)
entry_nome_arquivo = tk.Entry(frame2, width=40)
entry_nome_arquivo.pack(side=tk.RIGHT)

# Linha 3
frame3 = tk.Frame(root)
frame3.pack(fill=tk.X, padx=10, pady=5)
btn_salvar_posicao  = tk.Button(frame3, text="Salvar Posição Sensores", command=salvar_posicao_sensores)
btn_salvar_posicao.pack()

# Linha 4 - Linha horizontal
frame4 = tk.Frame(root, height=2, bd=1, relief=tk.SUNKEN)
frame4.pack(fill=tk.X, padx=10, pady=5)

# Linha 5
frame5 = tk.Frame(root)
frame5.pack(fill=tk.X, padx=10, pady=5)
tk.Label(frame5, text="Nome Sensor:").pack(side=tk.LEFT)
entry_nome_sensor = tk.Entry(frame5, width=40)
entry_nome_sensor.pack(side=tk.RIGHT)


# Linha 6
frame6 = tk.Frame(root)
frame6.pack(fill=tk.X, padx=10, pady=5)
btn_add_sensor =tk.Button(frame6, text="Adicionar Sensor", command=adicionar_sensor)
btn_add_sensor.pack()


# Linha 7
frame7 = tk.Frame(root)
frame7.pack(fill=tk.X, padx=10, pady=5)
btn_remove_sensor = tk.Button(frame7, text="Remover Sensor", command=remover_sensor)
btn_remove_sensor.pack()



def toggle_pause():
    global is_paused, thread_listener, FREIO_DE_MAO, stop_threads
    is_paused = not is_paused

    if is_paused:
        toggle_button.config(text="Pausar")
        FREIO_DE_MAO = False



        start_mouse_listener()
        for sensor in sensors:
            sensor.disable_dragging()
        ##
        btn_salvar_posicao.config(state="disabled")
        btn_procurar.config(state="disabled")
        btn_add_sensor.config(state="disabled")
        btn_remove_sensor.config(state="disabled")
        ##
        print("Sensores bloqueados.")
    else:
        toggle_button.config(text="Executar")
        FREIO_DE_MAO = True

        ##
        btn_salvar_posicao.config(state="normal")
        btn_procurar.config(state="normal")
        btn_add_sensor.config(state="normal")
        btn_remove_sensor.config(state="normal")
        ##

        # Para o listener do mouse
        if thread_listener:
            thread_listener.stop()
            thread_listener = None

        # Finaliza o processamento de cliques
        stop_threads = True
        #click_queue.put((None, None, None))  # força sair da fila

        for sensor in sensors:
            sensor.enable_dragging()
        print("Sensores liberados.")



# Linha 8
frame8 = tk.Frame(root)
frame8.pack(fill=tk.X, padx=10, pady=5)
toggle_button = tk.Button(frame8, text="Executar", command=toggle_pause)
toggle_button.pack()  # Apenas empacota após criar o botão




# Rodando a interface
tk.mainloop()


