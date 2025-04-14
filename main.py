import telebot
from telebot import types
import os
import threading
from time import time

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

waiting_users = []
active_chats = {}
waiting_start_time = {}
user_languages = {}

# Add a Lock to handle concurrent updates safely
lock = threading.Lock()

messages = {
    'vi': {
        'start': "👋 Xin chào! Chọn chức năng bên dưới để bắt đầu.",
        'in_chat': "❗ Bạn đang trong một cuộc trò chuyện rồi!\nDùng 👉 /next để tìm người mới hoặc 👉 /stop để dừng lại.",
        'waiting': "⏳ Bạn đã vào hàng đợi. Đợi tí nhé...",
        'already_waiting': "🕐 Bạn đang chờ sẵn rồi.",
        'no_chat': "⚠️ Bạn chưa có cuộc trò chuyện nào.\nNhấn 👉 /search để tìm người nhé!",
        'stop': "🚫 Bạn đã dừng trò chuyện.",
        'search': "🔗 Đã tìm được người chat! Bắt đầu nào!",
        'online': "👥 Hiện có {0} người đang chờ.",
        'help': "📖 Hướng dẫn:\n\n👉 /search — Tìm người trò chuyện\n👉 /next — Chuyển người khác\n👉 /stop — Dừng trò chuyện\n👉 /online — Xem số người chờ\n👉 /lang — Đổi ngôn ngữ"
    },
    'en': {
        'start': "👋 Hello! Choose an option below to get started.",
        'in_chat': "❗ You're already in a chat!\nUse 👉 /next to find someone new or 👉 /stop to end.",
        'waiting': "⏳ You're in the queue. Please wait...",
        'already_waiting': "🕐 You're already waiting.",
        'no_chat': "⚠️ You have no active chat.\nPress 👉 /search to find someone!",
        'stop': "🚫 You have left the chat.",
        'search': "🔗 You’ve been matched! Start chatting!",
        'online': "👥 {0} people are waiting.",
        'help': "📖 Instructions:\n\n👉 /search — Find a chat partner\n👉 /next — Find someone else\n👉 /stop — Stop chatting\n👉 /online — See who's waiting\n👉 /lang — Change language"
    }
}

def get_message(user_id, key, *args):
    language = user_languages.get(user_id, 'vi')
    return messages[language].get(key, '').format(*args)

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
        user1 = waiting_users.pop(0)
        user2 = waiting_users.pop(0)
        active_chats[user1] = user2
        active_chats[user2] = user1
        bot.send_message(user1, get_message(user1, 'search'))
        bot.send_message(user2, get_message(user2, 'search'))

def is_user_in_chat(user_id):
    return user_id in active_chats or user_id in waiting_users

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    if user_id not in user_languages:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🇻🇳 Tiếng Việt", "🇺🇸 English")
        bot.send_message(user_id, "👋 Chào bạn! Vui lòng chọn ngôn ngữ:", reply_markup=markup)
    else:
        main_menu(user_id)

def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔍 Tìm người trò chuyện")
    markup.add("🌐 Đổi ngôn ngữ")
    bot.send_message(user_id, get_message(user_id, 'start'), reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ["🇻🇳 Tiếng Việt", "🇺🇸 English"])
def set_language(message):
    user_id = message.chat.id
    user_languages[user_id] = 'vi' if "Việt" in message.text else 'en'
    main_menu(user_id)
    bot.send_message(user_id, get_message(user_id, 'help'))

@bot.message_handler(func=lambda message: message.text == "🌐 Đổi ngôn ngữ")
def lang(message):
    user_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🇻🇳 Tiếng Việt", "🇺🇸 English")
    bot.send_message(user_id, "🌐 Vui lòng chọn ngôn ngữ:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🔍 Tìm người trò chuyện")
def search_button(message):
    search(message)

@bot.message_handler(commands=['search'])
def search(message):
    user_id = message.chat.id
    if is_user_in_chat(user_id):
        bot.send_message(user_id, get_message(user_id, 'in_chat'))
        return

    with lock:
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

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, get_message(message.chat.id, 'help'))

@bot.message_handler(content_types=['text', 'photo', 'video', 'sticker', 'voice', 'document'])
def chat(message):
    user_id = message.chat.id
    partner_id = active_chats.get(user_id)

    if not partner_id or active_chats.get(partner_id) != user_id:
        bot.send_message(user_id, get_message(user_id, 'no_chat'))
        stop_chat(user_id)
        return

    try:
        if message.content_type == 'text':
            bot.send_message(partner_id, message.text)
        elif message.content_type == 'photo':
            bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption)
        elif message.content_type == 'video':
            bot.send_video(partner_id, message.video.file_id, caption=message.caption)
        elif message.content_type == 'sticker':
            bot.send_sticker(partner_id, message.sticker.file_id)
        elif message.content_type == 'voice':
            bot.send_voice(partner_id, message.voice.file_id)
        elif message.content_type == 'document':
            bot.send_document(partner_id, message.document.file_id, caption=message.caption)
        else:
            bot.send_message(user_id, "❗ Không hỗ trợ loại nội dung này.")
    except Exception as e:
        print(e)
        bot.send_message(user_id, get_message(user_id, 'no_chat'))
        stop_chat(user_id)

# Use long_polling() instead of infinity_polling()
bot.polling(none_stop=True, interval=0)
