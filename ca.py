import os
import re
import random
import aiohttp
import asyncio
import tempfile

from telethon import TelegramClient, events, Button

# =========================
# تنظیمات
# =========================
API_ID = 8477522
API_HASH = "366c19cf69e02cad530261ad81212a85"
BOT_TOKEN = "8659591236:AAGMCysp5Ntx-L4_6XJ3tzwiNMqlPbaS6Kw"

client = TelegramClient(
    "canada_bot",
    API_ID,
    API_HASH,
    use_ipv6=False
)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

WHITELIST_FILE = os.path.join(DATA_DIR, "allowed_users.txt")

# ساخت فایل allowlist اگه وجود نداشت
if not os.path.exists(WHITELIST_FILE):
    with open(WHITELIST_FILE, "w") as f:
        f.write("5190717598\n")

user_index = {}
user_data = {}
user_state = {}
user_auto_code = {}

# =========================
# Admin & Whitelist
# =========================
ADMIN_IDS = {5190717598}


def load_whitelist():
    allowed = set()
    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line.isdigit():
                    allowed.add(int(line))
    return allowed


def save_whitelist(allowed_set):
    with open(WHITELIST_FILE, "w") as f:
        for uid in sorted(allowed_set):
            f.write(f"{uid}\n")


def is_allowed(user_id):
    if user_id in ADMIN_IDS:
        return True
    allowed = load_whitelist()
    return user_id in allowed


def add_to_whitelist(user_id):
    allowed = load_whitelist()
    allowed.add(user_id)
    save_whitelist(allowed)


def remove_from_whitelist(user_id):
    allowed = load_whitelist()
    allowed.discard(user_id)
    save_whitelist(allowed)


# =========================
# Gmail helpers
# =========================
def mixed_case(text):
    return ''.join(random.choice([c.upper(), c.lower()]) for c in text)


def get_gmail(user_id):
    gmail_path = os.path.join(DATA_DIR, f"{user_id}_gmail.txt")
    if os.path.exists(gmail_path):
        with open(gmail_path, "r") as f:
            return f.read().strip()
    return None


def save_gmail(user_id, gmail):
    gmail_path = os.path.join(DATA_DIR, f"{user_id}_gmail.txt")
    with open(gmail_path, "w") as f:
        f.write(gmail)


def delete_gmail(user_id):
    gmail_path = os.path.join(DATA_DIR, f"{user_id}_gmail.txt")
    if os.path.exists(gmail_path):
        os.remove(gmail_path)
        return True
    return False


# =========================
# Count numbers for user
# =========================
def count_numbers(user_id):
    file_path = os.path.join(DATA_DIR, f"{user_id}.txt")
    if not os.path.exists(file_path):
        return 0
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    return len(lines)


# =========================
# Panel helpers
# =========================
def get_stats_text():
    allowed = load_whitelist()
    data_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".txt") and not f.endswith("_gmail.txt") and f != "allowed_users.txt"]
    total_users = len(allowed)
    total_files = len(data_files)
    user_list = "\n".join(str(uid) for uid in sorted(allowed)) if allowed else "No users"
    return (
        "🧊 <b>ADMIN PANEL</b>\n"
        "────────────────\n"
        f"👥 Allowed Users: {total_users}\n"
        f"📁 Data Files: {total_files}\n"
        "────────────────\n"
        f"<b>User List:</b>\n<code>{user_list}</code>"
    )


# =========================
# دکمه‌ها (پریمیوم)
# =========================
def main_buttons(user_id=None):
    auto_status = "🟢 ON" if user_auto_code.get(user_id) else "🔴 OFF"
    count = count_numbers(user_id)
    return [
        [Button.inline(f"🔢  استخراج کد", b"get_code")],
        [Button.inline(f"➡️  شماره بعدی", b"get_next")],
        [
            Button.inline(f"📊  {count} شماره", b"line"),
            Button.inline(f"🔄  Auto Code {auto_status}", b"auto_code")
        ],
        [
            Button.inline("📧  جیمیل", b"gmail"),
            Button.inline("📥  آپلود فایل", b"upload_file")
        ]
    ]


def panel_buttons():
    return [
        [Button.inline("➕  افزودن کاربر", b"panel_add")],
        [Button.inline("➖  حذف کاربر", b"panel_remove")],
        [
            Button.inline("📊  آمار", b"panel_stats"),
            Button.inline("📋  لیست کاربران", b"panel_list")
        ]
    ]


# =========================
# اسم کانادایی
# =========================
async def get_canadian_name():
    try:
        url = "https://randomuser.me/api/?nat=ca"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                user = data["results"][0]["name"]
                return f"{user['first']} {user['last']}"
    except:
        return "Canadian User"


# =========================
# استخراج کد
# =========================
def extract_code(html):
    match = re.search(r"\b\d{5,6}\b", html)
    return match.group(0) if match else None


# =========================
# /start
# =========================
@client.on(events.NewMessage(pattern="/start"))
async def start(event):
    user_id = event.sender_id
    if not is_allowed(user_id):
        await event.respond(
            f"❌ Access Denied.\n"
            f"Your ID: <code>{user_id}</code>\n"
            "Send this to admin.",
            parse_mode="html"
        )
        return
    count = count_numbers(user_id)
    await event.respond(
        "🧊 <b>Canada Robot</b>\n"
        "────────────────\n"
        f"📞 شماره‌ها: {count}\n"
        "────────────────\n"
        "Welcome to system panel",
        buttons=[[Button.inline("🚀  شروع", b"get_next")]],
        parse_mode="html"
    )


# =========================
# /help
# =========================
@client.on(events.NewMessage(pattern="/help"))
async def help_command(event):
    user_id = event.sender_id
    if not is_allowed(user_id):
        await event.respond(
            f"❌ Access Denied.\n"
            f"Your ID: <code>{user_id}</code>\n"
            "Send this to admin.",
            parse_mode="html"
        )
        return
    await event.respond(
        "🧊 <b>HELP</b>\n"
        "────────────────\n"
        "/start — Open main panel\n"
        "/reset — Clear all saved numbers\n"
        "/help — Show this help message\n"
        "────────────────\n"
        "<b>Buttons:</b>\n"
        "🚀 Start — Begin browsing numbers\n"
        "🔢 Get Code — Extract code from link\n"
        "➡️ Next — Go to next number\n"
        "📊 Line — Show progress\n"
        "🔄 Auto Code — Toggle auto code mode\n"
        "📧 Gmail — Manage your Gmail\n"
        "📥 Upload — Upload TXT file with numbers\n"
        "────────────────\n"
        "<b>Admin Commands:</b>\n"
        "/panel — Open admin panel",
        parse_mode="html"
    )


# =========================
# /panel (Admin Only)
# =========================
@client.on(events.NewMessage(pattern="/panel"))
async def panel_command(event):
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.respond("❌ Admin access required.")
        return
    await event.respond(
        get_stats_text(),
        buttons=panel_buttons(),
        parse_mode="html"
    )


# =========================
# Panel callbacks
# =========================
@client.on(events.CallbackQuery(data=b"panel_add"))
async def panel_add(event):
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.answer("❌ Admin only", alert=True)
        return
    user_state[user_id] = "waiting_add_user"
    await event.edit(
        "➕ <b>Add User</b>\n"
        "────────────────\n"
        "Send the numeric user ID to add:",
        parse_mode="html"
    )


@client.on(events.CallbackQuery(data=b"panel_remove"))
async def panel_remove(event):
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.answer("❌ Admin only", alert=True)
        return
    user_state[user_id] = "waiting_remove_user"
    await event.edit(
        "➖ <b>Remove User</b>\n"
        "────────────────\n"
        "Send the numeric user ID to remove:",
        parse_mode="html"
    )


@client.on(events.CallbackQuery(data=b"panel_stats"))
async def panel_stats(event):
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.answer("❌ Admin only", alert=True)
        return
    await event.edit(
        get_stats_text(),
        buttons=panel_buttons(),
        parse_mode="html"
    )


@client.on(events.CallbackQuery(data=b"panel_list"))
async def panel_list(event):
    user_id = event.sender_id
    if user_id not in ADMIN_IDS:
        await event.answer("❌ Admin only", alert=True)
        return
    allowed = load_whitelist()
    user_list = "\n".join(str(uid) for uid in sorted(allowed)) if allowed else "No users"
    await event.edit(
        "📋 <b>User List</b>\n"
        "────────────────\n"
        f"<code>{user_list}</code>",
        buttons=panel_buttons(),
        parse_mode="html"
    )


# =========================
# /reset
# =========================
@client.on(events.NewMessage(pattern="/reset"))
async def reset_command(event):
    user_id = event.sender_id
    if not is_allowed(user_id):
        await event.respond(
            f"❌ Access Denied.\n"
            f"Your ID: <code>{user_id}</code>\n"
            "Send this to admin.",
            parse_mode="html"
        )
        return
    file_path = os.path.join(DATA_DIR, f"{user_id}.txt")

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            await event.reply(f"❌ Error: {e}")
            return

    user_index[user_id] = 0
    user_data[user_id] = None

    await event.reply("♻️ Reset Done\nAll registered numbers have been cleared.")


# =========================
# Upload TXT File
# =========================
@client.on(events.CallbackQuery(data=b"upload_file"))
async def upload_file_handler(event):
    user_id = event.sender_id
    if not is_allowed(user_id):
        await event.answer("❌ Access Denied", alert=True)
        return

    user_state[user_id] = "waiting_file"
    await event.edit(
        "📥 <b>آپلود فایل شماره</b>\n"
        "────────────────\n"
        "فایل TXT خود را ارسال کنید.\n"
        "هر خط شامل: شماره | لینک\n"
        "────────────────\n"
        "فرمت‌ها:\n"
        "<code>+1234567890|https://link.com</code>\n"
        "<code>+1234567890||||https://link.com</code>\n"
        "<code>+1234567890----https://link.com</code>",
        parse_mode="html"
    )


@client.on(events.NewMessage(func=lambda e: e.file and e.file.name and e.file.name.endswith('.txt')))
async def handle_file_upload(event):
    user_id = event.sender_id
    if not is_allowed(user_id):
        await event.reply("❌ Access Denied")
        return

    state = user_state.get(user_id)
    if state != "waiting_file":
        return

    user_state.pop(user_id, None)

    try:
        # Download file
        file_path = os.path.join(DATA_DIR, f"{user_id}_upload.txt")
        await event.download_media(file=file_path)

        # Read and count
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]

        if not lines:
            await event.reply("❌ فایل خالی است.")
            os.remove(file_path)
            return

        # Append to user data file
        data_path = os.path.join(DATA_DIR, f"{user_id}.txt")
        with open(data_path, "a", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")

        # Clean up upload file
        os.remove(file_path)

        total = count_numbers(user_id)

        await event.reply(
            f"✅ <b>فایل آپلود شد!</b>\n"
            "────────────────\n"
            f"📥 شماره‌های اضافه شده: <code>{len(lines)}</code>\n"
            f"📊 کل شماره‌ها: <code>{total}</code>",
            parse_mode="html",
            buttons=main_buttons(user_id)
        )

    except Exception as e:
        await event.reply(f"❌ Error: {e}")


# =========================
# ذخیره دیتا + state handling
# =========================
@client.on(events.NewMessage)
async def save_data(event):
    if (
        event.raw_text.startswith("/")
        or not event.raw_text
    ):
        return

    user_id = event.sender_id

    state = user_state.get(user_id)

    if state == "waiting_gmail":
        gmail = event.raw_text.strip()
        if "@" not in gmail or "." not in gmail:
            await event.reply("❌ Invalid Gmail format. Please send a valid Gmail address:")
            return
        save_gmail(user_id, gmail)
        user_state.pop(user_id, None)
        await event.reply(
            f"✅ Gmail saved: <code>{mixed_case(gmail)}</code>",
            parse_mode="html"
        )
        return

    elif state == "waiting_add_user":
        user_state.pop(user_id, None)
        target = event.raw_text.strip()
        if not target.isdigit():
            await event.reply("❌ Invalid ID. Send a numeric user ID.")
            return
        target_id = int(target)
        add_to_whitelist(target_id)
        await event.reply(f"✅ User <code>{target_id}</code> added to whitelist.", parse_mode="html")
        return

    elif state == "waiting_remove_user":
        user_state.pop(user_id, None)
        target = event.raw_text.strip()
        if not target.isdigit():
            await event.reply("❌ Invalid ID. Send a numeric user ID.")
            return
        target_id = int(target)
        if target_id in ADMIN_IDS:
            await event.reply("❌ Cannot remove admin users.")
            return
        remove_from_whitelist(target_id)
        await event.reply(f"✅ User <code>{target_id}</code> removed from whitelist.", parse_mode="html")
        return

    if not is_allowed(user_id):
        await event.reply(
            f"❌ Access Denied.\n"
            f"Your ID: <code>{user_id}</code>\n"
            "Send this to admin.",
            parse_mode="html"
        )
        return

    file_path = os.path.join(DATA_DIR, f"{user_id}.txt")

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(event.raw_text + "\n")

    total = count_numbers(user_id)
    await event.reply(f"✅ Saved | 📊 کل شماره‌ها: {total}")


# =========================
# Auto Code Toggle
# =========================
@client.on(events.CallbackQuery(data=b"auto_code"))
async def auto_code_toggle(event):
    user_id = event.sender_id
    if not is_allowed(user_id):
        await event.answer("❌ Access Denied", alert=True)
        return

    current = user_auto_code.get(user_id, False)
    user_auto_code[user_id] = not current

    new_status = "🟢 ON" if user_auto_code[user_id] else "🔴 OFF"

    await event.edit(
        f"🔄 <b>Auto Code: {new_status}</b>\n"
        "────────────────\n"
        f"{'⚡ Code will be auto-fetched after Next and sent as text, deletes after 15s' if user_auto_code[user_id] else 'OFF — Use Get Code button manually'}",
        buttons=[
            [Button.inline(f"🔄 Auto Code {new_status}", b"auto_code")],
            [Button.inline("⬅️ Back", b"get_next")]
        ],
        parse_mode="html"
    )


# =========================
# Next
# =========================
@client.on(events.CallbackQuery(data=b"get_next"))
async def get_next(event):
    user_id = event.sender_id
    if not is_allowed(user_id):
        await event.answer("❌ Access Denied", alert=True)
        return

    file_path = os.path.join(DATA_DIR, f"{user_id}.txt")

    if not os.path.exists(file_path):
        await event.edit("❌ Empty list")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if user_id not in user_index:
        user_index[user_id] = 0

    i = user_index[user_id]

    if i >= len(lines):
        await event.edit("✅ Done")
        return

    item = lines[i].strip()

    if "||||" in item:
        number, link = item.split("||||", 1)
    elif "----" in item:
        number, link = item.split("----", 1)
    elif "|" in item:
        number, link = item.split("|", 1)
    else:
        match = re.match(r"^(\+?\d+)(https?://.+)$", item)
        if match:
            number = match.group(1)
            link = match.group(2)
        else:
            await event.edit("❌ Bad format")
            return

    number = number.strip()
    link = link.strip()

    if not number or not link:
        await event.edit("❌ Bad format")
        return

    user_index[user_id] += 1
    user_data[user_id] = link

    gmail = get_gmail(user_id)
    gmail_line = ""
    if gmail:
        gmail_line = f"📧 Gmail: <code>{mixed_case(gmail)}</code>\n"

    remaining = len(lines) - user_index[user_id]

    await event.edit(
        "🧊 <b>DATA PANEL</b>\n"
        "────────────────\n"
        f"📞 Number: <code>{number}</code>\n"
        f"{gmail_line}"
        f"📊 باقی‌مانده: {remaining}\n"
        "────────────────\n"
        "⚡ Ready to get code",
        buttons=main_buttons(user_id),
        parse_mode="html"
    )

    # Auto code: check site every 2s until code found, send with name, delete after 15s
    if user_auto_code.get(user_id):
        try:
            for _ in range(90):  # max 3 minutes (90 x 2s)
                await asyncio.sleep(2)
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(link, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                            html = await resp.text()
                            code = extract_code(html)

                            if code:
                                name = await get_canadian_name()
                                code_msg = await client.send_message(
                                    event.chat_id,
                                    f"🧊 <b>CODE READY</b>\n"
                                    "────────────────\n"
                                    f"🔢 Code: <code>{code}</code>\n"
                                    "────────────────\n"
                                    f"👤 Name:\n<code>{name}</code>",
                                    parse_mode="html"
                                )
                                await asyncio.sleep(15)
                                try:
                                    await code_msg.delete()
                                except:
                                    pass
                                return
                except:
                    pass

        except Exception:
            pass


# =========================
# Get Code (manual)
# =========================
@client.on(events.CallbackQuery(data=b"get_code"))
async def get_code(event):
    user_id = event.sender_id
    if not is_allowed(user_id):
        await event.answer("❌ Access Denied", alert=True)
        return

    link = user_data.get(user_id)

    if not link:
        await event.edit("❌ No link found")
        return

    msg = await event.edit("⏳ Processing... 10%")

    await asyncio.sleep(0.15)
    await msg.edit("⏳ Processing... 40%")

    await asyncio.sleep(0.15)
    await msg.edit("⏳ Processing... 70%")

    await asyncio.sleep(0.15)
    await msg.edit("⏳ Processing... 100%")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(link, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                html = await resp.text()
                code = extract_code(html)

                if code:
                    name = await get_canadian_name()

                    await msg.edit(
                        "🧊 <b>RESULT</b>\n"
                        "────────────────\n"
                        f"🔢 Code: <code>{code}</code>\n"
                        "────────────────\n"
                        f"👤 Name:\n<code>{name}</code>",
                        buttons=main_buttons(user_id),
                        parse_mode="html"
                    )
                else:
                    await msg.edit(
                        "🧊 <b>DATA PANEL</b>\n"
                        "────────────────\n"
                        "❌ No code found\n"
                        "────────────────\n"
                        "⚡ Ready to get code",
                        buttons=main_buttons(user_id),
                        parse_mode="html"
                    )

    except Exception as e:
        await msg.edit(
            "🧊 <b>DATA PANEL</b>\n"
            "────────────────\n"
            f"❌ Error:\n<code>{e}</code>\n"
            "────────────────\n"
            "⚡ Ready to get code",
            buttons=main_buttons(user_id),
            parse_mode="html"
        )


# =========================
# Line
# =========================
@client.on(events.CallbackQuery(data=b"line"))
async def line(event):
    user_id = event.sender_id
    if not is_allowed(user_id):
        await event.answer("❌ Access Denied", alert=True)
        return

    file_path = os.path.join(DATA_DIR, f"{user_id}.txt")

    if not os.path.exists(file_path):
        await event.edit("No data")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        total = len(f.readlines())

    current = user_index.get(user_id, 0)

    await event.edit(f"📊 {current}/{total}")


# =========================
# Gmail handler
# =========================
@client.on(events.CallbackQuery(data=b"gmail"))
async def gmail_handler(event):
    user_id = event.sender_id
    if not is_allowed(user_id):
        await event.answer("❌ Access Denied", alert=True)
        return

    gmail = get_gmail(user_id)

    if gmail:
        await event.edit(
            "📧 <b>Your Gmail</b>\n"
            "────────────────\n"
            f"Email: <code>{mixed_case(gmail)}</code>\n"
            "────────────────",
            buttons=[
                [Button.inline("🗑️ Delete Gmail", b"gmail_delete")],
                [Button.inline("⬅️ Back", b"get_next")]
            ],
            parse_mode="html"
        )
    else:
        user_state[user_id] = "waiting_gmail"
        await event.edit(
            "📧 <b>Set Gmail</b>\n"
            "────────────────\n"
            "Please send your Gmail address:",
            parse_mode="html"
        )


# =========================
# Gmail Delete handler
# =========================
@client.on(events.CallbackQuery(data=b"gmail_delete"))
async def gmail_delete_handler(event):
    user_id = event.sender_id
    if not is_allowed(user_id):
        await event.answer("❌ Access Denied", alert=True)
        return

    deleted = delete_gmail(user_id)

    if deleted:
        await event.edit(
            "🗑️ <b>Gmail Deleted</b>\n"
            "────────────────\n"
            "Your Gmail has been removed.",
            buttons=[Button.inline("⬅️ Back", b"get_next")],
            parse_mode="html"
        )
    else:
        await event.edit(
            "❌ No Gmail found to delete.",
            buttons=[Button.inline("⬅️ Back", b"get_next")],
            parse_mode="html"
        )


# =========================
# Run
# =========================
print("Bot is running...")
print(f"Admin IDs: {ADMIN_IDS}")
print(f"Whitelist file: {WHITELIST_FILE}")
print(f"Whitelist exists: {os.path.exists(WHITELIST_FILE)}")
client.start(bot_token=BOT_TOKEN)
print("Bot connected to Telegram!")
client.run_until_disconnected()
