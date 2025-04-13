import telebot
from telebot import types
from config import TOKEN

bot = telebot.TeleBot(TOKEN)

waiting_users = []
active_chats = {}

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

def match_users():
    while len(waiting_users) >= 2:
        user1 = waiting_users.pop(0)
        user2 = waiting_users.pop(0)
        active_chats[user1] = user2
        active_chats[user2] = user1
        bot.send_message(user1, "🔗 Đã tìm được người chat! Bắt đầu trò chuyện nào!")
        bot.send_message(user2, "🔗 Đã tìm được người chat! Bắt đầu trò chuyện nào!")

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('/search', '/next', '/stop')
    bot.send_message(message.chat.id, "👋 Xin chào! Chọn chức năng bên dưới để bắt đầu.", reply_markup=markup)

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
    bot.send_message(message.chat.id, f"👥 Hiện có {len(waiting_users)} người đang chờ ghép.")

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """📖 Hướng dẫn:
👉 /search — Tìm người để trò chuyện
👉 /next — Chuyển người khác
👉 /stop — Dừng trò chuyện
👉 /online — Xem số người đang chờ"""
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(content_types=['text', 'photo', 'video', 'sticker', 'voice', 'document'])
def chat(message):
    user_id = message.chat.id
    partner_id = active_chats.get(user_id)

    if not partner_id or active_chats.get(partner_id) != user_id:
        bot.send_message(user_id, "⚠️ Bạn chưa có người trò chuyện.\nNhấn /search để bắt đầu tìm người nhé!")
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
    except Exception:
        bot.send_message(user_id, "❗ Gửi tin nhắn thất bại. Có thể người kia đã rời khỏi.")
        stop_chat(user_id)

bot.infinity_polling()
