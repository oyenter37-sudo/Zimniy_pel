import telebot
from telebot import types
import time
import json
import os
import random
from datetime import datetime, timedelta

BOT_TOKEN = "8597327264:AAHBn3QiVZHk8U7JvzyzqioXiNlgYKN7XNQ"
ADMIN_ID = 7040380265  # Замени на свой ID

bot = telebot.TeleBot(BOT_TOKEN)

DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def get_user(user_id):
    db = load_db()
    user_id = str(user_id)
    if user_id not in db:
        db[user_id] = {
            "name": "🦔 Радостный ежик❄️",
            "balance": 0,
            "earned_tasks": 0,
            "work_count": 0,
            "burn_count": 0,
            "snowballs": 0,
            "casino_lost": 0,
            "withdrawn": 0,
            "tree_decorated": False,
            "first_join": datetime.now().isoformat(),
            "last_bonus": None,
            "task_burn_claimed": 0,
            "task_withdraw_claimed": False,
            "task_2days_claimed": False
        }
        save_db(db)
    return db[user_id]

def update_user(user_id, data):
    db = load_db()
    user_id = str(user_id)
    db[user_id] = data
    save_db(db)

def get_main_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("👤  Я  👤", callback_data="profile"))
    keyboard.add(types.InlineKeyboardButton("❄️ Задания ❄️", callback_data="tasks"))
    keyboard.add(types.InlineKeyboardButton("🎁 Бонус 🎁", callback_data="bonus"))
    keyboard.add(types.InlineKeyboardButton("🎽 Работа 🎽", callback_data="work"))
    keyboard.add(types.InlineKeyboardButton("🎧 Джингл Беллс 🎧", callback_data="jingle"))
    keyboard.add(types.InlineKeyboardButton("📎 Доп. 📎", callback_data="extra"))
    keyboard.add(types.InlineKeyboardButton("♻️ Вывод 🔥", callback_data="withdraw"))
    return keyboard

def get_main_text():
    return """❄️ Приветствую тебя в боте "НГ ЕЖ🦔❄️!
❄️ Здесь ты можешь заработать дополнительную валюту к балансу бота!
🦔 Это - неоригинальный бот, этот бот нужен чтобы получить подарки! Оригинал заработает 8 января ♦️!"""

@bot.message_handler(commands=['start'])
def start(message):
    user = get_user(message.from_user.id)
    bot.send_message(message.chat.id, get_main_text(), reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "main")
def back_to_main(call):
    bot.edit_message_text(get_main_text(), call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def profile(call):
    user = get_user(call.from_user.id)
    text = f"""🍬 Заработано за задания - {user['earned_tasks']}
🎽 Ты работал - {user['work_count']} раз.
💫 Конфет0чек у тебя - {user['balance']}
🦔 Имя ежа - {user['name']}"""
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("♻️ Поменять имя", callback_data="change_name"))
    keyboard.add(types.InlineKeyboardButton("Назад ◀️◀️◀️", callback_data="main"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "change_name")
def change_name_start(call):
    msg = bot.edit_message_text("✏️ Напиши новое имя для ежа:", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, change_name_finish, call.from_user.id)

def change_name_finish(message, user_id):
    user = get_user(user_id)
    user['name'] = message.text
    update_user(user_id, user)
    bot.send_message(message.chat.id, f"✅ Имя изменено на: {message.text}", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "work")
def work(call):
    text = """🎽 Поубирай улицы 🌳
🎁 Награда - 1 🍬"""
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🎽 За работу! 🎽", callback_data="do_work"))
    keyboard.add(types.InlineKeyboardButton("Назад ◀️◀️◀️", callback_data="main"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "do_work")
def do_work(call):
    bot.edit_message_text("🦔 Ёжик убирает улицы... Подожди 40 секунд! 🧹", call.message.chat.id, call.message.message_id)
    time.sleep(40)
    
    user = get_user(call.from_user.id)
    user['balance'] += 1
    user['work_count'] += 1
    update_user(call.from_user.id, user)
    
    bot.edit_message_text(get_main_text() + "\n\n✅ Работа выполнена! +1 🍬", call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "bonus")
def bonus(call):
    user = get_user(call.from_user.id)
    
    can_claim = True
    hours = 0
    minutes = 0
    if user['last_bonus']:
        last = datetime.fromisoformat(user['last_bonus'])
        if datetime.now() - last < timedelta(days=1):
            can_claim = False
            remaining = timedelta(days=1) - (datetime.now() - last)
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
    
    if can_claim:
        user['balance'] += 4.5
        user['last_bonus'] = datetime.now().isoformat()
        update_user(call.from_user.id, user)
        bot.edit_message_text("🎁 Ты получил ежедневный бонус: +4.5 🍬!", call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard())
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("Назад ◀️◀️◀️", callback_data="main"))
        bot.edit_message_text(f"⏰ Бонус уже получен! Приходи через {hours}ч {minutes}мин", call.message.chat.id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "jingle")
def jingle(call):
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "extra")
def extra(call):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Сжечь 🔥", callback_data="burn"))
    keyboard.add(types.InlineKeyboardButton("Каз 🎰 60/40", callback_data="casino"))
    keyboard.add(types.InlineKeyboardButton("Слепить ❄️", callback_data="snowball"))
    keyboard.add(types.InlineKeyboardButton("Топ 🔝", callback_data="top"))
    keyboard.add(types.InlineKeyboardButton("Нарядить 🎄", callback_data="decorate"))
    keyboard.add(types.InlineKeyboardButton("Назад ◀️◀️◀️", callback_data="main"))
    
    bot.edit_message_text("📎 Дополнительное меню:", call.message.chat.id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "burn")
def burn(call):
    bot.edit_message_text("🔥 Сжигаем! 🔥\nОст. 5 минут! 🕜", call.message.chat.id, call.message.message_id)
    time.sleep(300)
    
    user = get_user(call.from_user.id)
    user['burn_count'] += 1
    update_user(call.from_user.id, user)
    
    bot.edit_message_text(get_main_text() + "\n\n🔥 Сжигание завершено!", call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "casino")
def casino(call):
    text = """🎰 Казино 60/40 🎰

💰 Шанс выиграть: 40%
💸 Шанс проиграть: 60%

Ставка: 0.5 🍬"""
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Деп", callback_data="casino_play"))
    keyboard.add(types.InlineKeyboardButton("Назад ◀️◀️◀️", callback_data="extra"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "casino_play")
def casino_play(call):
    user = get_user(call.from_user.id)
    
    if user['balance'] < 0.5:
        bot.answer_callback_query(call.id, "❌ Недостаточно конфет!")
        return
    
    if random.randint(1, 100) <= 40:
        user['balance'] += 0.5
        result = "🎉 Ты выиграл! +0.5 🍬"
    else:
        user['balance'] -= 0.5
        user['casino_lost'] += 0.5
        result = "😢 Ты проиграл! -0.5 🍬"
    
    update_user(call.from_user.id, user)
    bot.answer_callback_query(call.id, result)
    casino(call)

@bot.callback_query_handler(func=lambda call: call.data == "snowball")
def snowball(call):
    user = get_user(call.from_user.id)
    
    text = f"""❄️ Слепить снежок ❄️

⛄ Ты слепил: {user['snowballs']} снежков"""
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("⛄ Слепить ком!", callback_data="make_snowball"))
    keyboard.add(types.InlineKeyboardButton("Назад ◀️◀️◀️", callback_data="extra"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "make_snowball")
def make_snowball(call):
    user = get_user(call.from_user.id)
    user['snowballs'] += 1
    update_user(call.from_user.id, user)
    snowball(call)

@bot.callback_query_handler(func=lambda call: call.data == "decorate")
def decorate(call):
    user = get_user(call.from_user.id)
    
    if user['tree_decorated']:
        bot.answer_callback_query(call.id, "🎄 Ты уже нарядил ёлку!")
        return
    
    bot.edit_message_text("🎄 Еж наряжает елку - 20 сек 🎨", call.message.chat.id, call.message.message_id)
    time.sleep(20)
    
    user['balance'] += 4
    user['tree_decorated'] = True
    update_user(call.from_user.id, user)
    
    bot.edit_message_text(get_main_text() + "\n\n🎄 Ёлка наряжена! +4 🍬", call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "top")
def top(call):
    db = load_db()
    
    top_balance = sorted(db.items(), key=lambda x: x[1].get('balance', 0), reverse=True)[:5]
    top_work = sorted(db.items(), key=lambda x: x[1].get('work_count', 0), reverse=True)[:5]
    top_snowballs = sorted(db.items(), key=lambda x: x[1].get('snowballs', 0), reverse=True)[:5]
    
    text = "🔝 ТОП ИГРОКОВ 🔝\n\n"
    
    text += "💰 По конфетам:\n"
    for i, (uid, data) in enumerate(top_balance, 1):
        text += f"{i}. {data['name']} - {data['balance']} 🍬\n"
    
    text += "\n🎽 По работе:\n"
    for i, (uid, data) in enumerate(top_work, 1):
        text += f"{i}. {data['name']} - {data['work_count']} раз\n"
    
    text += "\n⛄ По снежкам:\n"
    for i, (uid, data) in enumerate(top_snowballs, 1):
        text += f"{i}. {data['name']} - {data['snowballs']} шт\n"
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Назад ◀️◀️◀️", callback_data="extra"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "tasks")
def tasks(call):
    text = """❄️ ЗАДАНИЯ ❄️

📉 Проиграть 10🍬 в каз
🎁 Награда - 3🍬

🔥 Сжечь 1 раз 
🎁 Награда - 5🍬 (только 10 раз!)

❄️ Слепить ровно 20, 200, 2000 или 5000 раз
🎁 Награда - 0.50🍬 

♻️ Вывести 10🍬
🎁 Награда - 5🍬 (только 1 раз!)

🦔 Пробыть в боте 2 дня 
🎁 Награда - 1🍬 (только 1 раз!)"""
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📥 Забрать награды", callback_data="claim_tasks"))
    keyboard.add(types.InlineKeyboardButton("Назад ◀️◀️◀️", callback_data="main"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "claim_tasks")
def claim_tasks(call):
    user = get_user(call.from_user.id)
    rewards = 0
    messages = []
    
    claims = int(user['casino_lost'] // 10)
    if claims > 0:
        reward = claims * 3
        rewards += reward
        user['casino_lost'] -= claims * 10
        messages.append(f"📉 Казино: +{reward}🍬")
    
    burn_claims = min(user['burn_count'], 10 - user['task_burn_claimed'])
    if burn_claims > 0:
        reward = burn_claims * 5
        rewards += reward
        user['burn_count'] -= burn_claims
        user['task_burn_claimed'] += burn_claims
        messages.append(f"🔥 Сжечь: +{reward}🍬")
    
    for target in [20, 200, 2000, 5000]:
        if user['snowballs'] == target:
            rewards += 0.5
            messages.append(f"❄️ Слепить {target}: +0.5🍬")
    
    if user['withdrawn'] >= 10 and not user['task_withdraw_claimed']:
        rewards += 5
        user['task_withdraw_claimed'] = True
        messages.append("♻️ Вывод: +5🍬")
    
    first_join = datetime.fromisoformat(user['first_join'])
    if datetime.now() - first_join >= timedelta(days=2) and not user['task_2days_claimed']:
        rewards += 1
        user['task_2days_claimed'] = True
        messages.append("🦔 2 дня в боте: +1🍬")
    
    user['balance'] += rewards
    user['earned_tasks'] += rewards
    update_user(call.from_user.id, user)
    
    if messages:
        result = "✅ Получено:\n" + "\n".join(messages)
    else:
        result = "❌ Нет наград для получения"
    
    bot.answer_callback_query(call.id, result[:200])
    tasks(call)

@bot.callback_query_handler(func=lambda call: call.data == "withdraw")
def withdraw(call):
    text = """♻️ Здесь ты можешь обменять свои конфет0чкi🍬 на Ежидзики👍.

⚡ Выводы будут осуществляться 8 января, на баланс бота @talking_hrenobus_bot

📈 Текущий курс - 1🍬 = 10🦔
Мин. 10🍬"""
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("♻️ ВЫВОД! 🔥", callback_data="do_withdraw"))
    keyboard.add(types.InlineKeyboardButton("Назад ◀️◀️◀️", callback_data="main"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "do_withdraw")
def do_withdraw(call):
    msg = bot.edit_message_text("💰 Введи сколько 🍬 хочешь вывести (мин. 10):", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, withdraw_amount, call.from_user.id)

def withdraw_amount(message, user_id):
    try:
        amount = float(message.text)
        if amount < 10:
            bot.send_message(message.chat.id, "❌ Минимум 10🍬!", reply_markup=get_main_keyboard())
            return
        
        user = get_user(user_id)
        if user['balance'] < amount:
            bot.send_message(message.chat.id, "❌ Недостаточно конфет!", reply_markup=get_main_keyboard())
            return
        
        msg = bot.send_message(message.chat.id, "🆔 Введи свой ID в боте @talking_hrenobus_bot:")
        bot.register_next_step_handler(msg, withdraw_id, user_id, amount)
    except:
        bot.send_message(message.chat.id, "❌ Введи число!", reply_markup=get_main_keyboard())

def withdraw_id(message, user_id, amount):
    target_id = message.text
    user = get_user(user_id)
    
    user['balance'] -= amount
    user['withdrawn'] += amount
    update_user(user_id, user)
    
    hedgehogs = int(amount * 10)
    
    admin_text = f"""📥 ЗАЯВКА НА ВЫВОД

👤 От: @{message.from_user.username or 'Без юзернейма'}
🆔 User ID: {user_id}
💰 Сумма: {amount}🍬 = {hedgehogs}🦔
📍 ID в боте: {target_id}"""
    
    admin_keyboard = types.InlineKeyboardMarkup()
    admin_keyboard.add(
        types.InlineKeyboardButton("✅ Принять", callback_data=f"accept_{user_id}_{amount}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"decline_{user_id}_{amount}")
    )
    
    bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_keyboard)
    bot.send_message(message.chat.id, "✅ Заявка отправлена! Ожидай подтверждения от админа.", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_"))
def accept_withdraw(call):
    parts = call.data.split("_")
    user_id = parts[1]
    amount = float(parts[2])
    
    bot.edit_message_text(call.message.text + "\n\n✅ ПРИНЯТО", call.message.chat.id, call.message.message_id)
    try:
        bot.send_message(int(user_id), f"✅ Твой вывод {amount}🍬 одобрен! Ежидзики будут начислены 8 января.")
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("decline_"))
def decline_withdraw(call):
    parts = call.data.split("_")
    user_id = parts[1]
    amount = float(parts[2])
    
    user = get_user(user_id)
    user['balance'] += amount
    user['withdrawn'] -= amount
    update_user(user_id, user)
    
    bot.edit_message_text(call.message.text + "\n\n❌ ОТКЛОНЕНО", call.message.chat.id, call.message.message_id)
    try:
        bot.send_message(int(user_id), f"❌ Твой вывод {amount}🍬 отклонён. Конфеты возвращены.")
    except:
        pass

if __name__ == "__main__":
    print("🦔 Бот запущен!")
    bot.polling(none_stop=True)
