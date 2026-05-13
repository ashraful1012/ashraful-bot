import logging
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import google.generativeai as genai

# ─── CONFIG ───────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = "8899945317:AAFd-hgwL6x21dJ6F8vUJmFL8o7muBgM54E"
GEMINI_API_KEY = "AIzaSyBwc1esYQ-wbWLZH442vCw2YmpkHahcbB0"
YOUR_CHAT_ID   = 1127540715
TASKS_FILE     = "tasks.json"

# ─── GEMINI SETUP ─────────────────────────────────────────────────────────────
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── TASK STORAGE ─────────────────────────────────────────────────────────────
def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    return []

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

# ─── USER STATE (for multi-step task creation) ────────────────────────────────
user_state = {}

# ─── /start ───────────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ নতুন Task যোগ করো", callback_data="add_task")],
        [InlineKeyboardButton("📋 সব Task দেখো",       callback_data="list_tasks")],
        [InlineKeyboardButton("🗑️ Task মুছে দাও",      callback_data="delete_task")],
        [InlineKeyboardButton("🤖 AI এর সাথে কথা বলো", callback_data="chat_ai")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🌟 *আসসালামু আলাইকুম Ashraful ভাই!*\n\n"
        "আমি তোমার Personal Assistant Bot 🤖\n"
        "কী করতে চাও নিচে থেকে বেছে নাও 👇",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# ─── CALLBACK HANDLER ─────────────────────────────────────────────────────────
async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    data = query.data

    if data == "add_task":
        user_state[chat_id] = {"step": "waiting_task_name"}
        await query.message.reply_text(
            "✏️ *নতুন Task এর নাম লেখো:*\n\nযেমন: BCS English পড়া, Exercise, ঘুম",
            parse_mode="Markdown"
        )

    elif data == "list_tasks":
        tasks = load_tasks()
        if not tasks:
            await query.message.reply_text("📭 এখনো কোনো task নেই! ➕ Add করো।")
            return
        msg = "📋 *তোমার সব Task:*\n\n"
        for i, t in enumerate(tasks, 1):
            days_str = ", ".join(t.get("days", ["প্রতিদিন"]))
            msg += f"{i}. *{t['name']}*\n   ⏰ {t['time']} | 📅 {days_str}\n\n"
        await query.message.reply_text(msg, parse_mode="Markdown")

    elif data == "delete_task":
        tasks = load_tasks()
        if not tasks:
            await query.message.reply_text("📭 কোনো task নেই মুছতে!")
            return
        keyboard = []
        for i, t in enumerate(tasks):
            keyboard.append([InlineKeyboardButton(
                f"🗑️ {t['name']} ({t['time']})", callback_data=f"del_{i}"
            )])
        await query.message.reply_text(
            "কোনটা মুছবে?", reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("del_"):
        idx = int(data.split("_")[1])
        tasks = load_tasks()
        if idx < len(tasks):
            removed = tasks.pop(idx)
            save_tasks(tasks)
            await query.message.reply_text(f"✅ *{removed['name']}* মুছে দেওয়া হয়েছে!", parse_mode="Markdown")

    elif data == "chat_ai":
        user_state[chat_id] = {"step": "chatting"}
        await query.message.reply_text(
            "🤖 *Gemini AI চালু!*\n\nযা খুশি জিজ্ঞেস করো। বাংলায় করলেও বুঝবে!\n\n"
            "Chat শেষ করতে /start লেখো।",
            parse_mode="Markdown"
        )

    elif data.startswith("days_"):
        # Day selection for task
        day = data.replace("days_", "")
        state = user_state.get(chat_id, {})
        if "selected_days" not in state:
            state["selected_days"] = []
        if day == "done":
            # Save task with selected days
            tasks = load_tasks()
            selected = state.get("selected_days", ["প্রতিদিন"])
            tasks.append({
                "name": state["task_name"],
                "time": state["task_time"],
                "days": selected if selected else ["প্রতিদিন"]
            })
            save_tasks(tasks)
            user_state.pop(chat_id, None)
            await query.message.reply_text(
                f"✅ *Task সেভ হয়ে গেছে!*\n\n"
                f"📌 {state['task_name']}\n"
                f"⏰ {state['task_time']}\n"
                f"📅 {', '.join(selected) if selected else 'প্রতিদিন'}",
                parse_mode="Markdown"
            )
        elif day == "everyday":
            state["selected_days"] = ["প্রতিদিন"]
            tasks = load_tasks()
            tasks.append({
                "name": state["task_name"],
                "time": state["task_time"],
                "days": ["প্রতিদিন"]
            })
            save_tasks(tasks)
            user_state.pop(chat_id, None)
            await query.message.reply_text(
                f"✅ *Task সেভ হয়ে গেছে!*\n\n"
                f"📌 {state['task_name']}\n"
                f"⏰ {state['task_time']}\n📅 প্রতিদিন",
                parse_mode="Markdown"
            )
        else:
            if day in state["selected_days"]:
                state["selected_days"].remove(day)
            else:
                state["selected_days"].append(day)
            user_state[chat_id] = state
            await query.message.reply_text(
                f"✔️ *{day}* সিলেক্ট হয়েছে!\nআরো দিন বাছো অথবা ✅ Done চাপো।"
            )

# ─── MESSAGE HANDLER ──────────────────────────────────────────────────────────
async def message_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text.strip()
    state = user_state.get(chat_id, {})

    # ── AI Chat mode ──
    if state.get("step") == "chatting":
        await update.message.reply_text("🤔 ভাবছি...")
        try:
            response = model.generate_content(
                f"তুমি Ashraful ভাই এর personal AI assistant। বাংলায় উত্তর দাও। প্রশ্ন: {text}"
            )
            await update.message.reply_text(response.text)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        return

    # ── Task creation flow ──
    if state.get("step") == "waiting_task_name":
        user_state[chat_id] = {"step": "waiting_task_time", "task_name": text}
        await update.message.reply_text(
            f"✅ Task: *{text}*\n\n"
            "⏰ এখন সময় লেখো (24-ঘণ্টা format এ):\n\nযেমন: `09:00` বা `21:30`",
            parse_mode="Markdown"
        )
        return

    if state.get("step") == "waiting_task_time":
        # Validate time format
        try:
            datetime.strptime(text, "%H:%M")
        except ValueError:
            await update.message.reply_text("❌ সময়ের format ঠিক নেই! এভাবে লেখো: `09:00`", parse_mode="Markdown")
            return

        user_state[chat_id]["task_time"] = text
        user_state[chat_id]["step"] = "waiting_days"

        keyboard = [
            [InlineKeyboardButton("📅 প্রতিদিন", callback_data="days_everyday")],
            [
                InlineKeyboardButton("শনি", callback_data="days_শনি"),
                InlineKeyboardButton("রবি", callback_data="days_রবি"),
                InlineKeyboardButton("সোম", callback_data="days_সোম"),
                InlineKeyboardButton("মঙ্গল", callback_data="days_মঙ্গল"),
            ],
            [
                InlineKeyboardButton("বুধ", callback_data="days_বুধ"),
                InlineKeyboardButton("বৃহস্পতি", callback_data="days_বৃহস্পতি"),
                InlineKeyboardButton("শুক্র", callback_data="days_শুক্র"),
            ],
            [InlineKeyboardButton("✅ Done", callback_data="days_done")],
        ]
        await update.message.reply_text(
            "📅 কোন দিন reminder চাও?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Default — show menu
    keyboard = [
        [InlineKeyboardButton("➕ নতুন Task যোগ করো", callback_data="add_task")],
        [InlineKeyboardButton("📋 সব Task দেখো",       callback_data="list_tasks")],
        [InlineKeyboardButton("🗑️ Task মুছে দাও",      callback_data="delete_task")],
        [InlineKeyboardButton("🤖 AI এর সাথে কথা বলো", callback_data="chat_ai")],
    ]
    await update.message.reply_text(
        "নিচ থেকে বেছে নাও 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ─── SCHEDULER: Send reminders ────────────────────────────────────────────────
async def send_reminders(app):
    tasks = load_tasks()
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    day_map = {0: "সোম", 1: "মঙ্গল", 2: "বুধ", 3: "বৃহস্পতি", 4: "শুক্র", 5: "শনি", 6: "রবি"}
    today = day_map[now.weekday()]

    for task in tasks:
        if task["time"] == current_time:
            days = task.get("days", ["প্রতিদিন"])
            if "প্রতিদিন" in days or today in days:
                messages = [
                    f"🔔 ভাই! এখন *{task['name']}* এর সময় হয়েছে! উঠুন! 💪",
                    f"⏰ Reminder: *{task['name']}* — এখনই শুরু করুন ভাই! 🚀",
                    f"📢 ভাই, *{task['name']}* বাকি আছে! ফোন রাখুন, কাজে লাগুন! 😄",
                ]
                import random
                msg = random.choice(messages)
                await app.bot.send_message(
                    chat_id=YOUR_CHAT_ID,
                    text=msg,
                    parse_mode="Markdown"
                )

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Scheduler — check every minute
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_reminders,
        "interval",
        minutes=1,
        args=[app]
    )
    scheduler.start()

    print("✅ Bot চালু হয়েছে! Telegram এ /start লেখো।")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
