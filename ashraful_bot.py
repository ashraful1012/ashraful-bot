import logging
import json
import os
import random
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import google.generativeai as genai

TELEGRAM_TOKEN = "8899945317:AAFd-hgwL6x21dJ6F8vUJmFL8o7muBgM54E"
GEMINI_API_KEY = "AIzaSyBwc1esYQ-wbWLZH442vCw2YmpkHahcbB0"
YOUR_CHAT_ID = 1127540715
TASKS_FILE = "tasks.json"

genai.configure(api_key=GEMINI_API_KEY)
gemini = genai.GenerativeModel("gemini-2.0-flash")
logging.basicConfig(level=logging.INFO)
user_state = {}

def load_tasks():
    try:
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return []

def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def main_menu():
    keyboard = [
        [InlineKeyboardButton("+ নতুন Task যোগ করো", callback_data="add_task")],
        [InlineKeyboardButton("📋 সব Task দেখো", callback_data="list_tasks")],
        [InlineKeyboardButton("🗑 Task মুছে দাও", callback_data="delete_task")],
        [InlineKeyboardButton("🤖 AI এর সাথে কথা বলো", callback_data="chat_ai")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "আসসালামু আলাইকুম Ashraful ভাই!\n\nআমি তোমার Personal Assistant Bot\nকী করতে চাও নিচে থেকে বেছে নাও",
        reply_markup=main_menu()
    )

async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    data = query.data

    if data == "add_task":
        user_state[chat_id] = {"step": "waiting_name"}
        await query.message.reply_text("Task এর নাম লেখো:\nযেমন: BCS পড়া, Exercise, ঘুম")

    elif data == "list_tasks":
        tasks = load_tasks()
        if not tasks:
            await query.message.reply_text("কোনো task নেই! Add করো।", reply_markup=main_menu())
            return
        msg = "তোমার Tasks:\n\n"
        for i, t in enumerate(tasks, 1):
            days = ", ".join(t.get("days", ["প্রতিদিন"]))
            msg += f"{i}. {t['name']} — {t['time']} | {days}\n"
        await query.message.reply_text(msg, reply_markup=main_menu())

    elif data == "delete_task":
        tasks = load_tasks()
        if not tasks:
            await query.message.reply_text("কোনো task নেই!", reply_markup=main_menu())
            return
        keyboard = [[InlineKeyboardButton(f"X {t['name']} ({t['time']})", callback_data=f"del_{i}")] for i, t in enumerate(tasks)]
        keyboard.append([InlineKeyboardButton("Back", callback_data="back")])
        await query.message.reply_text("কোনটা মুছবে?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("del_"):
        idx = int(data.split("_")[1])
        tasks = load_tasks()
        if idx < len(tasks):
            name = tasks[idx]["name"]
            tasks.pop(idx)
            save_tasks(tasks)
            await query.message.reply_text(f"{name} মুছে গেছে!", reply_markup=main_menu())

    elif data == "chat_ai":
        user_state[chat_id] = {"step": "chatting"}
        await query.message.reply_text("Gemini AI চালু!\n\nযা খুশি জিজ্ঞেস করো। ফিরে যেতে /start লেখো।")

    elif data == "everyday":
        state = user_state.get(chat_id, {})
        if state:
            tasks = load_tasks()
            tasks.append({"name": state["name"], "time": state["time"], "days": ["প্রতিদিন"]})
            save_tasks(tasks)
            user_state.pop(chat_id, None)
            await query.message.reply_text(f"Task সেভ!\n{state['name']}\n{state['time']}\nপ্রতিদিন", reply_markup=main_menu())

    elif data == "back":
        await query.message.reply_text("কী করতে চাও?", reply_markup=main_menu())

async def message_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text.strip()
    state = user_state.get(chat_id, {})

    if state.get("step") == "chatting":
        await update.message.reply_text("ভাবছি...")
        try:
            resp = gemini.generate_content(
                f"তুমি Ashraful ভাই এর personal AI assistant। সংক্ষেপে বাংলায় উত্তর দাও। প্রশ্ন: {text}"
            )
            await update.message.reply_text(resp.text)
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")
        return

    if state.get("step") == "waiting_name":
        user_state[chat_id] = {"step": "waiting_time", "name": text}
        await update.message.reply_text(f"Task: {text}\n\nসময় লেখো (যেমন: 09:00 বা 21:30)")
        return

    if state.get("step") == "waiting_time":
        try:
            datetime.strptime(text, "%H:%M")
        except ValueError:
            await update.message.reply_text("Format ঠিক নেই! এভাবে লেখো: 09:00")
            return
        user_state[chat_id]["time"] = text
        user_state[chat_id]["step"] = "waiting_days"
        keyboard = [[InlineKeyboardButton("প্রতিদিন", callback_data="everyday")]]
        await update.message.reply_text("কোন দিন reminder চাও?", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    await update.message.reply_text("কী করতে চাও?", reply_markup=main_menu())

async def send_reminders(context: ContextTypes.DEFAULT_TYPE):
    tasks = load_tasks()
    current_time = datetime.now().strftime("%H:%M")
    msgs = [
        "ভাই! এখন {name} এর সময়! উঠুন!",
        "{name} এখনই শুরু করুন ভাই!",
        "ভাই, {name} বাকি আছে! ফোন রাখুন!",
    ]
    for task in tasks:
        if task["time"] == current_time:
            msg = random.choice(msgs).format(name=task["name"])
            await context.bot.send_message(chat_id=YOUR_CHAT_ID, text=msg)
            print("Reminder checker started!")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.job_queue.run_repeating(send_reminders, interval=60, first=15)
    print("Bot চালু!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
