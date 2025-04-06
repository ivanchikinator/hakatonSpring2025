import re
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text
from sqlalchemy.dialects.postgresql import psycopg2
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import telebot
from constants import *
from contextlib import suppress
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

DATABASE_URL = "postgresql://ivan:123@localhost:5432/database"

engine = create_engine(DATABASE_URL, echo=True)
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    role = Column(String, nullable=False)
    notifications = Column(String, nullable=False)
    organisation = Column(String, nullable=True)
    science_themes = Column(String, nullable=True)
    can_post = Column(Boolean, default=True)
    name = Column(String(20), nullable=True)


class Organisation(Base):
    __tablename__ = 'organisations'
    name = Column(String(20), primary_key=True)
    admin_id = Column(Integer, nullable=False)


class Post(Base):
    __tablename__ = 'posts'
    text = Column(Text, nullable=False)
    tags = Column(Text, nullable=True)


Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

API_TOKEN = "7781448243:AAFlty1i8-xAgU7TTWVzC19FX4pxz3w-e3M"
bot = telebot.TeleBot(API_TOKEN)


def main_menu(message, new_draw: bool):
    keyboard = InlineKeyboardMarkup(row_width=5)
    with suppress(IntegrityError):
        user = User(
            id=message.chat.id,
            role='ANONIM',
            notifications='1',
            organisation='None',
            science_themes="БиологияМедицинаФизикаХимияМатематикаАгрокультураИнженерные наукиНауки о землеГуманитарные науки",
            can_post=True,
            name=message.from_user.username
        )
        session.add(user)
        session.commit()
    keyboard.add(InlineKeyboardButton(NEWS_BUTTON, callback_data='news'))
    role = session.query(User.role).filter_by(id=message.chat.id).first()[0]
    can_post = session.query(User.can_post).filter_by(id=message.chat.id).first()[0]

    if can_post and role != 'ANONIM':
        keyboard.add(InlineKeyboardButton(CREATE_POST, callback_data='create_post'))
    if role == 'ADMIN':
        keyboard.add(InlineKeyboardButton(YOUR_ORGANISATIONS, callback_data='organisation_members'))
        keyboard.add(InlineKeyboardButton(DELETE_ORGANISATION, callback_data='delete_organisation'))
    if role == 'ANONIM':
        keyboard.add(InlineKeyboardButton(CREATE_ORGANISATION, callback_data='create_organisation'))
        keyboard.add(InlineKeyboardButton(JOIN_ORGANISATION, callback_data='enter_organisation'))
    if role == 'USER':
        keyboard.add(InlineKeyboardButton(LEAVE_ORGANISATION, callback_data='leave_organisation'))
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


def split_by_capital_letters_to_array(text):
    return re.findall('[А-ЯЁ][^А-ЯЁ]*', text)


@bot.callback_query_handler(func=lambda call: call.data == 'Получить новость')
def read_news_by_topic(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(GET_NEWS, callback_data='Получить новость'))
    keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_menu'))
    result = ''
    try:
        conn = psycopg2.connect("news_titles.db")
        cursor2 = conn.cursor()
        themes = split_by_capital_letters_to_array(
            session.query(User.science_themes).filter_by(id=call.message.chat.id).first()[0])

        for theme in themes:
            cursor2.execute("SELECT * FROM news WHERE topic=%s", (theme,))
            rows = cursor2.fetchall()[0]
            if rows:
                topic, title, link, intro, date = rows
                result += title + "\n"
                result += link + "\n"
                result += intro + "\n"
                result += date + "\n"
                bot.send_message(call.message.chat.id, result)
                result = ''
            else:
                result = f"Новостей по теме не найдено."

    except psycopg2.Error as e:
        print(f"Ошибка при работе с базой данных: {e}")
    finally:
        if conn:
            conn.close()
    with open('bot_logo.png', 'rb') as photo:
        bot.send_photo(call.message.chat.id, photo, caption=result, parse_mode='HTML',
                       reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == 'create_post')
def create_post(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(BACK, callback_data='back_to_menu'))
    role = session.query(User.role).filter_by(id=call.message.chat.id).first()[0]
    with open('bot_logo.png', "rb") as photo:
        bot.edit_message_media(
            media=telebot.types.InputMediaPhoto(photo, caption=ENTER_POST_TEXT, parse_mode='HTML'),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )
    if role == 'ADMIN':
        pass
    else:
        pass


@bot.callback_query_handler(func=lambda call: call.data == 'interesting_themes')
def interesting_themes(call: CallbackQuery):
    user = session.query(User).filter(User.id == call.message.chat.id).first()
    user_themes = user.science_themes if user else ""

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
    user = session.query(User).filter(User.id == call.message.chat.id).first()
    user_themes = user.science_themes if user else ""

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

    user.science_themes = user_themes
    session.commit()

    interesting_themes(call)


@bot.callback_query_handler(func=lambda call: call.data == 'notifications')
def notifications(call: CallbackQuery):
    user = session.query(User).filter(User.id == call.message.chat.id).first()
    check = user.notifications if user else "0"

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
    user = session.query(User).filter(User.id == call.message.chat.id).first()
    user.notifications = new_status
    session.commit()

    notifications(call)


bot.infinity_polling()
