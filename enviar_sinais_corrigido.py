import random
from datetime import datetime, timedelta
import requests
import os
import json
import time
import logging

# === CONFIGURAÇÕES ===
BOT_TOKEN = "6511111939:AAE92-VGCX03v8JA4EaG8654By8e6W2TSpQ"

# === Arquivo para armazenar dados de TODOS os chats ===
CHAT_DATA_FILE = "chat_data.json"

# === Arquivo para armazenar a lista de jogos configurados ===
JOGOS_CONFIG_FILE = "jogos_config.json"

# === Dicionário global para armazenar todos os dados dos chats ===
CHAT_DATA = {}

# === Variável global para armazenar a lista de jogos (será carregada do arquivo) ===
JOGOS_CONFIG = [] 

# === Lista global para gerenciar mensagens a serem deletadas (confirmações do bot) ===
MESSAGES_TO_DELETE = []

# === Lista de jogos com emoji e nome ===
JOGOS_CONFIG = [
    {"emoji": "🐯", "nome": "Fortune Tiger"},
    {"emoji": "🐮", "nome": "Fortune Ox"},
    {"emoji": "🐲", "nome": "Fortune Dragon"},
    {"emoji": "🐰", "nome": "Fortune Rabbit"}
]

# === CONFIGURAÇÃO DE LOGGING ===
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# === FUNÇÕES DE UTILITÁRIO ===

def aleatorio(min_val, max_val):
    """Gera um número inteiro aleatório dentro de um intervalo."""
    return random.randint(min_val, max_val)

def bolinha(p):
    """Retorna um emoji de bolinha com base na porcentagem de probabilidade."""
    if p >= 91:
        return "🟢"
    elif p >= 86:
        return "🟡"
    return "🔴"

def estrategia_valida(p):
    """
    Gera a string da estratégia com base na probabilidade 'p'.
    Retorna "Não jogar!" se p for muito baixo.
    """
    if p < 86:
        return "NÃO JOGAR!!!"

    t, n = 0, 0
    while not (5 <= t + n <= 10):
        t = aleatorio(1, 10)
        n = aleatorio(1, 10)
    
    return f"{t}x 🚀 Turbo + {n}x 🎯 Normal"

def minutos_unicos(qtd):
    """Gera uma lista de 'qtd' minutos únicos aleatórios dentro de 0-59."""
    set_minutos = set()
    while len(set_minutos) < qtd:
        set_minutos.add(aleatorio(0, 59))
    return sorted(list(set_minutos))

# === FUNÇÕES DE DADOS (CHAT_DATA e JOGOS_CONFIG) ===
def ler_chat_data():
    """Lê o dicionário de dados de todos os chats do arquivo JSON."""
    global CHAT_DATA
    if os.path.exists(CHAT_DATA_FILE):
        try:
            with open(CHAT_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    logging.warning(f"Conteúdo de '{CHAT_DATA_FILE}' não é um dicionário. Reinicializando CHAT_DATA.")
                    CHAT_DATA = {}
                else:
                    CHAT_DATA = data
                logging.info(f"Dados de chats carregados de '{CHAT_DATA_FILE}'. Total de chats: {len(CHAT_DATA)}")
        except json.JSONDecodeError:
            logging.error(f"Erro ao decodificar JSON de '{CHAT_DATA_FILE}'. Arquivo corrompido. Reinicializando CHAT_DATA.")
            CHAT_DATA = {}
        except Exception as e:
            logging.error(f"Erro inesperado ao ler '{CHAT_DATA_FILE}': {e}. Reinicializando CHAT_DATA.")
            CHAT_DATA = {}
    else:
        logging.info(f"Arquivo '{CHAT_DATA_FILE}' não encontrado. CHAT_DATA inicializado como vazio.")
        CHAT_DATA = {}

def salvar_chat_data():
    """Salva o dicionário de dados de todos os chats no arquivo JSON."""
    try:
        with open(CHAT_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(CHAT_DATA, f, indent=4, ensure_ascii=False)
        logging.info(f"Dados de chats salvos com sucesso em '{CHAT_DATA_FILE}'.")
    except Exception as e:
        logging.error(f"Erro ao salvar dados de chats em '{CHAT_DATA_FILE}': {e}")

def ler_jogos_config():
    """Lê a lista de jogos do arquivo JSON."""
    global JOGOS_CONFIG
    if os.path.exists(JOGOS_CONFIG_FILE):
        try:
            with open(JOGOS_CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    logging.warning(f"Conteúdo de '{JOGOS_CONFIG_FILE}' não é uma lista. Reinicializando JOGOS_CONFIG.")
                    JOGOS_CONFIG = []
                else:
                    JOGOS_CONFIG = data
                logging.info(f"Jogos configurados carregados de '{JOGOS_CONFIG_FILE}'. Total de jogos: {len(JOGOS_CONFIG)}")
        except json.JSONDecodeError:
            logging.error(f"Erro ao decodificar JSON de '{JOGOS_CONFIG_FILE}'. Arquivo corrompido. Reinicializando JOGOS_CONFIG.")
            JOGOS_CONFIG = []
        except Exception as e:
            logging.error(f"Erro inesperado ao ler '{JOGOS_CONFIG_FILE}': {e}. Reinicializando JOGOS_CONFIG.")
            JOGOS_CONFIG = []
    else:
        logging.info(f"Arquivo '{JOGOS_CONFIG_FILE}' não encontrado. JOGOS_CONFIG inicializado como vazio.")
        JOGOS_CONFIG = []

def salvar_jogos_config():
    """Salva a lista de jogos no arquivo JSON."""
    try:
        with open(JOGOS_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(JOGOS_CONFIG, f, indent=4, ensure_ascii=False)
        logging.info(f"Jogos configurados salvos com sucesso em '{JOGOS_CONFIG_FILE}'.")
    except Exception as e:
        logging.error(f"Erro ao salvar jogos configurados em '{JOGOS_CONFIG_FILE}': {e}")


# === FUNÇÕES DE MENSAGEM E EXCLUSÃO ===
def enviar_mensagem(chat_id_destino, mensagem, delete_after_seconds=0):
    """
    Envia uma mensagem para o chat do Telegram especificado.
    Se delete_after_seconds > 0, agenda a mensagem para exclusão.
    Retorna o message_id da mensagem enviada, ou None em caso de falha.
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id_destino,
        "text": mensagem,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, data=payload, timeout=5)
        response.raise_for_status()
        json_response = response.json()
        if json_response.get("ok"):
            message_id = json_response["result"]["message_id"]
            logging.info(f"Mensagem enviada com sucesso para {chat_id_destino}. ID: {message_id}")
            
            if delete_after_seconds > 0:
                deletion_time = datetime.now() + timedelta(seconds=delete_after_seconds)
                MESSAGES_TO_DELETE.append((message_id, chat_id_destino, deletion_time))
                logging.debug(f"Mensagem {message_id} agendada para exclusão em {delete_after_seconds} segundos.")
            return message_id
        else:
            logging.warning(f"Telegram API respondeu com 'ok: false' ao enviar mensagem para {chat_id_destino}: {json_response.get('description', 'N/A')}")
            return None
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao enviar mensagem para o Telegram ({chat_id_destino}): {e}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Erro ao decodificar JSON na resposta de envio de mensagem para {chat_id_destino}.")
        return None

def delete_specific_message(chat_id_to_delete, message_id_to_delete):
    """
    Deleta uma mensagem específica do Telegram.
    """
    if message_id_to_delete is None:
        logging.debug("Tentativa de deletar mensagem com ID None. Ignorando.")
        return

    delete_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage"
    delete_payload = {
        "chat_id": chat_id_to_delete,
        "message_id": message_id_to_delete
    }
    try:
        response = requests.post(delete_url, data=delete_payload, timeout=5)
        response.raise_for_status()
        json_response = response.json()
        if json_response.get("ok"):
            logging.info(f"Mensagem {message_id_to_delete} (chat {chat_id_to_delete}) deletada com sucesso.")
        else:
            logging.warning(f"Telegram API respondeu com 'ok: false' ao deletar {message_id_to_delete}: {json_response.get('description', 'N/A')}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro na requisição para deletar mensagem {message_id_to_delete}: {e}")
    except json.JSONDecodeError:
        logging.error(f"Erro ao decodificar JSON na resposta de deleção para {message_id_to_delete}.")

def check_and_delete_confirmations():
    """
    Verifica a lista de mensagens agendadas e deleta aquelas cujo tempo expirou.
    """
    global MESSAGES_TO_DELETE
    messages_to_keep = []
    current_time = datetime.now()

    for msg_id, chat_id, deletion_time in MESSAGES_TO_DELETE:
        if current_time >= deletion_time:
            logging.debug(f"Deletando mensagem agendada: ID {msg_id}, Chat {chat_id}")
            delete_specific_message(chat_id, msg_id)
        else:
            messages_to_keep.append((msg_id, chat_id, deletion_time))
    
    MESSAGES_TO_DELETE = messages_to_keep


# === FUNÇÃO DE GERAÇÃO E ENVIO DE SINAL ===
def gerar_e_enviar_sinal_para_chat(chat_id_alvo):
    """
    Gera e envia uma mensagem de sinal formatada para um chat específico,
    seguindo as regras de porcentagem e o limite de jogos.
    """
    chat_data = CHAT_DATA.get(chat_id_alvo)
    if not chat_data:
        logging.error(f"Tentativa de gerar sinal para chat {chat_id_alvo} sem dados. Pulando.")
        return

    casas_disponiveis = chat_data["casas"]
    
    if not casas_disponiveis:
        logging.warning(f"Chat {chat_id_alvo}: Não há casas configuradas para enviar um sinal. Use /addcasa.")
        enviar_mensagem(chat_id_alvo, "❗ Não consigo gerar sinais agora. Nenhuma casa de apostas configurada para este canal. Use `/addcasa` para adicionar.", delete_after_seconds=10)
        return
    
    if not JOGOS_CONFIG: # Verifica se há jogos configurados globalmente
        logging.warning(f"Chat {chat_id_alvo}: Não há jogos configurados para gerar um sinal. Use /addjogo.")
        enviar_mensagem(chat_id_alvo, "❗ Não consigo gerar sinais agora. Nenhum jogo configurado. Use `/addjogo` para adicionar.", delete_after_seconds=10)
        return

    last_signal_msg_id = chat_data["last_sent_signal_message_id"]
    if last_signal_msg_id is not None:
        logging.info(f"Chat {chat_id_alvo}: Apagando sinal anterior (ID: {last_signal_msg_id}).")
        delete_specific_message(chat_id_alvo, last_signal_msg_id)
        chat_data["last_sent_signal_message_id"] = None

    now = datetime.now()
    hora = f"{now.hour:02d}"
    dia = f"{now.day:02d}"
    mes = f"{now.month:02d}"
    ano = now.year

    msg = f"*Sinais do dia {dia}/{mes}/{ano} das {hora}:00.*\n\n"

    # Determina quantos blocos de jogo enviar, respeitando o limite do admin e o número de casas/jogos disponíveis
    actual_max_blocks_by_content = min(len(casas_disponiveis), len(JOGOS_CONFIG))
    
    num_blocks_to_send = 0
    max_games_limit = chat_data.get("max_games_per_signal") 

    if max_games_limit is not None and max_games_limit > 0:
        num_blocks_to_send = min(actual_max_blocks_by_content, max_games_limit)
    elif max_games_limit == 0:
        num_blocks_to_send = 0
    else: # No admin limit, use all available blocks (up to content limits)
        num_blocks_to_send = actual_max_blocks_by_content
    
    if num_blocks_to_send == 0:
        logging.info(f"Chat {chat_id_alvo}: Limite de jogos setado para 0 ou sem casas/jogos/blocos disponíveis. Não enviando blocos de jogo no sinal.")
        return

    # === Lógica aprimorada para seleção de casas (prioriza únicas, depois repete com nova porcentagem) ===
    casas_para_blocos_final = [] # Esta será a lista final de casas com suas porcentagens atribuídas
    
    if casas_disponiveis: # Garante que há casas para sortear
        # Primeiro, pegamos todas as casas únicas disponíveis
        unique_houses_to_consider = list(casas_disponiveis) # Faz uma cópia
        
        num_unique_to_take = min(num_blocks_to_send, len(unique_houses_to_consider))
        
        # Seleciona as primeiras N casas únicas necessárias
        # random.sample() seleciona sem repetição
        selected_unique_houses = random.sample(unique_houses_to_consider, num_unique_to_take)
        
        # Adiciona essas casas com porcentagens aleatórias
        for casa in selected_unique_houses:
            casas_para_blocos_final.append({
                "nome": casa['nome'],
                "link": casa['link'],
                "porcentagem": aleatorio(93, 98) # Porcentagem para a casa principal
            })
        
        # Se ainda faltam blocos para preencher, adiciona casas repetidas
        remaining_slots = num_blocks_to_send - num_unique_to_take
        if remaining_slots > 0:
            # random.choices() permite repetição
            repeated_houses_raw = random.choices(casas_disponiveis, k=remaining_slots)
            for repeated_casa in repeated_houses_raw:
                casas_para_blocos_final.append({
                    "nome": repeated_casa['nome'],
                    "link": repeated_casa['link'],
                    "porcentagem": aleatorio(93, 98) # Nova porcentagem para a casa repetida
                })
        
        # O passo final: Ordenar a lista completa de casas (únicas + repetidas) por porcentagem decrescente
        casas_para_blocos_final.sort(key=lambda x: x['porcentagem'], reverse=True)
    else:
        logging.warning(f"Chat {chat_id_alvo}: Casas disponíveis vazias ao tentar gerar blocos. Nenhum bloco gerado.")
        return


    jogos_embaralhados = list(JOGOS_CONFIG)
    random.shuffle(jogos_embaralhados)

    # Itera pelo número final de blocos a serem enviados
    for i in range(num_blocks_to_send): 
        jogo = jogos_embaralhados[i] 
        casa_associada = casas_para_blocos_final[i] # Pega a i-ésima melhor casa (já ordenada por porcentagem)
        
        topo_bola_casa = bolinha(casa_associada['porcentagem'])
        msg += f"{topo_bola_casa} {casa_associada['porcentagem']}% [{casa_associada['nome']}]({casa_associada['link']})\n\n"
        msg += f"\t\t{jogo['emoji']} {jogo['nome']} {jogo['emoji']}\n"

        signal_points_for_game = []

        all_percentages = []
        for _ in range(3):
            all_percentages.append(aleatorio(93, min(98, casa_associada['porcentagem']))) 
        for _ in range(4):
            all_percentages.append(aleatorio(80, min(98, casa_associada['porcentagem'])))
        
        random.shuffle(all_percentages)

        all_minutes_for_game = sorted(random.sample(range(60), 7))

        for j in range(7):
            minute = all_minutes_for_game[j]
            perc = all_percentages[j]
            bola = bolinha(perc)
            est = estrategia_valida(perc)
            
            signal_points_for_game.append({
                "minute": minute,
                "bola": bola,
                "perc": perc,
                "est": est
            })
        
        signal_points_for_game.sort(key=lambda x: x['minute'])
        logging.debug(f"Pontos de sinal ordenados para {jogo['nome']} (Chat {chat_id_alvo}): {signal_points_for_game}")

        for sp in signal_points_for_game:
            hora_minuto_formatado = f"{hora}:{sp['minute']:02d}"
            msg += f"\t\t🕒 {hora_minuto_formatado} | {sp['bola']} {sp['perc']}%\n Estratégia: {sp['est']}\n"

        msg += "\n"

    logging.info(f"Chat {chat_id_alvo}: Gerando e enviando sinal:\n{msg}") 
    new_signal_id = enviar_mensagem(chat_id_alvo, msg)
    if new_signal_id:
        chat_data["last_sent_signal_message_id"] = new_signal_id
        salvar_chat_data()


# === FUNÇÃO DE TRATAMENTO DE COMANDOS ===
def tratar_comandos():
    """
    Função principal que busca e processa as atualizações do Telegram.
    Lida com comandos e os direciona para o chat correto.
    """
    global ULTIMO_UPDATE_ID, CHAT_DATA, JOGOS_CONFIG

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    if ULTIMO_UPDATE_ID is not None:
        url += f"?offset={ULTIMO_UPDATE_ID + 1}"
    
    logging.debug(f"Buscando atualizações. Último update ID conhecido: {ULTIMO_UPDATE_ID}")

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        updates_data = response.json()

        if not updates_data.get("ok"):
            logging.error(f"Resposta 'not ok' do getUpdates: {updates_data.get('description', 'Desconhecido')}")
            return

        updates = updates_data.get("result", [])
        if not updates:
            logging.debug("Nenhuma nova atualização encontrada.")
            return

        logging.info(f"Encontradas {len(updates)} novas atualizações.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao obter atualizações do Telegram: {e}")
        return

    for update in updates:
        current_update_id = update["update_id"]
        if ULTIMO_UPDATE_ID is None or current_update_id > ULTIMO_UPDATE_ID:
            ULTIMO_UPDATE_ID = current_update_id
        
        logging.debug(f"Processando update_id: {current_update_id}")
        logging.debug(f"Conteúdo completo do update {current_update_id}: {json.dumps(update, indent=2, ensure_ascii=False)}")

        message = update.get("message")
        if not message:
            message = update.get("channel_post")

        if not message:
            logging.debug(f"Update {current_update_id} não contém uma mensagem válida (nem post de canal). Pulando.")
            continue

        chat_id_msg = str(message.get("chat", {}).get("id"))
        from_user = message.get("from", {})
        is_bot = from_user.get("is_bot", False)
        user_id = from_user.get("id")
        
        sender_chat_obj = message.get("sender_chat", {}) 
        sender_chat_id = sender_chat_obj.get("id") if sender_chat_obj else None

        message_id = message.get("message_id")
        text = message.get("text", "").strip()

        if not is_bot and (user_id or sender_chat_id):
            logging.info(f"Comando recebido: '{text}' (ID: {message_id}) de User ID: {user_id if user_id else sender_chat_id} no Chat ID: {chat_id_msg}")

            if text == "/iniciarbot":
                if chat_id_msg in CHAT_DATA:
                    enviar_mensagem(chat_id_msg, "❗ Este canal já está inicializado.", delete_after_seconds=5)
                else:
                    CHAT_DATA[chat_id_msg] = {
                        "casas": [],
                        "last_signal_hour": -1,
                        "last_sent_signal_message_id": None,
                        "max_games_per_signal": None
                    }
                    salvar_chat_data()
                    enviar_mensagem(chat_id_msg, 
                                   "✅ Bot inicializado para este canal! Por favor, use `/addcasa <nome> <link>` para adicionar a primeira casa de aposta.", 
                                   delete_after_seconds=10)
                delete_specific_message(chat_id_msg, message_id)
                continue

            elif text.startswith("/addjogo"):
                text_after_command = text[len("/addjogo"):].strip() 
                
                if not text_after_command:
                    enviar_mensagem(chat_id_msg, "Uso correto: `/addjogo <nome do jogo> <emoji>`", delete_after_seconds=5)
                else:
                    last_space_index = text_after_command.rfind(' ')
                    
                    if last_space_index == -1:
                        enviar_mensagem(chat_id_msg, "Nome do jogo ou emoji não fornecido. Uso: `/addjogo <nome do jogo> <emoji>`", delete_after_seconds=5)
                    else:
                        nome_jogo = text_after_command[:last_space_index].strip()
                        emoji_jogo = text_after_command[last_space_index + 1:].strip()

                        if not nome_jogo or not emoji_jogo:
                            enviar_mensagem(chat_id_msg, "Nome do jogo ou emoji não fornecido. Uso: `/addjogo <nome do jogo> <emoji>`", delete_after_seconds=5)
                        elif not (1 <= len(emoji_jogo) <= 4):
                             enviar_mensagem(chat_id_msg, "Emoji inválido. Por favor, forneça um único emoji (ex: 🐯).", delete_after_seconds=5)
                        elif any(j['nome'].lower() == nome_jogo.lower() for j in JOGOS_CONFIG):
                            enviar_mensagem(chat_id_msg, f"❗ O jogo *{nome_jogo}* já existe na lista de jogos.", delete_after_seconds=5)
                        else:
                            JOGOS_CONFIG.append({"nome": nome_jogo, "emoji": emoji_jogo})
                            salvar_jogos_config()
                            enviar_mensagem(chat_id_msg, f"✅ Jogo *{nome_jogo}* {emoji_jogo} adicionado com sucesso.", delete_after_seconds=2)
                delete_specific_message(chat_id_msg, message_id)
                continue

            elif text.startswith("/removerjogo"):
                parts = text.split(" ", 1)
                if len(parts) >= 2:
                    nome_jogo_remover = parts[1].strip()
                    original_jogos_count = len(JOGOS_CONFIG)
                    jogos_filtrados = [j for j in JOGOS_CONFIG if j['nome'].lower() != nome_jogo_remover.lower()]

                    if len(jogos_filtrados) < original_jogos_count:
                        JOGOS_CONFIG[:] = jogos_filtrados
                        salvar_jogos_config()
                        enviar_mensagem(chat_id_msg, f"❌ Jogo *{nome_jogo_remover}* removido com sucesso.", delete_after_seconds=2)
                    else:
                        enviar_mensagem(chat_id_msg, f"❗ O jogo *{nome_jogo_remover}* não foi encontrado na lista de jogos.", delete_after_seconds=5)
                else:
                    enviar_mensagem(chat_id_msg, "Uso correto: `/removerjogo <nome do jogo>`", delete_after_seconds=5)
                delete_specific_message(chat_id_msg, message_id)
                continue

            elif text.startswith("/listajogos"):
                if not JOGOS_CONFIG:
                    enviar_mensagem(chat_id_msg, "Nenhum jogo configurado. Use `/addjogo` para adicionar.", delete_after_seconds=10)
                else:
                    message_text = "*Jogos configurados:*\n\n"
                    for i, jogo_item in enumerate(JOGOS_CONFIG):
                        message_text += f"*{i+1}. {jogo_item['nome']} {jogo_item['emoji']}*\n"
                    enviar_mensagem(chat_id_msg, message_text, delete_after_seconds=20)
                delete_specific_message(chat_id_msg, message_id)
                continue

            elif text.startswith("/limitarjogos"):
                parts = text.split(" ", 1)
                if len(parts) >= 2:
                    try:
                        limit_str = parts[1].strip()
                        if limit_str.lower() == "0" or limit_str.lower() == "ilimitado" or limit_str.lower() == "remover":
                            CHAT_DATA[chat_id_msg]["max_games_per_signal"] = None
                            salvar_chat_data()
                            enviar_mensagem(chat_id_msg, "✅ Limite de jogos por sinal removido. O bot enviará o máximo de jogos possível.", delete_after_seconds=5)
                        else:
                            limit_num = int(limit_str)
                            if limit_num > 0:
                                CHAT_DATA[chat_id_msg]["max_games_per_signal"] = limit_num
                                salvar_chat_data()
                                enviar_mensagem(chat_id_msg, f"✅ Limite de jogos por sinal definido para *{limit_num}*.", delete_after_seconds=5)
                            else:
                                enviar_mensagem(chat_id_msg, "❗ O limite deve ser um número positivo ou 0 para remover. Uso: `/limitarjogos <número>` ou `/limitarjogos 0`.", delete_after_seconds=7)
                    except ValueError:
                        enviar_mensagem(chat_id_msg, "❗ Limite inválido. Por favor, forneça um número ou '0' para remover. Uso: `/limitarjogos <número>` ou `/limitarjogos 0`.", delete_after_seconds=7)
                else:
                    enviar_mensagem(chat_id_msg, "Uso correto: `/limitarjogos <número>` ou `/limitarjogos 0` para remover o limite.", delete_after_seconds=7)
                delete_specific_message(chat_id_msg, message_id)
                continue

            if chat_id_msg not in CHAT_DATA:
                logging.warning(f"Comando em chat não inicializado ({chat_id_msg}): '{text}'. Ignorando e sugerindo /iniciarbot.")
                enviar_mensagem(chat_id_msg, "❗ Este canal não está inicializado. Por favor, digite `/iniciarbot` para começar.", delete_after_seconds=10)
                delete_specific_message(chat_id_msg, message_id)
                continue

            current_chat_casas = CHAT_DATA[chat_id_msg]["casas"]

            if text.startswith("/addcasa"):
                parts = text.split(" ", 2)
                if len(parts) >= 3:
                    nome = parts[1].strip()
                    link = parts[2].strip()
                    if not nome or not link:
                        enviar_mensagem(chat_id_msg, "Por favor, forneça um nome e um link válidos. Ex: `/addcasa MinhaCasa https://link.com`", delete_after_seconds=5)
                    elif any(c['nome'].lower() == nome.lower() for c in current_chat_casas):
                        enviar_mensagem(chat_id_msg, f"❗ A casa *{nome}* já existe na lista deste canal.", delete_after_seconds=5)
                    else:
                        current_chat_casas.append({"nome": nome, "link": link})
                        CHAT_DATA[chat_id_msg]["casas"] = current_chat_casas
                        salvar_chat_data()
                        enviar_mensagem(chat_id_msg, f"✅ Casa *{nome}* adicionada com sucesso a este canal.", delete_after_seconds=2)
                else:
                    enviar_mensagem(chat_id_msg, "Uso correto: `/addcasa <nome da casa> <link da casa>`", delete_after_seconds=5)

            elif text.startswith("/removercasa"):
                parts = text.split(" ", 1)
                if len(parts) >= 2:
                    nome_para_remover = parts[1].strip()
                    if not nome_para_remover:
                        enviar_mensagem(chat_id_msg, "Por favor, forneça o nome da casa a ser removida. Ex: `/removercasa MinhaCasa`", delete_after_seconds=5)
                    else:
                        original_casas_count = len(current_chat_casas)
                        casas_filtradas = [c for c in current_chat_casas if c['nome'].lower() != nome_para_remover.lower()]

                        if len(casas_filtradas) < original_casas_count:
                            CHAT_DATA[chat_id_msg]["casas"] = casas_filtradas
                            salvar_chat_data()
                            enviar_mensagem(chat_id_msg, f"❌ Casa *{nome_para_remover}* removida com sucesso deste canal.", delete_after_seconds=2)
                        else:
                            enviar_mensagem(chat_id_msg, f"❗ A casa *{nome_para_remover}* não foi encontrada na lista deste canal.", delete_after_seconds=5)
                else:
                    enviar_mensagem(chat_id_msg, "Uso correto: `/removercasa <nome da casa>`", delete_after_seconds=5)
            
            elif text.startswith("/listarcasas"):
                if not current_chat_casas:
                    enviar_mensagem(chat_id_msg, "Nenhuma casa de apostas configurada para este canal. Use `/addcasa` para adicionar.", delete_after_seconds=10) 
                else:
                    message_text = f"*Casas de apostas configuradas para este canal:*\n\n" + "".join([f"*{i+1}. {casa['nome']}*\nLink: {casa['link']}\n\n" for i, casa in enumerate(current_chat_casas)])
                    enviar_mensagem(chat_id_msg, message_text)
            
            elif text == "/sinalagora":
                if not JOGOS_CONFIG:
                    enviar_mensagem(chat_id_msg, "❗ Não posso enviar sinais. Nenhum jogo configurado globalmente. Use `/addjogo` para adicionar jogos.", delete_after_seconds=10)
                else:
                    logging.info(f"Comando /sinalagora recebido no chat {chat_id_msg}. Enviando sinal de teste.")
                    gerar_e_enviar_sinal_para_chat(chat_id_msg)

            else:
                logging.info(f"Mensagem não é um comando reconhecido no chat {chat_id_msg}: '{text}'")
                enviar_mensagem(chat_id_msg, f"❓ Comando '{text.split(' ')[0]}' não reconhecido. Use /addcasa, /removercasa, /listarcasas, /sinalagora, /addjogo, /removerjogo, /listajogos, /limitarjogos ou /iniciarbot.", delete_after_seconds=5)
                
            delete_specific_message(chat_id_msg, message_id)

        else:
            logging.debug(f"Mensagem ignorada. (chat_id_msg: {chat_id_msg}, is_bot: {is_bot}, user_id: {user_id}, sender_chat_id: {sender_chat_id})")


# === INICIALIZAÇÃO DO BOT ===
def initialize_bot_state():
    global ULTIMO_UPDATE_ID, CHAT_DATA, JOGOS_CONFIG
    
    ler_chat_data()
    ler_jogos_config()

    if not JOGOS_CONFIG:
        logging.info("Nenhum jogo configurado no arquivo. Adicionando jogos padrão.")
        JOGOS_CONFIG.extend([
            {"emoji": "🐯", "nome": "Fortune Tiger"},
            {"emoji": "🐮", "nome": "Fortune Ox"},
            {"emoji": "🐲", "nome": "Fortune Dragon"},
            {"emoji": "🐰", "nome": "Fortune Rabbit"}
        ])
        salvar_jogos_config()

    try:
        response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?limit=1&offset=-1", timeout=5)
        response.raise_for_status()
        updates_data = response.json()
        if updates_data.get("ok") and updates_data["result"]:
            ULTIMO_UPDATE_ID = updates_data["result"][0]["update_id"]
            logging.info(f"Bot inicializado. Último update_id encontrado no Telegram: {ULTIMO_UPDATE_ID}")
        else:
            logging.info("Nenhum update_id anterior encontrado no Telegram. Iniciando do zero.")
            ULTIMO_UPDATE_ID = None
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao tentar obter último update_id na inicialização: {e}. Bot pode reprocessar mensagens antigas.")
        ULTIMO_UPDATE_ID = None

# --- INÍCIO DA EXECUÇÃO DO BOT ---
if __name__ == "__main__":
    initialize_bot_state()

    logging.info("Bot está rodando e monitorando comandos em tempo real...")
    logging.info("==========================================================================")
    logging.info("ATENÇÃO: A causa mais comum de looping é ter MÚLTIPLAS INSTÂNCIAS do bot rodando.")
    logging.info("Por favor, verifique cuidadosamente todos os seus processos e servidores para")
    logging.info("garantir que APENAS UMA CÓPIA deste script está ativa. ISSO É CRÍTICO!")
    logging.info("==========================================================================")
    logging.info(f"Bot pronto para operar em {len(CHAT_DATA)} canais/grupos registrados.")
    if not CHAT_DATA:
        logging.info("Nenhum canal/grupo registrado. Use o comando /iniciarbot em um chat para começar.")

    while True:
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute

        for chat_id_registrado, chat_specific_data in list(CHAT_DATA.items()): 
            last_signal_hour_for_chat = chat_specific_data["last_signal_hour"]
            
            if current_minute == 0 and current_hour != last_signal_hour_for_chat:
                if chat_specific_data["casas"] and JOGOS_CONFIG: 
                    logging.info(f"Hora de enviar um sinal para o chat {chat_id_registrado}! Atual: {current_hour:02d}:00")
                    gerar_e_enviar_sinal_para_chat(chat_id_registrado)
                    chat_specific_data["last_signal_hour"] = current_hour 
                    salvar_chat_data()
                else:
                    if not chat_specific_data["casas"]:
                        logging.info(f"Chat {chat_id_registrado}: Não enviando sinal automático. Nenhuma casa configurada.")
                    if not JOGOS_CONFIG:
                        logging.info(f"Chat {chat_id_registrado}: Não enviando sinal automático. Nenhum jogo configurado globalmente.")

        tratar_comandos()
        check_and_delete_confirmations()

        time.sleep(3)