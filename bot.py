import logging
import asyncio
from datetime import datetime, timedelta
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters, ConversationHandler
)
from config import BOT_TOKEN, ADMIN_ID, UPI_ID, DATA_DIR
from database import (
    init_db, add_subscriber, get_subscribers, get_subscriber_count,
    get_admin, get_latest_booklet, get_latest_booklet_published_date,
    set_setting, get_setting,
    create_donation, approve_donation, reject_donation, get_donation, get_total_donations,
    add_darood_image, get_darood_images, delete_darood_image,
    add_hadees, get_next_hadees, get_all_hadees, get_hadees_count,
    delete_hadees, reset_hadees_sent
)
from scraper import scrape_latest_booklet
from upi_qr import generate_upi_qr

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

IST = pytz.timezone('Asia/Kolkata')

def is_admin(user_id):
    return user_id == ADMIN_ID

# ═══════════════════════════════════════════
#  /start COMMAND
# ═══════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_subscriber(user.id, user.username, user.first_name)
    
    welcome_text = (
        f"╔══════════════════════════╗\n"
        f"   🌙 *Assalamu Alaikum* 🌙\n"
        f"╚══════════════════════════╝\n\n"
        f"Welcome *{user.first_name}*!\n\n"
        f"🕌 *Dawateislami India Bot*\n\n"
        f"This bot provides you with:\n"
        f"📜 Daily Hadees Shareef\n"
        f"📖 Weekly Risala (Hindi & Urdu)\n"
        f"🤲 Darood Sharif Collection\n"
        f"💝 Donate to support us\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Choose an option below 👇"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("📜 Hadees", callback_data='hadees_menu'),
            InlineKeyboardButton("📖 Risala", callback_data='risala_menu'),
        ],
        [
            InlineKeyboardButton("🤲 Darood Sharif", callback_data='darood_menu'),
            InlineKeyboardButton("💝 Donate", callback_data='donate_start'),
        ],
        [InlineKeyboardButton("✅ Subscribe", callback_data='subscribe')],
    ]
    
    if is_admin(user.id):
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_photo = get_setting('welcome_photo')
    
    if welcome_photo:
        try:
            await update.message.reply_photo(
                photo=welcome_photo,
                caption=welcome_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            return
        except Exception as e:
            logger.error(f"Failed to send welcome photo: {e}")
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# ═══════════════════════════════════════════
#  MAIN MENU CALLBACK
# ═══════════════════════════════════════════

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    
    keyboard = [
        [
            InlineKeyboardButton("📜 Hadees", callback_data='hadees_menu'),
            InlineKeyboardButton("📖 Risala", callback_data='risala_menu'),
        ],
        [
            InlineKeyboardButton("🤲 Darood Sharif", callback_data='darood_menu'),
            InlineKeyboardButton("💝 Donate", callback_data='donate_start'),
        ],
        [InlineKeyboardButton("✅ Subscribe", callback_data='subscribe')],
    ]
    
    if is_admin(user.id):
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(
        "🏠 *Main Menu*\n\nChoose an option below 👇",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# ═══════════════════════════════════════════
#  HADEES SECTION
# ═══════════════════════════════════════════

async def hadees_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    total, unsent = get_hadees_count()
    
    text = (
        "📜 *Hadees Shareef*\n\n"
        "Receive daily Hadees every morning at 6:00 AM.\n"
        "Subscribe to never miss a Hadees!\n\n"
        f"📚 Total Hadees: *{total}*\n"
        f"📤 Remaining to send: *{unsent}*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Subscribe to Daily Hadees", callback_data='subscribe')],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data='back_menu')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

# ═══════════════════════════════════════════
#  RISALA SECTION
# ═══════════════════════════════════════════

async def risala_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    booklet = get_latest_booklet()
    if booklet:
        title = booklet[0]
        text = (
            f"📖 *Weekly Risala*\n\n"
            f"📕 Latest: *{title}*\n\n"
            f"Available in Hindi & Urdu\n"
            f"Choose your language below 👇\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━"
        )
    else:
        text = (
            "📖 *Weekly Risala*\n\n"
            "No Risala available yet.\n"
            "New Risala is published every week.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━"
        )
    
    keyboard = [
        [
            InlineKeyboardButton("📗 Hindi", callback_data='get_hindi'),
            InlineKeyboardButton("📘 Urdu", callback_data='get_urdu'),
        ],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data='back_menu')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

# ═══════════════════════════════════════════
#  DAROOD SHARIF SECTION
# ═══════════════════════════════════════════

async def darood_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    images = get_darood_images()
    
    if images:
        text = (
            "🤲 *Darood Sharif Collection*\n\n"
            f"📸 {len(images)} Darood Sharif image(s) available\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━"
        )
        keyboard = [
            [InlineKeyboardButton("📸 View All Darood Sharif", callback_data='view_darood')],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data='back_menu')],
        ]
    else:
        text = (
            "🤲 *Darood Sharif*\n\n"
            "No Darood Sharif images added yet.\n"
            "Admin will add them soon InshaAllah.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━"
        )
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Menu", callback_data='back_menu')],
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def view_darood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    images = get_darood_images()
    if not images:
        await query.message.reply_text("No Darood Sharif images available yet.")
        return
    
    for img_id, file_id, caption in images:
        cap = caption if caption else "🤲 Darood Sharif"
        try:
            await query.message.reply_photo(photo=file_id, caption=cap)
        except Exception as e:
            logger.error(f"Failed to send darood image {img_id}: {e}")
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='back_menu')]]
    await query.message.reply_text("🤲 *May Allah accept your Darood*", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

# ═══════════════════════════════════════════
#  DONATE SECTION
# ═══════════════════════════════════════════

async def donate_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = (
        "💝 *Donate to Dawateislami India Bot*\n\n"
        "Your donation helps us maintain this bot and\n"
        "spread the message of Islam.\n\n"
        "🎁 *JazakAllah Khair* for your generosity!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Choose an amount or enter custom amount:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("₹51", callback_data='donate_51'),
            InlineKeyboardButton("₹101", callback_data='donate_101'),
            InlineKeyboardButton("₹251", callback_data='donate_251'),
        ],
        [
            InlineKeyboardButton("₹501", callback_data='donate_501'),
            InlineKeyboardButton("₹1001", callback_data='donate_1001'),
            InlineKeyboardButton("₹2001", callback_data='donate_2001'),
        ],
        [InlineKeyboardButton("💰 Custom Amount", callback_data='donate_custom')],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data='back_menu')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def donate_amount_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    amount = query.data.replace('donate_', '')
    context.user_data['donate_amount'] = amount
    
    qr_image = generate_upi_qr(amount)
    
    text = (
        f"💝 *Donation: ₹{amount}*\n\n"
        f"📱 *UPI ID:* `{UPI_ID}`\n\n"
        f"Scan the QR code below to pay:\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"After payment, click the button below 👇"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Payment Done?", callback_data='payment_done')],
        [InlineKeyboardButton("❌ Cancel", callback_data='back_menu')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_photo(
        photo=qr_image,
        caption=text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def donate_custom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['awaiting_custom_amount'] = True
    await query.message.reply_text(
        "💰 *Enter Custom Amount*\n\n"
        "Please type the amount you want to donate (in ₹):\n"
        "Example: 500",
        parse_mode='Markdown'
    )

async def handle_custom_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        amount = int(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid amount (numbers only). Try again:")
        return
    
    context.user_data['awaiting_custom_amount'] = False
    context.user_data['donate_amount'] = str(amount)
    
    qr_image = generate_upi_qr(str(amount))
    
    msg_text = (
        f"💝 *Donation: ₹{amount}*\n\n"
        f"📱 *UPI ID:* `{UPI_ID}`\n\n"
        f"Scan the QR code below to pay:\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"After payment, click the button below 👇"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Payment Done?", callback_data='payment_done')],
        [InlineKeyboardButton("❌ Cancel", callback_data='back_menu')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_photo(
        photo=qr_image,
        caption=msg_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def payment_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    amount = context.user_data.get('donate_amount', '0')
    
    text = (
        f"🤔 *Are you sure?*\n\n"
        f"You are confirming payment of *₹{amount}*\n\n"
        f"Please make sure you have completed the payment\n"
        f"before confirming.\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Yes, I have paid!", callback_data='payment_confirmed')],
        [InlineKeyboardButton("❌ No, cancel", callback_data='back_menu')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def payment_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    amount = context.user_data.get('donate_amount', '0')
    
    donation_id = create_donation(user.id, user.username, user.first_name, amount)
    
    thank_text = (
        f"╔══════════════════════════╗\n"
        f"   💝 *JazakAllah Khair!* 💝\n"
        f"╚══════════════════════════╝\n\n"
        f"🎉 Thank you *{user.first_name}*!\n\n"
        f"💰 Amount: *₹{amount}*\n"
        f"🔖 Donation ID: *#{donation_id}*\n\n"
        f"Your donation has been submitted for\n"
        f"admin approval. You will receive a\n"
        f"confirmation message once approved.\n\n"
        f"🤲 *May Allah reward you abundantly*\n"
        f"🤲 *and accept your generosity!*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    keyboard = [[InlineKeyboardButton("🏠 Back to Menu", callback_data='back_menu')]]
    await query.message.reply_text(thank_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    
    admin_text = (
        f"💰 *New Donation Received!*\n\n"
        f"👤 From: *{user.first_name}* (@{user.username or 'N/A'})\n"
        f"🆔 User ID: `{user.id}`\n"
        f"💵 Amount: *₹{amount}*\n"
        f"🔖 Donation ID: *#{donation_id}*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    admin_keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f'approve_donation_{donation_id}'),
            InlineKeyboardButton("❌ Reject", callback_data=f'reject_donation_{donation_id}'),
        ],
    ]
    admin_markup = InlineKeyboardMarkup(admin_keyboard)
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode='Markdown',
            reply_markup=admin_markup
        )
    except Exception as e:
        logger.error(f"Failed to send donation notification to admin: {e}")

async def handle_donation_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        await query.message.reply_text("❌ Unauthorized.")
        return
    
    data = query.data
    
    if data.startswith('approve_donation_'):
        donation_id = int(data.replace('approve_donation_', ''))
        donation = get_donation(donation_id)
        if not donation:
            await query.message.reply_text("Donation not found.")
            return
        
        approve_donation(donation_id)
        await query.message.reply_text(f"✅ Donation #{donation_id} approved!")
        
        user_id = donation[1]
        first_name = donation[3]
        amount = donation[4]
        
        confirm_text = (
            f"╔══════════════════════════╗\n"
            f"   ✅ *DONATION APPROVED* ✅\n"
            f"╚══════════════════════════╝\n\n"
            f"🎉 *Congratulations {first_name}!*\n\n"
            f"Your donation of *₹{amount}* has been\n"
            f"verified and approved by the admin.\n\n"
            f"🔖 Donation ID: *#{donation_id}*\n\n"
            f"🤲 *JazakAllah Khair!*\n"
            f"May Allah bless you with more\n"
            f"and reward you in this world\n"
            f"and the hereafter. Ameen! 🤲\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━"
        )
        
        try:
            await context.bot.send_message(chat_id=user_id, text=confirm_text, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Failed to send approval to user {user_id}: {e}")
    
    elif data.startswith('reject_donation_'):
        donation_id = int(data.replace('reject_donation_', ''))
        donation = get_donation(donation_id)
        if not donation:
            await query.message.reply_text("Donation not found.")
            return
        
        reject_donation(donation_id)
        await query.message.reply_text(f"❌ Donation #{donation_id} rejected.")
        
        user_id = donation[1]
        first_name = donation[3]
        amount = donation[4]
        
        reject_text = (
            f"❌ *Donation Update*\n\n"
            f"Dear {first_name}, your donation of ₹{amount}\n"
            f"(ID: #{donation_id}) could not be verified.\n\n"
            f"If you believe this is an error, please\n"
            f"contact the admin.\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━"
        )
        
        try:
            await context.bot.send_message(chat_id=user_id, text=reject_text, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Failed to send rejection to user {user_id}: {e}")

# ═══════════════════════════════════════════
#  SUBSCRIBE
# ═══════════════════════════════════════════

async def subscribe_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    add_subscriber(user.id, user.username, user.first_name)
    
    text = (
        "✅ *Subscribed Successfully!*\n\n"
        "You will now receive:\n"
        "📜 Daily Hadees at 6:00 AM\n"
        "📖 New Risala notifications\n\n"
        "🤲 *JazakAllah Khair!*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    keyboard = [[InlineKeyboardButton("🏠 Back to Menu", callback_data='back_menu')]]
    await query.message.reply_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

# ═══════════════════════════════════════════
#  RISALA BUTTONS
# ═══════════════════════════════════════════

async def get_risala(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    booklet = get_latest_booklet()
    lang = "Hindi" if query.data == 'get_hindi' else "Urdu"
    emoji = "📗" if lang == "Hindi" else "📘"
    idx = 1 if lang == "Hindi" else 2
    
    if booklet and booklet[idx]:
        await query.message.reply_text(f"{emoji} Fetching latest {lang} Risala: *{booklet[0]}*...", parse_mode='Markdown')
        try:
            await query.message.reply_document(document=booklet[idx], caption=f"{emoji} Latest Risala ({lang}): {booklet[0]}")
        except Exception as e:
            await query.message.reply_text(f"{emoji} Here is the {lang} Risala link:\n{booklet[idx]}")
    else:
        await query.message.reply_text(f"{lang} Risala not available yet. Please check back later.")

# ═══════════════════════════════════════════
#  ADMIN PANEL
# ═══════════════════════════════════════════

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        await query.message.reply_text("❌ Unauthorized.")
        return
    
    sub_count = get_subscriber_count()
    donations = get_total_donations()
    booklet = get_latest_booklet()
    total_hadees, unsent_hadees = get_hadees_count()
    now_ist = datetime.now(IST)
    
    text = (
        f"⚙️ *Admin Panel*\n\n"
        f"📊 *Bot Statistics:*\n"
        f"👥 Subscribers: *{sub_count}*\n"
        f"💰 Approved Donations: *{donations[0]}* (₹{donations[1]:.0f})\n"
        f"📜 Hadees: *{total_hadees}* total, *{unsent_hadees}* unsent\n"
    )
    
    if booklet:
        text += f"📖 Latest Risala: *{booklet[0]}*\n"
    
    text += (
        f"\n🕐 Time (IST): {now_ist.strftime('%Y-%m-%d %H:%M')}\n"
        f"⏰ Daily Hadees: 6:00 AM IST\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Choose an action below 👇"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("📜 Add Hadees", callback_data='admin_add_hadees'),
            InlineKeyboardButton("📋 View Hadees", callback_data='admin_view_hadees'),
        ],
        [
            InlineKeyboardButton("📢 Broadcast Now", callback_data='admin_broadcast'),
            InlineKeyboardButton("📸 Add Darood Image", callback_data='admin_add_darood'),
        ],
        [
            InlineKeyboardButton("🖼 Set Welcome Photo", callback_data='admin_set_welcome'),
            InlineKeyboardButton("🗑 Remove Welcome Photo", callback_data='admin_remove_welcome'),
        ],
        [
            InlineKeyboardButton("📊 View Subscribers", callback_data='admin_view_subs'),
            InlineKeyboardButton("🗑 Manage Darood", callback_data='admin_manage_darood'),
        ],
        [
            InlineKeyboardButton("🗑 Manage Hadees", callback_data='admin_manage_hadees'),
            InlineKeyboardButton("🔄 Reset Hadees Sent", callback_data='admin_reset_hadees'),
        ],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data='back_menu')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

# ═══════════════════════════════════════════
#  ADMIN - HADEES MANAGEMENT
# ═══════════════════════════════════════════

async def admin_add_hadees(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    context.user_data['awaiting_hadees'] = True
    await query.message.reply_text(
        "📜 *Add New Hadees*\n\n"
        "Please type the Hadees message.\n"
        "You can add multiple Hadees one by one.\n\n"
        "Send /done when finished adding.\n"
        "Send /cancel to cancel.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode='Markdown'
    )

async def admin_view_hadees(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    all_hadees = get_all_hadees()
    if not all_hadees:
        await query.message.reply_text(
            "📜 *No Hadees Added Yet*\n\nUse 'Add Hadees' to start adding.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Admin", callback_data='admin_panel')]])
        )
        return
    
    total, unsent = get_hadees_count()
    text = f"📜 *All Hadees ({total} total, {unsent} unsent)*\n\n"
    
    # Show last 10 hadees
    shown = all_hadees[:10]
    for h_id, msg, is_sent in shown:
        status = "✅" if is_sent else "⏳"
        short_msg = (msg[:60] + "...") if len(msg) > 60 else msg
        text += f"{status} *#{h_id}:* {short_msg}\n\n"
    
    if len(all_hadees) > 10:
        text += f"_...and {len(all_hadees) - 10} more_\n"
    
    text += "\n━━━━━━━━━━━━━━━━━━━━━━━"
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Admin", callback_data='admin_panel')]]
    await query.message.reply_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_manage_hadees(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    all_hadees = get_all_hadees()
    if not all_hadees:
        await query.message.reply_text("No Hadees to manage.")
        return
    
    text = "🗑 *Manage Hadees*\n\nClick to delete:\n\n"
    keyboard = []
    for h_id, msg, is_sent in all_hadees[:15]:
        short_msg = (msg[:30] + "...") if len(msg) > 30 else msg
        status = "✅" if is_sent else "⏳"
        keyboard.append([InlineKeyboardButton(f"🗑 {status} #{h_id}: {short_msg}", callback_data=f'del_hadees_{h_id}')])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Admin", callback_data='admin_panel')])
    await query.message.reply_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_reset_hadees(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    reset_hadees_sent()
    await query.message.reply_text(
        "🔄 *All Hadees reset to unsent!*\n\nThe daily broadcast will start from the beginning again.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Admin", callback_data='admin_panel')]])
    )

# ═══════════════════════════════════════════
#  ADMIN - OTHER SETTINGS
# ═══════════════════════════════════════════

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    context.user_data['awaiting_broadcast'] = True
    await query.message.reply_text(
        "📢 *Broadcast Message*\n\n"
        "Please type the message you want to\n"
        "broadcast to all subscribers:\n\n"
        "_(Send /cancel to cancel)_",
        parse_mode='Markdown'
    )

async def admin_set_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    context.user_data['awaiting_welcome_photo'] = True
    await query.message.reply_text(
        "🖼 *Set Welcome Photo*\n\n"
        "Please send the photo you want to show\n"
        "when users start the bot.\n\n"
        "_(Send /cancel to cancel)_",
        parse_mode='Markdown'
    )

async def admin_remove_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    set_setting('welcome_photo', '')
    await query.message.reply_text("✅ Welcome photo removed!")

async def admin_add_darood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    context.user_data['awaiting_darood_image'] = True
    await query.message.reply_text(
        "🤲 *Add Darood Sharif Image*\n\n"
        "Please send the Darood Sharif image.\n"
        "You can add a caption with it.\n\n"
        "_(Send /cancel to cancel)_",
        parse_mode='Markdown'
    )

async def admin_manage_darood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    images = get_darood_images()
    if not images:
        await query.message.reply_text("No Darood Sharif images to manage.")
        return
    
    text = "🗑 *Manage Darood Images*\n\nClick to delete:\n\n"
    keyboard = []
    for img_id, file_id, caption in images:
        cap_short = (caption[:30] + "...") if caption and len(caption) > 30 else (caption or f"Image #{img_id}")
        keyboard.append([InlineKeyboardButton(f"🗑 {cap_short}", callback_data=f'del_darood_{img_id}')])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Admin", callback_data='admin_panel')])
    await query.message.reply_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_view_subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    count = get_subscriber_count()
    await query.message.reply_text(
        f"👥 *Total Subscribers: {count}*",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Admin", callback_data='admin_panel')]])
    )

# ═══════════════════════════════════════════
#  MESSAGE HANDLERS
# ═══════════════════════════════════════════

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    
    if context.user_data.get('awaiting_welcome_photo'):
        context.user_data['awaiting_welcome_photo'] = False
        photo = update.message.photo[-1]
        file_id = photo.file_id
        set_setting('welcome_photo', file_id)
        await update.message.reply_text(
            "✅ *Welcome photo updated!*\n\n"
            "Users will now see this photo when they /start the bot.",
            parse_mode='Markdown'
        )
    
    elif context.user_data.get('awaiting_darood_image'):
        context.user_data['awaiting_darood_image'] = False
        photo = update.message.photo[-1]
        file_id = photo.file_id
        caption = update.message.caption or "🤲 Darood Sharif"
        add_darood_image(file_id, caption)
        await update.message.reply_text(
            "✅ *Darood Sharif image added!*\n\n"
            "Users can now view this in the Darood Sharif section.",
            parse_mode='Markdown'
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Handle custom donation amount
    if context.user_data.get('awaiting_custom_amount'):
        await handle_custom_amount(update, context)
        return
    
    # Handle adding hadees from admin
    if is_admin(user.id) and context.user_data.get('awaiting_hadees'):
        message_text = update.message.text.strip()
        hadees_id = add_hadees(message_text)
        total, unsent = get_hadees_count()
        
        await update.message.reply_text(
            f"✅ *Hadees #{hadees_id} Added!*\n\n"
            f"📚 Total Hadees: *{total}*\n"
            f"📤 Unsent: *{unsent}*\n\n"
            f"Send another Hadees or /done to finish.",
            parse_mode='Markdown'
        )
        return
    
    # Handle broadcast from admin
    if is_admin(user.id) and context.user_data.get('awaiting_broadcast'):
        context.user_data['awaiting_broadcast'] = False
        message_to_send = update.message.text
        
        subscribers = get_subscribers()
        count = 0
        failed = 0
        
        for sub_id in subscribers:
            try:
                await context.bot.send_message(
                    chat_id=sub_id,
                    text=f"📢 *Broadcast*\n\n{message_to_send}",
                    parse_mode='Markdown'
                )
                count += 1
            except Exception as e:
                logger.error(f"Failed to send to {sub_id}: {e}")
                failed += 1
        
        await update.message.reply_text(
            f"✅ *Broadcast Complete!*\n\n"
            f"📤 Sent to: *{count}* subscribers\n"
            f"❌ Failed: *{failed}*",
            parse_mode='Markdown'
        )
        return

async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish adding hadees."""
    if context.user_data.get('awaiting_hadees'):
        context.user_data['awaiting_hadees'] = False
        total, unsent = get_hadees_count()
        await update.message.reply_text(
            f"✅ *Done Adding Hadees!*\n\n"
            f"📚 Total Hadees: *{total}*\n"
            f"📤 Unsent: *{unsent}*\n\n"
            f"Daily Hadees will be sent at 6:00 AM IST.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("Nothing to finish.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Operation cancelled.")

# ═══════════════════════════════════════════
#  CALLBACK ROUTER
# ═══════════════════════════════════════════

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == 'back_menu':
        await main_menu(update, context)
    elif data == 'hadees_menu':
        await hadees_menu(update, context)
    elif data == 'risala_menu':
        await risala_menu(update, context)
    elif data == 'darood_menu':
        await darood_menu(update, context)
    elif data == 'view_darood':
        await view_darood(update, context)
    elif data == 'donate_start':
        await donate_start(update, context)
    elif data == 'donate_custom':
        await donate_custom(update, context)
    elif data.startswith('donate_') and data.replace('donate_', '').isdigit():
        await donate_amount_selected(update, context)
    elif data == 'payment_done':
        await payment_done(update, context)
    elif data == 'payment_confirmed':
        await payment_confirmed(update, context)
    elif data == 'subscribe':
        await subscribe_callback(update, context)
    elif data in ('get_hindi', 'get_urdu'):
        await get_risala(update, context)
    elif data == 'admin_panel':
        await admin_panel(update, context)
    elif data == 'admin_add_hadees':
        await admin_add_hadees(update, context)
    elif data == 'admin_view_hadees':
        await admin_view_hadees(update, context)
    elif data == 'admin_manage_hadees':
        await admin_manage_hadees(update, context)
    elif data == 'admin_reset_hadees':
        await admin_reset_hadees(update, context)
    elif data == 'admin_broadcast':
        await admin_broadcast(update, context)
    elif data == 'admin_set_welcome':
        await admin_set_welcome(update, context)
    elif data == 'admin_remove_welcome':
        await admin_remove_welcome(update, context)
    elif data == 'admin_add_darood':
        await admin_add_darood(update, context)
    elif data == 'admin_manage_darood':
        await admin_manage_darood(update, context)
    elif data == 'admin_view_subs':
        await admin_view_subs(update, context)
    elif data.startswith('approve_donation_') or data.startswith('reject_donation_'):
        await handle_donation_approval(update, context)
    elif data.startswith('del_darood_'):
        img_id = int(data.replace('del_darood_', ''))
        delete_darood_image(img_id)
        await query.answer("Deleted!")
        await admin_manage_darood(update, context)
    elif data.startswith('del_hadees_'):
        h_id = int(data.replace('del_hadees_', ''))
        delete_hadees(h_id)
        await query.answer("Hadees deleted!")
        await admin_manage_hadees(update, context)

# ═══════════════════════════════════════════
#  BROADCAST /broadcast COMMAND
# ═══════════════════════════════════════════

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    if context.args:
        message_to_send = " ".join(context.args)
    elif update.message.reply_to_message:
        message_to_send = update.message.reply_to_message.text
    else:
        await update.message.reply_text("Usage: /broadcast <message>\nOr reply to a message with /broadcast")
        return
    
    subscribers = get_subscribers()
    count = 0
    failed = 0
    for sub_id in subscribers:
        try:
            await context.bot.send_message(chat_id=sub_id, text=f"📢 *Broadcast*\n\n{message_to_send}", parse_mode='Markdown')
            count += 1
        except Exception as e:
            logger.error(f"Failed to send to {sub_id}: {e}")
            failed += 1
    
    await update.message.reply_text(f"✅ Broadcast complete!\nSent to: {count}\nFailed: {failed}")

# ═══════════════════════════════════════════
#  AUTO BROADCAST NEW RISALA
# ═══════════════════════════════════════════

async def broadcast_new_risala(bot, title, hindi_url, urdu_url):
    subscribers = get_subscribers()
    if not subscribers:
        logger.info("No subscribers for Risala broadcast.")
        return
    
    count = 0
    failed = 0
    
    for sub_id in subscribers:
        try:
            await bot.send_message(
                chat_id=sub_id,
                text=(
                    f"╔══════════════════════════╗\n"
                    f"   📖 *New Weekly Risala!* 📖\n"
                    f"╚══════════════════════════╝\n\n"
                    f"🎉 *{title}*\n\n"
                    f"Sending you both Hindi & Urdu versions...\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━"
                ),
                parse_mode='Markdown'
            )
            
            if hindi_url:
                try:
                    await bot.send_document(chat_id=sub_id, document=hindi_url, caption=f"📗 Risala (Hindi): {title}")
                except:
                    await bot.send_message(chat_id=sub_id, text=f"📗 Hindi Risala:\n{hindi_url}")
            
            if urdu_url:
                try:
                    await bot.send_document(chat_id=sub_id, document=urdu_url, caption=f"📘 Risala (Urdu): {title}")
                except:
                    await bot.send_message(chat_id=sub_id, text=f"📘 Urdu Risala:\n{urdu_url}")
            
            count += 1
        except Exception as e:
            logger.error(f"Failed to send Risala to {sub_id}: {e}")
            failed += 1
    
    logger.info(f"Risala broadcast: sent={count}, failed={failed}")
    
    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📢 *Auto-Broadcast Complete!*\n\n📖 {title}\n✅ Sent: {count}\n❌ Failed: {failed}",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")

# ═══════════════════════════════════════════
#  DAILY HADEES BROADCASTER (6 AM IST)
# ═══════════════════════════════════════════

async def daily_hadees_broadcaster(app: Application):
    """Send one hadees daily at 6:00 AM IST."""
    while True:
        try:
            now = datetime.now(IST)
            
            # Calculate next 6:00 AM IST
            next_6am = now.replace(hour=6, minute=0, second=0, microsecond=0)
            if now >= next_6am:
                next_6am += timedelta(days=1)
            
            wait_seconds = (next_6am - now).total_seconds()
            logger.info(f"Next daily Hadees: {next_6am.strftime('%Y-%m-%d %H:%M:%S')} IST ({wait_seconds/3600:.1f}h)")
            await asyncio.sleep(wait_seconds)
            
            # It's 6 AM - get next hadees
            hadees = get_next_hadees()
            
            if hadees is None:
                logger.info("No Hadees in database. Skipping daily broadcast.")
                try:
                    await app.bot.send_message(
                        chat_id=ADMIN_ID,
                        text="⚠️ *Daily Hadees Skipped*\n\nNo Hadees found in database. Please add Hadees from Admin Panel.",
                        parse_mode='Markdown'
                    )
                except:
                    pass
                continue
            
            hadees_id, hadees_msg = hadees
            
            # Broadcast to all subscribers
            subscribers = get_subscribers()
            count = 0
            failed = 0
            
            broadcast_text = (
                f"╔══════════════════════════╗\n"
                f"   📜 *Hadees of the Day* 📜\n"
                f"╚══════════════════════════╝\n\n"
                f"{hadees_msg}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🕌 _Dawateislami India Bot_"
            )
            
            for sub_id in subscribers:
                try:
                    await app.bot.send_message(
                        chat_id=sub_id,
                        text=broadcast_text,
                        parse_mode='Markdown'
                    )
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to send hadees to {sub_id}: {e}")
                    failed += 1
            
            logger.info(f"Daily Hadees #{hadees_id} broadcast: sent={count}, failed={failed}")
            
            # Notify admin
            total, unsent = get_hadees_count()
            try:
                await app.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=(
                        f"📜 *Daily Hadees Sent!*\n\n"
                        f"🔖 Hadees #{hadees_id}\n"
                        f"✅ Sent to: {count} subscribers\n"
                        f"❌ Failed: {failed}\n\n"
                        f"📚 Remaining unsent: {unsent}/{total}"
                    ),
                    parse_mode='Markdown'
                )
            except:
                pass
                
        except Exception as e:
            logger.error(f"Daily hadees broadcaster error: {e}")
            await asyncio.sleep(3600)

# ═══════════════════════════════════════════
#  SATURDAY SCRAPER
# ═══════════════════════════════════════════

async def saturday_scraper(app: Application):
    """Scrape every Saturday at 12:00 AM IST, retry hourly if not found."""
    while True:
        try:
            now = datetime.now(IST)
            
            days_until_saturday = (5 - now.weekday()) % 7
            if days_until_saturday == 0 and (now.hour > 0 or now.minute > 0):
                days_until_saturday = 7
            
            next_saturday = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=days_until_saturday)
            wait_seconds = (next_saturday - now).total_seconds()
            
            if wait_seconds > 0:
                logger.info(f"Next scrape: {next_saturday.strftime('%Y-%m-%d %H:%M:%S')} IST ({wait_seconds/3600:.1f}h)")
                await asyncio.sleep(wait_seconds)
            
            logger.info("Saturday midnight! Starting Risala scrape...")
            old_date = get_latest_booklet_published_date()
            
            found_new = False
            max_retries = 48
            retry_count = 0
            
            while not found_new and retry_count < max_retries:
                try:
                    result = scrape_latest_booklet()
                    if result:
                        new_date = result.get('published_on', '')
                        if old_date is None or new_date != old_date:
                            logger.info(f"🎉 New Risala: {result['title']}")
                            found_new = True
                            await broadcast_new_risala(app.bot, result['title'], result.get('hindi_url'), result.get('urdu_url'))
                        else:
                            logger.info(f"No new Risala. Retry in 1h... ({retry_count+1})")
                            retry_count += 1
                            await asyncio.sleep(3600)
                    else:
                        logger.info(f"Scrape empty. Retry in 1h...")
                        retry_count += 1
                        await asyncio.sleep(3600)
                except Exception as e:
                    logger.error(f"Scrape error: {e}")
                    retry_count += 1
                    await asyncio.sleep(3600)
            
            if not found_new:
                logger.warning(f"No new Risala after {retry_count} retries.")
                
        except Exception as e:
            logger.error(f"Saturday scraper error: {e}")
            await asyncio.sleep(3600)

# ═══════════════════════════════════════════
#  POST INIT - START BACKGROUND TASKS
# ═══════════════════════════════════════════

async def post_init(application: Application):
    asyncio.create_task(saturday_scraper(application))
    asyncio.create_task(daily_hadees_broadcaster(application))

# ═══════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════

def main() -> None:
    init_db()
    
    try:
        scrape_latest_booklet()
    except Exception as e:
        logger.error(f"Initial scrape failed: {e}")
    
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("done", done_command))
    application.add_handler(CommandHandler("cancel", cancel))
    
    # Photo handler
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Text handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Callback query handler
    application.add_handler(CallbackQueryHandler(callback_router))

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
