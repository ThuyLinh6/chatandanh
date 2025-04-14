import telebot
from telebot import types
import os
from time import time

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

waiting_users = []
active_chats = {}
waiting_start_time = {}
user_languages = {}

messages = {
    'vi': {
        'start': "👋 Xin chào! Chọn chức năng bên dưới để bắt đầu.",
        'in_chat': "❗ Bạn đang trong một cuộc trò chuyện rồi!\nDùng /next để tìm người mới hoặc /stop để dừng lại.",
        'waiting': "⏳ Bạn đã vào hàng đợi. Đợi tí nhé...",
        'already_waiting': "🕐 Bạn đang chờ sẵn rồi. Đợi hệ thống ghép cặp nhé!",
        'no_chat': "⚠️ Bạn chưa có người trò chuyện.\nNhấn /search để bắt đầu tìm người nhé!",
        'stop': "🚫 Bạn đã dừng trò chuyện.",
        'search': "🔗 Đã tìm được nhóm chat! Bắt đầu trò chuyện nào!",
        'online': "👥 Hiện có {0} người đang chờ ghép.",
        'help': """ 📚 Hướng dẫn:
👉 /search — Tìm người để trò chuyện
👉 /next — Chuyển nhóm khác
👉 /stop — Dừng trò chuyện
👉 /online — Xem số người đang chờ
👉 /lang — Chuyển đổi ngôn ngữ"""
    },
}

def get_message(user_id, key, *args):
    language = user_languages.get(user_id, 'vi')
    return messages[language].get(key, '').format(*args)

def stop_chat(user_id, notify=True):
    if user_id in active_chats:
        group = active_chats.pop(user_id)
        for member in group:
            if member != user_id:
                active_chats.pop(member, None)
                if notify:
                    bot.send_message(member, get_message(member, 'stop'))
    elif user_id in waiting_users:
        waiting_users.remove(user_id)

    if notify:
        bot.send_message(user_id, get_message(user_id, 'stop'))

def match_users():
    while len(waiting_users) >= 4:
        group = [waiting_users.pop(0) for _ in range(4)]
        for user in group:
            active_chats[user] = group
            bot.send_message(user, get_message(user, 'search'))

def is_user_in_chat(user_id):
    return user_id in active_chats or user_id in waiting_users

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('/search', '/next', '/stop', '/online')
    bot.send_message(user_id, get_message(user_id, 'start'), reply_markup=markup)

@bot.message_handler(commands=['search'])
def search(message):
    user_id = message.chat.id
    if is_user_in_chat(user_id):
        bot.send_message(user_id, get_message(user_id, 'in_chat'))
        return
    waiting_users.append(user_id)
    bot.send_message(user_id, get_message(user_id, 'waiting'))
    match_users()

@bot.message_handler(commands=['next'])
def next(message):
    user_id = message.chat.id
    stop_chat(user_id, notify=False)
    search(message)

@bot.message_handler(commands=['stop'])
def stop(message):
    user_id = message.chat.id
    stop_chat(user_id)

@bot.message_handler(commands=['online'])
def online(message):
    bot.send_message(message.chat.id, get_message(message.chat.id, 'online', len(waiting_users)))

@bot.message_handler(content_types=['text', 'photo', 'video', 'sticker', 'voice', 'document'])
def chat(message):
    user_id = message.chat.id
    group = active_chats.get(user_id)
    if not group or user_id not in group:
        bot.send_message(user_id, get_message(user_id, 'no_chat'))
        stop_chat(user_id)
        return

    sender_index = group.index(user_id) + 1
    for member_id in group:
        if member_id == user_id:
            continue
        if message.content_type == 'text':
            bot.send_message(member_id, f"Người {sender_index}: {message.text}")
        elif message.content_type == 'photo':
            bot.send_photo(member_id, message.photo[-1].file_id, caption=f"Người {sender_index}: {message.caption or ''}")
        elif message.content_type == 'video':
            bot.send_video(member_id, message.video.file_id, caption=f"Người {sender_index}: {message.caption or ''}")
        elif message.content_type == 'sticker':
            bot.send_message(member_id, f"Người {sender_index} gửi sticker:")
            bot.send_sticker(member_id, message.sticker.file_id)
        elif message.content_type == 'voice':
            bot.send_message(member_id, f"Người {sender_index} gửi voice:")
            bot.send_voice(member_id, message.voice.file_id)
        elif message.content_type == 'document':
            bot.send_message(member_id, f"Người {sender_index} gửi file:")
            bot.send_document(member_id, message.document.file_id, caption=f"Người {sender_index}: {message.caption or ''}")
        else:
            bot.send_message(user_id, "❗ Không hỗ trợ loại nội dung này.")

bot.infinity_polling()
