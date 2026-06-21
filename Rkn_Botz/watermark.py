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

import os
import io
import tempfile
from PIL import Image, ImageDraw, ImageFont
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Rkn_Botz
from .database import rkn_botz

# Create temp folder
TEMP_FOLDER = "temp_watermark"
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)

async def add_watermark_to_image(image_data, watermark_config):
    """
    Add text watermark to image
    """
    try:
        # Load image
        image = Image.open(io.BytesIO(image_data)).convert("RGBA")
        width, height = image.size
        
        # Create transparent overlay
        txt = Image.new('RGBA', image.size, (255,255,255,0))
        draw = ImageDraw.Draw(txt)
        
        # Set font size based on image size
        font_size = min(width, height) // watermark_config.get('size', 20)
        font_size = max(10, min(font_size, 100))  # Limit font size
        
        try:
            # Try to load custom font
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                # Try system font
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            except:
                # Fallback to default font
                font = ImageFont.load_default()
        
        # Get text bbox
        try:
            bbox = draw.textbbox((0, 0), watermark_config['text'], font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            text_width, text_height = draw.textsize(watermark_config['text'], font=font)
        
        # Position calculation
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
        
        position = watermark_config.get('position', 'bottom_right')
        x, y = positions.get(position, positions['bottom_right'])
        
        # Draw semi-transparent background for better visibility
        bbox = (x - 10, y - 10, x + text_width + 10, y + text_height + 10)
        draw.rectangle(bbox, fill=(0, 0, 0, 100))
        
        # Text color mapping
        color_map = {
            "white": (255, 255, 255, 255),
            "black": (0, 0, 0, 255),
            "red": (255, 0, 0, 255),
            "blue": (0, 0, 255, 255),
            "green": (0, 255, 0, 255),
            "yellow": (255, 255, 0, 255),
            "orange": (255, 165, 0, 255),
            "purple": (128, 0, 128, 255),
            "pink": (255, 192, 203, 255)
        }
        color = color_map.get(watermark_config.get('color', 'white'), (255, 255, 255, 255))
        
        # Draw text
        draw.text((x, y), watermark_config['text'], font=font, fill=color)
        
        # Combine images
        combined = Image.alpha_composite(image, txt)
        
        # Convert back to RGB
        combined = combined.convert('RGB')
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        combined.save(img_byte_arr, format='JPEG', quality=95)
        img_byte_arr.seek(0)
        
        return img_byte_arr.getvalue()
        
    except Exception as e:
        print(f"Watermark error: {e}")
        return None

@Client.on_message(filters.command("set_watermark") & filters.channel)
async def set_watermark(client, message):
    """
    Set watermark for channel
    /set_watermark Your Text [position] [size] [color]
    """
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply(
                "**📝 Usage:**\n"
                "/set_watermark Your Watermark Text [position] [size] [color]\n\n"
                "**Positions:** top_left, top_center, top_right, center, bottom_left, bottom_center, bottom_right\n"
                "**Size:** 10-50 (smaller number = bigger text)\n"
                "**Colors:** white, black, red, blue, green, yellow, orange, purple, pink\n\n"
                "**Example:**\n"
                "/set_watermark @MyChannel bottom_right 20 white"
            )
            return
        
        channel_id = message.chat.id
        
        # Parse arguments
        args = parts[1:]
        
        # Default values
        pos = "bottom_right"
        size = 20
        color = "white"
        
        # Check for color (last parameter)
        colors = ['white', 'black', 'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink']
        if args and args[-1].lower() in colors:
            color = args[-1].lower()
            args = args[:-1]
        
        # Check for size (last parameter if number)
        if args and args[-1].isdigit():
            size = int(args[-1])
            if size < 5: size = 5
            if size > 50: size = 50
            args = args[:-1]
        
        # Check for position (last parameter)
        positions = ['top_left', 'top_center', 'top_right', 'center', 
                    'bottom_left', 'bottom_center', 'bottom_right']
        if args and args[-1].lower() in positions:
            pos = args[-1].lower()
            args = args[:-1]
        
        # Remaining is watermark text
        watermark_text = " ".join(args)
        
        if not watermark_text:
            await message.reply("❌ Please provide watermark text!")
            return
        
        # Save to database
        success = await rkn_botz.set_channel_watermark(
            channel_id, 
            watermark_text, 
            pos, 
            size, 
            color
        )
        
        if success:
            await message.reply(
                f"**✅ Watermark Set Successfully!**\n\n"
                f"**Text:** `{watermark_text}`\n"
                f"**Position:** `{pos}`\n"
                f"**Size:** `{size}`\n"
                f"**Color:** `{color}`\n\n"
                f"🔹 To delete: /del_watermark\n"
                f"🔹 To check: /watermark_status"
            )
        else:
            await message.reply("❌ Failed to set watermark. Please try again.")
        
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

@Client.on_message(filters.command("del_watermark") & filters.channel)
async def delete_watermark(client, message):
    """
    Delete watermark for channel
    """
    try:
        channel_id = message.chat.id
        result = await rkn_botz.delete_channel_watermark(channel_id)
        
        if result:
            await message.reply("✅ Watermark deleted successfully!")
        else:
            await message.reply("ℹ️ No watermark found for this channel.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

@Client.on_message(filters.command("watermark_status") & filters.channel)
async def watermark_status(client, message):
    """
    Check watermark status for channel
    """
    try:
        channel_id = message.chat.id
        watermark = await rkn_botz.get_channel_watermark(channel_id)
        
        if watermark and watermark.get('text'):
            await message.reply(
                f"**📊 Watermark Status**\n\n"
                f"**Text:** `{watermark['text']}`\n"
                f"**Position:** `{watermark['position']}`\n"
                f"**Size:** `{watermark['size']}`\n"
                f"**Color:** `{watermark['color']}`\n\n"
                f"🔹 To delete: /del_watermark\n"
                f"🔹 To change: /set_watermark New Text"
            )
        else:
            await message.reply(
                "ℹ️ No watermark set for this channel.\n\n"
                "Set one using:\n"
                "/set_watermark Your Text bottom_right 20 white"
            )
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
