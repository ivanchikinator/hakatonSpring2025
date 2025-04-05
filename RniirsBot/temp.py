import telebot
from constants import *
from contextlib import suppress
from sqlite3 import connect, IntegrityError
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

connection = connect('database.db', check_same_thread=False)

cursor = connection.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
id INT UNIQUE,
role TEXT,
notifications TEXT,
organisation TEXT,
science_themes TEXT,
data_relevances TEXT,
data_resources TEXT,
can_post BOOLEAN,
name TEXT varchar(20)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Organisations (
name TEXT varchar(20),
admin_id INT UNIQUE
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Posts (
text TEXT,
tags TEXT
)
''')
#7781448243:AAFlty1i8-xAgU7TTWVzC19FX4pxz3w-e3M
#7964476020:AAFzkUKqZLWIzYkatzaqG1attRUrSAk3rZY
API_TOKEN = "7964476020:AAFzkUKqZLWIzYkatzaqG1attRUrSAk3rZY"

bot = telebot.TeleBot(API_TOKEN)


def main_menu(message, new_draw: bool):
    keyboard = InlineKeyboardMarkup(row_width=5)
    with suppress(IntegrityError):
        cursor.execute(
            'INSERT INTO Users (id, role, notifications, organisation, science_themes, data_relevances, '
            'data_resources, can_post,name) VALUES (?, ? ,?, ?, ?, ?, ?, ?, ?)',
            (message.chat.id, 'ANONIM', '1', 'None',
             "БиологияМедицинаФизикаХимияМатематикаАгрокультураИнженерные наукиНауки о землеГуманитарные науки", 'THIS YEAR', 'ScienceDirect,наука.рф,'
                                                  'РНФ,Elibrary,IEEE,Scopus', 'FALSE', message.from_user.username))
        connection.commit()
    keyboard.add(InlineKeyboardButton(NEWS_BUTTON, callback_data='news'))
    cursor.execute('SELECT role FROM Users WHERE id = ?', (message.chat.id,))
    role = list(cursor.fetchall()[0])[0]
    cursor.execute('SELECT can_post FROM Users WHERE id = ?', (message.chat.id,))
    can_post = list(cursor.fetchall()[0])[0]
    if can_post == 'TRUE' and role != 'ANONIM':
        keyboard.add(InlineKeyboardButton(CREATE_POST, callback_data='create_post'))
    if role == 'ADMIN':
        keyboard.add(InlineKeyboardButton(YOUR_ORGANISATIONS, callback_data='organisation_members'))
        keyboard.add(InlineKeyboardButton('Удалить организацию', callback_data='delete_organisation'))
    if role == 'ANONIM':
        keyboard.add(InlineKeyboardButton(CREATE_ORGANISATION, callback_data='create_organisation'))
        keyboard.add(InlineKeyboardButton('Вступить в организацию', callback_data='enter_organisation'))
    if role == 'USER':
        keyboard.add(InlineKeyboardButton('Покинуть организацию', callback_data='leave_organisation'))
    keyboard.add(InlineKeyboardButton(OPTIONS_BUTTON, callback_data='settings'))
    if new_draw:
        with open('bot_logo.png', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=GREET_TEXT, parse_mode='HTML', reply_markup=keyboard)
    else:
        with open('bot_logo.png', 'rb') as photo:
            bot.edit_message_media(
                media=telebot.types.InputMediaPhoto(photo, caption=GREET_TEXT, parse_mode='HTML'),
                chat_id=message.chat.id,
                message_id=message.message_id,
                reply_markup=keyboard
            )


def draw_settings(message):
    keyboard = InlineKeyboardMarkup(row_width=5)
    keyboard.add(InlineKeyboardButton(INTERESTING_THEMES, callback_data='interesting_themes'))
    keyboard.add(InlineKeyboardButton(NOTIFICATIONS, callback_data='notifications'))
    keyboard.add(InlineKeyboardButton(RESOURCES, callback_data='resources'))
    keyboard.add(InlineKeyboardButton(RELEVANCES, callback_data='relevances'))
    keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_menu'))
    with open('bot_logo.png', "rb") as photo:
        bot.edit_message_media(
            media=telebot.types.InputMediaPhoto(photo, caption=SETTINGS_CATALOG, parse_mode='HTML'),
            chat_id=message.chat.id,
            message_id=message.message_id,
            reply_markup=keyboard
        )


@bot.message_handler(commands=['start'])
def start(message):
    main_menu(message, True)
@bot.callback_query_handler(func=lambda call: call.data == 'delete_organisation')
def delete_organisation(call : CallbackQuery):
    cursor.execute('SELECT name FROM Organisations WHERE admin_id = ?', (call.message.chat.id,))
    organisation = cursor.fetchone()[0]
    cursor.execute('SELECT id FROM Users WHERE organisation = ?', (organisation,))
    ids = cursor.fetchall()
    cursor.execute('SELECT admin_id FROM Organisations WHERE name = ?', (organisation,))
    admin_id = cursor.fetchone()[0]
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_menu'))
    for id in ids:
        cursor.execute('UPDATE Users SET organisation = ? WHERE id = ?', ('None', call.message.chat.id,))
        cursor.execute('UPDATE Users SET role = ? WHERE id = ?', ('ANONIM', call.message.chat.id,))
        with open('bot_logo.png', 'rb') as photo:
            bot.send_photo(id[0], photo, caption='Ваша организация расформированна', parse_mode='HTML', reply_markup=keyboard)
    cursor.execute('DELETE FROM Organisations WHERE name = ?', (organisation,))
    connection.commit()
@bot.callback_query_handler(func=lambda call: call.data == 'leave_organisation')
def leave_organisation(call : CallbackQuery):
    cursor.execute('UPDATE Users SET organisation = ? WHERE id = ?', ('None', call.message.chat.id,))
    cursor.execute('UPDATE Users SET role = ? WHERE id = ?', ('ANONIM', call.message.chat.id,))
    connection.commit()
    with open('bot_logo.png', "rb") as photo:
        bot.edit_message_media(
            media=telebot.types.InputMediaPhoto(photo, caption="Вы успешно покинули организацию"),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
@bot.callback_query_handler(func=lambda call: call.data == 'enter_organisation')
def enter_organisation(call: CallbackQuery):
    cursor.execute('SELECT role FROM Users WHERE id = ?', (call.message.chat.id,))
    role = cursor.fetchone()[0]
    if role == 'ANONIM':
        cursor.execute('SELECT * FROM Organisations' )
        organisations = cursor.fetchall()
        print(organisations)
        info = ''
        for organisation in organisations:
            info += organisation[0] +"\n"
        with open('bot_logo.png', "rb") as photo:
            bot.edit_message_media(
                media=telebot.types.InputMediaPhoto(photo, caption="Введите название организации"),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )
        bot.register_next_step_handler(call.message, choose_organisation)
def choose_organisation(message):
    print(message.text)
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_menu'))
    cursor.execute('SELECT name FROM Organisations WHERE name = ?', (message.text,))
    if cursor.fetchone() is not None:
        organisation = cursor.fetchone()[0]
        print(organisation)
        cursor.execute('UPDATE Users SET organisation = ? WHERE id = ?', (organisation, message.chat.id,))
        cursor.execute('UPDATE Users SET role = ? WHERE id = ?', ('USER', message.chat.id,))
        connection.commit()
        #cursor.execute('SELECT admin_id FROM Organisations WHERE name = ?', (organisation,))
        #admin_id = str(cursor.fetchone()[0])
        #bot.send_message(admin_id, f"Человек с {message.chat.id} вступил в организацию")
        with open('bot_logo.png', "rb") as photo:
            bot.edit_message_media(
                media=telebot.types.InputMediaPhoto(photo, caption="Вы вступили в организацию"),
                chat_id=message.chat.id,
                message_id=message.message_id,
                reply_markup=keyboard
            )
    else:
        with open('bot_logo.png', "rb") as photo:
            bot.edit_message_media(
                media=telebot.types.InputMediaPhoto(photo, caption="Организация не найдена"),
                chat_id=message.chat.id,
                message_id=message.message_id-1,
                reply_markup=keyboard
            )

@bot.callback_query_handler(func=lambda call: call.data == 'news')
def show_news(call: CallbackQuery):
    with open('bot_logo.png', "rb") as photo:
        bot.edit_message_media(
            media=telebot.types.InputMediaPhoto(photo, caption="Здесь будут последние новости!"),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )


@bot.callback_query_handler(func=lambda call: call.data == 'create_post')
def create_post(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_menu'))
    cursor.execute('SELECT role FROM Users WHERE id = ?', (call.message.chat.id,))
    role = str(cursor.fetchall()[0])
    with open('bot_logo.png', "rb") as photo:
        bot.edit_message_media(
            media=telebot.types.InputMediaPhoto(photo, caption=ENTER_POST_TEXT, parse_mode='HTML'),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )
    if role == 'ADMIN':
            bot.register_next_step_handler(call.message, post)
    else:
        bot.register_next_step_handler(call.message, implement_post)

def implement_post(message):
    cursor.execute('SELECT organisation FROM Users WHERE id = ?', (message.chat.id,))
    organisation = str(cursor.fetchall()[0])
    cursor.execute('SELECT admin_id FROM Organisations WHERE name = ?', (organisation,))
    admin_id = str(cursor.fetchall()[0])
    admin_keyboard = InlineKeyboardMarkup()
    admin_keyboard.add(InlineKeyboardButton(DECLINE_POST, callback_data='decline_post' + message.text),
                       InlineKeyboardButton(ACCEPT_POST, callback_data='accept_post'+ message.text))
    with open('bot_logo.png', 'rb') as photo:
        bot.send_photo(admin_id, photo, caption=message.text, parse_mode='HTML', reply_markup=admin_keyboard)
    bot.send_message(message.chat.id, "Пост отправлен на модерацию")

@bot.callback_query_handler(func=lambda call: call.data.startswith('accept_post') or call.data.startswith('decline_post'))
def answer_from_admin(call: CallbackQuery):
    if call.data.startswith('accept_post'):
        post(call.message)
    else:
        bot.reply_to(call.message, 'Пост отклонён')
def post(message):
    cursor.execute('SELECT organisation FROM Users WHERE id = ?', (message.chat.id,))
    organisation = str(cursor.fetchall()[0])
    cursor.execute('SELECT id FROM Users WHERE organisation = ?', (organisation,))
    ids = cursor.fetchall()
    if message.text.startswith('accept_post'):
        message.text.replace('accept_post', '')
    cursor.execute('INSERT INTO Posts (text, tags) VALUES (?, ?)', (message, ''))
    connection.commit()
    for id in ids:
        with open('bot_logo.png', 'rb') as photo:
            bot.send_photo(id[0], photo, caption=message, parse_mode='HTML')

# with open('bot_logo.png', "rb") as photo:
#     bot.edit_message_media(
#         media=telebot.types.InputMediaPhoto(photo, caption=call.message, parse_mode='HTML'),
#         chat_id=call.message.chat.id,
#         message_id=call.message.message_id,
#     )
@bot.callback_query_handler(func=lambda call: call.data == 'organisation_members' or call.data == 'back_to_organisations')
def organisation_members(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup()
    cursor.execute('SELECT name FROM Organisations WHERE admin_id = ?', (call.message.chat.id,))
    organisations = cursor.fetchall()

    if not organisations:
        caption = YOU_HAVENT_ORGANISATIONS
        keyboard.add(InlineKeyboardButton(CREATE_ORGANISATION, callback_data='create_organisation'))
    else:
        caption = YOUR_ORGANISATION + "\n"
        cursor.execute('SELECT organisation FROM Users WHERE id = ?', (call.message.chat.id,))
        organisation = cursor.fetchone()

        if organisation:
            organisation = organisation[0]
            cursor.execute('SELECT name FROM Users WHERE organisation = ?', (organisation,))
            users = cursor.fetchall()

            if users:
                for user in users:
                    caption += user[0] + "\n"
                keyboard.add(InlineKeyboardButton("Забанить/разбанить человека", callback_data='change_access'))
            else:
                caption = NOBODY_IN_ORGANISATION
        else:
            caption = NOBODY_IN_ORGANISATION

    keyboard.add(InlineKeyboardButton(ADD_ORGANISATION_MEMBER, callback_data='search_user'))
    keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_menu'))

    with open('bot_logo.png', "rb") as photo:
        bot.edit_message_media(
            media=telebot.types.InputMediaPhoto(photo, caption=caption, parse_mode='HTML'),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )


@bot.callback_query_handler(func=lambda call: call.data == 'search_user')
def search_user(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup()
    cursor.execute('SELECT name FROM Users WHERE organisation = ?', ('None',))
    user_names = list(cursor.fetchall())
    cursor.execute('SELECT id FROM Users WHERE organisation = ?', ('None',))
    user_id = list(cursor.fetchall()[0])
    for id in user_id:
        for name in user_names:
            keyboard.add(InlineKeyboardButton(name, callback_data='adduser_' + id))
    keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_my_organisation'))
    with open('bot_logo.png', "rb") as photo:
        bot.edit_message_media(
            media=telebot.types.InputMediaPhoto(photo, caption=ADD_USER, parse_mode='HTML'),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )


@bot.callback_query_handler(func=lambda call: call.data == 'change_access')
def change_access(call : CallbackQuery):
    bot.send_message(call.message.chat.id, "Введите имя пользователя")
    bot.register_next_step_handler(call.message, handle_user)


def handle_user(message):
    cursor.execute("SELECT name FROM Users WHERE name = ?", (message.text.strip(),))
    name = cursor.fetchall()[0]
    cursor.execute("SELECT can_post FROM Users WHERE name = ?", (message.text.strip(),))
    can_post = cursor.fetchall()[0]
    can_post = not can_post
    if name != "":
        cursor.execute('UPDATE Users SET can_post = ? WHERE name = ?', (str(can_post).upper(), name))
        if not can_post:
            bot.send_message(message.chat.id,
                             "Пользователь обновлён, до обновления пользователь имел доступ к созданию постов")
        else:
            bot.send_message(message.chat.id,
                             "Пользователь обновлён, до обновления пользователь не имел доступ к созданию постов")
        connection.commit()
    else:
        bot.send_message(message.chat.id,
                         "Пользователь не найдён")


@bot.callback_query_handler(func=lambda call: call.data == 'back_to_menu')
def create_organisation(call: CallbackQuery):
    main_menu(call.message, False)


@bot.callback_query_handler(func=lambda call: call.data == 'create_organisation')
def create_organisation(call: CallbackQuery):
    cursor.execute('SELECT role FROM Users WHERE id = ?', (call.message.chat.id,))
    role = cursor.fetchone()[0]
    if role == 'ANONIM':
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_menu'))
        with open('bot_logo.png', "rb") as photo:
            bot.edit_message_media(
                media=telebot.types.InputMediaPhoto(photo, caption=ENTER_NAME_OF_ORGANISATION, parse_mode='HTML'),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=keyboard
            )
            bot.register_next_step_handler(call.message, confirm_organisation)


def confirm_organisation(message):
    cursor.execute('INSERT INTO Organisations (name, admin_id) VALUES (?, ?)',
                   (message.text, message.chat.id,))
    cursor.execute('UPDATE Users set role = ?, organisation = ?, can_post = ? WHERE id = ?',
                   ('ADMIN', message.text, 'TRUE', message.chat.id,))
    connection.commit()
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(OK, callback_data='back_to_menu'))
    with open('bot_logo.png', 'rb') as photo:
        bot.send_photo(message.chat.id, photo, caption=ORGANISATION_IS_CREATED, parse_mode='HTML',
                       reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == 'back_to_creating_organisation')
def back_to_creating_organisation(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_organisations'))
    with open('bot_logo.png', "rb") as photo:
        bot.edit_message_media(
            media=telebot.types.InputMediaPhoto(photo, caption=ENTER_NAME_OF_ORGANISATION, parse_mode='HTML'),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )


@bot.callback_query_handler(func=lambda call: call.data == 'settings')
def settings(call: CallbackQuery):
    draw_settings(call.message)


@bot.callback_query_handler(func=lambda call: call.data == 'interesting_themes')
def interesting_themes(call: CallbackQuery):
    cursor.execute('SELECT science_themes FROM Users WHERE id = ?', (call.message.chat.id,))
    user_themes = list(cursor.fetchall())
    if 'Биология' in user_themes:
        biology = BIOLOGY + '✔'
    else:
        biology = BIOLOGY + '❌'
    if 'Медицина' in user_themes:
        medicine = MEDICINE + '✔'
    else:
        medicine = MEDICINE + '❌'
    if 'Физика' in user_themes:
        physics = PHYSICS + '✔'
    else:
        physics = PHYSICS + '❌'
    if 'Химия' in user_themes:
        chemistry = CHEMISTRY + '✔'
    else:
        chemistry = MEDICINE + '❌'
    if 'Математика' in user_themes:
        maths = MATHS + '✔'
    else:
        maths = MATHS + '❌'
    if 'Агрокультура' in user_themes:
        agro = AGRO + '✔'
    else:
        agro = AGRO + '❌'
    if 'Инженерные науки' in user_themes:
        engineer = ENGINEER + '✔'
    else:
        engineer = ENGINEER + '❌'
    if 'Науки о земле' in user_themes:
        earth_science = EARTH_SCIENCE + '✔'
    else:
        earth_science = EARTH_SCIENCE + '❌'
    if 'Гуманитарные науки' in user_themes:
        social_inst = SOCIAL_INST + '✔'
    else:
        social_inst = SOCIAL_INST + '❌'
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(biology, callback_data='switch_interesting_theme_biology'))
    keyboard.add(InlineKeyboardButton(medicine, callback_data='switch_interesting_theme_medicine'))
    keyboard.add(InlineKeyboardButton(physics, callback_data='switch_interesting_theme_physics'))
    keyboard.add(InlineKeyboardButton(chemistry, callback_data='switch_interesting_theme_chemistry'))
    keyboard.add(InlineKeyboardButton(maths, callback_data='switch_interesting_theme_maths'))
    keyboard.add(InlineKeyboardButton(agro, callback_data='switch_interesting_theme_agro'))
    keyboard.add(InlineKeyboardButton(engineer, callback_data='switch_interesting_theme_engineer'))
    keyboard.add(InlineKeyboardButton(earth_science, callback_data='switch_interesting_theme_earth_science'))
    keyboard.add(InlineKeyboardButton(social_inst, callback_data='switch_interesting_theme_social_inst'))
    keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_settings'))
    with open('bot_logo.png', "rb") as photo:
        bot.edit_message_media(
            media=telebot.types.InputMediaPhoto(photo, caption=SELECT_THEMES, parse_mode='HTML'),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith('switch_interesting_theme_'))
def switch_science(call: CallbackQuery):
    cursor.execute('SELECT science_themes FROM Users WHERE id = ?', (call.message.chat.id,))
    user_themes = list(cursor.fetchall()[0])[0]
    print(user_themes)
    theme = call.data.replace('switch_interesting_theme_', '')
    if theme == "physics_science":
        if 'Физические науки' in user_themes:
            user_themes = user_themes.replace('Физические науки', '')
        else:
            user_themes = user_themes + 'Физические науки'
    cursor.execute('INSERT INTO Users (science_themes) VALUES ')


@bot.callback_query_handler(func=lambda call: call.data == 'back_to_settings')
def back_to_settings(call: CallbackQuery):
    draw_settings(call.message)


@bot.callback_query_handler(func=lambda call: call.data == 'notifications')
def notifications(call: CallbackQuery):
    cursor.execute('SELECT notifications FROM Users WHERE id = ?', (call.message.chat.id,))
    check = list(cursor.fetchall()[0])[0]
    keyboard = InlineKeyboardMarkup()
    if check == "1":
        notification_caption = TURN_OFF_NOTIFICATIONS
        param = '0'
    else:
        notification_caption = TURN_ON_NOTIFICATIONS
        param = '1'
    keyboard.add(InlineKeyboardButton(notification_caption, callback_data='switch_notification_' + param))
    keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_settings'))
    with open('bot_logo.png', "rb") as photo:
        bot.edit_message_media(
            media=telebot.types.InputMediaPhoto(photo, caption=SELECT_VALUE, parse_mode='HTML'),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith('switch_notification_'))
def switch_notification(call: CallbackQuery):
    new_status = call.data.replace('switch_notification_', '')
    cursor.execute('UPDATE Users set notifications = ? WHERE id = ?',
                   (new_status, call.message.chat.id,))
    connection.commit()
    notifications(call)


bot.infinity_polling()