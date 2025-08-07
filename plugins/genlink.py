from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import string
import re
from info import ADMINS, PUBLIC_FILE_STORE
from utils import temp

async def allowed(_, __, message):
    if PUBLIC_FILE_STORE:
        return True
    if message.from_user and message.from_user.id in ADMINS:
        return True
    return False

@Client.on_message(filters.command(["sbatch"]) & filters.create(allowed))
async def gen_sbatch_links(bot, message):
    if " " not in message.text:
        return await message.reply("❌ Format:\n<code>/sbatch https://t.me/yourchannel/100 https://t.me/yourchannel/110</code>")

    parts = message.text.strip().split(" ")
    if len(parts) != 3:
        return await message.reply("❌ Use correct format:\n<code>/sbatch https://t.me/.../123 https://t.me/.../456</code>")

    _, first, last = parts

    # Full link matcher: supports t.me/c/... and t.me/channel/...
    regex = re.compile(r"https?://t\.me/(c/)?([a-zA-Z0-9_]+)/(\d+)")
    
    # Match first
    match1 = regex.match(first)
    if not match1:
        return await message.reply("❌ Invalid first message link.")
    is_private = match1.group(1) == "c/"
    f_chat = match1.group(2)
    f_msg_id = int(match1.group(3))
    if is_private:
        f_chat = int("-100" + f_chat)

    # Match second
    match2 = regex.match(last)
    if not match2:
        return await message.reply("❌ Invalid second message link.")
    is_private2 = match2.group(1) == "c/"
    l_chat = match2.group(2)
    l_msg_id = int(match2.group(3))
    if is_private2:
        l_chat = int("-100" + l_chat)

    # Both messages must be in the same channel
    if f_chat != l_chat:
        return await message.reply("❌ Both messages must be from the same channel.")

    # Try accessing chat
    try:
        await bot.get_chat(f_chat)
    except Exception as e:
        return await message.reply(f"❌ Could not access chat:\n<code>{e}</code>")

    # Collect media messages
    files = []
    async for msg in bot.iter_messages(f_chat, min_id=min(f_msg_id, l_msg_id)-1, max_id=max(f_msg_id, l_msg_id)+1):
        if msg.empty or msg.service or not msg.media:
            continue
        file_type = msg.media
        file = getattr(msg, file_type.value)
        if file:
            files.append({
                "file_id": file.file_id,
                "file_name": getattr(file, "file_name", "Unnamed"),
                "file_size": file.file_size
            })

    if not files:
        return await message.reply("⚠️ No media found between the given message IDs.")

    # Generate keyword and store in temp
    keyword = f"sbatch_{message.from_user.id}_{''.join(random.choices(string.ascii_lowercase, k=4))}"
    temp.GETALL[keyword] = files

    await message.reply(
        f"✅ `{len(files)}` files indexed.\nClick below to browse in inline mode.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 View Files", switch_inline_query_current_chat=keyword)]
        ])
    )
    
