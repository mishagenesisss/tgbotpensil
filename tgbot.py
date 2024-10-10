from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import random
import datetime
import json
import logging
from collections import defaultdict

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Токен вашего бота
telegram_token = '7386664572:AAHu4G_xp_KW1osuxiHMge-xQebopTRhI0c'

# Файл для хранения данных о пэнсиле
DATABASE_FILE = "growth_database.json"
# Файл для хранения данных о предложениях дуэли
DUEL_OFFERS_FILE = "duel_offers.json"
LOTTERY_DATA_FILE = 'lottery_data.json'  # Файл для сохранения данных о лотерее

# Глобальные переменные
users_growth = {}
duel_offers = {}
lottery_active = False  # Переменная для отслеживания активности лотереи
lottery_end_time = None  # Время окончания лотереи
lottery_tickets = {}  # Словарь для хранения билетов на лотерею

def log_message(message):
    """Выводит сообщение в консоль с текущим временем."""
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] {message}")

def load_data():
    """Загружает данные о пользователях из файла."""
    try:
        with open(DATABASE_FILE, 'r') as f:
            data = json.load(f)
            log_message(f"Данные загружены из файла: {data}")
            return {str(key): value for key, value in data.items()}
    except FileNotFoundError:
        log_message(f"Файл базы данных не найден: {DATABASE_FILE}")
        return {}

def save_data():
    """Сохраняет данные в файл."""
    global users_growth  
    with open(DATABASE_FILE, 'w') as f:
        json.dump(users_growth, f)

def load_duel_offers():
    """Загружает данные о предложениях дуэли из файла."""
    try:
        with open(DUEL_OFFERS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_duel_offers():
    """Сохраняет данные о предложениях дуэли в файл."""
    global duel_offers  
    with open(DUEL_OFFERS_FILE, 'w') as f:
        json.dump(duel_offers, f)

def start(update: Update, context: CallbackContext):
    """Отправляет приветственное сообщение при запуске бота."""
    user = update.effective_user
    update.message.reply_html(
        rf"Привет, {user.mention_html()}! Используйте /help для получения списка команд.",
        reply_markup=ForceReply(selective=True),
    )

def handle_growth(user_id):
    global users_growth
    """Обрабатывает команду /пэнсил"""
    
    user_id = str(user_id)  # Преобразовать в строку 
    current_date = datetime.date.today().strftime('%Y-%m-%d')
    
    if user_id in users_growth:
        if 'chikchik_used' in users_growth[user_id] and users_growth[user_id]['chikchik_used']:
            # Special case: If chikchik was used, allow growth even if it's the same day
            growth_today = random.randint(1, 10)
            users_growth[user_id]['length'] += growth_today
            users_growth[user_id]['last_measure_date'] = current_date
            del users_growth[user_id]['chikchik_used']  # Reset the flag
            save_data()
            message = f"@id{user_id}, ваш пэнсил вырос на {growth_today} см. " \
                      f"Теперь его длина {users_growth[user_id]['length']} см."
            return message
        elif users_growth[user_id]['last_measure_date'] == current_date:
            return "Вы сегодня уже измеряли свой пэнсил. Попробуйте завтра!"
        else:
            # Изменяем длину, если измерение в другой день
            growth_today = random.randint(1, 10)
            users_growth[user_id]['length'] += growth_today
            users_growth[user_id]['last_measure_date'] = current_date
    else:
        # Создаем новую запись, если пользователь новый
        growth_today = random.randint(1, 10)
        users_growth[user_id] = {
            'length': growth_today,
            'last_measure_date': current_date
        }
    
    save_data()  # Сохраняем данные после изменения
    
    message = f"@id{user_id}, ваш пэнсил вырос на {growth_today} см. " \
              f"Теперь его длина {users_growth[user_id]['length']} см."
    return message

def handle_top_chat():
    """Обрабатывает команду /топчата"""
    
    sorted_users = sorted(users_growth.items(), key=lambda item: item[1]['length'], reverse=True)
    
    top_chat_message = "🏆 Топ-чат по пэнсилу:\n"
    for i, (user_id, data) in enumerate(sorted_users[:10]):
        top_chat_message += f"{i+1}. @id{user_id} - {data['length']} см\n"
    
    return top_chat_message

def handle_casino(user_id, bet):
    """Обрабатывает команду /казино с равными шансами на выигрыш и проигрыш"""
    
    user_id = str(user_id)  # Ensure user_id is a string

    if user_id not in users_growth:
        return "Вы еще не играли в /пэнсил. Начните играть, чтобы узнать свой пэнсил!"
    
    if bet <= 0:
        return "Ставка должна быть больше нуля!"
    
    if users_growth[user_id]['length'] < bet:
        return "У вас недостаточно пэнсила для такой ставки!"
    
    # Генерируем случайное число 0 или 1
    # 0 - проигрыш, 1 - выигрыш
    result = random.randint(0, 1)  
    
    if result == 1:
        users_growth[user_id]['length'] += bet
        result_message = f"🎉 Вы выиграли! Ваш пэнсил увеличился на {bet} см."
    else:
        users_growth[user_id]['length'] -= bet
        result_message =  f"😔 Вы проиграли ставку в {bet} см."
    
    save_data()  # Сохранение данных после изменения
    return result_message

def handle_chikchik(user_id):
    """Обрабатывает команду /чикчик"""
    
    user_id = str(user_id)  # Ensure user_id is a string
    
    if user_id not in users_growth:
        return "У вас и так нет пэнсила. Начните с команды /пэнсил"
    
    if users_growth[user_id]['length'] == 0:
        return "Ваш пэнсил и так уже сломан! 😱 Начните заново с команды /пэнсил"
    
    users_growth[user_id]['length'] = 0
    users_growth[user_id]['chikchik_used'] = True  # Добавляем флаг "chikchik_used"
    save_data()  # Сохранение данных после изменения
    return "😨 Ваш пэнсил исчез! Начните заново с команды /пэнсил"

def handle_help():
    """Обрабатывает команду /хелп"""
    help_text = "Список команд:\n" \
                "/пэнсил - измеряет ваш пэнсил\n" \
                "/казино [число] - игра на ваш пэнсил\n" \
                "/топчата - показывает топ-10 пользователей по пэнсилу\n" \
                "/чикчик - удаляет ваш пэнсил\n" \
                "/хелп - показывает это сообщение\n" \
                "/дуэль [ставка] - бросает вызов на дуэль\n" \
                "/дуэль принять - принимает дуэль\n" \
                "/дуэль отклонить - отклоняет дуэль"
    return help_text

def handle_my_growth(user_id):
    """Обрабатывает команду /я"""
    user_id = str(user_id)
    if user_id in users_growth:
        user_length = users_growth[user_id]['length']
        return f"Длина вашего пэнсила: {user_length} см."
    else:
        return "Вы еще не играли в /пэнсил. Начните играть, чтобы узнать свой пэнсил!"

def handle_duel(user_id, message_text, peer_id):
    global duel_offers
    """Обрабатывает команду /дуэль"""

    user_id = str(user_id)

    try:
        bet = int(message_text.split()[1])
    except (IndexError, ValueError):
        return "Неверный формат команды. Используйте: /дуэль [ставка]"

    if user_id not in users_growth:
        return "У вас нет пэнсила. Начните с команды /пэнсил."

    if users_growth[user_id]['length'] < bet:
        return "У вас недостаточно пэнсила для такой ставки!"

    # Создаем предложение дуэли
    duel_offers[peer_id] = {
        "challenger_id": user_id,
        "bet": bet,
        "timestamp": time.time() + 300,  # Время действия предложения дуэли (5 минут)
        "accepted": False  # Добавляем ключ "accepted"
    }
    save_duel_offers()

    user_info = vk.users.get(user_ids=user_id)[0]
    user_name = user_info['first_name']

    return f"@id{user_id} ({user_name}) бросил вызов на дуэль! Ставка: {bet} см. \n" \
           f"Напишите /дуэль принять, чтобы принять вызов."

def handle_accept_duel(user_id, peer_id):
    global duel_offers
    """Обрабатывает команду /дуэль принять"""

    user_id = str(user_id)

    if peer_id not in duel_offers:
        return "Нет активного предложения дуэли в этом чате."

    if duel_offers[peer_id]["challenger_id"] == user_id:
        return "Вы не можете принять свою собственную дуэль!"

    if user_id not in users_growth:
        return "У вас нет пэнсила. Начните с команды /пэнсил."

    if users_growth[user_id]['length'] < duel_offers[peer_id]["bet"]:
        return "У вас недостаточно пэнсила для такой ставки!"

    if time.time() > duel_offers[peer_id]['timestamp']:
        del duel_offers[peer_id]
        save_duel_offers()
        return "Время на принятие дуэли истекло."

    challenger_id = duel_offers[peer_id]["challenger_id"]
    bet = duel_offers[peer_id]["bet"]

    # Проводим дуэль сразу после принятия вызова
    duel_result(challenger_id, user_id, bet, peer_id)

def duel_result(challenger_id, user_id, bet, peer_id):
    """Обрабатывает результат дуэли"""

    global users_growth, duel_offers

    challenger_id = str(challenger_id)
    user_id = str(user_id)

    challenger_info = vk.users.get(user_ids=challenger_id)[0]
    user_info = vk.users.get(user_ids=user_id)[0]
    
    challenger_name = challenger_info['first_name']  # Получаем имя здесь
    user_name = user_info['first_name']              # Получаем имя здесь

    result = random.randint(0, 1)

    if result == 1:
        winner_id = challenger_id
        loser_id = user_id
        winner_name = challenger_name  # Используем имя, полученное выше
        loser_name = user_name        # Используем имя, полученное выше
    else:
        winner_id = user_id
        loser_id = challenger_id
        winner_name = user_name        # Используем имя, полученное выше
        loser_name = challenger_name  # Используем имя, полученное выше

    users_growth[winner_id]['length'] += bet
    users_growth[loser_id]['length'] -= bet
    save_data()

    # Отправляем сообщение о результате дуэли
    vk.messages.send(
        peer_id=peer_id,
        message=f"🎉 @id{winner_id} ({winner_name}) выиграл дуэль!\n"
                f"😔 @id{loser_id} ({loser_name}) проиграл дуэль!",
        random_id=random.randint(1, 2*31)
    )

    del duel_offers[peer_id]
    save_duel_offers()

def check_and_handle_duels(peer_id, from_id):
    """Проверяет активные дуэли и обрабатывает их результат."""
    global duel_offers
    log_message(f"check_and_handle_duels: duel_offers = {duel_offers}")
    if peer_id in duel_offers and duel_offers[peer_id]["accepted"]:
        log_message(f"check_and_handle_duels: Found active duel")
        challenger_id = duel_offers[peer_id]["challenger_id"]
        bet = duel_offers[peer_id]["bet"]
        duel_result(challenger_id, from_id, bet, peer_id)
        


def handle_give(update: Update, context: CallbackContext):
    """Обрабатывает команду /дать."""
    global users_growth
    user_id = str(update.effective_user.id)
    message_text = update.message.text.lower()

    try:
        parts = message_text.split()
        if len(parts) != 3:
            return "Неверный формат команды. Используйте: /дать idпользователя число"

        recipient_id = parts[1]
        amount = int(parts[2])

        if recipient_id not in users_growth:
            return "Пользователь не найден."

        if user_id not in users_growth:
            return "У вас нет пэнсила."
        if users_growth[user_id]['length'] < amount:
            return "У вас недостаточно пэнсила для передачи."
        if amount <= 0:
            return "Количество должно быть больше нуля."

        users_growth[user_id]['length'] -= amount
        users_growth[recipient_id]['length'] += amount
        save_data()  # Сохранение данных после каждой передачи

        user_info = context.bot.get_user_profile_photos(user_id)
        user_name = user_info.first_name
        recipient_info = context.bot.get_user_profile_photos(recipient_id)
        recipient_name = recipient_info.first_name
        return f"🎉 @{user_name} передал {amount} см @{recipient_name}!"

    except (IndexError, ValueError):
        return "Неверный формат команды. Используйте: /дать idпользователя число"

def handle_give_pencil(from_id, message_text):
    """Обрабатывает команду /выдать, только для администратора"""
    global users_growth
    from_id = str(from_id)
    message_parts = message_text.split()
    
    if from_id != '7182691827':  # Замените '378134543' на ID администратора
        return "У вас нет прав на использование этой команды."
    
    if len(message_parts) != 3:
        return "Неверный формат команды. Используйте: /выдать idпользователя число"

    try:
        recipient_id = int(message_parts[1])
        amount = int(message_parts[2])
    except ValueError:
        return "Неверный формат данных."
    
    recipient_id = str(recipient_id)

    if recipient_id not in users_growth:
        return "Пользователь с таким ID не найден."

    users_growth[recipient_id]['length'] += amount
    save_data()

    log_message(f"Администратор {from_id} выдал {amount} см пэнсила пользователю {recipient_id}")
    return f"Выдали {amount} см пэнсила пользователю с ID {recipient_id}"

def handle_statistics():
    """Обрабатывает команду /статистика"""
    global users_growth, user_quests
    
    total_players = len(users_growth)
    total_pencil = sum(user['length'] for user in users_growth.values())
    completed_quests = sum(1 for user_data in user_quests.values() if user_data['current_quest'] is None)

    return f"Статистика игры:\n" \
           f"Количество игроков: {total_players}\n" \
           f"Общая сумма пэнсила: {total_pencil} см\n" \
           f"Количество выполненных квестов: {completed_quests}"

def handle_lottery_start():
    """Обрабатывает команду /лотерея, запускает лотерею"""
    global lottery_end_time, lottery_tickets, lottery_active

    if lottery_active:
        return "Лотерея уже запущена! Ждите ее окончания."

    lottery_active = True
    lottery_end_time = datetime.datetime.now() + datetime.timedelta(hours=1)
    lottery_end_time = lottery_end_time.timestamp()
    print(f"Время окончания лотереи: {datetime.datetime.fromtimestamp(lottery_end_time)}")
    lottery_tickets = {}
    
    save_lottery_data()

    return "Лотерея началась! Напишите /билет, чтобы купить билет за 10 см. Победитель будет объявлен через 1 час."

def save_lottery_data():
    """Сохраняет данные о лотерее в файл"""
    global lottery_active, lottery_end_time, lottery_tickets
    data = {
        'active': lottery_active,
        'end_time': lottery_end_time,
        'tickets': lottery_tickets 
    }
    with open(LOTTERY_DATA_FILE, 'w') as f:
        json.dump(data, f)
    log_message(f"Сохранена информация о лотерее в файл: {LOTTERY_DATA_FILE}")

def load_lottery_data():
    """Загружает данные о лотерее из файла"""
    global lottery_active, lottery_end_time, lottery_tickets
    try:
        with open(LOTTERY_DATA_FILE, 'r') as f:
            data = json.load(f)
            lottery_active = data['active']
            lottery_end_time = data.get('end_time')
            lottery_tickets = data.get('tickets', {})
            log_message(f"Информация о лотерее загружена из файла: {LOTTERY_DATA_FILE}")
    except FileNotFoundError:
        log_message(f"Файл с данными о лотерее не найден: {LOTTERY_DATA_FILE}")

def handle_buy_ticket(user_id):
    """Обрабатывает команду /билет"""
    global users_growth, lottery_tickets, lottery_active, lottery_end_time
     
    user_id = str(user_id)
     
    if not lottery_active:
        return "Лотерея не запущена. Напишите /лотерея, чтобы начать ее."
     
    if users_growth[user_id]['length'] < 10:
        return "У вас недостаточно пэнсила для покупки билета (необходимо 10 см)."

    users_growth[user_id]['length'] -= 10
    if user_id not in lottery_tickets:
        lottery_tickets[user_id] = True
    save_data()
    save_lottery_data()
    return "Вы купили билет! Удачи в лотерее!"

def handle_lottery_check():
    """Проверяет, закончилась ли лотерея, и объявляет победителя каждые 10 секунд"""
    global lottery_tickets, lottery_end_time, lottery_active, users_growth

    while True:
        current_datetime = datetime.datetime.fromtimestamp(time.time())
        if lottery_active and lottery_end_time is not None and current_datetime >= datetime.datetime.fromtimestamp(lottery_end_time):
            winner_id = random.choice(list(lottery_tickets.keys()))
            total_tickets = len(lottery_tickets)
            lottery_pencil = total_tickets * 10

            users_growth[winner_id]['length'] += lottery_pencil
            save_data()

            try:
                context.bot.send_message(
                    chat_id=your_chat_id,  # Замените на ваш chat_id
                    text=f"Поздравляем! Победитель лотереи: @{winner_id}! Вам достался {lottery_pencil} см пэнсила!🎉",
                )
            except Exception as e:
                print(f"Ошибка отправки сообщения: {e}")

            log_message(f"Победитель лотереи: {winner_id}")
            lottery_tickets.clear()
            lottery_end_time = None

    


 
def determine_winner(game, vk):
    """Определяет победителя игры КМБ."""
    winner = None
    if game['player1_choice'] == game['player2_choice']:
        winner = 'Ничья'
    elif (game['player1_choice'] == 'камень' and game['player2_choice'] == 'ножницы') or \
         (game['player1_choice'] == 'ножницы' and game['player2_choice'] == 'бумага') or \
         (game['player1_choice'] == 'бумага' and game['player2_choice'] == 'камень'):
        winner = game['player1']
    else:
        winner = game['player2']
 
    game['winner'] = winner
 
    player1_info = vk.users.get(user_ids=game['player1'])[0]
    player2_info = vk.users.get(user_ids=game['player2'])[0]
 
    vk.messages.send(peer_id=game['player1'], message=f"Игра завершена! {winner} ({player1_info['first_name']} если вы победили)!", random_id=random.randint(1, 2*31))
    vk.messages.send(peer_id=game['player2'], message=f"Игра завершена! {winner} ({player2_info['first_name']} если вы победили)!", random_id=random.randint(1, 2*31))
 
    del rps_game[game['player1']]
    
def handle_message(update: Update, context: CallbackContext):
    """Обработка входящего сообщения."""
    user_id = update.effective_user.id
    message_text = update.message.text.lower()

    log_message(f"Получено сообщение от пользователя {user_id}: '{message_text}'")

    response_message = None

    # Обработка команд
    try:
        if message_text == '/пэнсил':
            response_message = handle_growth(user_id)
        elif message_text == '/топчата':
            response_message = handle_top_chat()
        elif message_text.startswith('/казино '):
            try:
                bet = int(message_text.split(' ')[1])
                response_message = handle_casino(user_id, bet)
            except (IndexError, ValueError):
                response_message = "Неверный формат команды. Используйте: /казино [число]"
        elif message_text == '/чикчик':
            response_message = handle_chikchik(user_id)
        elif message_text == '/хелп':
            response_message = handle_help()
        elif message_text.startswith('/дуэль'):
            response_message = handle_duel(user_id, message_text)
        elif message_text == '/я':
            response_message = handle_my_growth(user_id)
        elif message_text.startswith('/дать '):
            response_message = handle_give(update, user_id)
        elif message_text.startswith('/выдать '):
            response_message = handle_give_pencil(user_id, message_text)
        elif message_text == '/статистика':
            response_message = handle_statistics()
        elif message_text == '/лотерея':
            response_message = handle_lottery_start()
        elif message_text == '/билет':
            response_message = handle_buy_ticket(user_id)

        # Отправка ответа
        if response_message:
            log_message(f"Отправка сообщения пользователю {user_id}: '{response_message}'")
            context.bot.send_message(chat_id=user_id, text=response_message)
        else:
            log_message(f"Нет ответа для пользователя {user_id}.")

    except Exception as e:
        log_message(f"Ошибка при обработке сообщения от пользователя {user_id}: {e}")

if __name__ == '__main__':
    log_message("Бот запущен")
    updater = Updater(token=telegram_token, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

handle_message()
