import telebot
from datetime import datetime, timedelta
import threading
import time
import schedule
import random
from telebot import types

API_TOKEN = '7696215411:AAGbnWxIu3ZTg1TN-YMy62lRxm7Z1WS1FqU'
bot = telebot.TeleBot(API_TOKEN)

user_tasks = {}
user_links = {}
user_ids = set()

# 💬 Цитаты
quotes = [
    "🌟 Великие дела начинаются с малого.",
    "🔥 Сложно — значит ты растёшь.",
    "🚀 Никогда не сдавайся.",
    "📘 Учёба — путь к свободе.",
    "💡 Каждый день — шанс стать лучше.",
    "⏳ Время — самый ценный ресурс.",
    "💪 Делай сегодня то, за что завтра скажешь спасибо.",
    "🧠 Знание — сила. Применение — ещё больше сила."
]

# Главное меню
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📝 Список задач", "🔗 Ссылки")
    markup.row("➕ Добавить задачу", "🧹 Очистить задачи")
    markup.row("🍅 Pomodoro", "📋 Помощь")
    return markup

# /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_ids.add(message.chat.id)
    bot.send_message(message.chat.id,
        "Привет! Я 🤖 *StudyMate* — твой помощник для учёбы.",
        parse_mode="Markdown",
        reply_markup=main_keyboard())
    send_help(message)

# /help
@bot.message_handler(commands=['help'])
@bot.message_handler(func=lambda m: m.text == "📋 Помощь")
def send_help(message):
    help_text = (
        "📋 *Команды:*\n"
        "➕ `/add` – добавить задачу\n"
        "📝 `/tasks` – список задач\n"
        "✅ `/edit <номер> Новый текст до дд.мм чч:мм` – изменить задачу\n"
        "🗑 `/delete <номер>` – удалить задачу\n"
        "🧹 `/clear_tasks` – удалить все задачи\n"
        "📅 `/week` – задачи по дням недели\n"
        "🔗 `/save <ссылка> Название` – сохранить ссылку\n"
        "🌐 `/links` – список ссылок\n"
        "🍅 `/pomodoro` – таймер Pomodoro (25 мин)\n"
        "💬 `/motivate` – мотивационная цитата\n"
        "ℹ️ `/help` – список команд"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown", reply_markup=main_keyboard())

# ➕ Добавить задачу
@bot.message_handler(func=lambda m: m.text == "➕ Добавить задачу")
@bot.message_handler(commands=['add'])
def ask_add(message):
    bot.reply_to(message, "✏️ Введи задачу в формате:\n`Текст до 25.05 23:59`", parse_mode="Markdown")

@bot.message_handler(func=lambda m: "до" in m.text and "." in m.text)
def add_task_text(message):
    user_id = message.from_user.id
    try:
        text = message.text
        task_text, deadline_str = text.rsplit("до", 1)
        deadline = datetime.strptime(deadline_str.strip(), "%d.%m %H:%M")
        task = {"task": task_text.strip(), "deadline": deadline, "done": False}
        user_tasks.setdefault(user_id, []).append(task)
        bot.reply_to(message, f"✅ Добавлено:\n📌 {task['task']} до {deadline.strftime('%d.%m %H:%M')}")
    except:
        bot.reply_to(message, "⚠️ Неверный формат. Пример:\n`Сделать отчёт до 25.05 23:59`", parse_mode="Markdown")

# 📝 Список задач
@bot.message_handler(commands=['tasks'])
@bot.message_handler(func=lambda m: m.text == "📝 Список задач")
def list_tasks(message):
    user_id = message.from_user.id
    tasks = sorted(user_tasks.get(user_id, []), key=lambda t: t['deadline'])
    if not tasks:
        bot.send_message(message.chat.id, "📭 У тебя пока нет задач.")
        return
    for idx, task in enumerate(tasks, 1):
        status = "✅" if task["done"] else "❗️"
        deadline = task["deadline"].strftime('%d.%m %H:%M')
        text = f"{idx}. {status} {task['task']} (до {deadline})"
        if not task["done"]:
            markup = types.InlineKeyboardMarkup()
            btn = types.InlineKeyboardButton("✅ Выполнено", callback_data=f"done_{idx}")
            markup.add(btn)
            bot.send_message(message.chat.id, text, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, text)

# Завершение задачи
@bot.callback_query_handler(func=lambda call: call.data.startswith("done_"))
def callback_done(call):
    user_id = call.from_user.id
    index = int(call.data.split("_")[1]) - 1
    try:
        user_tasks[user_id][index]["done"] = True
        bot.answer_callback_query(call.id, "Задача завершена!")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id, f"✅ Задача #{index+1} завершена.")
    except:
        bot.answer_callback_query(call.id, "Ошибка.")

# Редактировать
@bot.message_handler(commands=['edit'])
def edit_task(message):
    user_id = message.from_user.id
    parts = message.text.split(" ", 2)
    if len(parts) < 3:
        bot.reply_to(message, "⚠️ Формат: `/edit 1 Новый текст до 26.05 12:00`", parse_mode="Markdown")
        return
    try:
        index = int(parts[1]) - 1
        new_text = parts[2]
        task_text, deadline_str = new_text.rsplit("до", 1)
        deadline = datetime.strptime(deadline_str.strip(), "%d.%m %H:%M")
        user_tasks[user_id][index]["task"] = task_text.strip()
        user_tasks[user_id][index]["deadline"] = deadline
        bot.reply_to(message, f"📝 Обновлено: #{index+1}")
    except:
        bot.reply_to(message, "❌ Ошибка редактирования. Проверь формат.")

# Удаление
@bot.message_handler(commands=['delete'])
def delete_task(message):
    user_id = message.from_user.id
    try:
        index = int(message.text.split()[1]) - 1
        task = user_tasks[user_id].pop(index)
        bot.reply_to(message, f"🗑️ Удалено: {task['task']}")
    except:
        bot.reply_to(message, "⚠️ Формат: `/delete 1`", parse_mode="Markdown")

# Очистить все
@bot.message_handler(commands=['clear_tasks'])
@bot.message_handler(func=lambda m: m.text == "🧹 Очистить задачи")
def clear_tasks(message):
    user_id = message.from_user.id
    user_tasks[user_id] = []
    bot.send_message(message.chat.id, "🧹 Все задачи удалены.")

# 🍅 Pomodoro
@bot.message_handler(commands=['pomodoro'])
@bot.message_handler(func=lambda m: m.text == "🍅 Pomodoro")
def start_pomodoro(message):
    bot.send_message(message.chat.id, "🍅 Pomodoro начат! 25 минут фокуса...")
    def timer():
        time.sleep(25 * 60)
        bot.send_message(message.chat.id, "⏰ Время вышло! Перерыв 5 минут.")
    threading.Thread(target=timer).start()

# 🔗 Сохранить ссылку
@bot.message_handler(commands=['save'])
def save_link(message):
    user_id = message.from_user.id
    try:
        url, name = message.text[6:].strip().split(" ", 1)
        user_links.setdefault(user_id, []).append({"name": name, "url": url})
        bot.reply_to(message, f"🔖 Сохранено: {name} – {url}")
    except:
        bot.reply_to(message, "⚠️ Формат: `/save https://site.com Название`", parse_mode="Markdown")

# 🌐 Показать ссылки
@bot.message_handler(commands=['links'])
@bot.message_handler(func=lambda m: m.text == "🔗 Ссылки")
def show_links(message):
    user_id = message.from_user.id
    links = user_links.get(user_id, [])
    if not links:
        bot.send_message(message.chat.id, "📭 Нет сохранённых ссылок.")
        return
    result = "🔗 *Ссылки:*\n"
    for idx, link in enumerate(links, 1):
        result += f"{idx}. [{link['name']}]({link['url']})\n"
    bot.send_message(message.chat.id, result, parse_mode="Markdown")

# 📅 Задачи по дням недели
@bot.message_handler(commands=['week'])
def week_tasks(message):
    user_id = message.from_user.id
    tasks = user_tasks.get(user_id, [])
    if not tasks:
        bot.send_message(message.chat.id, "📭 У тебя нет задач.")
        return

    week = {day: [] for day in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]}
    for task in tasks:
        day = task["deadline"].strftime('%a')
        rus_day = {"Mon": "Пн", "Tue": "Вт", "Wed": "Ср", "Thu": "Чт", "Fri": "Пт", "Sat": "Сб", "Sun": "Вс"}.get(day)
        if rus_day:
            week[rus_day].append(task)

    msg = "📅 *Задачи на неделю:*\n\n"
    for day in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]:
        msg += f"*{day}:*\n"
        if week[day]:
            for t in week[day]:
                time = t["deadline"].strftime("%H:%M")
                status = "✅" if t["done"] else "❗"
                msg += f"- {status} {t['task']} ({time})\n"
        else:
            msg += "–\n"
        msg += "\n"
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

# 💬 Цитата
@bot.message_handler(commands=['motivate'])
def send_quote(message):
    quote = random.choice(quotes)
    bot.send_message(message.chat.id, f"💬 {quote}")

# ⏰ Проверка дедлайнов и рассылка цитат
def check_deadlines():
    now = datetime.now()
    for user_id, tasks in user_tasks.items():
        for task in tasks:
            if not task["done"]:
                time_left = task["deadline"] - now
                if timedelta(minutes=59) < time_left < timedelta(hours=1, minutes=1):
                    bot.send_message(user_id, f"⏰ Напоминание: '{task['task']}' через 1 час!")

def send_daily_quotes():
    quote = random.choice(quotes)
    for user_id in user_ids:
        bot.send_message(user_id, f"☀️ Доброе утро!\n💬 {quote}")

# Планировщик
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(10)

schedule.every(1).minutes.do(check_deadlines)
schedule.every().day.at("09:00").do(send_daily_quotes)
threading.Thread(target=run_schedule, daemon=True).start()

# Обработка всего остального
@bot.message_handler(func=lambda message: True)
def default_handler(message):
    bot.send_message(message.chat.id, "🤖 Не понял. Вот доступные команды:", reply_markup=main_keyboard())
    send_help(message)

# Запуск
print("✅ Бот запущен")
bot.polling()