import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# تم تحديث التوكن الجديد الخاص بك هنا
API_TOKEN = '8820376264:AAFQpf1DTwbgZZJnJPQE0EL4wwnk1ErhjrA'
bot = telebot.TeleBot(API_TOKEN)

# معرف حسابك كآدمن للبوت
ADMIN_ID = 1979950905

# قاعدة بيانات مؤقتة لحفظ البيانات (أقسام، شاليهات، صور)
DATA = {}

# لحفظ حالة الآدمن أثناء الإضافة
ADMIN_STATE = {}

def get_main_keyboard(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    for gov in DATA.keys():
        markup.add(InlineKeyboardButton(gov, callback_data=f"gov_{gov}"))
    
    if user_id == ADMIN_ID:
        markup.add(InlineKeyboardButton("➕ إضافة محافظة جديدة", callback_data="admin_add_gov"))
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    ADMIN_STATE.pop(message.chat.id, None)
    text = "💡 أهلاً بك في بوت الحجوزات والشاليهات!\n\nالرجاء اختيار المحافظة من الأزرار أدناه:"
    if message.chat.id == ADMIN_ID:
        text += "\n\n⚙️ أهلاً بك يا آدمن، يمكنك التحكم بالأزرار والإضافة مباشرة."
    
    bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard(message.chat.id))

@bot.callback_query_handler(func=lambda call: True)
def handle_clicks(call):
    chat_id = call.message.chat.id
    data = call.data

    # --- لوحة التحكم (الآدمن) ---
    if data == "admin_add_gov" and chat_id == ADMIN_ID:
        ADMIN_STATE[chat_id] = {'action': 'waiting_for_gov_name'}
        bot.send_message(chat_id, "✍️ أرسل الآن اسم المحافظة الجديدة (مثال: النجف الأشرف):")
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_add_dist_") and chat_id == ADMIN_ID:
        gov = data.replace("admin_add_dist_", "")
        ADMIN_STATE[chat_id] = {'action': 'waiting_for_dist_name', 'gov': gov}
        bot.send_message(chat_id, f"✍️ أرسل اسم القضاء الجديد التابع لـ ({gov}) (مثال: الكوفة):")
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_add_chalet_") and chat_id == ADMIN_ID:
        parts = data.replace("admin_add_chalet_", "").split(";")
        gov, dist = parts[0], parts[1]
        ADMIN_STATE[chat_id] = {'action': 'waiting_for_chalet_photo', 'gov': gov, 'dist': dist}
        bot.send_message(chat_id, f"📸 أرسل الآن صورة الشاليه الجديد في {dist}:")
        bot.answer_callback_query(call.id)
        return

    if data.startswith("admin_del_gov_") and chat_id == ADMIN_ID:
        gov = data.replace("admin_del_gov_", "")
        DATA.pop(gov, None)
        bot.send_message(chat_id, f"🗑️ تم حذف محافظة {gov} بالكامل.")
        bot.edit_message_text("الرجاء اختيار المحافظة من الأزرار أدناه:", chat_id, call.message.message_id, reply_markup=get_main_keyboard(chat_id))
        return

    # --- تصفح المستخدمين ---
    if data.startswith("gov_"):
        gov = data.replace("gov_", "")
        markup = InlineKeyboardMarkup(row_width=2)
        if gov in DATA:
            for dist in DATA[gov].keys():
                markup.add(InlineKeyboardButton(dist, callback_data=f"dist_{gov};{dist}"))
        
        if chat_id == ADMIN_ID:
            markup.add(InlineKeyboardButton("➕ إضافة قضاء جديد", callback_data=f"admin_add_dist_{gov}"))
            markup.add(InlineKeyboardButton("🗑️ حذف هذه المحافظة", callback_data=f"admin_del_gov_{gov}"))
        markup.add(InlineKeyboardButton("⬅️ عودة للمحافظات", callback_data="back_to_main"))
        
        bot.edit_message_text(f"📍 أقضية محافظة ({gov}):", chat_id, call.message.message_id, reply_markup=markup)

    elif data.startswith("dist_"):
        parts = data.replace("dist_", "").split(";")
        gov, dist = parts[0], parts[1]
        markup = InlineKeyboardMarkup(row_width=1)
        
        if gov in DATA and dist in DATA[gov]:
            for i, chalet in enumerate(DATA[gov][dist]):
                markup.add(InlineKeyboardButton(chalet['title'], callback_data=f"view_{gov};{dist};{i}"))
        
        if chat_id == ADMIN_ID:
            markup.add(InlineKeyboardButton("➕ إضافة شاليه جديد هنا", callback_data=f"admin_add_chalet_{gov};{dist}"))
        markup.add(InlineKeyboardButton("⬅️ عودة للأقضية", callback_data=f"gov_{gov}"))
        
        bot.edit_message_text(f"🏡 الشاليهات المتوفرة في {dist}:", chat_id, call.message.message_id, reply_markup=markup)

    elif data.startswith("view_"):
        parts = data.replace("view_", "").split(";")
        gov, dist, index = parts[0], parts[1], int(parts[2])
        chalet = DATA[gov][dist][index]
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬅️ عودة للقائمة", callback_data=f"dist_{gov};{parts[1]}"))
        
        bot.delete_message(chat_id, call.message.message_id)
        bot.send_photo(chat_id, chalet['photo'], caption=f"🌟 *{chalet['title']}*\n\n📝 *التفاصيل:*\n{chalet['desc']}", parse_mode="Markdown", reply_markup=markup)

    elif data == "back_to_main":
        bot.edit_message_text("الرجاء اختيار المحافظة من الأزرار أدناه:", chat_id, call.message.message_id, reply_markup=get_main_keyboard(chat_id))

    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['text', 'photo'])
def handle_admin_inputs(message):
    chat_id = message.chat.id
    if chat_id != ADMIN_ID or chat_id not in ADMIN_STATE:
        return

    state = ADMIN_STATE[chat_id]

    if state['action'] == 'waiting_for_gov_name' and message.text:
        gov_name = message.text
        if gov_name not in DATA:
            DATA[gov_name] = {}
        bot.send_message(chat_id, f"✅ تم إضافة محافظة ({gov_name}) بنجاح!\nاضغط /start لمشاهدتها.")
        ADMIN_STATE.pop(chat_id)

    elif state['action'] == 'waiting_for_dist_name' and message.text:
        dist_name = message.text
        gov = state['gov']
        if dist_name not in DATA[gov]:
            DATA[gov][dist_name] = []
        bot.send_message(chat_id, f"✅ تم إضافة قضاء ({dist_name}) إلى {gov}!\nاضغط /start للمعاينة.")
        ADMIN_STATE.pop(chat_id)

    elif state['action'] == 'waiting_for_chalet_photo' and message.photo:
        photo_id = message.photo[-1].file_id
        ADMIN_STATE[chat_id] = {
            'action': 'waiting_for_chalet_title',
            'gov': state['gov'],
            'dist': state['dist'],
            'photo': photo_id
        }
        bot.send_message(chat_id, "✍️ الآن أرسل اسم الشاليه (مثال: شاليه الكوفة الملكي):")

    elif state['action'] == 'waiting_for_chalet_title' and message.text:
        title = message.text
        ADMIN_STATE[chat_id] = {
            'action': 'waiting_for_chalet_desc',
            'gov': state['gov'],
            'dist': state['dist'],
            'photo': state['photo'],
            'title': title
        }
        bot.send_message(chat_id, "✍️ أخيراً، أرسل تفاصيل الشاليه (الأسعار، الخدمات، الموقِع، إلخ):")

    elif state['action'] == 'waiting_for_chalet_desc' and message.text:
        desc = message.text
        gov, dist = state['gov'], state['dist']
        
        DATA[gov][dist].append({
            'title': state['title'],
            'photo': state['photo'],
            'desc': desc
        })
        bot.send_message(chat_id, f"🎉 ممتاز! تم حفظ شاليه ({state['title']}) بنجاح داخل قسم {dist}.\nاضغط /start لتجربته بنفسك.")
        ADMIN_STATE.pop(chat_id)

# تشغيل البوت
print("البوت يعمل الآن بنجاح بالتوكن الجديد...")
bot.polling(none_stop=True)
