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
        'in_chat': "❗ Bạn đang trong một cuộc trò chuyện rồi!\nDùng nút bên dưới để tìm người mới hoặc dừng lại.",
        'waiting': "⏳ Bạn đã vào hàng đợi. Đợi tí nhé...",
        'already_waiting': "🕐 Bạn đang chờ sẵn rồi. Đợi hệ thống ghép cặp nhé!",
        'no_chat': "⚠️ Bạn chưa có người trò chuyện.\nNhấn 'Tìm người trò chuyện' để bắt đầu tìm người nhé!",
        'stop': "🚫 Bạn đã dừng trò chuyện.",
        'search': "🔗 Đã tìm được người chat! Bắt đầu trò chuyện nào!",
        'online': "👥 Hiện có {0} người đang chờ ghép.",
        'help': """📖 Hướng dẫn:
👉 Tìm người trò chuyện — Bắt đầu tìm người
👉 Tìm người khác — Chuyển người khác
👉 Dừng trò chuyện — Kết thúc cuộc trò chuyện
👉 Đổi ngôn ngữ — Chọn ngôn ngữ giao diện"""
    },
    'en': {
        'start': "👋 Hello! Choose an option below to get started.",
        'in_chat': "❗ You're already in a chat!\nUse the buttons below to find a new person or stop.",
        'waiting': "⏳ You are in the queue. Please wait...",
        'already_waiting': "🕐 You are already waiting. The system is matching you.",
        'no_chat': "⚠️ You don't have a chat partner yet.\nPress 'Find Chat Partner' to start finding someone!",
        'stop': "🚫 You have ended the conversation.",
        'search': "🔗 You've been matched with a chat partner! Let's start chatting!",
        'online': "👥 There are {0} people waiting to be matched.",
        'help': """📖 Instructions:
👉 Find Chat Partner — Start finding someone
👉 Find Another — Switch to another person
👉 Stop Chat — End the conversation
👉 Change Language — Change the interface language"""
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
        update_chat_markup(user1)
        update_chat_markup(user2)
        bot.send_message(user1, get_message(user1, 'search'))
        bot.send_message(user2, get_message(user2, 'search'))

def is_user_in_chat(user_id):
    return user_id in active_chats or user_id in waiting_users

def update_start_markup(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Tìm người trò chuyện", "Đổi ngôn ngữ")
    bot.send_message(user_id, get_message(user_id, 'start'), reply_markup=markup)
    bot.send_message(user_id, get_message(user_id, 'help'))

def update_chat_markup(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Tìm người khác", "Dừng trò chuyện")
    bot.send_message(user_id, get_message(user_id, 'in_chat'), reply_markup=markup)

def update_lang_markup(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Tiếng Việt", "English")
    bot.send_message(user_id, "🌐 Vui lòng chọn ngôn ngữ:", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    if user_id not in user_languages:
        update_lang_markup(user_id)
    else:
        update_start_markup(user_id)

@bot.message_handler(func=lambda message: message.text in ["Tiếng Việt", "English"])
def set_language(message):
    user_id = message.chat.id
    user_languages[user_id] = 'vi' if message.text == "Tiếng Việt" else 'en'
    update_start_markup(user_id)

@bot.message_handler(func=lambda message: message.text in ["Tìm người trò chuyện"])
def search_btn(message):
    user_id = message.chat.id
    if is_user_in_chat(user_id):
        bot.send_message(user_id, get_message(user_id, 'in_chat'))
        return
    waiting_users.append(user_id)
    waiting_start_time[user_id] = time()
    bot.send_message(user_id, get_message(user_id, 'waiting'))
    match_users()

@bot.message_handler(func=lambda message: message.text in ["Tìm người khác"])
def next_btn(message):
    user_id = message.chat.id
    stop_chat(user_id, notify=False)
    waiting_users.append(user_id)
    waiting_start_time[user_id] = time()
    bot.send_message(user_id, get_message(user_id, 'waiting'))
    match_users()

@bot.message_handler(func=lambda message: message.text in ["Dừng trò chuyện"])
def stop_btn(message):
    user_id = message.chat.id
    stop_chat(user_id)
    update_start_markup(user_id)

@bot.message_handler(func=lambda message: message.text in ["Đổi ngôn ngữ"])
def lang_btn(message):
    user_id = message.chat.id
    update_lang_markup(user_id)

@bot.message_handler(content_types=['text', 'photo', 'video', 'sticker', 'voice', 'document'])
def chat(message):
    user_id = message.chat.id
    partner_id = active_chats.get(user_id)
    if not partner_id or active_chats.get(partner_id) != user_id:
        bot.send_message(user_id, get_message(user_id, 'no_chat'))
        stop_chat(user_id)
        update_start_markup(user_id)
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
        update_start_markup(user_id)

bot.infinity_polling()
