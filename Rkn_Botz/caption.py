# AutoCaptionBot by RknDeveloper
# Copyright (c) 2024 RknDeveloper
# Licensed under the MIT License
# https://github.com/RknDeveloper/Rkn-AutoCaptionBot/blob/main/LICENSE
# Please retain this credit when using or forking this code.

# Developer Contacts:
# Telegram: @RknDeveloperr
# Updates Channel: @Rkn_Bots_Updates & @Rkn_Botz
# Special Thanks To: @ReshamOwner
# Update Channels: @Digital_Botz & @DigitalBotz_Support

# ⚠️ Please do not remove this credit!

from pyrogram import Client, filters, errors, types
from config import Rkn_Botz
from .database import rkn_botz
import asyncio, time, re, os, sys, tempfile
from .watermark import add_watermark_to_image

@Client.on_message(filters.private & filters.user(Rkn_Botz.ADMIN) & filters.command("rknusers"))
async def show_user_stats(client, message):
    start = time.monotonic()
    rkn = await message.reply_text("🔍 Gathering bot statistics...")
    total = await rkn_botz.fetch_total_users()
    uptime = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - client.uptime))
    ping = (time.monotonic() - start) * 1000
    await rkn.edit_text(
        f"📊 <b>Bot Stats</b>\n\n"
        f"⏱️ <b>Uptime:</b> {uptime}\n"
        f"📡 <b>Ping:</b> <code>{ping:.2f} ms</code>\n"
        f"👤 <b>Total Users:</b> <code>{total}</code>"
    )
    
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
        try:
            await rkn_status_msg.edit(
                f"<u><b>📣 ʙʀᴏᴀᴅᴄᴀsᴛ ᴘʀᴏᴄᴇssɪɴɢ...</b></u>\n\n"
                f"• 👥 ᴛᴏᴛᴀʟ ᴜsᴇʀs: <code>{total_users}</code>\n"
                f"• ✅ sᴜᴄᴄᴇssғᴜʟ: <code>{success}</code>\n"
                f"• ⛔ ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs: <code>{blocked}</code>\n"
                f"• 🗑️ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs: <code>{deactivated}</code>\n"
                f"• ⚠️ ᴜɴsᴜᴄᴄᴇssғᴜʟ: <code>{failed}</code>"
            )
        except Exception:
            pass
    await rkn_status_msg.edit(
        f"<u><b>✅ ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</b></u>\n\n"
        f"• 👥 ᴛᴏᴛᴀʟ ᴜsᴇʀs: <code>{total_users}</code>\n"
        f"• ✅ sᴜᴄᴄᴇssғᴜʟ: <code>{success}</code>\n"
        f"• ⛔ ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs: <code>{blocked}</code>\n"
        f"• 🗑️ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs: <code>{deactivated}</code>\n"
        f"• ⚠️ ᴜɴsᴜᴄᴄᴇssғᴜʟ: <code>{failed}</code>"
    )

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
        caption=(
            f"<b>Hey, {message.from_user.mention} 👋\n\n"
            f"I'm an Auto Caption Bot.\n"
            f"I auto-edit captions for videos, audio, documents posted in channels.\n\n"
            f"/set_caption – Set your custom caption\n"
            f"/delcaption – Delete and use default caption\n"
            f"/set_watermark – Set watermark for images\n"
            f"/del_watermark – Delete watermark\n\n"
            f"Note: Commands only work in channels where I'm admin.</b>"
        ),
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

# ✅ MAIN AUTO CAPTION FUNCTION - FIXED
@Client.on_message(filters.channel)
async def auto_caption(client, message):
    if not message.media:
        return

    # Get file info
    for mtype in ("video", "audio", "document", "voice"):
        media = getattr(message, mtype, None)
        if media and hasattr(media, "file_name"):
            file_name = re.sub(r"@\w+", "", media.file_name or "").replace("_", " ").replace(".", " ").strip()
            file_size = getattr(media, "file_size", None)
            break
    else:
        return

    channel_id = message.chat.id
    cap_data = await rkn_botz._channels_collection.find_one({"channelId": channel_id})
    original_caption = message.caption or file_name

    try:
        # Format caption
        if cap_data and cap_data.get("caption"):
            custom_caption = cap_data.get("caption", "")
            formatted = custom_caption.format(
                file_name=file_name,
                caption=original_caption,
                language=detect_language(original_caption),
                episode=detect_episode(original_caption),
                season=detect_season(original_caption),
                year=detect_year(original_caption),
                quelty=detect_quality(original_caption),
                file_size=convert_size(file_size) if file_size else "Unknown"
            )
        else:
            formatted = Rkn_Botz.DEFAULT_CAPTION.format(
                file_name=file_name,
                caption=original_caption,
                language=detect_language(original_caption),
                episode=detect_episode(original_caption),
                season=detect_season(original_caption),
                year=detect_year(original_caption),
                quelty=detect_quality(original_caption),
                file_size=convert_size(file_size) if file_size else "Unknown"
            )
        
        # ✅ CRITICAL FIX: Check if caption is already same
        if message.caption and message.caption == formatted:
            print("✅ Caption already same, skipping edit")
            return  # Skip completely if same
        
        # ✅ Check watermark
        watermark_config = await rkn_botz.get_channel_watermark(channel_id)
        
        # Apply watermark for photos and videos
        if watermark_config and watermark_config.get('text'):
            if message.photo or (message.video and message.video.thumbs):
                try:
                    file_path = await client.download_media(message)
                    if file_path:
                        with open(file_path, 'rb') as f:
                            file_data = f.read()
                        watermarked_data = await add_watermark_to_image(file_data, watermark_config)
                        if watermarked_data:
                            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                            temp_file.write(watermarked_data)
                            temp_file.close()
                            if message.photo:
                                await client.send_photo(
                                    chat_id=message.chat.id,
                                    photo=temp_file.name,
                                    caption=formatted,
                                    reply_to_message_id=message.id
                                )
                            elif message.video:
                                await client.send_video(
                                    chat_id=message.chat.id,
                                    video=temp_file.name,
                                    caption=formatted,
                                    reply_to_message_id=message.id,
                                    supports_streaming=True
                                )
                            await message.delete()
                            os.remove(temp_file.name)
                            os.remove(file_path)
                            return
                except Exception as e:
                    print(f"Watermark error: {e}")
                    # Fall through to normal edit

        # ✅ Edit caption with error handling
        try:
            await message.edit_caption(formatted)
            print("✅ Caption edited successfully")
        except errors.MessageNotModified:
            print("ℹ️ Caption not modified, skipping")
            pass
        except errors.FloodWait as e:
            print(f"⏳ Flood wait: {e.value} seconds")
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"❌ Edit error: {e}")
            
    except errors.FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        print(f"❌ Caption error: {e}")

# ————
# End of file
# Original author: @RknDeveloperr
# GitHub: https://github.com/RknDeveloper
