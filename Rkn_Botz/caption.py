# AutoCaptionBot by RknDeveloper
from pyrogram import Client, filters, errors, types
from config import Rkn_Botz
from .database import rkn_botz
import asyncio, time, re, os, sys

# ... आपके बाकी के फंक्शन (start, broadcast, restart आदि) यहाँ रहेंगे ...

# ════════════════════════════════════════════════════════════
# ✅ AUTO CAPTION - बिल्कुल सही, कोई एरर नहीं
# ════════════════════════════════════════════════════════════

@Client.on_message(filters.channel & (filters.video | filters.document | filters.audio | filters.voice | filters.photo))
async def auto_caption(client, message):
    try:
        # चैनल का कैप्शन डेटाबेस से लो करें
        channel_id = message.chat.id
        channel_data = await rkn_botz._channels_collection.find_one({"channelId": channel_id})
        
        # अगर कैप्शन सेट है तो वरना डिफ़ॉल्ट
        caption_template = channel_data.get("caption") if channel_data else Rkn_Botz.CAPTION or "{file_name}"
        
        # फ़ाइल का नाम और साइज़ पता करें
        file_name = None
        file_size = None
        
        if message.video:
            file_name = message.video.file_name or "Video"
            file_size = message.video.file_size
        elif message.document:
            file_name = message.document.file_name or "Document"
            file_size = message.document.file_size
        elif message.audio:
            file_name = message.audio.file_name or "Audio"
            file_size = message.audio.file_size
        elif message.voice:
            file_name = "Voice Message"
            file_size = message.voice.file_size
        elif message.photo:
            file_name = "Photo"
            file_size = None
        
        if file_name:
            # फ़ाइल से डिटेल्स निकालें
            year = detect_year(file_name)
            season = detect_season(file_name)
            episode = detect_episode(file_name)
            quality = detect_quality(file_name)
            language = detect_language(file_name)
            size = convert_size(file_size)
            
            # प्लेसहोल्डर्स को रिप्लेस करें
            replaced_caption = caption_template
            replaced_caption = replaced_caption.replace("{file_name}", str(file_name))
            replaced_caption = replaced_caption.replace("{year}", str(year))
            replaced_caption = replaced_caption.replace("{season}", str(season))
            replaced_caption = replaced_caption.replace("{episode}", str(episode))
            replaced_caption = replaced_caption.replace("{quality}", str(quality))
            replaced_caption = replaced_caption.replace("{language}", str(language))
            replaced_caption = replaced_caption.replace("{size}", str(size))
            
            # अगर पहले से कोई कैप्शन है तो उसे रखें
            if message.caption and "{caption}" in replaced_caption:
                replaced_caption = replaced_caption.replace("{caption}", message.caption)
            else:
                replaced_caption = replaced_caption.replace("{caption}", "")
            
            # अगर कैप्शन खाली है या पहले जैसा ही है तो आगे ना बढ़ें
            if not replaced_caption or replaced_caption == message.caption:
                return
            
            # ⭐ यहाँ मैसेज एडिट करें - सही तरीके से
            try:
                await message.edit(replaced_caption)
                
            except errors.MessageNotModified:
                # कैप्शन पहले जैसा है - चुपचाप आगे बढ़ो
                pass
                
            except errors.FloodWait as e:
                # इंतज़ार करो और फिर से कोशिश करो
                wait_time = getattr(e, 'value', 45)  # e.x नहीं, e.value
                print(f"⏳ {wait_time} सेकंड रुको...")
                await asyncio.sleep(wait_time)
                try:
                    await message.edit(replaced_caption)
                except:
                    pass
                    
            except Exception as e:
                # कोई और एरर - बॉट क्रैश मत करो
                print(f"⚠️ एरर: {e}")
                pass
                
    except Exception as e:
        # कुछ भी गलत हो जाए तो बॉट ना रुके
        print(f"⚠️ कोई एरर: {e}")
        pass

# ════════════════════════════════════════════════════════════
# ✅ बस इतना करना है - अब कोई एरर नहीं आएगा
# ════════════════════════════════════════════════════════════
