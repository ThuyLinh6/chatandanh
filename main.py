import telebot
from telebot import types
import os

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

user_languages = {}
rooms = {}  # { room_id: { 'users': [user1, user2, ...], 'done_users': [user1, user2, ...], 'nicknames': ['Ẩn danh 1', 'Ẩn danh 2', ...] } }
user_rooms = {}  # { user_id: room_id }

messages = {
    'vi': {
        'start': "👋 Xin chào! Chọn chức năng bên dưới để bắt đầu.",
        'help': """📖 Hướng dẫn:
👉 /room — Vào phòng trò chuyện
👉 /leaveroom — Rời phòng
👉 /lang — Chuyển ngôn ngữ""",
        'joined_room': "✅ Bạn đã tham gia phòng số {0} với tên ẩn danh: {1}.",
        'left_room': "🚪 Bạn đã rời phòng.",
        'not_in_room': "❗ Bạn không ở phòng nào.",
        'room_broadcast': "📣 Tin nhắn từ {0}: {1}",
    },
    'en': {
        'start': "👋 Hello! Choose an option below to get started.",
        'help': """📖 Instructions:
👉 /room — Join the chat room
👉 /leaveroom — Leave the room
👉 /lang — Change language""",
        'joined_room': "✅ You've joined room #{0} with the nickname: {1}.",
        'left_room': "🚪 You've left the room.",
        'not_in_room': "❗ You're not in any room.",
        'room_broadcast': "📣 Message from {0}: {1}",
    }
}

def get_message(user_id, key, *args):
    lang = user_languages.get(user_id, 'vi')
    return messages[lang][key].format(*args)

def main_menu(user_id):
    lang = user_languages.get(user_id, 'vi')
    room_label = "Phòng trò chuyện" if lang == 'vi' else "Chat room"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"👥 {room_label}", callback_data="room"))
    markup.add(types.InlineKeyboardButton("🌍 Ngôn ngữ", callback_data="lang"))
    bot.send_message(user_id, get_message(user_id, 'start'), reply_markup=markup)

def get_available_room():
    for room_id, room_data in rooms.items():
        if len(room_data['users']) < 4:
            return room_id
    new_room_id = len(rooms) + 1
    rooms[new_room_id] = {'users': [], 'done_users': [], 'nicknames': []}
    return new_room_id

def assign_nickname(room_id, user_id):
    room_data = rooms[room_id]
    nickname = f"Ẩn danh {len(room_data['nicknames']) + 1}"
    room_data['nicknames'].append(nickname)
    return nickname

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    if user_id not in user_languages:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Tiếng Việt", "English")
        bot.send_message(user_id, get_message(user_id, 'start'), reply_markup=markup)
    else:
        main_menu(user_id)

@bot.message_handler(commands=['room'])
def join_room(message):
    user_id = message.chat.id
    if user_id in user_rooms:
        bot.send_message(user_id, "❗ Bạn đã tham gia phòng rồi.")
        return

    room_id = get_available_room()
    nickname = assign_nickname(room_id, user_id)
    rooms[room_id]['users'].append(user_id)
    user_rooms[user_id] = room_id

    bot.send_message(user_id, get_message(user_id, 'joined_room', room_id, nickname))
    bot.send_message(user_id, get_message(user_id, 'help'))

@bot.message_handler(commands=['leaveroom'])
def leave_room(message):
    user_id = message.chat.id
    if user_id not in user_rooms:
        bot.send_message(user_id, get_message(user_id, 'not_in_room'))
        return

    room_id = user_rooms.pop(user_id)
    rooms[room_id]['users'].remove(user_id)

    # Remove nickname
    nickname_index = rooms[room_id]['users'].index(user_id)
    rooms[room_id]['nicknames'].pop(nickname_index)

    bot.send_message(user_id, get_message(user_id, 'left_room'))

@bot.message_handler(content_types=['text'])
def handle_message(message):
    user_id = message.chat.id
    if user_id not in user_rooms:
        bot.send_message(user_id, get_message(user_id, 'not_in_room'))
        return

    room_id = user_rooms[user_id]
    nickname = rooms[room_id]['nicknames'][rooms[room_id]['users'].index(user_id)]
    text = message.text

    # Broadcast message to the room
    for user in rooms[room_id]['users']:
        bot.send_message(user, get_message(user, 'room_broadcast', nickname, text))

bot.infinity_polling()
