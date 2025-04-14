import telebot
from telebot import types
import os

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

waiting_users = []
active_chats = {}
user_languages = {}

messages = {
    'vi': {
        'start': "👋 Xin chào! Chọn chức năng bên dưới để bắt đầu.",
        'in_chat': "❗ Bạn đang trong một cuộc trò chuyện rồi!",
        'waiting': "⏳ Bạn đã vào hàng đợi. Đợi tí nhé...",
        'no_chat': "⚠️ Bạn chưa có cuộc trò chuyện nào.\nNhấn /search để tìm người nhé!",
        'stop': "🚫 Bạn đã dừng trò chuyện.",
        'search': "🔗 Đã tìm được người chat! Bắt đầu trò chuyện!",
        'online': "👥 Hiện có {0} người đang chờ ghép.",
        'help': """📖 Hướng dẫn:
👉 /search - Tìm người trò chuyện
👉 /next - Chuyển người khác
👉 /stop - Dừng trò chuyện
👉 /online - Xem số người chờ
👉 /lang - Đổi ngôn ngữ"""
    },
    'en': {
        'start': "👋 Hello! Choose an option below to get started.",
        'in_chat': "❗ You're already in a chat!",
        'waiting': "⏳ You are in the queue. Please wait...",
        'no_chat': "⚠️ You don't have a chat yet.\nType /search to find someone!",
        'stop': "🚫 You have ended the conversation.",
        'search': "🔗 You've been matched! Start chatting!",
        'online': "👥 {0} users are waiting.",
        'help': """📖 Instructions:
👉 /search - Find someone to chat
👉 /next - Switch to another
👉 /stop - End the conversation
👉 /online - See online users
👉 /lang - Change language"""
    }
}

def get_message(user_id, key, *args):
    lang = user_languages.get(user_id, 'vi')
    return messages[lang][key].format(*args)

def set_main_menu(user_id, in_chat=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if in_chat:
        markup.add("Chuyển người khác", "Dừng trò chuyện")
    else:
        markup.add("Tìm người trò chuyện", "Đổi ngôn ngữ")
    bot.send_message(user_id, get_message(user_id, 'start'), reply_markup=markup)

def stop_chat(user_id):
    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        if partner_id in active_chats:
            active_chats.pop(partner_id)
            bot.send_message(partner_id, get_message(partner_id, 'stop'))
        bot.send_message(user_id, get_message(user_id, 'stop'))

def match_users():
    while len(waiting_users) >= 2:
        user1 = waiting_users.pop(0)
        user2 = waiting_users.pop(0)
        active_chats[user1] = user2
        active_chats[user2] = user1
        set_main_menu(user1, True)
        set_main_menu(user2, True)
        bot.send_message(user1, get_message(user1, 'search'))
        bot.send_message(user2, get_message(user2, 'search'))

def is_in_chat(user_id):
    return user_id in active_chats

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    if user_id not in user_languages:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Tiếng Việt", "English")
        bot.send_message(user_id, "👋 Chọn ngôn ngữ:", reply_markup=markup)
    else:
        set_main_menu(user_id)
        bot.send_message(user_id, get_message(user_id, 'help'))

@bot.message_handler(commands=['search'])
def search(message):
    user_id = message.chat.id
    if is_in_chat(user_id):
        bot.send_message(user_id, get_message(user_id, 'in_chat'))
        return
    if user_id in waiting_users:
        bot.send_message(user_id, get_message(user_id, 'waiting'))
        return
    waiting_users.append(user_id)
    bot.send_message(user_id, get_message(user_id, 'waiting'))
    match_users()

@bot.message_handler(commands=['next'])
def next(message):
    stop_chat(message.chat.id)
    search(message)

@bot.message_handler(commands=['stop'])
def stop(message):
    stop_chat(message.chat.id)
    set_main_menu(message.chat.id)

@bot.message_handler(commands=['online'])
def online(message):
    bot.send_message(message.chat.id, get_message(message.chat.id, 'online', len(waiting_users)))

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, get_message(message.chat.id, 'help'))

@bot.message_handler(commands=['lang'])
def lang(message):
    user_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Tiếng Việt", "English")
    bot.send_message(user_id, "🌐 Vui lòng chọn ngôn ngữ:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["Tiếng Việt", "English"])
def set_language(message):
    user_id = message.chat.id
    lang = 'vi' if message.text == "Tiếng Việt" else 'en'
    user_languages[user_id] = lang
    set_main_menu(user_id)
    bot.send_message(user_id, get_message(user_id, 'help'))

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.chat.id
    text = message.text

    if text == "Tìm người trò chuyện":
        search(message)
    elif text == "Chuyển người khác":
        next(message)
    elif text == "Dừng trò chuyện":
        stop(message)
    elif text == "Đổi ngôn ngữ":
        lang(message)
    else:
        if is_in_chat(user_id):
            partner_id = active_chats[user_id]
            bot.send_message(partner_id, text)
        else:
            bot.send_message(user_id, get_message(user_id, 'no_chat'))

bot.infinity_polling()
