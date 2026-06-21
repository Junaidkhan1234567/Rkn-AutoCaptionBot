from pyrogram import Client, filters, errors
from config import Rkn_Botz
from .database import rkn_botz
import io
from PIL import Image, ImageDraw, ImageFont
import os

# ✅ SET WATERMARK
@Client.on_message(filters.command("set_watermark") & filters.channel)
async def set_watermark(client, message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply(
                "**📝 Usage:**\n"
                "/set_watermark Your Text [position] [size] [color]\n\n"
                "**Positions:** top_left, top_center, top_right, center, bottom_left, bottom_center, bottom_right\n"
                "**Size:** 10-50\n"
                "**Colors:** white, black, red, blue, green, yellow, orange, purple, pink\n\n"
                "**Example:** /set_watermark @MyChannel bottom_right 20 white"
            )
            return
        
        channel_id = message.chat.id
        args = parts[1:]
        
        # Default values
        pos = "bottom_right"
        size = 20
        color = "white"
        
        # Parse color
        colors = ['white', 'black', 'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink']
        if args and args[-1].lower() in colors:
            color = args[-1].lower()
            args = args[:-1]
        
        # Parse size
        if args and args[-1].isdigit():
            size = int(args[-1])
            if size < 5: size = 5
            if size > 50: size = 50
            args = args[:-1]
        
        # Parse position
        positions = ['top_left', 'top_center', 'top_right', 'center', 
                    'bottom_left', 'bottom_center', 'bottom_right']
        if args and args[-1].lower() in positions:
            pos = args[-1].lower()
            args = args[:-1]
        
        watermark_text = " ".join(args)
        
        if not watermark_text:
            await message.reply("❌ Please provide watermark text!")
            return
        
        # Save to database
        await rkn_botz._channels_collection.update_one(
            {"channelId": channel_id},
            {"$set": {
                "watermark_text": watermark_text,
                "watermark_position": pos,
                "watermark_size": size,
                "watermark_color": color
            }},
            upsert=True
        )
        
        await message.reply(
            f"**✅ Watermark Set Successfully!**\n\n"
            f"**Text:** `{watermark_text}`\n"
            f"**Position:** `{pos}`\n"
            f"**Size:** `{size}`\n"
            f"**Color:** `{color}`"
        )
        
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# ✅ DELETE WATERMARK
@Client.on_message(filters.command("del_watermark") & filters.channel)
async def delete_watermark(client, message):
    try:
        channel_id = message.chat.id
        await rkn_botz._channels_collection.update_one(
            {"channelId": channel_id},
            {"$unset": {
                "watermark_text": "",
                "watermark_position": "",
                "watermark_size": "",
                "watermark_color": ""
            }}
        )
        await message.reply("✅ Watermark deleted successfully!")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# ✅ WATERMARK STATUS
@Client.on_message(filters.command("watermark_status") & filters.channel)
async def watermark_status(client, message):
    try:
        channel_id = message.chat.id
        channel_data = await rkn_botz._channels_collection.find_one({"channelId": channel_id})
        
        if channel_data and channel_data.get("watermark_text"):
            await message.reply(
                f"**📊 Watermark Status**\n\n"
                f"**Text:** `{channel_data['watermark_text']}`\n"
                f"**Position:** `{channel_data.get('watermark_position', 'bottom_right')}`\n"
                f"**Size:** `{channel_data.get('watermark_size', 20)}`\n"
                f"**Color:** `{channel_data.get('watermark_color', 'white')}`"
            )
        else:
            await message.reply("ℹ️ No watermark set.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# ✅ ADD WATERMARK TO PHOTOS
@Client.on_message(filters.channel & filters.photo)
async def add_watermark(client, message):
    try:
        channel_id = message.chat.id
        channel_data = await rkn_botz._channels_collection.find_one({"channelId": channel_id})
        
        if not channel_data or not channel_data.get("watermark_text"):
            return
        
        watermark_text = channel_data["watermark_text"]
        position = channel_data.get("watermark_position", "bottom_right")
        size = channel_data.get("watermark_size", 20)
        color = channel_data.get("watermark_color", "white")
        
        # Download photo
        photo = await client.download_media(message.photo.file_id)
        
        if not photo:
            return
        
        # Add watermark
        img = Image.open(photo).convert("RGBA")
        width, height = img.size
        
        # Create overlay
        txt = Image.new('RGBA', img.size, (255,255,255,0))
        draw = ImageDraw.Draw(txt)
        
        font_size = max(10, min(int(width * size / 100), 100))
        
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # Get text size
        try:
            bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            text_width, text_height = draw.textsize(watermark_text, font=font)
        
        # Position
        padding = 20
        positions = {
            "top_left": (padding, padding),
            "top_center": ((width - text_width) // 2, padding),
            "top_right": (width - text_width - padding, padding),
            "center": ((width - text_width) // 2, (height - text_height) // 2),
            "bottom_left": (padding, height - text_height - padding),
            "bottom_center": ((width - text_width) // 2, height - text_height - padding),
            "bottom_right": (width - text_width - padding, height - text_height - padding)
        }
        
        x, y = positions.get(position, positions["bottom_right"])
        
        # Background
        bbox = (x - 10, y - 10, x + text_width + 10, y + text_height + 10)
        draw.rectangle(bbox, fill=(0, 0, 0, 100))
        
        # Color
        colors = {
            "white": (255,255,255,255),
            "black": (0,0,0,255),
            "red": (255,0,0,255),
            "blue": (0,0,255,255),
            "green": (0,255,0,255),
            "yellow": (255,255,0,255),
            "orange": (255,165,0,255),
            "purple": (128,0,128,255),
            "pink": (255,192,203,255)
        }
        text_color = colors.get(color, (255,255,255,255))
        
        draw.text((x, y), watermark_text, font=font, fill=text_color)
        
        # Combine
        final = Image.alpha_composite(img, txt).convert('RGB')
        
        # Save
        output_path = photo.replace(".", "_watermarked.")
        final.save(output_path, 'JPEG', quality=95)
        
        # Send watermarked photo
        await message.reply_photo(
            photo=output_path,
            caption=message.caption
        )
        
        # Delete original
        await message.delete()
        
        # Cleanup
        os.remove(photo)
        os.remove(output_path)
        
    except Exception as e:
        print(f"Watermark error: {e}")
