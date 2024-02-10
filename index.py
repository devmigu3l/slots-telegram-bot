import telegram
import time
from datetime import datetime
import random
import pymongo
from datetime import timedelta

client = pymongo.MongoClient("")
db = client[""]
collection = db[""]


def update_chat_info_if_changed(chat, collection):
    id = chat['id']
    token = chat['token']
    bot = telegram.Bot(token)

    try:
       
        chat_info = bot.get_chat(id)
        chat_title = chat_info.title

        changes_detected = (chat.get('room') != chat_title)

        if changes_detected:
            new_invite_link = bot.export_chat_invite_link(chat_id=id)
            members_count = bot.get_chat_member_count(chat_id=chat['id'])  

            collection.update_one(
                {"chats.id": id},
                {"$set": {
                    "chats.$.room": chat_title,
                    "chats.$.invite_link": new_invite_link,  
                    "chats.$.members_count": members_count,

                }}
            )

            print(f"Informações do chat {id} foram atualizadas.")

    except Exception as e:
        print(f"Erro ao atualizar informações do chat {id}: {e}")



message_ids = []
chat_states = {}
time_margin = timedelta(seconds=10)

def time_in_range(start, end, x):
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end

def is_in_free_hours(free_hours, now):
    in_free_hours = False
    
    time_periods = ["morning", "afternoon", "night"]
    for period in time_periods:
        if period in free_hours:
            time_range = [datetime.strptime(time_str, "%H:%M").time() for time_str in free_hours[period]]
            in_free_hours = in_free_hours or time_in_range(time_range[0], time_range[1], now)
    
    return in_free_hours

jogo_atual_por_chat = {}

while True:

    config = collection.find_one()
    chats = config['chats']
    
    now = datetime.now()

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    global_active = config.get('global_active', True)

    for chat in chats:
        update_chat_info_if_changed(chat, collection)


    if global_active:
        for chat in chats:
            if chat['active']:
                try:
                    if chat['free']:
                        
                        now = datetime.now().time()
                        free_hours = chat['free_hours']
                        in_free_hours = False

                        in_free_hours = is_in_free_hours(free_hours, now)

                        if not in_free_hours:
                            continue
                    
                    id = chat['id']
                    token = chat['token']
                    bot = telegram.Bot(token)

                    chat_info = bot.get_chat(id)
                    chat_title = chat_info.title


                    bonus_links = chat['links']
                    global_messages = chat['global_messages']

                    jogos_ativos = [jogo for jogo in chat['games'] if jogo['active']]

                    if jogos_ativos:
                        if id not in jogo_atual_por_chat or jogo_atual_por_chat[id]['name'] not in [jogo['name'] for jogo in jogos_ativos]:

                            jogo_atual_por_chat[id] = random.choice(jogos_ativos)
                            
                        jogo_atual = jogo_atual_por_chat[id]['name']
                        links = jogo_atual_por_chat[id]['links']

                        link_celular_str = ""
                        if 'phone' in links:
                            link_celular = f"<a href='{links['phone']['url']}'>{links['phone']['text']}</a>"
                            link_celular_str = f"{link_celular}"

                        link_computador_str = ""
                        if 'computer' in links:
                            link_computador = f"<a href='{links['computer']['url']}'>{links['computer']['text']}</a>"
                            link_computador_str = f"{link_computador}"
                
                    else:
                        print(f"there are no active games for the room {chat_title} with chat id {id}")
                        continue  
                    
                    link_bonus_str = ""
                    if 'bonus' in bonus_links:
                        link_bonus = f"<a href='{bonus_links['bonus']['url']}'>{bonus_links['bonus']['text']}</a>"
                        link_bonus_str = f"{link_bonus}" 
                    
                    link_adicional_str = ""
                    if 'link_adicional' in bonus_links:
                        link_adicional = f"<a href='{bonus_links['link_adicional']['url']}'>{bonus_links['link_adicional']['text']}</a>"
                        link_adicional_str = f"{link_adicional}"
                        
                    
                    message_template = global_messages['alert_message']
                    message_text = message_template.format(game=jogo_atual, link_computer=link_computador_str, link_phone=link_celular_str, link_bonus=link_bonus_str, link_adicional=link_adicional_str)
                    
                    data = bot.send_message(id, text=message_text, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)
                    message_ids.append((token, id, chat_title, data.message_id, jogo_atual, link_bonus_str, link_adicional_str, global_messages))
                    print(f"sending alert message to chat ({id}) and room ({chat_title}) and game ({jogo_atual}) ")
                    time.sleep(0.01)
                    
                except Exception as e:
                    print(f"An error occurred when sending alert message to chat {id} and room ({chat_title}): {e}")
        time.sleep(10)
                    
        for (token, id, chat_title, message_id, jogo_atual, link_bonus_str, link_adicional_str, global_messages) in message_ids:
            try:
                bot = telegram.Bot(token)
                print(f"deleting alert message for chat ({id}) and room ({chat_title}) and game ({jogo_atual}) ")
                bot.delete_message(id, message_id)
                
            except Exception as e:
                print(f"An error occurred when deleting alert message for chat {id} and room ({chat_title}): {e}")
                
        message_ids = []

        time.sleep(10)

        for chat in chats:
            if chat['active']:
                try:
                    if chat['free']:
                        
                        now = datetime.now().time()
                        free_hours = chat['free_hours']
                        in_free_hours = False

                        in_free_hours = is_in_free_hours(free_hours, now)

                        if not in_free_hours:
                            continue
                    
                    id = chat['id']
                    token = chat['token']
                    bot = telegram.Bot(token)

                    chat_info = bot.get_chat(id)
                    chat_title = chat_info.title


                    bonus_links = chat['links']
                    global_messages = chat['global_messages']
                    
                    multiplier_normal = random.randint(1, 12)
                    multiplier_turbo = random.randint(1, 12)
                    betting_level = random.randint(1, 10)

                    strategy = "💰 {}x Normal\n💰 {}x Turbo\n🆙 Nível de aposta: {}\n⚡️ Intercalando".format(multiplier_normal, multiplier_turbo, betting_level)

                    jogos_ativos = [jogo for jogo in chat['games'] if jogo['active']]

                    if jogos_ativos:
                        if id not in jogo_atual_por_chat or jogo_atual_por_chat[id]['name'] not in [jogo['name'] for jogo in jogos_ativos]:

                            jogo_atual_por_chat[id] = random.choice(jogos_ativos)
                            
                        jogo_atual = jogo_atual_por_chat[id]['name']
                        links = jogo_atual_por_chat[id]['links']  

                        
                        link_celular_str = ""
                        if 'phone' in links:
                            link_celular = f"<a href='{links['phone']['url']}'>{links['phone']['text']}</a>"
                            link_celular_str = f"{link_celular}"

                        
                        link_computador_str = ""
                        if 'computer' in links:
                            link_computador = f"<a href='{links['computer']['url']}'>{links['computer']['text']}</a>"
                            link_computador_str = f"{link_computador}"
                
                    else:
                        print(f"there are no active games for the room {chat_title} with chat id {id}")
                        continue  
                    
                    link_bonus_str = ""
                    if 'bonus' in bonus_links:
                        link_bonus = f"<a href='{bonus_links['bonus']['url']}'>{bonus_links['bonus']['text']}</a>"
                        link_bonus_str = f"{link_bonus}" 
                    
                    link_adicional_str = ""
                    if 'link_adicional' in bonus_links:
                        link_adicional = f"<a href='{bonus_links['link_adicional']['url']}'>{bonus_links['link_adicional']['text']}</a>"
                        link_adicional_str = f"{link_adicional}"
                        
                    
                    message_template = global_messages['entry_message']
                    message_text = message_template.format(game=jogo_atual, link_computer=link_computador_str, link_phone=link_celular_str, link_bonus=link_bonus_str, link_adicional=link_adicional_str,strategy=strategy)
                    
                    data = bot.send_message(id, text=message_text, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)
                    message_ids.append((token, id, chat_title, data.message_id, jogo_atual, link_bonus_str, link_adicional_str, global_messages))
                    print(f"sending confirmed message to chat ({id}) and room ({chat_title}) and game ({jogo_atual})")
                    time.sleep(0.01)
                    
                except Exception as e:
                    print(f"An error occurred when sending confirmed message for chat {id} and room ({chat_title}): {e}")

   
        time.sleep(120)
    
    
        for chat in chats:  
            if chat['active']:
                try:
                    if chat['free']:
                    
                    
                        now = datetime.now().time()
                        free_hours = chat['free_hours']
                        in_free_hours = False

                        in_free_hours = is_in_free_hours(free_hours, now)

                        if not in_free_hours:
                            continue

                    id = chat['id']
                    token = chat['token']
                    bot = telegram.Bot(token)
                    bonus_links = chat['links']

                    link_bonus_str = ""
                    if 'bonus' in bonus_links:
                        link_bonus = f"<a href='{bonus_links['bonus']['url']}'>{bonus_links['bonus']['text']}</a>"
                        link_bonus_str = f"{link_bonus}" 

                    
                    jogo_atual = jogo_atual_por_chat[id]  

            
                    global_messages = chat['global_messages']
                    for (token, id, chat_title, message_id, jogo_atual, link_bonus_str, link_adicional_str, global_messages) in message_ids:
                        
                        
                        bot = telegram.Bot(token)
                        print(f"editing confirmed message to chat ({id}) and room ({chat_title}) and game ({jogo_atual})")
                        bot.edit_message_text(global_messages['finished_message'].format(game=jogo_atual, link_bonus=link_bonus_str, link_adicional=link_adicional_str), id, message_id, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)
                    
                    message_ids = []
                
                except Exception as e:
                    print(f"An error occurred when editing message in chat {id} and room ({chat_title}): {e}")
        
    time.sleep(400)
    print(f'\n-------------------------------\n{current_time}')

    for id in jogo_atual_por_chat:
        if id in [chat['id'] for chat in chats]:  
            jogos_ativos = [jogo for jogo in next(chat['games'] for chat in chats if chat['id'] == id) if jogo['active']]
            if jogos_ativos:
                jogo_atual_por_chat[id] = random.choice(jogos_ativos)   
                
               