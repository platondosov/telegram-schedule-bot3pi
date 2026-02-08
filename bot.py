import telebot
from telebot import types
from datetime import datetime, timedelta
import requests
import os
import time
import threading
from flask import Flask
import json
import pickle
import atexit

# Flask приложение для Render
app = Flask(__name__)


@app.route('/')
def home():
    return "Bot is running!", 200


@app.route('/ping')
def ping():
    return "pong", 200


@app.route('/health')
def health():
    return "OK", 200


def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


BOT_TOKEN = "8548678485:AAGqzI-DbUPOhbwYd_jZ2e6en4Ifnnqx4PI"
bot = telebot.TeleBot(BOT_TOKEN)

# Дата начала весеннего семестра 2025-2026
START_DATE = datetime(2026, 2, 9)  # 09.02.2026 - начало семестра

# Словари для хранения данных пользователей
user_selected_weeks = {}
user_selected_subgroups = {}  # 1 или 2 подгруппа
DATA_FILE = "user_data.pkl"


def save_data():
    """Сохраняет данные пользователей в файл"""
    try:
        data = {
            'weeks': user_selected_weeks,
            'subgroups': user_selected_subgroups
        }
        with open(DATA_FILE, 'wb') as f:
            pickle.dump(data, f)
        print("✅ Данные сохранены")
    except Exception as e:
        print(f"❌ Ошибка сохранения данных: {e}")


def load_data():
    """Загружает данные пользователей из файла"""
    global user_selected_weeks, user_selected_subgroups
    try:
        with open(DATA_FILE, 'rb') as f:
            data = pickle.load(f)
            user_selected_weeks = data.get('weeks', {})
            user_selected_subgroups = data.get('subgroups', {})
        print(f"✅ Данные загружены. Пользователей: {len(user_selected_subgroups)}")
    except FileNotFoundError:
        print("ℹ️ Файл данных не найден, создаем новый")
        user_selected_weeks = {}
        user_selected_subgroups = {}
    except Exception as e:
        print(f"❌ Ошибка загрузки данных: {e}")
        user_selected_weeks = {}
        user_selected_subgroups = {}


# Загружаем данные при старте
load_data()
atexit.register(save_data)


def get_current_week():
    today = datetime.now()
    print(f"🔍 Отладка: Сегодня: {today.strftime('%d.%m.%Y')}, Начало семестра: {START_DATE.strftime('%d.%m.%Y')}")

    # Если сегодня день начала семестра - это II неделя (по условию задачи)
    if today.date() == START_DATE.date():
        print("🔍 Отладка: Сегодня начало семестра, возвращаем II (согласно условию)")
        return "II"

    # Если до начала семестра
    if today < START_DATE:
        print("🔍 Отладка: До начала семестра, возвращаем II (согласно условию)")
        return "II"

    days_diff = (today - START_DATE).days
    week_num = (days_diff // 7) % 2

    print(f"🔍 Отладка: Дней от начала: {days_diff}, Неделя №: {week_num}")

    # ИЗМЕНЕНО: Семестр начинается со II недели, поэтому:
    # 0 -> II неделя (было I)
    # 1 -> I неделя (было II)
    result = "II" if week_num == 0 else "I"  # ИНВЕРСИРОВАНО!
    print(f"🔍 Отладка: Результат: {result}")
    return result


# Функция получения недели для конкретного пользователя
def get_user_week(user_id):
    """Возвращает неделю для пользователя: выбранную или автоматическую"""
    if user_id in user_selected_weeks:
        if user_selected_weeks[user_id] == "auto":
            return get_current_week()
        return user_selected_weeks[user_id]
    return get_current_week()


# Функция получения подгруппы пользователя
def get_user_subgroup(user_id):
    """Возвращает подгруппу пользователя (1 или 2)"""
    return user_selected_subgroups.get(user_id, 1)  # По умолчанию 1 подгруппа


# Расписание для двух подгрупп (ЗАМЕНЕНО НА НОВОЕ)
schedule = {
    # Подгруппа 1
    1: {
        "Понедельник": {
            "I": """📅 *ПОНЕДЕЛЬНИК | I неделя | Подгруппа 1*

*1 пара (08:00-09:25):*
• История белорусской государственности (лк 100-3а, доц. Коваль О.В.)

*2 пара (09:35-11:00):*
• Скриптовые языки программирования (лк 301-4, доц. Жиляк Н.А.)

*3 пара (11:25-12:50):*
• Скриптовые языки программирования (лр 324-1)

*4 пара (13:00-14:25):*
• Основы алгоритмизации и программирования (лр 206-1)""",

            "II": """📅 *ПОНЕДЕЛЬНИК | II неделя | Подгруппа 1*

*1 пара (08:00-09:25):*
• История белорусской государственности (лк 100-3а, доц. Коваль О.В.)

*2 пара (09:35-11:00):*
• Скриптовые языки программирования (лк 301-4, доц. Жиляк Н.А.)

*3 пара (11:25-12:50):*
• Пропуск

*4 пара (13:00-14:25):*
• Пропуск"""
        },

        "Вторник": {
            "I": """📅 *ВТОРНИК | I неделя | Подгруппа 1*

*1 пара (08:00-09:25):*
• Физика (лр 506, 512, 503, 513-1)

*2 пара (09:35-11:00):*
• Основы алгоритмизации и программирования (лк 100-3а, доц. Белодед Н.И.)

*3 пара (11:25-12:50):*
• Инженерная и машинная графика (лр 104-3)

*4 пара (13:00-14:25):*
• Политология (пз 336-4) - с 17.03""",

            "II": """📅 *ВТОРНИК | II неделя | Подгруппа 1*

*1 пара (08:00-09:25):*
• Физика (лр 506, 512, 503, 513-1)

*2 пара (09:35-11:00):*
• Основы алгоритмизации и программирования (лк 100-3а, доц. Белодед Н.И.)

*3 пара (11:25-12:50):*
• Инженерная и машинная графика (лр 104-3)

*4 пара (13:00-14:25):*
• История мировой культуры (пз 339-4) - с 24.02"""
        },

        "Среда": {
            "I": """📅 *СРЕДА | I неделя | Подгруппа 1*

*1 пара (08:00-09:25):*
• Пропуск

*2 пара (09:35-11:00):*
• История мировой культуры (лк 100-3а, доц. Доморад А.А.)
• Политология (лк 137-4, доц. Крючек П.С.)

*3 пара (11:25-12:50):*
• История белорусской государственности (пз 334-4)

*4 пара (13:00-14:25):*
• Физическая культура""",

            "II": """📅 *СРЕДА | II неделя | Подгруппа 1*

*1 пара (08:00-09:25):*
• Пропуск

*2 пара (09:35-11:00):*
• История мировой культуры (лк 100-3а, доц. Доморад А.А.)
• Политология (лк 137-4, доц. Крючек П.С.)

*3 пара (11:25-12:50):*
• История белорусской государственности (пз 334-4)

*4 пара (13:00-14:25):*
• Физическая культура"""
        },

        "Четверг": {
            "I": """📅 *ЧЕТВЕРГ | I неделя | Подгруппа 1*

*1 пара (08:00-09:25):*
• Физика (лк 408-2, доц. Мисевич А.В.)

*2 пара (09:35-11:00):*
• Скриптовые языки программирования (лр 324-1)

*3 пара (11:25-12:50):*
• Математический анализ (пз 308а-4)

*4 пара (13:00-14:25):*
• Пропуск""",

            "II": """📅 *ЧЕТВЕРГ | II неделя | Подгруппа 1*

*1 пара (08:00-09:25):*
• Великая Отечественная война советского народа (лк 100-3а, доц. Крючек П.С.)

*2 пара (09:35-11:00):*
• Скриптовые языки программирования (лр 324-1)

*3 пара (11:25-12:50):*
• Математический анализ (пз 308а-4)

*4 пара (13:00-14:25):*
• Физика (пз 120-4)"""
        },

        "Пятница": {
            "I": """📅 *ПЯТНИЦА | I неделя | Подгруппа 1*

*1 пара (08:00-09:25):*
• Пропуск

*2 пара (09:35-11:00):*
• Структуры данных (лк 137-4, доц. Белодед Н.И.)

*3 пара (11:25-12:50):*
• Английский язык (пз 221-2 общ.)

*4 пара (13:00-14:25):*
• Основы алгоритмизации и программирования (лр 206-1)""",

            "II": """📅 *ПЯТНИЦА | II неделя | Подгруппа 1*

*1 пара (08:00-09:25):*
• Пропуск

*2 пара (09:35-11:00):*
• Структуры данных (лк 137-4, доц. Белодед Н.И.)

*3 пара (11:25-12:50):*
• Английский язык (пз 221-2 общ.)

*4 пара (13:00-14:25):*
• Основы алгоритмизации и программирования (лр 206-1)"""
        },

        "Суббота": {
            "I": """📅 *СУББОТА | I неделя | Подгруппа 1*

*1 пара (08:00-09:25):*
• Структуры данных (лр 413-1)

*2 пара (09:35-11:00):*
• Физическая культура

*3 пара (11:25-12:50):*
• Физика (лк 408-2, доц. Мисевич А.В.)

*4 пара (13:00-14:25):*
• Математический анализ (лк 440-4, доц. Ловенецкая Е.И.)""",

            "II": """📅 *СУББОТА | II неделя | Подгруппа 1*

*1 пара (08:00-09:25):*
• Структуры данных (лр 413-1)

*2 пара (09:35-11:00):*
• Физическая культура

*3 пара (11:25-12:50):*
• Физика (лк 408-2, доц. Мисевич А.В.)

*4 пара (13:00-14:25):*
• Математический анализ (лк 440-4, доц. Ловенецкая Е.И.)"""
        }
    },

    # Подгруппа 2
    2: {
        "Понедельник": {
            "I": """📅 *ПОНЕДЕЛЬНИК | I неделя | Подгруппа 2*

*1 пара (08:00-09:25):*
• История белорусской государственности (лк 100-3а, доц. Коваль О.В.)

*2 пара (09:35-11:00):*
• Скриптовые языки программирования (лк 301-4, доц. Жиляк Н.А.)

*3 пара (11:25-12:50):*
• Скриптовые языки программирования (лр 413-1)

*4 пара (13:00-14:25):*
• Пропуск""",

            "II": """📅 *ПОНЕДЕЛЬНИК | II неделя | Подгруппа 2*

*1 пара (08:00-09:25):*
• История белорусской государственности (лк 100-3а, доц. Коваль О.В.)

*2 пара (09:35-11:00):*
• Скриптовые языки программирования (лк 301-4, доц. Жиляк Н.А.)

*3 пара (11:25-12:50):*
• Скриптовые языки программирования (лр 413-1)

*4 пара (13:00-14:25):*
• Основы алгоритмизации и программирования (лр 202-4)"""
        },

        "Вторник": {
            "I": """📅 *ВТОРНИК | I неделя | Подгруппа 2*

*1 пара (08:00-09:25):*
• Физика (лр 506, 512, 503, 513-1)

*2 пара (09:35-11:00):*
• Основы алгоритмизации и программирования (лк 100-3а, доц. Белодед Н.И.)

*3 пара (11:25-12:50):*
• Инженерная и машинная графика (лр 105-3)

*4 пара (13:00-14:25):*
• Политология (пз 336-4) - с 17.03""",

            "II": """📅 *ВТОРНИК | II неделя | Подгруппа 2*

*1 пара (08:00-09:25):*
• Физика (лр 506, 512, 503, 513-1)

*2 пара (09:35-11:00):*
• Основы алгоритмизации и программирования (лк 100-3а, доц. Белодед Н.И.)

*3 пара (11:25-12:50):*
• Инженерная и машинная графика (лр 105-3)

*4 пара (13:00-14:25):*
• История мировой культуры (пз 339-4) - с 24.02"""
        },

        "Среда": {
            "I": """📅 *СРЕДА | I неделя | Подгруппа 2*

*1 пара (08:00-09:25):*
• Структуры данных (лр 324-4)

*2 пара (09:35-11:00):*
• История мировой культуры (лк 100-3а, доц. Доморад А.А.)
• Политология (лк 137-4, доц. Крючек П.С.)

*3 пара (11:25-12:50):*
• История белорусской государственности (пз 334-4)

*4 пара (13:00-14:25):*
• Физическая культура""",

            "II": """📅 *СРЕДА | II неделя | Подгруппа 2*

*1 пара (08:00-09:25):*
• Структуры данных (лр 324-4)

*2 пара (09:35-11:00):*
• История мировой культуры (лк 100-3а, доц. Доморад А.А.)
• Политология (лк 137-4, доц. Крючек П.С.)

*3 пара (11:25-12:50):*
• История белорусской государственности (пз 334-4)

*4 пара (13:00-14:25):*
• Физическая культура"""
        },

        "Четверг": {
            "I": """📅 *ЧЕТВЕРГ | I неделя | Подгруппа 2*

*1 пара (08:00-09:25):*
• Физика (лк 408-2, доц. Мисевич А.В.)

*2 пара (09:35-11:00):*
• Английский язык (пз 123-2 общ.)

*3 пара (11:25-12:50):*
• Математический анализ (пз 308а-4)

*4 пара (13:00-14:25):*
• Пропуск""",

            "II": """📅 *ЧЕТВЕРГ | II неделя | Подгруппа 2*

*1 пара (08:00-09:25):*
• Великая Отечественная война советского народа (лк 100-3а, доц. Крючек П.С.)

*2 пара (09:35-11:00):*
• Английский язык (пз 123-2 общ.)

*3 пара (11:25-12:50):*
• Математический анализ (пз 308а-4)

*4 пара (13:00-14:25):*
• Физика (пз 120-4)"""
        },

        "Пятница": {
            "I": """📅 *ПЯТНИЦА | I неделя | Подгруппа 2*

*1 пара (08:00-09:25):*
• Скриптовые языки программирования (лр 413-1)

*2 пара (09:35-11:00):*
• Структуры данных (лк 137-4, доц. Белодед Н.И.)

*3 пара (11:25-12:50):*
• Основы алгоритмизации и программирования (лр 202-4)

*4 пара (13:00-14:25):*
• Пропуск""",

            "II": """📅 *ПЯТНИЦА | II неделя | Подгруппа 2*

*1 пара (08:00-09:25):*
• Пропуск

*2 пара (09:35-11:00):*
• Структуры данных (лк 137-4, доц. Белодед Н.И.)

*3 пара (11:25-12:50):*
• Основы алгоритмизации и программирования (лр 202-4)

*4 пара (13:00-14:25):*
• Пропуск"""
        },

        "Суббота": {
            "I": """📅 *СУББОТА | I неделя | Подгруппа 2*

*1 пара (08:00-09:25):*
• Пропуск

*2 пара (09:35-11:00):*
• Физическая культура

*3 пара (11:25-12:50):*
• Физика (лк 408-2, доц. Мисевич А.В.)

*4 пара (13:00-14:25):*
• Математический анализ (лк 440-4, доц. Ловенецкая Е.И.)""",

            "II": """📅 *СУББОТА | II неделя | Подгруппа 2*

*1 пара (08:00-09:25):*
• Пропуск

*2 пара (09:35-11:00):*
• Физическая культура

*3 пара (11:25-12:50):*
• Физика (лк 408-2, доц. Мисевич А.В.)

*4 пара (13:00-14:25):*
• Математический анализ (лк 440-4, доц. Ловенецкая Е.И.)"""
        }
    }
}


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id

    # Если пользователь не выбрал подгруппу, показываем меню выбора
    if user_id not in user_selected_subgroups:
        show_subgroup_selection(message)
        return

    # Продолжаем обычный старт
    user_week = get_user_week(user_id)
    user_subgroup = get_user_subgroup(user_id)
    today = datetime.now()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    # Кнопки дней недели
    days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
    buttons = [types.KeyboardButton(day) for day in days]

    # Располагаем по 2 кнопки в ряд
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            markup.row(buttons[i], buttons[i + 1])
        else:
            markup.row(buttons[i])

    # Дополнительные кнопки
    markup.row(
        types.KeyboardButton('📅 Сегодня'),
        types.KeyboardButton('📆 Завтра')
    )
    markup.row(
        types.KeyboardButton('ℹ️ Какая неделя?'),
        types.KeyboardButton('🔄 Сменить неделю')
    )
    markup.row(
        types.KeyboardButton('👥 Сменить подгруппу'),
        types.KeyboardButton('/help')
    )

    # Определяем статус недели
    week_status = ""
    if user_id in user_selected_weeks:
        if user_selected_weeks[user_id] == "auto":
            week_status = "Автоматический режим"
        else:
            week_status = f"Ручной режим: {user_selected_weeks[user_id]} неделя"
    else:
        week_status = "Автоматический режим"

    # Приветственное сообщение
    week_num = (today - START_DATE).days // 7 + 1 if today >= START_DATE else 0
    welcome_msg = f"""
🎓 *Расписание БГТУ*
*Семестр начинается:* {START_DATE.strftime('%d.%m.%Y')}
*Текущая неделя:* {get_current_week()} неделя
*Ваша неделя:* {user_week} неделя
*Ваша подгруппа:* {user_subgroup}
*Режим:* {week_status}
*С начала семестра:* {week_num} учебная неделя

📅 *{today.strftime('%d.%m.%Y')}* ({['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][today.weekday()]})

Выберите день недели:
"""

    bot.send_message(message.chat.id, welcome_msg,
                     reply_markup=markup, parse_mode='Markdown')
    # Сохраняем данные
    save_data()


def show_subgroup_selection(message):
    """Показывает меню выбора подгруппы"""
    markup = types.InlineKeyboardMarkup(row_width=2)

    btn_subgroup_1 = types.InlineKeyboardButton(
        '👥 Подгруппа 1',
        callback_data='select_subgroup_1'
    )
    btn_subgroup_2 = types.InlineKeyboardButton(
        '👥 Подгруппа 2',
        callback_data='select_subgroup_2'
    )

    markup.row(btn_subgroup_1, btn_subgroup_2)

    bot.send_message(
        message.chat.id,
        "👋 *Добро пожаловать в бот расписания БГТУ!*\n\n"
        "📚 *Пожалуйста, выберите вашу подгруппу:*\n\n"
        "Вы всегда сможете сменить подгруппу в главном меню.",
        reply_markup=markup,
        parse_mode='Markdown'
    )


@bot.message_handler(commands=['help'])
def help_command(message):
    print(f"🔍 DEBUG: Получена команда /help от {message.chat.id}")

    try:
        current_week = get_current_week()
        start_date_str = START_DATE.strftime('%d.%m.%Y')

        help_text = f"""📚 *ПОМОЩЬ ПО БОТУ РАСПИСАНИЯ БГТУ*

*📋 ОСНОВНЫЕ КОМАНДЫ:*
/start - Главное меню
/today - Расписание на сегодня
/tomorrow - Расписание на завтра
/week - Какая сейчас неделя (I/II)
/switch_week - Сменить неделю
/auto_week - Автоматическое определение недели
/change_subgroup - Сменить подгруппу
/help - Эта справка

*📅 КАК ПОЛЬЗОВАТЬСЯ:*
1. При первом запуске выберите свою подгруппу (1 или 2)
2. Нажмите на кнопку с днем недели
3. Бот покажет расписание для этого дня
4. Используйте кнопки под расписанием для смены недели

*⚙️ РЕЖИМЫ РАБОТЫ:*
• 🤖 *Автоматический* - бот сам определяет текущую неделю
• 👨‍💻 *Ручной* - вы выбираете неделю вручную (I или II)

*ℹ️ ИНФОРМАЦИЯ:*
• Начало семестра: {start_date_str}
• Текущая неделя: {current_week}
• Подгруппы могут иметь разное расписание

*🔧 ВОЗМОЖНЫЕ ПРОБЛЕМЫ:*
• Если бот не отвечает - перезапустите его командой /start
• Если не видите кнопки - нажмите значок 🎛️ справа от поля ввода
• Для сброса настроек удалите чат с ботом и начните заново"""

        bot.send_message(
            message.chat.id,
            help_text,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        print(f"✅ DEBUG: Помощь отправлена пользователю {message.chat.id}")

    except Exception as e:
        print(f"❌ ERROR в help_command: {e}")
        print(f"❌ Тип ошибки: {type(e).__name__}")
        import traceback
        traceback.print_exc()

        # Простое сообщение без форматирования
        simple_help = """📚 ПОМОЩЬ ПО БОТУ

Основные команды:
/start - Главное меню
/today - Расписание на сегодня
/tomorrow - Расписание на завтра
/week - Какая неделя
/switch_week - Сменить неделю
/auto_week - Авторежим
/change_subgroup - Сменить подгруппу
/help - Справка"""

        bot.send_message(message.chat.id, simple_help)


@bot.message_handler(commands=['today'])
def today_command(message):
    user_id = message.chat.id
    if user_id not in user_selected_subgroups:
        show_subgroup_selection(message)
        return
    show_day_schedule(message, "today")


@bot.message_handler(commands=['tomorrow'])
def tomorrow_command(message):
    user_id = message.chat.id
    if user_id not in user_selected_subgroups:
        show_subgroup_selection(message)
        return
    show_day_schedule(message, "tomorrow")


@bot.message_handler(commands=['week'])
def week_command(message):
    user_id = message.chat.id
    if user_id not in user_selected_subgroups:
        show_subgroup_selection(message)
        return

    current_week = get_current_week()
    user_week = get_user_week(user_id)
    user_subgroup = get_user_subgroup(user_id)
    today = datetime.now()
    week_num = (today - START_DATE).days // 7 + 1 if today >= START_DATE else 0

    week_info = f"""
📆 *Информация о неделе:*

*Текущая неделя:* {current_week}
*Ваша неделя:* {user_week}
*Ваша подгруппа:* {user_subgroup}
*Учебная неделя №:* {week_num}
*Дата:* {today.strftime('%d.%m.%Y')}

*Начало семестра:* {START_DATE.strftime('%d.%m.%Y')}
*Прошло дней:* {(today - START_DATE).days if today >= START_DATE else 0}

*Режим:* {"Ручной" if user_id in user_selected_weeks and user_selected_weeks[user_id] != "auto" else "Автоматический"}
"""
    bot.send_message(message.chat.id, week_info, parse_mode='Markdown')


@bot.message_handler(commands=['switch_week'])
def switch_week_command(message):
    """Команда для смены недели"""
    user_id = message.chat.id
    if user_id not in user_selected_subgroups:
        show_subgroup_selection(message)
        return
    show_week_selection_menu(message)


@bot.message_handler(commands=['auto_week'])
def auto_week_command(message):
    """Вернуться к автоматическому определению недели"""
    user_id = message.chat.id
    if user_id not in user_selected_subgroups:
        show_subgroup_selection(message)
        return

    user_selected_weeks[user_id] = "auto"
    save_data()

    bot.send_message(
        message.chat.id,
        "✅ *Режим переключен на автоматический!*\n\n"
        f"Теперь бот будет показывать расписание *{get_current_week()} недели* "
        "(текущей недели).",
        parse_mode='Markdown'
    )


@bot.message_handler(commands=['change_subgroup'])
def change_subgroup_command(message):
    """Сменить подгруппу"""
    show_subgroup_selection(message)


@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.chat.id

    # Проверяем, выбрана ли подгруппа
    if user_id not in user_selected_subgroups:
        show_subgroup_selection(message)
        return

    if message.text == '📅 Сегодня':
        show_day_schedule(message, "today")
    elif message.text == '📆 Завтра':
        show_day_schedule(message, "tomorrow")
    elif message.text == 'ℹ️ Какая неделя?':
        week_command(message)
    elif message.text == '🔄 Сменить неделю':
        show_week_selection_menu(message)
    elif message.text == '👥 Сменить подгруппу':
        show_subgroup_selection(message)
    elif message.text in ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]:
        show_day_with_week_buttons(message, message.text)
    else:
        bot.send_message(message.chat.id,
                         "Пожалуйста, выберите день недели из меню ниже 👇")


def show_day_schedule(message, day_type):
    days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
    today = datetime.now().weekday()

    if day_type == "today":
        if today < 6:
            day_name = days[today]
            prefix = f"📅 *СЕГОДНЯ ({day_name})*"
        else:
            bot.send_message(message.chat.id,
                             "Сегодня воскресенье - выходной день! 🎉\nОтдыхайте и готовьтесь к новой неделе!")
            return
    else:  # tomorrow
        tomorrow = (today + 1) % 7
        if tomorrow < 6:
            day_name = days[tomorrow]
            tomorrow_date = datetime.now() + timedelta(days=1)
            prefix = f"📆 *ЗАВТРА ({day_name}, {tomorrow_date.strftime('%d.%m')})*"
        else:
            bot.send_message(message.chat.id,
                             "Завтра воскресенье - выходной день! 🎉")
            return

    show_day_with_week_buttons(message, day_name, prefix)


def show_day_with_week_buttons(message, day_name, prefix=""):
    user_id = message.chat.id
    user_week = get_user_week(user_id)
    user_subgroup = get_user_subgroup(user_id)

    # Проверяем наличие расписания для данной подгруппы, дня и недели
    if (user_subgroup in schedule and
            day_name in schedule[user_subgroup] and
            user_week in schedule[user_subgroup][day_name]):

        response = f"{prefix}\n\n"
        response += schedule[user_subgroup][day_name][user_week]

        # Создаем inline-кнопки
        markup_inline = types.InlineKeyboardMarkup(row_width=2)

        # Определяем какую неделю показывать для переключения
        other_week = "II" if user_week == "I" else "I"
        current_week = get_current_week()

        btn_other_week = types.InlineKeyboardButton(
            f'🔄 Показать {other_week} неделю',
            callback_data=f'week_{other_week}_{day_name}'
        )
        btn_switch_global = types.InlineKeyboardButton(
            f'⚙️ Сменить на {other_week}',
            callback_data=f'switch_global_{other_week}'
        )
        btn_today = types.InlineKeyboardButton(
            '📅 Сегодня',
            callback_data='show_today'
        )
        btn_auto = types.InlineKeyboardButton(
            '🤖 Авто',
            callback_data='switch_auto'
        )
        btn_menu = types.InlineKeyboardButton(
            '🏠 Меню',
            callback_data='back_to_menu'
        )

        markup_inline.row(btn_other_week)
        markup_inline.row(btn_switch_global)
        markup_inline.row(btn_today, btn_auto, btn_menu)

        mode_text = "Ручной режим" if user_id in user_selected_weeks and user_selected_weeks[
            user_id] != "auto" else "Автоматический режим"

        # Добавляем информацию о неделе и кнопки в ОДНО сообщение с расписанием
        response += f"\n\n*Сейчас отображается {user_week} неделя*\n"
        response += f"*Подгруппа:* {user_subgroup}\n"
        response += f"*Режим:* {mode_text}\n"
        response += f"*Текущая неделя:* {current_week}"

        # Отправляем ОДНО сообщение с расписанием и кнопками
        bot.send_message(message.chat.id, response,
                         reply_markup=markup_inline,
                         parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id,
                         f"Расписание на {day_name} для подгруппы {user_subgroup} не найдено")

def show_week_selection_menu(message):
    """Показывает меню выбора недели"""
    user_id = message.chat.id
    current_week = get_current_week()

    markup_inline = types.InlineKeyboardMarkup(row_width=2)

    btn_week_i = types.InlineKeyboardButton(
        '📘 I неделя',
        callback_data='set_week_I'
    )
    btn_week_ii = types.InlineKeyboardButton(
        '📗 II неделя',
        callback_data='set_week_II'
    )
    btn_auto = types.InlineKeyboardButton(
        '🤖 Автоматически',
        callback_data='set_week_auto'
    )
    btn_current_week = types.InlineKeyboardButton(
        f'📅 Текущая ({current_week})',
        callback_data='set_week_current'
    )
    btn_cancel = types.InlineKeyboardButton(
        '❌ Отмена',
        callback_data='cancel_week_switch'
    )

    markup_inline.row(btn_week_i, btn_week_ii)
    markup_inline.row(btn_auto, btn_current_week)
    markup_inline.row(btn_cancel)

    # Определяем текущий статус
    current_mode = "Автоматический" if user_id not in user_selected_weeks or user_selected_weeks[
        user_id] == "auto" else "Ручной"
    current_week_display = get_user_week(user_id)

    bot.send_message(
        message.chat.id,
        f"*🔄 Смена недели*\n\n"
        f"*Текущий режим:* {current_mode}\n"
        f"*Показывается неделя:* {current_week_display}\n"
        f"*Текущая неделя:* {current_week}\n\n"
        f"Выберите действие:",
        reply_markup=markup_inline,
        parse_mode='Markdown'
    )


@bot.callback_query_handler(func=lambda callback: True)
def callback_handler(callback):
    user_id = callback.message.chat.id
    print(f"🔍 Callback: {callback.data} от пользователя {user_id}")

    # Обработка выбора подгруппы
    if callback.data == 'select_subgroup_1':
        user_selected_subgroups[user_id] = 1
        save_data()

        bot.edit_message_text(
            "✅ *Выбрана Подгруппа 1!*\n\n"
            "Теперь бот будет показывать расписание для первой подгруппы.\n"
            "Для смены подгруппы используйте кнопку '👥 Сменить подгруппу' в главном меню.",
            callback.message.chat.id,
            callback.message.message_id,
            parse_mode='Markdown'
        )

        # Запускаем обычный старт
        time.sleep(1)
        msg = bot.send_message(user_id, "🔄 Загрузка меню...")
        start(msg)

    elif callback.data == 'select_subgroup_2':
        user_selected_subgroups[user_id] = 2
        save_data()

        bot.edit_message_text(
            "✅ *Выбрана Подгруппа 2!*\n\n"
            "Теперь бот будет показывать расписание для второй подгруппы.\n"
            "Для смены подгруппы используйте кнопку '👥 Сменить подгруппу' в главном меню.",
            callback.message.chat.id,
            callback.message.message_id,
            parse_mode='Markdown'
        )

        # Запускаем обычный старт
        time.sleep(1)
        msg = bot.send_message(user_id, "🔄 Загрузка меню...")
        start(msg)


    elif callback.data.startswith('week_I_'):

        # Показать I неделю для конкретного дня

        day_name = callback.data.split('_')[2]

        user_subgroup = get_user_subgroup(user_id)

        if (user_subgroup in schedule and

                day_name in schedule[user_subgroup] and

                "I" in schedule[user_subgroup][day_name]):

            try:

                # Определяем префикс из текущего сообщения

                message_text = callback.message.text

                lines = message_text.split('\n')

                prefix = lines[0]  # Берем первую строку как префикс

                # Формируем новое сообщение с I неделей

                response = f"{prefix}\n\n"

                response += schedule[user_subgroup][day_name]["I"]

                # Обновляем кнопки

                markup_inline = types.InlineKeyboardMarkup(row_width=2)

                btn_other_week = types.InlineKeyboardButton(

                    '📗 II неделя',

                    callback_data=f'week_II_{day_name}'

                )

                btn_switch_global = types.InlineKeyboardButton(

                    '⚙️ Сменить на II',

                    callback_data='switch_global_II'

                )

                btn_today = types.InlineKeyboardButton(

                    '📅 Сегодня',

                    callback_data='show_today'

                )

                btn_auto = types.InlineKeyboardButton(

                    '🤖 Авто',

                    callback_data='switch_auto'

                )

                btn_menu = types.InlineKeyboardButton(

                    '🏠 Меню',

                    callback_data='back_to_menu'

                )

                markup_inline.row(btn_other_week)

                markup_inline.row(btn_switch_global)

                markup_inline.row(btn_today, btn_auto, btn_menu)

                # Добавляем информацию о неделе

                response += f"\n\n*Отображается I неделя*\n"

                response += f"*Подгруппа:* {user_subgroup}\n"

                response += f"*Режим:* Ручной\n"

                response += f"*Текущая неделя:* {get_current_week()}"

                # Редактируем текущее сообщение

                bot.edit_message_text(

                    response,

                    callback.message.chat.id,

                    callback.message.message_id,

                    reply_markup=markup_inline,

                    parse_mode='Markdown'

                )

                bot.answer_callback_query(callback.id, "Показана I неделя")

            except Exception as e:

                print(f"Ошибка: {e}")

                bot.answer_callback_query(callback.id, "Ошибка обновления")


    elif callback.data.startswith('week_II_'):

        # Показать II неделю для конкретного дня

        day_name = callback.data.split('_')[2]

        user_subgroup = get_user_subgroup(user_id)

        if (user_subgroup in schedule and

                day_name in schedule[user_subgroup] and

                "II" in schedule[user_subgroup][day_name]):

            try:

                # Определяем префикс из текущего сообщения

                message_text = callback.message.text

                lines = message_text.split('\n')

                prefix = lines[0]  # Берем первую строку как префикс

                # Формируем новое сообщение с II неделей

                response = f"{prefix}\n\n"

                response += schedule[user_subgroup][day_name]["II"]

                # Обновляем кнопки

                markup_inline = types.InlineKeyboardMarkup(row_width=2)

                btn_other_week = types.InlineKeyboardButton(

                    '📘 I неделя',

                    callback_data=f'week_I_{day_name}'

                )

                btn_switch_global = types.InlineKeyboardButton(

                    '⚙️ Сменить на I',

                    callback_data='switch_global_I'

                )

                btn_today = types.InlineKeyboardButton(

                    '📅 Сегодня',

                    callback_data='show_today'

                )

                btn_auto = types.InlineKeyboardButton(

                    '🤖 Авто',

                    callback_data='switch_auto'

                )

                btn_menu = types.InlineKeyboardButton(

                    '🏠 Меню',

                    callback_data='back_to_menu'

                )

                markup_inline.row(btn_other_week)

                markup_inline.row(btn_switch_global)

                markup_inline.row(btn_today, btn_auto, btn_menu)

                # Добавляем информацию о неделе

                response += f"\n\n*Отображается II неделя*\n"

                response += f"*Подгруппа:* {user_subgroup}\n"

                response += f"*Режим:* Ручной\n"

                response += f"*Текущая неделя:* {get_current_week()}"

                # Редактируем текущее сообщение

                bot.edit_message_text(

                    response,

                    callback.message.chat.id,

                    callback.message.message_id,

                    reply_markup=markup_inline,

                    parse_mode='Markdown'

                )

                bot.answer_callback_query(callback.id, "Показана II неделя")

            except Exception as e:

                print(f"Ошибка: {e}")

                bot.answer_callback_query(callback.id, "Ошибка обновления")

    elif callback.data.startswith('switch_global_'):
        # Глобальное переключение недели
        week_to_set = callback.data.split('_')[2]
        user_selected_weeks[user_id] = week_to_set
        save_data()

        bot.answer_callback_query(callback.id, f"Установлена {week_to_set} неделя")

        # Закрываем меню и показываем сообщение
        bot.edit_message_text(
            f"✅ *Расписание переключено на {week_to_set} неделю!*\n\n"
            f"Теперь все дни будут показываться для *{week_to_set} недели*.\n"
            f"Для возврата к автоматическому режиму используйте команду /auto_week",
            callback.message.chat.id,
            callback.message.message_id,
            parse_mode='Markdown'
        )

    elif callback.data == 'switch_auto':
        # Включить автоматический режим
        user_selected_weeks[user_id] = "auto"
        save_data()

        current_week = get_current_week()
        bot.answer_callback_query(callback.id, f"Включен автоматический режим. Текущая неделя: {current_week}")

        # Закрываем меню и показываем сообщение
        bot.edit_message_text(
            f"✅ *Включен автоматический режим!*\n\n"
            f"Теперь бот показывает расписание *{current_week} недели* (текущей).",
            callback.message.chat.id,
            callback.message.message_id,
            parse_mode='Markdown'
        )

    elif callback.data == 'set_week_I':
        # Установить I неделю
        user_selected_weeks[user_id] = "I"
        save_data()

        bot.answer_callback_query(callback.id, "Установлена I неделя")

        # Закрываем меню и показываем сообщение
        bot.edit_message_text(
            "✅ *Расписание переключено на I неделю!*\n\n"
            "Теперь все дни будут показываться для *I недели*.\n"
            "Для возврата к автоматическому режиму используйте команду /auto_week",
            callback.message.chat.id,
            callback.message.message_id,
            parse_mode='Markdown'
        )

    elif callback.data == 'set_week_II':
        # Установить II неделю
        user_selected_weeks[user_id] = "II"
        save_data()

        bot.answer_callback_query(callback.id, "Установлена II неделя")

        # Закрываем меню и показываем сообщение
        bot.edit_message_text(
            "✅ *Расписание переключено на II неделю!*\n\n"
            "Теперь все дни будут показываться для *II недели*.\n"
            "Для возврата к автоматическому режиму используйте команду /auto_week",
            callback.message.chat.id,
            callback.message.message_id,
            parse_mode='Markdown'
        )

    elif callback.data == 'set_week_auto':
        # Включить автоматический режим
        user_selected_weeks[user_id] = "auto"
        save_data()
        current_week = get_current_week()

        bot.answer_callback_query(callback.id, f"Включен авторежим. Текущая неделя: {current_week}")

        # Закрываем меню и показываем сообщение
        bot.edit_message_text(
            f"✅ *Включен автоматический режим!*\n\n"
            f"Теперь бот показывает расписание *{current_week} недели* (текущей).",
            callback.message.chat.id,
            callback.message.message_id,
            parse_mode='Markdown'
        )

    elif callback.data == 'set_week_current':
        # Установить текущую неделю
        current_week = get_current_week()
        user_selected_weeks[user_id] = current_week
        save_data()

        bot.answer_callback_query(callback.id, f"Установлена {current_week} неделя")

        # Закрываем меню и показываем сообщение
        bot.edit_message_text(
            f"✅ *Установлена текущая неделя ({current_week})!*\n\n"
            f"Теперь бот показывает расписание *{current_week} недели*.",
            callback.message.chat.id,
            callback.message.message_id,
            parse_mode='Markdown'
        )

    elif callback.data == 'cancel_week_switch':
        # Отмена смены недели
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        bot.answer_callback_query(callback.id, "Отменено")

    elif callback.data == 'back_to_menu':
        bot.answer_callback_query(callback.id, "Возврат в меню")
        try:
            bot.delete_message(callback.message.chat.id, callback.message.message_id)
        except:
            pass
        # Отправляем обновленное меню
        msg = bot.send_message(callback.message.chat.id, "🔄 Обновление меню...")
        start(msg)

    elif callback.data == 'show_today':
        bot.answer_callback_query(callback.id, "Показываю сегодня")
        today_command(callback.message)


# ================ ЗАПУСК ================

def run_flask_server():
    try:
        port = int(os.environ.get('PORT', 10000))
        print(f"🚀 Flask сервер запускается на порту: {port}")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        print(f"❌ Ошибка Flask: {e}")
        return


def keep_alive():
    """
    Периодически пингует бота, чтобы он не засыпал на Render Free
    """
    time.sleep(40)

    # Ваш URL с Render
    YOUR_RENDER_URL = "https://telegram-schedule-bot3pi.onrender.com"

    while True:
        try:
            response = requests.get(f"{YOUR_RENDER_URL}/ping", timeout=10)
            print(f"✅ Keep-alive ping отправлен: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Keep-alive не удался: {e}")

        time.sleep(480)


def run_telegram_bot():
    print("🤖 Telegram бот запущен!")
    print(f"📅 Семестр начинается: {START_DATE.strftime('%d.%m.%Y')}")
    current_week = get_current_week()
    print(f"📆 Текущая неделя: {current_week}")
    print(f"🔍 Отладка: Дней от начала семестра: {(datetime.now() - START_DATE).days}")
    bot.polling(none_stop=True, interval=1, timeout=60)


if __name__ == "__main__":
    print("🎬 ===== НАЧАЛО ЗАПУСКА СИСТЕМЫ =====")

    # Загружаем данные
    load_data()

    # 1. Запускаем keep-alive в отдельном потоке
    print("1. Запуск системы keep-alive...")
    keep_alive_thread = threading.Thread(target=keep_alive)
    keep_alive_thread.daemon = True
    keep_alive_thread.start()

    # 2. Запускаем Flask сервер
    print("2. Запуск Flask сервера...")
    flask_thread = threading.Thread(target=run_flask_server)
    flask_thread.daemon = True
    flask_thread.start()

    # 3. Ждем запуска Flask
    print("3. Ожидание запуска компонентов (5 секунд)...")
    time.sleep(5)

    # 4. Запускаем Telegram бота
    print("4. Запуск Telegram бота...")
    run_telegram_bot()


    print("🏁 Все системы успешно запущены!")

