import re
import sqlite3

import telebot

import Parser
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
#await asyncio.sleep(3600)
        #cursor.execute('SELECT admin_id FROM Organisations WHERE name = ?', (organisation,))
        #admin_id = str(cursor.fetchone()[0])
        #bot.send_message(admin_id, f"Человек с {message.chat.id} вступил в организацию")
#7781448243:AAFlty1i8-xAgU7TTWVzC19FX4pxz3w-e3M
#7964476020:AAFzkUKqZLWIzYkatzaqG1attRUrSAk3rZY
API_TOKEN = "7964476020:AAFzkUKqZLWIzYkatzaqG1attRUrSAk3rZY"

bot = telebot.TeleBot(API_TOKEN)


def main_menu(message, new_draw: bool):
    keyboard = InlineKeyboardMarkup(row_width=5)
    with suppress(IntegrityError):
        cursor.execute(
            'INSERT INTO Users (id, role, notifications, organisation, science_themes, data_relevances, '
            'can_post,name) VALUES (?, ? ,?, ?, ?, ?, ?, ?)',
            (message.chat.id, 'ANONIM', '1', 'None',
             "Математика", 'THIS YEAR', 'FALSE', message.from_user.username))
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
    keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_menu'))
    with open('bot_logo.png', "rb") as photo:
        bot.edit_message_media(
            media=telebot.types.InputMediaPhoto(photo, caption=SETTINGS_CATALOG, parse_mode='HTML'),
            chat_id=message.chat.id,
            message_id=message.message_id,
            reply_markup=keyboard
        )

def split_by_capital_letters_to_array(text):
    return re.findall('[А-ЯЁ][^А-ЯЁ]*', text)

@bot.callback_query_handler(func=lambda call: call.data == 'Получить новость')
def read_news_by_topic(call : CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("Получить новости", callback_data='Получить новость'))
    keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_menu'))
    result = ''
    try:
        conn = sqlite3.connect("news_titles.db")
        cursor2 = conn.cursor()
        cursor.execute("SELECT science_themes FROM Users WHERE id=?", (call.message.chat.id,))  # Используем параметризованный запрос
        themes = split_by_capital_letters_to_array(cursor.fetchone()[0])

        for theme in themes:
            cursor2.execute("SELECT * FROM news WHERE topic=?", (theme,)) # Используем параметризованный запрос
            print(cursor2.fetchall())
            rows = cursor2.fetchall()[0]
            if rows:
                topic, title, link, intro, date = rows
                result += title + "\n"
                result += link + "\n"
                result += intro + "\n"
                result += date + "\n"
                bot.send_message(call.message.chat.id, text=result)
                result = ""
            else:
                result = f"Новостей по теме не найдено."

    except sqlite3.Error as e:
        print(f"Ошибка при работе с базой данных: {e}")
    finally:
        if conn:
            conn.close()
    with open('bot_logo.png', 'rb') as photo:
        bot.send_photo(call.message.chat.id, photo, parse_mode='HTML', reply_markup=keyboard)


@bot.message_handler(commands=['start'])
def start(message):
    main_menu(message, True)
@bot.callback_query_handler(func=lambda call: call.data == 'delete_organisation')
def delete_organisation(call : CallbackQuery):
    cursor.execute('SELECT name FROM Organisations WHERE admin_id = ?', (call.message.chat.id,))
    organisation = cursor.fetchone()[0]
    cursor.execute('SELECT id FROM Users WHERE organisation = ?', (organisation,))
    ids = cursor.fetchall()
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_menu'))
    for id in ids:
        cursor.execute('UPDATE Users SET organisation = ? WHERE id = ?', ('None', id[0],))
        cursor.execute('UPDATE Users SET role = ? WHERE id = ?', ('ANONIM', id[0],))
        with open('bot_logo.png', 'rb') as photo:
            bot.send_photo(id[0], photo, caption='Ваша организация расформированна', parse_mode='HTML', reply_markup=keyboard)
    cursor.execute('DELETE FROM Organisations WHERE name = ?', (organisation,))
    connection.commit()
@bot.callback_query_handler(func=lambda call: call.data == 'leave_organisation')
def leave_organisation(call : CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_menu'))
    cursor.execute('SELECT role FROM Users WHERE id = ?', (call.message.chat.id,))
    role = cursor.fetchone()[0]
    if role == 'USER':
        cursor.execute('UPDATE Users SET organisation = ? WHERE id = ?', ('None', call.message.chat.id,))
        cursor.execute('UPDATE Users SET role = ? WHERE id = ?', ('ANONIM', call.message.chat.id,))
        connection.commit()
        with open('bot_logo.png', "rb") as photo:
            bot.edit_message_media(
                media=telebot.types.InputMediaPhoto(photo, caption="Вы успешно покинули организацию"),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=keyboard
            )
@bot.callback_query_handler(func=lambda call: call.data == 'enter_organisation')
def enter_organisation(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_menu'))
    cursor.execute('SELECT role FROM Users WHERE id = ?', (call.message.chat.id,))
    role = cursor.fetchone()[0]
    if role == 'ANONIM':
        cursor.execute('SELECT * FROM Organisations' )
        organisations = cursor.fetchall()
        print(organisations)
        info = ''
        if len(organisations) > 0:
            for organisation in organisations:
                info += organisation[0] +"\n"
            with open('bot_logo.png', "rb") as photo:
                bot.edit_message_media(
                    media=telebot.types.InputMediaPhoto(photo, caption="Введите название организации: Доступные - " + info),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=keyboard
                )
            bot.register_next_step_handler(call.message, choose_organisation)
        else:
            with open('bot_logo.png', "rb") as photo:
                bot.edit_message_media(
                    media=telebot.types.InputMediaPhoto(photo, caption="Нет доступных организаций"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=keyboard
                )
def choose_organisation(message):
    print(message.text)
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_menu'))
    cursor.execute('SELECT name FROM Organisations WHERE name = ?', (message.text,))
    organisation = cursor.fetchone()[0]
    print(organisation)
    cursor.execute('UPDATE Users SET organisation = ? WHERE id = ?', (organisation, message.chat.id,))
    cursor.execute('UPDATE Users SET role = ? WHERE id = ?', ('USER', message.chat.id,))
    connection.commit()
    with open('bot_logo.png', "rb") as photo:
        with open('bot_logo.png', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption="Вы вступили в организацию", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == 'news')
def show_news(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_menu'))
    keyboard.add(InlineKeyboardButton("Получить новости", callback_data='Получить новость'))
    with open('bot_logo.png', "rb") as photo:
        bot.edit_message_media(
            media=telebot.types.InputMediaPhoto(photo, caption="Здесь будут последние новости!"),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard
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
    cursor.execute('SELECT name FROM Organisations WHERE admin_id = ?', (call.message.chat.id,))
    keyboard = InlineKeyboardMarkup()
    if cursor.fetchone() is None:
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

    keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_menu'))

    with open('bot_logo.png', "rb") as photo:
        bot.edit_message_media(
            media=telebot.types.InputMediaPhoto(photo, caption=caption, parse_mode='HTML'),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )

@bot.callback_query_handler(func=lambda call: call.data == 'change_access')
def change_access(call : CallbackQuery):
    bot.send_message(call.message.chat.id, "Введите имя пользователя")
    bot.register_next_step_handler(call.message, handle_user)


def handle_user(message):
    cursor.execute("SELECT id FROM Users WHERE name = ?", (message.text,))
    id_result = cursor.fetchone()

    if not id_result:
        bot.send_message(message.chat.id, "Пользователь не найден")
        return

    user_id = id_result[0]

    cursor.execute("SELECT can_post FROM Users WHERE name = ?", (message.text,))
    can_post_result = cursor.fetchone()
    can_post_raw = can_post_result[0] if can_post_result else 'FALSE'

    # Переводим строку в логическое значение
    can_post_bool = str(can_post_raw).upper() == 'TRUE'

    # Меняем значение на противоположное
    new_can_post = 'FALSE' if can_post_bool else 'TRUE'

    # Обновляем
    cursor.execute('UPDATE Users SET can_post = ? WHERE id = ?', (new_can_post, user_id))

    # Отправляем сообщение
    if can_post_bool:
        bot.send_message(message.chat.id,
                         "Пользователь обновлён, до обновления пользователь имел доступ к созданию постов")
    else:
        bot.send_message(message.chat.id,
                         "Пользователь обновлён, до обновления пользователь не имел доступ к созданию постов")

    connection.commit()


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
    cursor.execute('SELECT * FROM Organisations WHERE name = ?', (message.text,))
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(OK, callback_data='back_to_menu'))
    if cursor.fetchone() == None:
        cursor.execute('INSERT INTO Organisations (name, admin_id) VALUES (?, ?)',
                       (message.text, message.chat.id,))
        cursor.execute('UPDATE Users set role = ?, organisation = ?, can_post = ? WHERE id = ?',
                       ('ADMIN', message.text, 'TRUE', message.chat.id,))
        connection.commit()
        with open('bot_logo.png', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=ORGANISATION_IS_CREATED, parse_mode='HTML',
                           reply_markup=keyboard)
    else:
        with open('bot_logo.png', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption="Организация уже существует", parse_mode='HTML',
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
    user_themes = list(cursor.fetchall()[0])[0]
    themes_map = {
        'Биология': ('biology', BIOLOGY),
        'Медицина': ('medicine', MEDICINE),
        'Физика': ('physics', PHYSICS),
        'Химия': ('chemistry', CHEMISTRY),
        'Математика': ('maths', MATHS),
        'Агрокультура': ('agro', AGRO),
        'Инженерные науки': ('engineer', ENGINEER),
        'Науки о земле': ('earth_science', EARTH_SCIENCE),
        'Гуманитарные науки': ('social_inst', SOCIAL_INST)
    }
    result_vars = {}
    for theme, (var_name, label) in themes_map.items():
        result_vars[var_name] = label + ('✔️' if theme in user_themes else '❌')
    biology = result_vars['biology']
    medicine = result_vars['medicine']
    physics = result_vars['physics']
    chemistry = result_vars['chemistry']
    maths = result_vars['maths']
    agro = result_vars['agro']
    engineer = result_vars['engineer']
    earth_science = result_vars['earth_science']
    social_inst = result_vars['social_inst']
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
    keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_menu'))
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
    theme = call.data.replace('switch_interesting_theme_', '')
    theme_map = {
        "biology": "Биология",
        "medicine": "Медицина",
        "physics": "Физика",
        "chemistry": "Химия",
        "maths": "Математика",
        "agro": "Агрокультура",
        "engineer": "Инженерные науки",
        "earth_science": "Науки о земле",
        "social_inst": "Гуманитарные науки"
    }
    if theme in theme_map:
        theme_name = theme_map[theme]
        if theme_name in user_themes:
            user_themes = user_themes.replace(theme_name, '')
        else:
            user_themes += theme_name
    cursor.execute('UPDATE Users set science_themes = ? WHERE id = ?', (user_themes,
                                                                        call.message.chat.id,))
    connection.commit()
    interesting_themes(call)


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
    keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_menu'))
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