import telebot from telebot import types import os from time import time

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

waiting_users = [] active_chats = {} waiting_start_time = {} user_languages = {}

messages = { 'vi': { 'start': "👋 Xin chào! Chọn chức năng bên dưới để bắt đầu.", 'in_chat': "❗ Bạn đang trong một cuộc trò chuyện rồi!\nDùng 🔄 Người khác để tìm người mới hoặc ❌ Dừng để dừng lại.", 'waiting': "⏳ Bạn đã vào hàng đợi. Đợi tí nhé...", 'already_waiting': "🕐 Bạn đang chờ sẵn rồi. Đợi hệ thống ghép cặp nhé!", 'no_chat': "⚠️ Bạn chưa có cuộc trò chuyện nào. Nhấn 🔍 Tìm người để bắt đầu tìm người nhé!", 'stop': "🚫 Bạn đã dừng trò chuyện.", 'search': "🔗 Đã tìm được người chat! Bắt đầu trò chuyện nào!", 'online': "👥 Hiện có {0} người đang chờ ghép.", 'help': """📖 Hướng dẫn:\n 🔍 Tìm người — tìm người trò chuyện\n🔄 Người khác — chuyển sang người khác\n❌ Dừng — dừng cuộc trò chuyện\n🌐 Ngôn ngữ — chuyển đổi ngôn ngữ""" }, 'en': { 'start': "👋 Hello! Choose an option below to get started.", 'in_chat': "❗ You're already in a chat!\nUse 🔄 Next to find a new person or ❌ Stop to end the conversation.", 'waiting': "⏳ You are in the queue. Please wait...", 'already_waiting': "🕐 You are already waiting. The system is matching you.", 'no_chat': "⚠️ You don't have a chat partner yet. Press 🔍 Search to start finding someone!", 'stop': "🚫 You have ended the conversation.", 'search': "🔗 You've been matched with a chat partner! Let's start chatting!", 'online': "👥 There are {0} people waiting to be matched.", 'help': """📖 Instructions:\n 🔍 Search — find someone to chat with\n🔄 Next — switch to another person\n❌ Stop — end the conversation\n🌐 Language — change language""" } }

def get_message(user_id, key, *args): language = user_languages.get(user_id, 'vi') return messages[language].get(key, '').format(*args)

def stop_chat(user_id, notify=True): if user_id in active_chats: partner_id = active_chats.pop(user_id) if partner_id in active_chats: active_chats.pop(partner_id) if notify: bot.send_message(partner_id, get_message(partner_id, 'stop')) elif user_id in waiting_users: waiting_users.remove(user_id)

if notify:
    bot.send_message(user_id, get_message(user_id, 'stop'))

def match_users(): while len(waiting_users) >= 2: user1 = waiting_users.pop(0) user2 = waiting_users.pop(0) active_chats[user1] = user2 active_chats[user2] = user1 bot.send_message(user1, get_message(user1, 'search')) bot.send_message(user2, get_message(user2, 'search'))

def is_in_chat(user_id): return user_id in active_chats

def set_main_menu(user_id, in_chat=False): markup = types.ReplyKeyboardMarkup(resize_keyboard=True) if in_chat: markup.add("🔄 Người khác", "❌ Dừng") else: markup.add("🔍 Tìm người", "🌐 Ngôn ngữ") bot.send_message(user_id, get_message(user_id, 'start'), reply_markup=markup)

@bot.message_handler(commands=['start']) def start(message): user_id = message.chat.id if user_id not in user_languages: markup = types.ReplyKeyboardMarkup(resize_keyboard=True) markup.add("🇻🇳 Tiếng Việt", "🇬🇧 English") bot.send_message(user_id, "👋 Chào bạn! Vui lòng chọn ngôn ngữ:", reply_markup=markup) else: set_main_menu(user_id) bot.send_message(user_id, get_message(user_id, 'help'))

@bot.message_handler(func=lambda m: m.text in ["🇻🇳 Tiếng Việt", "🇬🇧 English"]) def set_language(message): user_id = message.chat.id lang = 'vi' if "Tiếng Việt" in message.text else 'en' user_languages[user_id] = lang set_main_menu(user_id) bot.send_message(user_id, get_message(user_id, 'help'))

@bot.message_handler(func=lambda message: message.text == "🌐 Ngôn ngữ") def lang(message): user_id = message.chat.id markup = types.ReplyKeyboardMarkup(resize_keyboard=True) markup.add("🇻🇳 Tiếng Việt", "🇬🇧 English") bot.send_message(user_id, "🌐 Vui lòng chọn ngôn ngữ:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🔍 Tìm người") def search(message): user_id = message.chat.id if is_in_chat(user_id) or user_id in waiting_users: bot.send_message(user_id, get_message(user_id, 'in_chat')) return waiting_users.append(user_id) waiting_start_time[user_id] = time() bot.send_message(user_id, get_message(user_id, 'waiting')) match_users()

@bot.message_handler(func=lambda message: message.text == "🔄 Người khác") def next(message): user_id = message.chat.id stop_chat(user_id, notify=False) search(message)

@bot.message_handler(func=lambda message: message.text == "❌ Dừng") def stop(message): user_id = message.chat.id stop_chat(user_id) set_main_menu(user_id)

@bot.message_handler(func=lambda message: True) def handle_text(message): user_id = message.chat.id text = message.text if text in ["🔍 Tìm người", "🔄 Người khác", "❌ Dừng", "🌐 Ngôn ngữ"]: return if is_in_chat(user_id): partner_id = active_chats.get(user_id) bot.send_message(partner_id, text) else: bot.send_message(user_id, get_message(user_id, 'no_chat'))

bot.infinity_polling()
