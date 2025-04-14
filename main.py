import telebot
from telebot import types
import os
from time import time

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

waiting_users = []
active_chats = {}
waiting_start_time = {}
user_languages = {}

waiting_rooms = []
active_rooms = {}
user_rooms = {}
room_counter = 0

# Tin nhắn ngôn ngữ
messages = {
    'vi': {
        'start': "👋 Xin chào! Chọn chức năng bên dưới để bắt đầu.",
        'in_chat': "❗ Bạn đang trong một cuộc trò chuyện rồi!\nDùng /next để tìm người mới hoặc /stop để dừng lại.",
        'waiting': "⏳ Bạn đã vào hàng đợi. Đợi tí nhé...",
        'already_waiting': "🕐 Bạn đang chờ sẵn rồi.",
        'no_chat': "⚠️ Bạn chưa có người trò chuyện.\nNhấn /search để tìm người nhé!",
        'stop': "🚫 Bạn đã dừng trò chuyện.",
        'search': "🔗 Đã tìm được người chat! Bắt đầu trò chuyện nào!",
        'online': "👥 Hiện có {0} người đang chờ.",
        'help': """📖 Hướng dẫn:
👉 /search — Tìm người để trò chuyện 1-1
👉 /next — Chuyển người khác
👉 /stop — Dừng trò chuyện
👉 /room — Vào phòng 4 người
👉 /leaveroom — Rời phòng
👉 /online — Xem số người chờ
👉 /lang — Chuyển ngôn ngữ"""
    },
    'en': {
        'start': "👋 Hello! Choose an option below to get started.",
        'in_chat': "❗ You're already in a chat!\nUse /next to find a new person or /stop to end the chat.",
        'waiting': "⏳ You are in the queue. Please wait...",
        'already_waiting': "🕐 You are already waiting.",
        'no_chat': "⚠️ You don't have a chat partner yet.\nUse /search to find someone!",
        'stop': "🚫 You have ended the chat.",
        'search': "🔗 You've been matched! Start chatting now!",
        'online': "👥 There are {0} people waiting.",
        'help': """📖 Instructions:
👉 /search — Find someone to chat 1-1
👉 /next — Switch to another
👉 /stop — End chat
👉 /room — Join 4-people room
👉 /leaveroom — Leave room
👉 /online — See people waiting
👉 /lang — Change language"""
    }
}

def get_message(user_id, key, *args):
    lang = user_languages.get(user_id, 'vi')
    return messages[lang][key].format(*args)

def main_menu(user_id):
    lang = user_languages.get(user_id, 'vi')
    room_label = "Phòng 4 người" if lang == 'vi' else "Room 4 people"
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🔍 1-1", callback_data="search"),
        types.InlineKeyboardButton(f"👥 {room_label}", callback_data="room")
    )
    markup.add(
        types.InlineKeyboardButton("❌ Dừng", callback_data="stop"),
        types.InlineKeyboardButton("🌍 Ngôn ngữ", callback_data="lang")
    )
    bot.send_message(user_id, get_message(user_id, 'start'), reply_markup=markup)

def stop_chat(user_id, notify=True):
    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        if partner_id in active_chats:
            active_chats.pop(partner_id)
            if notify:
                bot.send_message(partner_id, get_message(partner_id, 'stop'))
    elif user_id in waiting_users:
        waiting_users.remove(user_id)
    if notify:
        bot.send_message(user_id, get_message(user_id, 'stop'))

def match_users():
    while len(waiting_users) >= 2:
        u1, u2 = waiting_users.pop(0), waiting_users.pop(0)
        active_chats[u1], active_chats[u2] = u2, u1
        bot.send_message(u1, get_message(u1, 'search'))
        bot.send_message(u2, get_message(u2, 'search'))

def join_room(user_id):
    global room_counter
    if user_id in user_rooms:
        bot.send_message(user_id, "⚠️ Bạn đang ở trong phòng.")
        return
    if user_id in waiting_rooms:
        bot.send_message(user_id, "🕐 Bạn đang chờ đủ người.")
        return
    waiting_rooms.append(user_id)
    bot.send_message(user_id, "⏳ Đang chờ đủ 4 người...")

    if len(waiting_rooms) >= 4:
        room_id = f"room_{room_counter}"
        room_counter += 1
        members = [waiting_rooms.pop(0) for _ in range(4)]
        active_rooms[room_id] = members
        for uid in members:
            user_rooms[uid] = room_id
            msg = "🎉 Đã tạo phòng với 4 người! Bắt đầu trò chuyện." if user_languages.get(uid, 'vi') == 'vi' else "🎉 Room created with 4 people! Start chatting."
            bot.send_message(uid, msg)

def leave_room(user_id):
    room_id = user_rooms.get(user_id)
    if not room_id:
        if user_id in waiting_rooms:
            waiting_rooms.remove(user_id)
            bot.send_message(user_id, "🚪 Đã rời hàng đợi.")
        else:
            bot.send_message(user_id, "❗ Bạn không ở phòng nào.")
        return
    members = active_rooms.get(room_id, [])
    for uid in members:
        if uid != user_id:
            bot.send_message(uid, "🚫 Một thành viên đã rời phòng.")
        user_rooms.pop(uid, None)
    active_rooms.pop(room_id, None)
    bot.send_message(user_id, "🚪 Đã rời phòng.")

def send_to_room(sender_id, message):
    room_id = user_rooms.get(sender_id)
    if not room_id:
        return
    for uid in active_rooms.get(room_id, []):
        if uid != sender_id:
            try:
                if message.content_type == 'text':
                    bot.send_message(uid, message.text)
                elif message.content_type == 'photo':
                    bot.send_photo(uid, message.photo[-1].file_id, caption=message.caption)
                elif message.content_type == 'video':
                    bot.send_video(uid, message.video.file_id, caption=message.caption)
                elif message.content_type == 'sticker':
                    bot.send_sticker(uid, message.sticker.file_id)
                elif message.content_type == 'voice':
                    bot.send_voice(uid, message.voice.file_id)
                elif message.content_type == 'document':
                    bot.send_document(uid, message.document.file_id, caption=message.caption)
            except Exception as e:
                print(f"Send failed: {e}")

def is_user_in_chat(user_id):
    return user_id in active_chats or user_id in waiting_users

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    if user_id not in user_languages:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Tiếng Việt", "English")
        bot.send_message(user_id, "🌐 Chọn ngôn ngữ:", reply_markup=markup)
    else:
        main_menu(user_id)

@bot.message_handler(func=lambda msg: msg.text in ["Tiếng Việt", "English"])
def handle_language(message):
    user_id = message.chat.id
    user_languages[user_id] = 'vi' if message.text == "Tiếng Việt" else 'en'
    main_menu(user_id)

@bot.message_handler(commands=['search'])
def search(message):
    user_id = message.chat.id
    if is_user_in_chat(user_id):
        bot.send_message(user_id, get_message(user_id, 'in_chat'))
        return
    waiting_users.append(user_id)
    waiting_start_time[user_id] = time()
    bot.send_message(user_id, get_message(user_id, 'waiting'))
    match_users()

@bot.message_handler(commands=['next'])
def next_cmd(message):
    user_id = message.chat.id
    stop_chat(user_id, notify=False)
    search(message)

@bot.message_handler(commands=['stop'])
def stop_cmd(message):
    stop_chat(message.chat.id)

@bot.message_handler(commands=['room'])
def room_cmd(message):
    join_room(message.chat.id)

@bot.message_handler(commands=['leaveroom'])
def leave_cmd(message):
    leave_room(message.chat.id)

@bot.message_handler(commands=['online'])
def online(message):
    bot.send_message(message.chat.id, get_message(message.chat.id, 'online', len(waiting_users)))

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(message.chat.id, get_message(message.chat.id, 'help'))

@bot.message_handler(commands=['lang'])
def lang_cmd(message):
    user_id = message.chat.id
    user_languages[user_id] = 'en' if user_languages.get(user_id, 'vi') == 'vi' else 'vi'
    main_menu(user_id)

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    user_id = call.message.chat.id
    data = call.data
    if data == "search":
        search(call.message)
    elif data == "room":
        join_room(user_id)
    elif data == "stop":
        stop_chat(user_id)
    elif data == "lang":
        user_languages[user_id] = 'en' if user_languages.get(user_id, 'vi') == 'vi' else 'vi'
        main_menu(user_id)

@bot.message_handler(content_types=['text', 'photo', 'video', 'sticker', 'voice', 'document'])
def handle_chat(message):
    user_id = message.chat.id
    if user_id in user_rooms:
        send_to_room(user_id, message)
        return
    partner_id = active_chats.get(user_id)
    if partner_id and active_chats.get(partner_id) == user_id:
        send_to_room(user_id, message)
    else:
        bot.send_message(user_id, get_message(user_id, 'no_chat'))

bot.infinity_polling()
