import telebot
from telebot import types
import time
import json
import os
import random
import string
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io

BOT_TOKEN = "8597327264:AAHBn3QiVZHk8U7JvzyzqioXiNlgYKN7XNQ"
ADMIN_ID = 7040380265

bot = telebot.TeleBot(BOT_TOKEN)

DB_FILE = "database.json"
PROMO_FILE = "promocodes.json"
FONT_PATH = "fonts/Comfortaa-Bold.ttf"
GENERATED_DIR = "generated"
MAX_FOLDER_SIZE_MB = 50

if not os.path.exists(GENERATED_DIR):
    os.makedirs(GENERATED_DIR)

# ==================== ОЧИСТКА ПАПКИ ====================

def get_folder_size_mb(folder):
    total_size = 0
    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)
        if os.path.isfile(file_path):
            total_size += os.path.getsize(file_path)
    return total_size / (1024 * 1024)

def cleanup_old_images():
    if not os.path.exists(GENERATED_DIR):
        return
    
    while get_folder_size_mb(GENERATED_DIR) > MAX_FOLDER_SIZE_MB:
        files = []
        for file in os.listdir(GENERATED_DIR):
            file_path = os.path.join(GENERATED_DIR, file)
            if os.path.isfile(file_path):
                files.append((file_path, os.path.getmtime(file_path)))
        
        if not files:
            break
        
        # Сортируем по времени (старые первые)
        files.sort(key=lambda x: x[1])
        
        # Удаляем самый старый файл
        oldest_file = files[0][0]
        try:
            os.remove(oldest_file)
            print(f"🗑️ Удалён старый файл: {oldest_file}")
        except:
            break

# ==================== БАЗА ДАННЫХ ====================

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def load_promos():
    if os.path.exists(PROMO_FILE):
        with open(PROMO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_promos(promos):
    with open(PROMO_FILE, "w", encoding="utf-8") as f:
        json.dump(promos, f, ensure_ascii=False, indent=2)

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
            "last_find_candy": None,
            "task_burn_claimed": 0,
            "task_withdraw_claimed": False,
            "task_2days_claimed": False,
            "snowball_20_claimed": False,
            "snowball_200_claimed": False,
            "snowball_2000_claimed": False,
            "snowball_5000_claimed": False,
            "used_promos": []
        }
        save_db(db)
    return db[user_id]

def update_user(user_id, data):
    db = load_db()
    user_id = str(user_id)
    db[user_id] = data
    save_db(db)

# ==================== ГЕНЕРАЦИЯ КАРТИНОК ====================

def draw_blurred_circles(img, num_circles=8):
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    for _ in range(num_circles):
        x = random.randint(-100, img.width + 100)
        y = random.randint(-100, img.height + 100)
        radius = random.randint(80, 200)
        alpha = random.randint(30, 80)
        color = (255, 255, 255, alpha)
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)
    
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=30))
    img.paste(overlay, (0, 0), overlay)
    return img

def draw_snowflakes(img, num_flakes=15):
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    for _ in range(num_flakes):
        x = random.randint(0, img.width)
        y = random.randint(0, img.height)
        size = random.randint(10, 30)
        alpha = random.randint(100, 200)
        
        import math
        for angle in range(0, 360, 60):
            end_x = x + size * math.cos(math.radians(angle))
            end_y = y + size * math.sin(math.radians(angle))
            draw.line([(x, y), (end_x, end_y)], fill=(255, 255, 255, alpha), width=2)
    
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=2))
    img.paste(overlay, (0, 0), overlay)
    return img

def create_promo_image(promo_code, amount, uses):
    # Проверяем и очищаем папку
    cleanup_old_images()
    
    width, height = 800, 500
    
    img = Image.new('RGBA', (width, height), (30, 60, 150, 255))
    img = draw_blurred_circles(img, num_circles=10)
    img = draw_snowflakes(img, num_flakes=20)
    
    blurred_bg = img.copy().filter(ImageFilter.GaussianBlur(radius=15))
    
    plash_margin = 50
    plash_top = 100
    plash_bottom = height - 80
    plash_area = (plash_margin, plash_top, width - plash_margin, plash_bottom)
    
    blurred_crop = blurred_bg.crop(plash_area)
    plash_overlay = Image.new('RGBA', (plash_area[2] - plash_area[0], plash_area[3] - plash_area[1]), (255, 255, 255, 40))
    
    img.paste(blurred_crop, (plash_margin, plash_top))
    img.paste(plash_overlay, (plash_margin, plash_top), plash_overlay)
    
    draw = ImageDraw.Draw(img)
    draw.rectangle(plash_area, outline=(255, 255, 255, 150), width=3)
    
    try:
        font_title = ImageFont.truetype(FONT_PATH, 32)
        font_code = ImageFont.truetype(FONT_PATH, 56)
        font_info = ImageFont.truetype(FONT_PATH, 28)
    except:
        font_title = ImageFont.load_default()
        font_code = ImageFont.load_default()
        font_info = ImageFont.load_default()
    
    title = f"Промокод на {amount} конфет!"
    title_bbox = draw.textbbox((0, 0), title, font=font_title)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((width - title_width) // 2, plash_top + 30), title, font=font_title, fill=(255, 255, 255, 255))
    
    code_bbox = draw.textbbox((0, 0), promo_code, font=font_code)
    code_width = code_bbox[2] - code_bbox[0]
    draw.text(((width - code_width) // 2, plash_top + 120), promo_code, font=font_code, fill=(255, 220, 100, 255))
    
    uses_text = f"Активаций: {uses}"
    uses_bbox = draw.textbbox((0, 0), uses_text, font=font_info)
    uses_width = uses_bbox[2] - uses_bbox[0]
    draw.text(((width - uses_width) // 2, plash_top + 220), uses_text, font=font_info, fill=(255, 255, 255, 255))
    
    img_bytes = io.BytesIO()
    img = img.convert('RGB')
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes

def create_text_image(text):
    # Проверяем и очищаем папку
    cleanup_old_images()
    
    width, height = 800, 600
    padding = 60
    
    img = Image.new('RGBA', (width, height), (30, 60, 150, 255))
    img = draw_blurred_circles(img, num_circles=10)
    img = draw_snowflakes(img, num_flakes=20)
    
    draw = ImageDraw.Draw(img)
    
    frame_margin = 40
    frame_rect = (frame_margin, frame_margin, width - frame_margin, height - frame_margin)
    
    blurred_bg = img.copy().filter(ImageFilter.GaussianBlur(radius=10))
    blurred_crop = blurred_bg.crop(frame_rect)
    img.paste(blurred_crop, (frame_margin, frame_margin))
    
    overlay = Image.new('RGBA', (frame_rect[2] - frame_rect[0], frame_rect[3] - frame_rect[1]), (255, 255, 255, 30))
    img.paste(overlay, (frame_margin, frame_margin), overlay)
    
    draw = ImageDraw.Draw(img)
    
    draw.rectangle(frame_rect, outline=(255, 255, 255, 200), width=4)
    inner_frame = (frame_margin + 10, frame_margin + 10, width - frame_margin - 10, height - frame_margin - 10)
    draw.rectangle(inner_frame, outline=(255, 220, 100, 150), width=2)
    
    max_width = width - padding * 2 - 80
    max_height = height - padding * 2 - 80
    
    font_size = 60
    lines = []
    
    while font_size > 16:
        try:
            font = ImageFont.truetype(FONT_PATH, font_size)
        except:
            font = ImageFont.load_default()
            break
        
        lines = []
        words = text.split()
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        line_height = font_size + 10
        total_height = len(lines) * line_height
        
        if total_height <= max_height:
            break
        
        font_size -= 4
    
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except:
        font = ImageFont.load_default()
    
    total_height = len(lines) * (font_size + 10)
    start_y = (height - total_height) // 2
    
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x = (width - line_width) // 2
        y = start_y + i * (font_size + 10)
        
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 50, 150))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
    
    img_bytes = io.BytesIO()
    img = img.convert('RGB')
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes

# ==================== КЛАВИАТУРЫ ====================

def get_main_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("👤  Я  👤", callback_data="profile"))
    keyboard.add(types.InlineKeyboardButton("❄️ Задания ❄️", callback_data="tasks"))
    keyboard.add(types.InlineKeyboardButton("🎁 Бонус 🎁", callback_data="bonus"))
    keyboard.add(types.InlineKeyboardButton("🎽 Работа 🎽", callback_data="work"))
    keyboard.add(types.InlineKeyboardButton("🎧 Джингл Беллс 🎧", callback_data="jingle"))
    keyboard.add(types.InlineKeyboardButton("📎 Доп. 📎", callback_data="extra"))
    keyboard.add(types.InlineKeyboardButton("♻️ Вывод 🔥", callback_data="withdraw"))
    keyboard.add(types.InlineKeyboardButton("🎫 Промокод 🎫", callback_data="promo_menu"))
    keyboard.add(types.InlineKeyboardButton("❄️ Найди 🍬❄️", callback_data="find_candy"))
    return keyboard

def get_main_text():
    return """❄️ Приветствую тебя в боте "НГ ЕЖ🦔❄️!
❄️ Здесь ты можешь заработать дополнительную валюту к балансу бота!
🦔 Это - неоригинальный бот, этот бот нужен чтобы получить подарки! Оригинал заработает 8 января ♦️!"""

# ==================== ОБРАБОТЧИКИ ====================

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
    keyboard.add(types.InlineKeyboardButton("🖼️ Сгенерировать текст", callback_data="generate_text"))
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
    
    if user['snowballs'] >= 20 and not user.get('snowball_20_claimed', False):
        rewards += 0.5
        user['snowballs'] -= 20
        user['snowball_20_claimed'] = True
        messages.append("❄️ Слепить 20: +0.5🍬")
    
    if user['snowballs'] >= 200 and not user.get('snowball_200_claimed', False):
        rewards += 0.5
        user['snowballs'] -= 200
        user['snowball_200_claimed'] = True
        messages.append("❄️ Слепить 200: +0.5🍬")
    
    if user['snowballs'] >= 2000 and not user.get('snowball_2000_claimed', False):
        rewards += 0.5
        user['snowballs'] -= 2000
        user['snowball_2000_claimed'] = True
        messages.append("❄️ Слепить 2000: +0.5🍬")
    
    if user['snowballs'] >= 5000 and not user.get('snowball_5000_claimed', False):
        rewards += 0.5
        user['snowballs'] -= 5000
        user['snowball_5000_claimed'] = True
        messages.append("❄️ Слепить 5000: +0.5🍬")
    
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

# ==================== ПРОМОКОДЫ ====================

@bot.callback_query_handler(func=lambda call: call.data == "promo_menu")
def promo_menu(call):
    text = """🎫 ПРОМОКОДЫ 🎫

Здесь ты можешь создать свой промокод или активировать чужой!

💰 Мин. награда: 0.1 🍬
💰 Макс. награда: 150 🍬"""
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("✨ Создать промокод", callback_data="create_promo"))
    keyboard.add(types.InlineKeyboardButton("🎁 Активировать промокод", callback_data="activate_promo"))
    keyboard.add(types.InlineKeyboardButton("Назад ◀️◀️◀️", callback_data="main"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "create_promo")
def create_promo_start(call):
    msg = bot.edit_message_text("💰 Сколько 🍬 за одну активацию? (от 0.1 до 150):", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, create_promo_amount, call.from_user.id)

def create_promo_amount(message, user_id):
    try:
        amount = float(message.text)
        if amount < 0.1:
            bot.send_message(message.chat.id, "❌ Минимум 0.1 🍬!", reply_markup=get_main_keyboard())
            return
        if amount > 150:
            bot.send_message(message.chat.id, "❌ Максимум 150 🍬!", reply_markup=get_main_keyboard())
            return
        
        msg = bot.send_message(message.chat.id, "🔢 Сколько активаций у промокода?")
        bot.register_next_step_handler(msg, create_promo_uses, user_id, amount)
    except:
        bot.send_message(message.chat.id, "❌ Введи число!", reply_markup=get_main_keyboard())

def create_promo_uses(message, user_id, amount):
    try:
        uses = int(message.text)
        if uses < 1:
            bot.send_message(message.chat.id, "❌ Минимум 1 активация!", reply_markup=get_main_keyboard())
            return
        
        total_cost = amount * uses
        user = get_user(user_id)
        
        if user['balance'] < total_cost:
            bot.send_message(message.chat.id, f"❌ Недостаточно конфет! Нужно: {total_cost} 🍬, у тебя: {user['balance']} 🍬", reply_markup=get_main_keyboard())
            return
        
        promo_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        user['balance'] -= total_cost
        update_user(user_id, user)
        
        promos = load_promos()
        promos[promo_code] = {
            "creator_id": user_id,
            "creator_name": message.from_user.username or message.from_user.first_name,
            "amount": amount,
            "max_uses": uses,
            "current_uses": 0,
            "used_by": []
        }
        save_promos(promos)
        
        img = create_promo_image(promo_code, amount, uses)
        bot.send_photo(message.chat.id, img, caption=f"✅ Промокод создан!\n\n🎫 Код: `{promo_code}`\n💰 Награда: {amount} 🍬\n🔢 Активаций: {uses}\n💸 Списано: {total_cost} 🍬", parse_mode="Markdown", reply_markup=get_main_keyboard())
        
        admin_text = f"""🆕 НОВЫЙ ПРОМОКОД

👤 Создатель: @{message.from_user.username or 'Без юзернейма'}
🆔 ID: {user_id}
🎫 Код: {promo_code}
💰 Награда: {amount} 🍬
🔢 Активаций: {uses}
💸 Всего: {total_cost} 🍬"""
        
        bot.send_message(ADMIN_ID, admin_text)
        
    except:
        bot.send_message(message.chat.id, "❌ Введи целое число!", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "activate_promo")
def activate_promo_start(call):
    msg = bot.edit_message_text("🎫 Введи промокод:", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, activate_promo_code, call.from_user.id)

def activate_promo_code(message, user_id):
    promo_code = message.text.upper().strip()
    promos = load_promos()
    
    if promo_code not in promos:
        bot.send_message(message.chat.id, "❌ Промокод не найден!", reply_markup=get_main_keyboard())
        return
    
    promo = promos[promo_code]
    
    if str(promo['creator_id']) == str(user_id):
        bot.send_message(message.chat.id, "❌ Нельзя активировать свой промокод!", reply_markup=get_main_keyboard())
        return
    
    if str(user_id) in promo['used_by']:
        bot.send_message(message.chat.id, "❌ Ты уже использовал этот промокод!", reply_markup=get_main_keyboard())
        return
    
    if promo['current_uses'] >= promo['max_uses']:
        bot.send_message(message.chat.id, "❌ Промокод закончился!", reply_markup=get_main_keyboard())
        return
    
    user = get_user(user_id)
    user['balance'] += promo['amount']
    
    if 'used_promos' not in user:
        user['used_promos'] = []
    user['used_promos'].append(promo_code)
    
    update_user(user_id, user)
    
    promo['current_uses'] += 1
    promo['used_by'].append(str(user_id))
    promos[promo_code] = promo
    save_promos(promos)
    
    bot.send_message(message.chat.id, f"✅ Промокод активирован! +{promo['amount']} 🍬", reply_markup=get_main_keyboard())

# ==================== ГЕНЕРАТОР ТЕКСТА ====================

@bot.callback_query_handler(func=lambda call: call.data == "generate_text")
def generate_text_start(call):
    msg = bot.edit_message_text("✏️ Напиши текст для генерации:", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, generate_text_finish)

def generate_text_finish(message):
    text = message.text
    
    if len(text) > 500:
        bot.send_message(message.chat.id, "❌ Текст слишком длинный! Максимум 500 символов.", reply_markup=get_main_keyboard())
        return
    
    img = create_text_image(text)
    bot.send_photo(message.chat.id, img, reply_markup=get_main_keyboard())

# ==================== НАЙДИ КОНФЕТУ ====================

@bot.callback_query_handler(func=lambda call: call.data == "find_candy")
def find_candy(call):
    user = get_user(call.from_user.id)
    
    if user.get('last_find_candy'):
        last = datetime.fromisoformat(user['last_find_candy'])
        if datetime.now() - last < timedelta(minutes=30):
            remaining = timedelta(minutes=30) - (datetime.now() - last)
            minutes = int(remaining.total_seconds() // 60)
            seconds = int(remaining.total_seconds() % 60)
            
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("Назад ◀️◀️◀️", callback_data="main"))
            bot.edit_message_text(f"⏰ Подожди ещё {minutes}м {seconds}с!", call.message.chat.id, call.message.message_id, reply_markup=keyboard)
            return
    
    cells = [0] * 25
    
    ones = random.sample(range(25), 12)
    for i in ones:
        cells[i] = 1
    
    remaining = [i for i in range(25) if i not in ones]
    five = random.choice(remaining)
    cells[five] = 5
    
    attempts = random.choice([1, 2])
    
    game_data = {
        "cells": cells,
        "attempts": attempts,
        "opened": []
    }
    
    user['find_candy_game'] = game_data
    update_user(call.from_user.id, user)
    
    keyboard = types.InlineKeyboardMarkup(row_width=5)
    buttons = []
    for i in range(25):
        buttons.append(types.InlineKeyboardButton("❄️", callback_data=f"cell_{i}"))
    keyboard.add(*buttons)
    keyboard.add(types.InlineKeyboardButton("Назад ◀️◀️◀️", callback_data="main"))
    
    bot.edit_message_text(f"❄️ Найди 🍬❄️\n\nУ тебя {attempts} попытка(и)!\nВыбери клетку:", call.message.chat.id, call.message.message_id, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cell_"))
def cell_click(call):
    cell_id = int(call.data.split("_")[1])
    user = get_user(call.from_user.id)
    
    if 'find_candy_game' not in user:
        bot.answer_callback_query(call.id, "❌ Игра не найдена!")
        return
    
    game = user['find_candy_game']
    
    if cell_id in game['opened']:
        bot.answer_callback_query(call.id, "❌ Уже открыто!")
        return
    
    game['opened'].append(cell_id)
    game['attempts'] -= 1
    reward = game['cells'][cell_id]
    user['balance'] += reward
    
    keyboard = types.InlineKeyboardMarkup(row_width=5)
    buttons = []
    for i in range(25):
        if i in game['opened']:
            val = game['cells'][i]
            if val == 0:
                buttons.append(types.InlineKeyboardButton("💨", callback_data=f"cell_{i}"))
            elif val == 1:
                buttons.append(types.InlineKeyboardButton("🍬", callback_data=f"cell_{i}"))
            else:
                buttons.append(types.InlineKeyboardButton("🍬5", callback_data=f"cell_{i}"))
        else:
            buttons.append(types.InlineKeyboardButton("❄️", callback_data=f"cell_{i}"))
    keyboard.add(*buttons)
    
    if game['attempts'] > 0:
        user['find_candy_game'] = game
        update_user(call.from_user.id, user)
        keyboard.add(types.InlineKeyboardButton("Назад ◀️◀️◀️", callback_data="main"))
        bot.edit_message_text(f"❄️ Найди 🍬❄️\n\n+{reward} 🍬!\nОсталось попыток: {game['attempts']}", call.message.chat.id, call.message.message_id, reply_markup=keyboard)
    else:
        user['last_find_candy'] = datetime.now().isoformat()
        del user['find_candy_game']
        update_user(call.from_user.id, user)
        
        total = sum(game['cells'][i] for i in game['opened'])
        bot.edit_message_text(f"❄️ Игра окончена! ❄️\n\nТы нашёл: {total} 🍬", call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard())

if __name__ == "__main__":
    print("🦔 Бот запущен!")
    bot.polling(none_stop=True)
