import telebot
from telebot import types

TOKEN = '7951367517:AAGHuBzbp7mSULjmjtacQieNVyQ2jhYoJic'
bot = telebot.TeleBot(TOKEN)

waiting_users = []
active_chats = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('/search', '/next', '/stop')
    bot.send_message(message.chat.id, "Xin chào! Chọn chức năng bên dưới để bắt đầu.", reply_markup=markup)

@bot.message_handler(commands=['search'])
def search(message):
    user_id = message.chat.id
    if user_id not in waiting_users:
        waiting_users.append(user_id)
        bot.send_message(user_id, "Bạn đã vào hàng đợi. Đợi tí nhé...")
        match_users()

def match_users():
    if len(waiting_users) >= 2:
        user1 = waiting_users.pop(0)
        user2 = waiting_users.pop(0)
        active_chats[user1] = user2
        active_chats[user2] = user1
        bot.send_message(user1, "Đã tìm được người chat! Gửi tin nhắn thôi!")
        bot.send_message(user2, "Đã tìm được người chat! Gửi tin nhắn thôi!")

@bot.message_handler(commands=['next'])
def next(message):
    stop(message)
    search(message)

@bot.message_handler(commands=['stop'])
def stop(message):
    user_id = message.chat.id
    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id, None)
        bot.send_message(partner_id, "Người bên kia đã dừng trò chuyện.Nhắn /search để tìm kiếm người mới nhé!")
    elif user_id in waiting_users:
        waiting_users.remove(user_id)
    bot.send_message(user_id, "Bạn đã dừng trò chuyện.")

@bot.message_handler(func=lambda message: True)
def chat(message):
    user_id = message.chat.id
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        bot.send_message(partner_id, message.text)
    else:
        bot.send_message(user_id, "Bạn chưa có người trò chuyện. Nhấn /search để tìm người nhé!")

bot.infinity_polling()
