```python
import logging
import json
import os
import random
from datetime import datetime

import pytz
import google.generativeai as genai

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# =========================
# YOUR TOKENS
# =========================

TELEGRAM_TOKEN = "8899945317:AAFd-hgwL6x21dJ6F8vUJmFL8o7muBgM54E"
GEMINI_API_KEY = "AIzaSyBjbucBgNwMYWm1pAqSueQVHso2YRrOGpU"

YOUR_CHAT_ID = 1127540715
TASKS_FILE = "tasks.json"

timezone = pytz.timezone("Asia/Dhaka")

# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# =========================
# GEMINI
# =========================

genai.configure(api_key=GEMINI_API_KEY)
gemini = genai.GenerativeModel("gemini-1.5-flash")

# =========================
# MEMORY
# =========================

user_state = {}

# =========================
# FILE FUNCTIONS
# =========================

def load_tasks():

    try:

        if os.path.exists(TASKS_FILE):

            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)

    except Exception as e:

        print("Load Error:", e)

    return []

def save_tasks(tasks):

    with open(TASKS_FILE, "w", encoding="utf-8") as f:

        json.dump(
            tasks,
            f,
            ensure_ascii=False,
            indent=2
        )

# =========================
# MAIN MENU
# =========================

def main_menu():

    keyboard = [

        [InlineKeyboardButton(
            "+ নতুন Task যোগ করো",
            callback_data="add_task"
        )],

        [InlineKeyboardButton(
            "📋 সব Task দেখো",
            callback_data="list_tasks"
        )],

        [InlineKeyboardButton(
            "🗑 Task মুছে দাও",
            callback_data="delete_task"
        )],

        [InlineKeyboardButton(
            "🤖 AI এর সাথে কথা বলো",
            callback_data="chat_ai"
        )]
    ]

    return InlineKeyboardMarkup(keyboard)

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(

        "আসসালামু আলাইকুম ভাই 😄\n\n"
        "আমি তোমার Personal Assistant Bot\n"
        "নিচে থেকে option বেছে নাও 👇",

        reply_markup=main_menu()
    )

# =========================
# BUTTON HANDLER
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    chat_id = query.message.chat_id
    data = query.data

    # =====================
    # ADD TASK
    # =====================

    if data == "add_task":

        user_state[chat_id] = {
            "step": "waiting_name"
        }

        await query.message.reply_text(

            "Task এর নাম লেখো 😄\n\n"
            "যেমন:\n"
            "BCS পড়া\n"
            "Exercise\n"
            "নামাজ"
        )

    # =====================
    # LIST TASKS
    # =====================

    elif data == "list_tasks":

        tasks = load_tasks()

        if not tasks:

            await query.message.reply_text(
                "কোনো task নেই 😢",
                reply_markup=main_menu()
            )

            return

        msg = "📋 তোমার Tasks\n\n"

        for i, task in enumerate(tasks, start=1):

            msg += (
                f"{i}. {task['name']} — "
                f"{task['time']}\n"
            )

        await query.message.reply_text(
            msg,
            reply_markup=main_menu()
        )

    # =====================
    # DELETE TASK
    # =====================

    elif data == "delete_task":

        tasks = load_tasks()

        if not tasks:

            await query.message.reply_text(
                "কোনো task নেই 😢",
                reply_markup=main_menu()
            )

            return

        keyboard = []

        for i, task in enumerate(tasks):

            keyboard.append([

                InlineKeyboardButton(
                    f"❌ {task['name']} ({task['time']})",
                    callback_data=f"del_{i}"
                )

            ])

        keyboard.append([

            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="back"
            )

        ])

        await query.message.reply_text(

            "কোন task মুছবে?",

            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # =====================
    # DELETE CONFIRM
    # =====================

    elif data.startswith("del_"):

        idx = int(data.split("_")[1])

        tasks = load_tasks()

        if idx < len(tasks):

            name = tasks[idx]["name"]

            tasks.pop(idx)

            save_tasks(tasks)

            await query.message.reply_text(

                f"{name} মুছে গেছে 😄",

                reply_markup=main_menu()
            )

    # =====================
    # AI CHAT
    # =====================

    elif data == "chat_ai":

        user_state[chat_id] = {
            "step": "chatting"
        }

        await query.message.reply_text(

            "🤖 AI Mode চালু!\n\n"
            "যা খুশি জিজ্ঞেস করো 😄\n"
            "ফিরে যেতে /start লেখো"
        )

    # =====================
    # EVERYDAY
    # =====================

    elif data == "everyday":

        state = user_state.get(chat_id)

        if state:

            tasks = load_tasks()

            tasks.append({

                "name": state["name"],
                "time": state["time"],
                "last_sent": ""

            })

            save_tasks(tasks)

            user_state.pop(chat_id)

            await query.message.reply_text(

                f"✅ Task Save হয়েছে\n\n"
                f"📌 {state['name']}\n"
                f"⏰ {state['time']}\n"
                f"🔁 প্রতিদিন",

                reply_markup=main_menu()
            )

    elif data == "back":

        await query.message.reply_text(

            "কি করতে চাও?",

            reply_markup=main_menu()
        )

# =========================
# MESSAGE HANDLER
# =========================

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id

    text = update.message.text.strip()

    state = user_state.get(chat_id, {})

    # =====================
    # AI CHAT
    # =====================

    if state.get("step") == "chatting":

        await update.message.reply_text("ভাবছি...")

        try:

            response = gemini.generate_content(

                f"তুমি Ashraful ভাই এর personal AI assistant। "
                f"সংক্ষেপে বাংলায় উত্তর দাও। প্রশ্ন: {text}"
            )

            await update.message.reply_text(response.text)

        except Exception as e:

            await update.message.reply_text(
                f"Error: {str(e)}"
            )

        return

    # =====================
    # TASK NAME
    # =====================

    if state.get("step") == "waiting_name":

        user_state[chat_id] = {

            "step": "waiting_time",
            "name": text
        }

        await update.message.reply_text(

            "সময় লেখো ⏰\n\n"
            "যেমন:\n"
            "09:00\n"
            "21:30"
        )

        return

    # =====================
    # TASK TIME
    # =====================

    if state.get("step") == "waiting_time":

        try:

            datetime.strptime(text, "%H:%M")

        except ValueError:

            await update.message.reply_text(

                "ভুল format 😢\n\n"
                "এভাবে লেখো:\n"
                "09:00"
            )

            return

        user_state[chat_id]["time"] = text

        keyboard = [[

            InlineKeyboardButton(
                "🔁 প্রতিদিন",
                callback_data="everyday"
            )

        ]]

        await update.message.reply_text(

            "কখন reminder দিবো?",

            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    await update.message.reply_text(

        "নিচে থেকে option বেছে নাও 👇",

        reply_markup=main_menu()
    )

# =========================
# SEND REMINDERS
# =========================

async def send_reminders(context: ContextTypes.DEFAULT_TYPE):

    print("Checking reminders...")

    tasks = load_tasks()

    current_time = datetime.now(timezone).strftime("%H:%M")

    today = datetime.now(timezone).strftime("%Y-%m-%d")

    msgs = [

        "ভাই 😄 এখন {name} এর সময়!",
        "{name} শুরু করুন 🔥",
        "📌 Reminder: {name}",
        "ভাই ফোন রাখুন 😭 {name} করুন!"
    ]

    changed = False

    for task in tasks:

        last_sent = task.get("last_sent", "")

        print("Task Time:", task["time"])
        print("Current Time:", current_time)

        if task["time"] == current_time and last_sent != today:

            msg = random.choice(msgs).format(
                name=task["name"]
            )

            try:

                await context.bot.send_message(

                    chat_id=YOUR_CHAT_ID,
                    text=msg
                )

                print("Reminder sent!")

                task["last_sent"] = today

                changed = True

            except Exception as e:

                print("Send Error:", e)

    if changed:
        save_tasks(tasks)

# =========================
# MAIN
# =========================

def main():

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # handlers

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler
        )
    )

    # reminder checker

    app.job_queue.run_repeating(

        send_reminders,

        interval=20,

        first=5
    )

    print("Bot Started 😄")

    app.run_polling(drop_pending_updates=True)

# =========================
# RUN
# =========================

if __name__ == "__main__":

    main()
```
