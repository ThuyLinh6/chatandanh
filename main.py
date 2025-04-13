import telebot
from telebot import types

TOKEN = '7951367517:AAGHuBzbp7mSULjmjtacQieNVyQ2jhYoJic'
bot = telebot.TeleBot(TOKEN)

waiting_users = []
active_chats = {}

# Hàm dừng trò chuyện an toàn
def stop_chat(user_id, notify=True):
    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        if partner_id in active_chats:
            active_chats.pop(partner_id)
            if notify:
                bot.send_message(partner_id, "❌ Người bên kia đã dừng trò chuyện.\nNhấn /search để tìm người mới nhé!")
    elif user_id in waiting_users:
        waiting_users.remove(user_id)
    
    if notify:
        bot.send_message(user_id, "🚫 Bạn đã dừng trò chuyện.")

# Ghép người dùng trong hàng đợi
def match_users():
    while len(waiting_users) >= 2:
        user1 = waiting_users.pop(0)
        user2 = waiting_users.pop(0)
        active_chats[user1] = user2
        active_chats[user2] = user1
        bot.send_message(user1, "🔗 Đã tìm được người chat! Bắt đầu trò chuyện nào!")
        bot.send_message(user2, "🔗 Đã tìm được người chat! Bắt đầu trò chuyện nào!")

# Lệnh /start
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('/search', '/next', '/stop')
    bot.send_message(message.chat.id, "👋 Xin chào! Chọn chức năng bên dưới để bắt đầu.", reply_markup=markup)

# Lệnh /search
@bot.message_handler(commands=['search'])
def search(message):
    user_id = message.chat.id
    if user_id in active_chats:
        bot.send_message(user_id, "❗ Bạn đang trong một cuộc trò chuyện rồi!\nDùng /next để tìm người mới hoặc /stop để dừng lại.")
    elif user_id not in waiting_users:
        waiting_users.append(user_id)
        bot.send_message(user_id, "⏳ Bạn đã vào hàng đợi. Đợi tí nhé...")
        match_users()
    else:
        bot.send_message(user_id, "🕐 Bạn đang chờ sẵn rồi. Đợi hệ thống ghép cặp nhé!")

# Lệnh /next
@bot.message_handler(commands=['next'])
def next(message):
    user_id = message.chat.id
    stop_chat(user_id, notify=False)
    search(message)

# Lệnh /stop
@bot.message_handler(commands=['stop'])
def stop(message):
    user_id = message.chat.id
    stop_chat(user_id)

# Xử lý tin nhắn thường
@bot.message_handler(func=lambda message: True)
def chat(message):
    user_id = message.chat.id
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        if partner_id in active_chats:
            bot.send_message(partner_id, message.text)
        else:
            bot.send_message(user_id, "❌ Người bên kia đã thoát. Nhấn /search để tìm người mới!")
            stop_chat(user_id)
    else:
        bot.send_message(user_id, "⚠️ Bạn chưa có người trò chuyện.\nNhấn /search để bắt đầu tìm người nhé!")

bot.infinity_polling()
