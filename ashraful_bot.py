import logging
import json
import os
import random
from datetime import datetime

import pytz
from openai import OpenAI

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

# ======================================
# TOKENS
# ======================================

TELEGRAM_TOKEN = "8899945317:AAFd-hgwL6x21dJ6F8vUJmFL8o7muBgM54E"
GEMINI_API_KEY = "AIzaSyBjbucBgNwMYWm1pAqSueQVHso2YRrOGpU"

YOUR_CHAT_ID = 1127540715
TASKS_FILE = "tasks.json"

# ======================================
# TIMEZONE
# ======================================

timezone = pytz.timezone("Asia/Dhaka")

# ======================================
# LOGGING
# ======================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ======================================
# GEMINI AI
# ======================================

OPENROUTER_API_KEY = "YOUR_OPENROUTER_API_KEY"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)
# ======================================
# MEMORY
# ======================================

user_state = {}

# ======================================
# FILE FUNCTIONS
# ======================================

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

# ======================================
# MAIN MENU
# ======================================

def main_menu():

    keyboard = [

        [
            InlineKeyboardButton("➕ Add Task", callback_data="add_task"),
            InlineKeyboardButton("📋 Tasks", callback_data="list_tasks")
        ],

        [
            InlineKeyboardButton("🔥 Focus Mode", callback_data="focus_mode"),
            InlineKeyboardButton("📊 Stats", callback_data="stats")
        ],

        [
            InlineKeyboardButton("🤖 AI Assistant", callback_data="chat_ai")
        ],

        [
            InlineKeyboardButton("🗑 Delete Task", callback_data="delete_task")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)

# ======================================
# START
# ======================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(

        "🔥 Advanced Productivity Assistant\n\n"
        "📚 Study • Focus • AI • Reminders\n\n"
        "Welcome Ashraful ভাই 😄",

        reply_markup=main_menu()
    )

# ======================================
# BUTTON HANDLER
# ======================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    chat_id = query.message.chat_id
    data = query.data

    # ==================================
    # ADD TASK
    # ==================================

    if data == "add_task":

        user_state[chat_id] = {
            "step": "waiting_name"
        }

        await query.message.reply_text(
            "📌 Task এর নাম লেখো 😄"
        )

    # ==================================
    # TASK LIST
    # ==================================

    elif data == "list_tasks":

        tasks = load_tasks()

        if not tasks:

            await query.message.reply_text(
                "😢 কোনো task নেই",
                reply_markup=main_menu()
            )

            return

        msg = "📋 Your Tasks\n\n"

        for i, task in enumerate(tasks, start=1):

            msg += (
                f"{i}. 📌 {task['name']}\n"
                f"⏰ {task['time']}\n\n"
            )

        await query.message.reply_text(
            msg,
            reply_markup=main_menu()
        )

    # ==================================
    # DELETE TASK
    # ==================================

    elif data == "delete_task":

        tasks = load_tasks()

        if not tasks:

            await query.message.reply_text(
                "😢 কোনো task নেই",
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

        await query.message.reply_text(
            "🗑 কোন task delete করবে?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ==================================
    # DELETE CONFIRM
    # ==================================

    elif data.startswith("del_"):

        idx = int(data.split("_")[1])

        tasks = load_tasks()

        if idx < len(tasks):

            name = tasks[idx]["name"]

            tasks.pop(idx)

            save_tasks(tasks)

            await query.message.reply_text(
                f"✅ {name} deleted",
                reply_markup=main_menu()
            )

    # ==================================
    # STATS
    # ==================================

    elif data == "stats":

        tasks = load_tasks()

        msg = (
            "📊 Productivity Dashboard\n\n"
            f"📌 Total Tasks: {len(tasks)}\n"
            "🔥 Focus Level: High\n"
            "📚 Keep studying consistently 😄"
        )

        await query.message.reply_text(
            msg,
            reply_markup=main_menu()
        )

    # ==================================
    # FOCUS MODE
    # ==================================

    elif data == "focus_mode":

        await query.message.reply_text(
            "🔥 Focus Mode Activated\n\n"
            "📚 Study for 45 minutes\n"
            "📵 Avoid distractions\n\n"
            "💪 You can do it ভাই 😄"
        )

    # ==================================
    # AI CHAT
    # ==================================

    elif data == "chat_ai":

        user_state[chat_id] = {
            "step": "chatting"
        }

        await query.message.reply_text(
            "🤖 AI Assistant Active\n\n"
            "যা খুশি জিজ্ঞেস করো 😄\n"
            "ফিরে যেতে /start লেখো"
        )

    # ==================================
    # EVERYDAY TASK
    # ==================================

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
                f"✅ Task Saved\n\n"
                f"📌 {state['name']}\n"
                f"⏰ {state['time']}\n"
                f"🔁 Everyday",
                reply_markup=main_menu()
            )

# ======================================
# MESSAGE HANDLER
# ======================================

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id

    text = update.message.text.strip()

    state = user_state.get(chat_id, {})

    # ==================================
    # AI CHAT
    # ==================================

    if state.get("step") == "chatting":

        await update.message.reply_text("🤖 Thinking...")

        try:
response = client.chat.completions.create(

    model="deepseek/deepseek-chat-v3-0324:free",

    messages=[

        {
            "role": "system",
            "content": "তুমি Ashraful ভাই এর smart AI assistant। বাংলায় সুন্দরভাবে উত্তর দাও।"
        },

        {
            "role": "user",
            "content": text
        }
    ]
)

reply = response.choices[0].message.content

await update.message.reply_text(reply)

        except Exception as e:

            await update.message.reply_text(
                f"Error: {str(e)}"
            )

        return

    # ==================================
    # TASK NAME
    # ==================================

    if state.get("step") == "waiting_name":

        user_state[chat_id] = {
            "step": "waiting_time",
            "name": text
        }

        await update.message.reply_text(
            "⏰ Time লেখো\n\n"
            "Example:\n"
            "09:00\n"
            "21:30"
        )

        return

    # ==================================
    # TASK TIME
    # ==================================

    if state.get("step") == "waiting_time":

        try:
            datetime.strptime(text, "%H:%M")

        except ValueError:

            await update.message.reply_text(
                "❌ ভুল format\n\n"
                "এভাবে লেখো:\n"
                "09:00"
            )

            return

        user_state[chat_id]["time"] = text

        keyboard = [[
            InlineKeyboardButton(
                "🔁 Everyday",
                callback_data="everyday"
            )
        ]]

        await update.message.reply_text(
            "✅ Reminder সেট হবে 😄",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    await update.message.reply_text(
        "👇 নিচে থেকে option বেছে নাও",
        reply_markup=main_menu()
    )

# ======================================
# SEND REMINDERS
# ======================================

async def send_reminders(context: ContextTypes.DEFAULT_TYPE):

    print("Checking reminders...")

    tasks = load_tasks()

    current_time = datetime.now(timezone).strftime("%H:%M")

    today = datetime.now(timezone).strftime("%Y-%m-%d")

    changed = False

    for task in tasks:

        last_sent = task.get("last_sent", "")

        if task["time"] == current_time and last_sent != today:

            msg = (
                "🔥 Reminder Time!\n\n"
                f"📌 Task: {task['name']}\n"
                f"⏰ Time: {task['time']}\n\n"
                "💪 Stay focused ভাই 😄"
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

# ======================================
# MAIN
# ======================================

def main():

    app = Application.builder().token(TELEGRAM_TOKEN).build()

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

    # Reminder checker

    app.job_queue.run_repeating(
        send_reminders,
        interval=20,
        first=5
    )

    print("🔥 Bot Started Successfully 😄")

    app.run_polling(drop_pending_updates=True)

# ======================================
# RUN
# ======================================

if __name__ == "__main__":

    main()
