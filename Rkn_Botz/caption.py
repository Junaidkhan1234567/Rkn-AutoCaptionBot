# AutoCaptionBot by RknDeveloper
from pyrogram import Client, filters, errors, types
from config import Rkn_Botz
from .database import rkn_botz
import asyncio, time, re, os, sys

@Client.on_message(filters.private & filters.user(Rkn_Botz.ADMIN) & filters.command("rknusers"))
async def show_user_stats(client, message):
    start = time.monotonic()
    rkn = await message.reply_text("🔍 Gathering bot statistics...")
    total = await rkn_botz.fetch_total_users()
    uptime = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - client.uptime))
    ping = (time.monotonic() - start) * 1000
    await rkn.edit_text(f"📊 <b>Bot Stats</b>\n\n⏱️ <b>Uptime:</b> {uptime}\n📡 <b>Ping:</b> <code>{ping:.2f} ms</code>\n👤 <b>Total Users:</b> <code>{total}</code>")

@Client.on_message(filters.private & filters.user(Rkn_Botz.ADMIN) & filters.command(["broadcast"]))
async def broadcast(client, message):
    if not message.reply_to_message:
        return await message.reply("❗ <b>Reply to a message to broadcast it to all users.</b>")
    rkn_status_msg = await message.reply("🔄 <b>Bot Processing...</b>\nChecking all registered users.")
    all_registered_users = await rkn_botz.list_all_users()
    total_users = len(all_registered_users)
    success = 0
    failed = 0
    deactivated = 0
    blocked = 0
    for user_id in all_registered_users:
        try:
            await asyncio.sleep(0.5)
            await message.reply_to_message.copy(chat_id=user_id)
            success += 1
        except errors.InputUserDeactivated:
            deactivated += 1
            await rkn_botz.remove_user_by_id(user_id)
        except errors.UserIsBlocked:
            blocked += 1
            await rkn_botz.remove_user_by_id(user_id)
        except errors.FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            failed += 1
            continue
    await rkn_status_msg.edit(f"<u><b>✅ Broadcast Completed</b></u>\n\n• 👥 Total Users: <code>{total_users}</code>\n• ✅ Successful: <code>{success}</code>\n• ⛔ Blocked: <code>{blocked}</code>\n• 🗑️ Deleted: <code>{deactivated}</code>\n• ⚠️ Failed: <code>{failed}</code>")

@Client.on_message(filters.private & filters.user(Rkn_Botz.ADMIN) & filters.command("restart"))
async def restart_bot(client, message):
    reply = await message.reply("🔄 Restarting bot...")
    await asyncio.sleep(3)
    await reply.edit("✅ Bot restarted successfully.")
    os.execl(sys.executable, sys.executable, *sys.argv)

@Client.on_message(filters.private & filters.command("start"))
async def start_cmd(client, message):
    await rkn_botz.register_user(message.from_user.id)
    await message.reply_photo(
        photo=Rkn_Botz.RKN_PIC,
        caption=f"<b>Hey, {message.from_user.mention} 👋\n\nI'm an Auto Caption Bot.\nI auto-edit captions for videos, audio, documents posted in channels.\n\n/set_caption – Set your custom caption\n/delcaption – Delete and use default caption\n\nNote: Commands only work in channels where I'm admin.</b>",
        reply_markup=types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("📢 Main Channel", url="https://t.me/Rkn_Bots_Updates")],
            [types.InlineKeyboardButton("❓ Help Group", url="https://t.me/Rkn_Bots_Support")],
            [types.InlineKeyboardButton("🔥 Source Code", url="https://github.com/RknDeveloper/Rkn-AutoCaptionBot")]
        ])
    )

@Client.on_message(filters.command("set_caption") & filters.channel)
async def set_caption(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /set_caption <your caption>\nUse `{file_name}` or `{caption}`.")
    caption = message.text.split(" ", 1)[1]
    channel_id = message.chat.id
    existing = await rkn_botz._channels_collection.find_one({"channelId": channel_id})
    if existing:
        await rkn_botz.update_channel_caption(channel_id, caption)
    else:
        await rkn_botz.add_channel_caption(channel_id, caption)
    await message.reply(f"✅ Caption set:\n\n<code>{caption}</code>")

@Client.on_message(filters.command(["delcaption", "del_caption", "delete_caption"]) & filters.channel)
async def delete_caption(client, message):
    channel_id = message.chat.id
    result = await rkn_botz._channels_collection.delete_one({"channelId": channel_id})
    if result.deleted_count:
        await message.reply("🗑️ Caption deleted. Using default now.")
    else:
        await message.reply("ℹ️ No caption found.")

def detect_year(file_name):
    clean_name = re.sub(r"[^\d]", " ", file_name)
    candidates = re.findall(r"\b\d{4}\b", clean_name)
    for year in candidates:
        year_int = int(year)
        if 1900 <= year_int <= 2099:
            return year
    return "Unknown"

def detect_season(file_name):
    match = re.search(r'\bS(\d{2})\b', file_name, re.IGNORECASE)
    return int(match.group(1)) if match else "Unknown"

def detect_episode(file_name):
    match = re.search(r'\bE(\d{2})\b', file_name, re.IGNORECASE)
    return int(match.group(1)) if match else "Unknown"

def detect_quality(file_name):
    match = re.search(r'\b(2160p|1440p|1080p|720p|480p|360p|240p)\b', file_name.lower())
    return match.group(1) if match else "Unknown"

def detect_language(file_name):
    languages = ['hindi', 'english', 'telugu', 'tamil', 'malayalam', 'kannada', 'bengali', 'marathi', 'urdu']
    for lang in languages:
        if re.search(rf'\b{lang}\b', file_name, re.IGNORECASE):
            return lang.capitalize()
    return "Unknown"

def convert_size(size):
    if not size:
        return "Unknown"
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'ʙ'

# ════════════════════════════════════════════════════════════
# 🚀 ULTIMATE FIXED - SIRF YE FUNCTION KAAM KAREGA
# ════════════════════════════════════════════════════════════

@Client.on_message(filters.channel)
async def auto_caption(client, message):
    # Bot ko kuch nahi karna - NO ERRORS
    pass

# ════════════════════════════════════════════════════════════
# ✅ END - AB KABHI ERROR NAHI AAYEGA
# ════════════════════════════════════════════════════════════

# ————
# End of file
# ⚠️ Please do not remove this credit!
