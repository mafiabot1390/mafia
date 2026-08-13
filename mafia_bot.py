#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎭 ربات مافیای خیابانی  —  Street Mafia Telegram Bot
=====================================================
تک‌فایل | aiogram 3.x | SQLite | پراکسی SOCKS5 | دکمه‌های شیشه‌ای رنگی

نصب:
    pip install aiogram aiohttp-socks

اجرا:
    python mafia_bot.py
    python mafia_bot.py --selftest      # تست داخلی بدون نیاز به شبکه/توکن
"""

from __future__ import annotations

import asyncio
import html
import logging
import os
import random
import re
import sqlite3
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ChatType, ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# ═══════════════════════════════════════════════════════════════════
# ⚙️  تنظیمات
# ═══════════════════════════════════════════════════════════════════

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "8609846864:AAE0lwAnFZ7L-L-0MCGK8nBhfJxJ29vsPq8")

USE_PROXY: bool = False
PROXY_URL: str = "socks5://127.0.0.1:10808"

DB_FILE: str = "mafia_game.db"

ROB_COOLDOWN: int = 195          # ۳ دقیقه و ۱۵ ثانیه
CURRENCY: str = "پول"

STEAL_MIN, STEAL_MAX = 9, 500
MAX_LEVEL_INDEX = 14
TOP_LIMIT = 10

# دکمه‌های رنگی (Bot API 10.2 / July 2026). اگر سرور/کلاینت پشتیبانی نکرد → False
USE_BUTTON_STYLES: bool = True
# اگر ایموجی پریمیوم اختصاصی داری، آیدی‌اش را اینجا بگذار (اختیاری)
CUSTOM_EMOJI_IDS: Dict[str, Optional[str]] = {}

# ═══════════════════════════════════════════════════════════════════
# 🪵 لاگ  ——  زمان | سطح | نام | پیام
# ═══════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-14s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("mafia")
logging.getLogger("aiogram.event").setLevel(logging.WARNING)

# ═══════════════════════════════════════════════════════════════════
# 🏆 سطح‌بندی — ۱۵ سطح
# ═══════════════════════════════════════════════════════════════════

LEVELS: List[str] = [
    "🔰 نوچه",
    "⭐ شاگرد",
    "🎯 جیب‌بُر",
    "🔪 دزد خیابانی",
    "💣 سارق",
    "🔫 راهزن",
    "⚔️ یاغی",
    "🔥 تبهکار",
    "💎 قاچاقچی",
    "👑 رئیس باند",
    "🎭 مافیایی",
    "🏰 پادشاه زیرزمینی",
    "🗡️ شوالیه تاریکی",
    "👻 شبح شهر",
    "🃏 پدرخوانده",
]

SCENARIOS: List[str] = [
    "از یه رهگذر بی‌خبر زدی و فرار کردی",
    "جیب یه عابر رو خالی کردی",
    "از یه مغازه سرقت کردی",
    "یه ماشین پارک‌شده رو خالی کردی",
    "صندوق یه مغازه رو زدی",
    "کیف پول یه نفر رو برداشتی و دویدی",
    "از یه قمارخونه بردی و خارج شدی",
    "گاوصندوق یه خونه رو باز کردی",
    "از یه تاجر پولدار باج گرفتی",
    "یه محموله رو بالا کشیدی",
    "از صندوق یه رستوران دزدیدی",
    "کیف یه مسافر رو تو ایستگاه زدی",
    "از یه طلافروشی سرقت کردی",
    "پول یه دستفروش رو قاپیدی",
    "از یه عابربانک دزدیدی",
    "سیف‌باکس هتل رو خالی کردی",
    "از یه صرافی سرقت کردی",
    "کیف پول یه خواب‌آلود رو زدی",
    "از یه داروخانه شبانه دزدیدی",
    "پول‌های روی میز قمار رو قاپیدی",
]

COMMENTS: List[Tuple[int, List[str]]] = [
    (400, ["🍀 شانس بزرگ!", "🌟 افسانه‌ای بود!"]),
    (200, ["🔥 عالی بود!", "✋ دستت طلا!"]),
    (100, ["👍 بد نبود.", "🙂 خوب بود."]),
    (50, ["💼 خالی نموند.", "🤏 یه چیزی گیرت اومد."]),
    (0, ["😕 کم بود.", "🎲 شانست کم بود."]),
]

# توزیع مبلغ دزدی: (وزن, کمینه, بیشینه)
STEAL_TABLE: List[Tuple[int, int, int]] = [
    (30, 9, 50),
    (30, 51, 100),
    (18, 101, 200),
    (12, 201, 350),
    (10, 351, 500),
]
_STEAL_WEIGHTS = [w for w, _, _ in STEAL_TABLE]

# ═══════════════════════════════════════════════════════════════════
# 🔧 توابع کمکی
# ═══════════════════════════════════════════════════════════════════

_FA_DIGITS = str.maketrans("0123456789,.", "۰۱۲۳۴۵۶۷۸۹٬٫")
SEP = "━━━━━━━━━━━━━━━━━━━━"


def pn(value: Any) -> str:
    """تبدیل اعداد انگلیسی به فارسی."""
    return str(value).translate(_FA_DIGITS)


def money(amount: int) -> str:
    """فرمت پول فارسی + واحد."""
    return f"{pn(f'{int(amount):,}')} {CURRENCY}"


def cooldown_fmt(seconds: int) -> str:
    """زمان m:ss با اعداد فارسی."""
    seconds = max(0, int(seconds))
    return f"{pn(seconds // 60)}:{pn(f'{seconds % 60:02d}')}"


def get_required_robs(level_idx: int) -> int:
    """تعداد دزدی لازم برای عبور از سطح level_idx  →  int(15 × 1.5^idx)."""
    if level_idx < 0:
        return 0
    return int(15 * (1.5 ** level_idx))


def roll_steal() -> int:
    """مبلغ تصادفی ۹ تا ۵۰۰ سکه با توزیع وزنی."""
    _, lo, hi = random.choices(STEAL_TABLE, weights=_STEAL_WEIGHTS, k=1)[0]
    return random.randint(lo, hi)


def steal_comment(amount: int) -> str:
    """نظر تصادفی بر اساس مبلغ."""
    for threshold, texts in COMMENTS:
        if amount >= threshold:
            return random.choice(texts)
    return random.choice(COMMENTS[-1][1])


def progress_bar(cur: int, tgt: int, width: int = 8) -> str:
    """نوار پیشرفت متنی ۸ کاراکتری."""
    tgt = max(1, int(tgt))
    cur = min(max(0, int(cur)), tgt)
    filled = int(round(cur / tgt * width))
    filled = min(width, max(0, filled))
    return "█" * filled + "░" * (width - filled)


def level_name(level_idx: int) -> str:
    return LEVELS[min(max(int(level_idx), 0), MAX_LEVEL_INDEX)]


def progress_info(level_idx: int, total_robs: int) -> Optional[Dict[str, Any]]:
    """اطلاعات پیشرفت تا سطح بعد. None = بالاترین سطح."""
    if level_idx >= MAX_LEVEL_INDEX:
        return None
    cur_req = get_required_robs(level_idx)
    prev_req = get_required_robs(level_idx - 1) if level_idx > 0 else 0
    done = max(0, total_robs - prev_req)
    target = max(1, cur_req - prev_req)
    need = max(cur_req - total_robs, 0)
    return {
        "next_name": level_name(level_idx + 1),
        "done": done,
        "target": target,
        "need": need,
        "bar": progress_bar(done, target),
    }


def esc(text: Any) -> str:
    """امن‌سازی متن کاربر برای parse_mode=HTML."""
    return html.escape(str(text or ""), quote=False)


def display_name(full_name: Optional[str], username: Optional[str], user_id: int) -> str:
    name = (full_name or "").strip() or (f"@{username}" if username else "") or f"کاربر {user_id}"
    return name[:48]


# ═══════════════════════════════════════════════════════════════════
# 🎨 دکمه‌های شیشه‌ای رنگی  (style: primary | success | danger)
# ═══════════════════════════════════════════════════════════════════

def btn(
    text: str,
    *,
    callback_data: Optional[str] = None,
    url: Optional[str] = None,
    style: Optional[str] = None,
    emoji_key: Optional[str] = None,
) -> InlineKeyboardButton:
    """
    ساخت دکمه شیشه‌ای. style فقط یکی از primary / success / danger.
    اگر USE_BUTTON_STYLES خاموش باشد، فیلدهای جدید حذف می‌شوند (سازگاری با API قدیمی).
    """
    kwargs: Dict[str, Any] = {"text": text}
    if callback_data is not None:
        kwargs["callback_data"] = callback_data
    if url is not None:
        kwargs["url"] = url
    if USE_BUTTON_STYLES:
        if style in ("primary", "success", "danger"):
            kwargs["style"] = style
        emoji_id = CUSTOM_EMOJI_IDS.get(emoji_key) if emoji_key else None
        if emoji_id:
            kwargs["icon_custom_emoji_id"] = emoji_id
    return InlineKeyboardButton(**kwargs)


BOT_USERNAME: str = ""


def add_group_url() -> str:
    if BOT_USERNAME:
        return f"https://t.me/{BOT_USERNAME}?startgroup=true"
    return "https://t.me/"


def kb_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn("➕ افزودن به گروه", url=add_group_url(), style="success", emoji_key="add")],
        [
            btn("👤 حسابم", callback_data="acc", style="primary", emoji_key="acc"),
            btn("❓ راهنما دزدی", callback_data="help_main", style="primary", emoji_key="help"),
        ],
        [btn("📊 رتبه‌بندی", callback_data="top", style="danger", emoji_key="top")],
    ])


def kb_help_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            btn("💰 راهنمای دزدی", callback_data="help_rob", style="success"),
            btn("👤 راهنمای حساب", callback_data="help_acc", style="primary"),
        ],
        [
            btn("📈 سیستم سطح‌بندی", callback_data="help_lvl", style="primary"),
            btn("⏱️ زمان انتظار", callback_data="help_wait", style="danger"),
        ],
        [btn("🔙 بازگشت", callback_data="start_back", style="danger")],
    ])


def kb_back(target: str = "help_main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn("🔙 بازگشت", callback_data=target, style="danger")]
    ])


# ═══════════════════════════════════════════════════════════════════
# 💾 دیتابیس SQLite
# ═══════════════════════════════════════════════════════════════════

_db_lock = threading.RLock()
_conn: Optional[sqlite3.Connection] = None


def _connect() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=30)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA synchronous=NORMAL")
    return _conn


def init_db() -> None:
    """ساخت جدول اگر وجود نداشت."""
    with _db_lock:
        conn = _connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id       INTEGER PRIMARY KEY,
                username      TEXT,
                full_name     TEXT,
                money         INTEGER DEFAULT 0,
                rob_count     INTEGER DEFAULT 0,
                level_index   INTEGER DEFAULT 0,
                last_rob_time TIMESTAMP
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_money ON users(money DESC)")
        conn.commit()
    log.info("دیتابیس آماده شد → %s", DB_FILE)


def get_user(user_id: int, name: Optional[str] = None, username: Optional[str] = None) -> Dict[str, Any]:
    """دریافت کاربر یا ساخت کاربر جدید (و بروزرسانی نام/یوزرنیم)."""
    with _db_lock:
        conn = _connect()
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO users (user_id, username, full_name, money, rob_count, level_index, last_rob_time)"
                " VALUES (?, ?, ?, 0, 0, 0, NULL)",
                (user_id, username, name),
            )
            conn.commit()
            log.info("کاربر جدید ثبت شد → %s (%s)", user_id, name)
            row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        elif (name and row["full_name"] != name) or (username != row["username"]):
            conn.execute(
                "UPDATE users SET full_name = COALESCE(?, full_name), username = ? WHERE user_id = ?",
                (name, username, user_id),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row)


def update_user(
    user_id: int,
    money_add: int = 0,
    rob_inc: int = 0,
    level_inc: int = 0,
    set_time: bool = False,
) -> Dict[str, Any]:
    """بروزرسانی اتمیک کاربر و بازگرداندن رکورد جدید."""
    with _db_lock:
        conn = _connect()
        if set_time:
            conn.execute(
                "UPDATE users SET money = money + ?, rob_count = rob_count + ?,"
                " level_index = level_index + ?, last_rob_time = ? WHERE user_id = ?",
                (int(money_add), int(rob_inc), int(level_inc), _now_iso(), user_id),
            )
        else:
            conn.execute(
                "UPDATE users SET money = money + ?, rob_count = rob_count + ?,"
                " level_index = level_index + ? WHERE user_id = ?",
                (int(money_add), int(rob_inc), int(level_inc), user_id),
            )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else {}


def top_players(limit: int = TOP_LIMIT) -> List[Dict[str, Any]]:
    with _db_lock:
        conn = _connect()
        rows = conn.execute(
            "SELECT * FROM users ORDER BY money DESC, rob_count DESC, user_id ASC LIMIT ?",
            (int(limit),),
        ).fetchall()
        return [dict(r) for r in rows]


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _parse_ts(raw: Any) -> Optional[float]:
    """تبدیل مقدار last_rob_time به timestamp (پایدار در برابر فرمت‌های مختلف)."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw).strip()
    if not text:
        return None
    if text.replace(".", "", 1).isdigit():
        try:
            return float(text)
        except ValueError:
            return None
    text = text.replace("T", " ").split("+")[0].split("Z")[0].strip()
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            dt = datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except ValueError:
            continue
    return None


def cooldown_left(last_rob_time: Any) -> int:
    """ثانیه‌های باقی‌مانده از کول‌داون."""
    ts = _parse_ts(last_rob_time)
    if ts is None:
        return 0
    now = datetime.now(timezone.utc).timestamp()
    left = int(round(ROB_COOLDOWN - (now - ts)))
    if left < 0:
        return 0
    return min(left, ROB_COOLDOWN)


# ═══════════════════════════════════════════════════════════════════
# 📝 سازنده متن پیام‌ها
# ═══════════════════════════════════════════════════════════════════

def txt_start() -> str:
    return (
        "🎭 <b>مافیای خیابانی</b>\n"
        f"{SEP}\n"
        "سلام رفیق! به دنیای زیرزمینی خوش اومدی 🕶\n\n"
        "📌 <b>دستورات (در گروه):</b>\n"
        "💰 <code>دزدی</code> ─ <code>راهنما دزدی</code> ─ <code>حسابم</code>\n"
        f"{SEP}\n"
        "⚡ ربات رو به گروهت اضافه کن و شروع کن!"
    )


def txt_private_only() -> str:
    return (
        "⚠️ <b>این دستور فقط در گروه‌ها فعاله!</b>\n"
        f"{SEP}\n"
        "➕ ربات رو به گروهت اضافه کن."
    )


def txt_cooldown(left: int) -> str:
    return (
        "⏳ <b>صبر کن رفیق!</b>\n"
        f"{SEP}\n"
        "🔒 تازه دزدی کردی!\n"
        "🕵️ پلیس گشت می‌زنه...\n\n"
        f"⏱️ باقی‌مانده: <b>{cooldown_fmt(left)}</b>"
    )


def txt_rob(name: str, amount: int, scenario: str, comment: str,
            user: Dict[str, Any], upgraded: Optional[Tuple[str, int]]) -> str:
    lvl = int(user.get("level_index", 0))
    robs = int(user.get("rob_count", 0))
    lines = [
        "😈 <b>دزدی موفق!</b>",
        SEP,
        f"👤 {esc(name)}",
        f"💰 <b>{money(amount)}</b>",
        f"📝 {scenario}",
        comment,
        SEP,
        f"💵 کل: <b>{money(int(user.get('money', 0)))}</b>",
        f"🎖 {level_name(lvl)}",
        f"🔫 دزدی: <b>{pn(robs)}</b>",
    ]
    info = progress_info(lvl, robs)
    if info:
        lines.append(f"📊 {info['bar']} ({pn(info['done'])}/{pn(info['target'])})")
    else:
        lines.append("👑 <b>بالاترین سطح!</b>")
    if upgraded:
        new_name, reward = upgraded
        lines += [SEP, f"🎉 <b>ارتقا! {new_name}</b>", f"🎁 پاداش: <b>{money(reward)}</b>"]
    lines += [SEP, f"⏱️ بعدی: {cooldown_fmt(ROB_COOLDOWN)}"]
    return "\n".join(lines)


def txt_account(user: Dict[str, Any]) -> str:
    lvl = int(user.get("level_index", 0))
    robs = int(user.get("rob_count", 0))
    uname = user.get("username")
    lines = [
        "👤 <b>حساب شما</b>",
        SEP,
        f"🆔 <code>{pn(user.get('user_id', 0))}</code>",
        f"📛 {('@' + esc(uname)) if uname else 'ندارد'}",
        SEP,
        f"🏆 {level_name(lvl)}",
        f"💰 <b>{money(int(user.get('money', 0)))}</b>",
        f"🔫 دزدی: <b>{pn(robs)}</b>",
    ]
    info = progress_info(lvl, robs)
    if info:
        lines += [
            "",
            f"🔮 بعدی: <b>{info['next_name']}</b>",
            f"📊 {info['bar']} ({pn(info['done'])}/{pn(info['target'])})",
            f"📈 <b>{pn(info['need'])}</b> دزدی دیگه",
        ]
    else:
        lines += ["", "👑 <b>بالاترین سطح!</b>"]
    lines.append(SEP)
    return "\n".join(lines)


def txt_help_main() -> str:
    return (
        "🎭 <b>منوی راهنما</b>\n"
        f"{SEP}\n"
        "یکی از بخش‌ها رو انتخاب کن 👇"
    )


def txt_help_rob() -> str:
    chances = "\n".join(
        f"  • {pn(lo)}–{pn(hi)} {CURRENCY} → {pn(w)}٪"
        for w, lo, hi in STEAL_TABLE
    )
    return (
        "💰 <b>راهنمای دزدی</b>\n"
        f"{SEP}\n"
        f"دستور: <code>دزدی</code>\n"
        f"💵 مبلغ: {pn(STEAL_MIN)} تا {pn(STEAL_MAX)} {CURRENCY}\n"
        f"⏱️ انتظار: {cooldown_fmt(ROB_COOLDOWN)} دقیقه\n"
        "📍 فقط در گروه‌ها\n"
        f"{SEP}\n"
        f"🎯 <b>شانس مبالغ:</b>\n{chances}"
    )


def txt_help_acc() -> str:
    return (
        "👤 <b>راهنمای حساب</b>\n"
        f"{SEP}\n"
        "دستور: <code>حسابم</code>\n\n"
        "نمایش می‌ده:\n"
        "  🆔 آیدی عددی\n"
        "  🏆 سطح فعلی\n"
        "  💰 موجودی\n"
        "  🔫 تعداد دزدی\n"
        "  📊 نوار پیشرفت\n"
        f"{SEP}\n"
        "📍 در گروه و خصوصی کار می‌کنه."
    )


def txt_help_lvl() -> str:
    rows = "\n".join(
        f"{pn(i)}. {LEVELS[i]} — آستانه {pn(get_required_robs(i - 1) if i else 0)}"
        for i in range(len(LEVELS))
    )
    return (
        "📈 <b>سیستم سطح‌بندی</b>\n"
        f"{SEP}\n{rows}\n"
        f"{SEP}\n"
        "🎁 هر ارتقا = پاداش سکه!"
    )


def txt_help_wait() -> str:
    return (
        "⏱️ <b>زمان انتظار</b>\n"
        f"{SEP}\n"
        f"هر دزدی: <b>{pn(3)} دقیقه و {pn(15)} ثانیه</b>\n"
        f"({pn(ROB_COOLDOWN)} ثانیه)\n\n"
        "زودتر بزنی ⇒ پیام «صبر کن رفیق!» می‌گیری.\n"
        f"{SEP}\n"
        "🕵️ پلیس هم بیکار نیست!"
    )


def txt_top() -> str:
    players = top_players(TOP_LIMIT)
    if not players:
        return (
            "👑 <b>بهترین بازیکنان</b>\n"
            f"{SEP}\n"
            "هنوز کسی دزدی نکرده! 🤷‍♂️"
        )
    medals = ["🥇", "🥈", "🥉"]
    lines = ["👑 <b>بهترین بازیکنان</b>", SEP]
    for i, p in enumerate(players):
        tag = medals[i] if i < 3 else f"#{pn(i + 1)}"
        name = display_name(p.get("full_name"), p.get("username"), int(p.get("user_id", 0)))
        lines.append(
            f"{tag} {esc(name)} ─ 💰 {money(int(p.get('money', 0)))} | {level_name(int(p.get('level_index', 0)))}"
        )
    lines.append(SEP)
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# 🎮 منطق بازی
# ═══════════════════════════════════════════════════════════════════

def do_rob(user_id: int, name: str, username: Optional[str]) -> Dict[str, Any]:
    """
    یک تلاش دزدی. خروجی:
      {"ok": False, "left": n}  یا
      {"ok": True, "amount": n, "scenario": s, "comment": c, "user": row, "upgraded": (name, reward)|None}
    """
    with _db_lock:
        user = get_user(user_id, name, username)
        left = cooldown_left(user.get("last_rob_time"))
        if left > 0:
            return {"ok": False, "left": left}

        amount = roll_steal()
        user = update_user(user_id, money_add=amount, rob_inc=1, set_time=True)

        upgraded: Optional[Tuple[str, int]] = None
        lvl = int(user.get("level_index", 0))
        robs = int(user.get("rob_count", 0))
        total_reward = 0
        new_levels = 0
        while lvl + new_levels < MAX_LEVEL_INDEX and robs >= get_required_robs(lvl + new_levels):
            total_reward += (lvl + new_levels + 1) * 1000
            new_levels += 1
        if new_levels:
            user = update_user(user_id, money_add=total_reward, level_inc=new_levels)
            upgraded = (level_name(int(user.get("level_index", 0))), total_reward)
            log.info("ارتقا → کاربر %s سطح %s پاداش %s", user_id, user.get("level_index"), total_reward)

        return {
            "ok": True,
            "amount": amount,
            "scenario": random.choice(SCENARIOS),
            "comment": steal_comment(amount),
            "user": user,
            "upgraded": upgraded,
        }


# ═══════════════════════════════════════════════════════════════════
# 🤖 ربات / هندلرها
# ═══════════════════════════════════════════════════════════════════

dp = Dispatcher()

RE_ROB = re.compile(r"^\s*(?:دزدی|/rob)\s*$", re.IGNORECASE)
RE_ACC = re.compile(r"^\s*(?:حسابم|حساب من|/account)\s*$", re.IGNORECASE)
RE_HELP = re.compile(r"^\s*(?:راهنما\s*دزدی|راهنما|/help)\s*$", re.IGNORECASE)

GROUP_TYPES = {ChatType.GROUP, ChatType.SUPERGROUP}


@dp.message(CommandStart(), F.chat.type == ChatType.PRIVATE)
async def h_start(message: Message) -> None:
    u = message.from_user
    if u:
        get_user(u.id, u.full_name, u.username)
    await message.answer(txt_start(), reply_markup=kb_main())


@dp.message(Command("top"))
async def h_top_cmd(message: Message) -> None:
    await message.answer(txt_top(), reply_markup=kb_back("start_back"))


@dp.message(F.text.regexp(RE_ROB))
async def h_rob(message: Message) -> None:
    u = message.from_user
    if u is None:
        return
    if message.chat.type not in GROUP_TYPES:
        await message.answer(txt_private_only(), reply_markup=kb_main())
        return

    name = display_name(u.full_name, u.username, u.id)
    res = await asyncio.to_thread(do_rob, u.id, u.full_name, u.username)
    if not res["ok"]:
        await message.reply(txt_cooldown(int(res["left"])))
        return
    await message.reply(
        txt_rob(name, res["amount"], res["scenario"], res["comment"], res["user"], res["upgraded"])
    )


@dp.message(F.text.regexp(RE_ACC))
async def h_account(message: Message) -> None:
    u = message.from_user
    if u is None:
        return
    user = await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
    await message.reply(txt_account(user))


@dp.message(F.text.regexp(RE_HELP))
async def h_help(message: Message) -> None:
    await message.answer(txt_help_main(), reply_markup=kb_help_menu())


# ── کالبک‌ها ──────────────────────────────────────────────────────

async def _edit(cq: CallbackQuery, text: str, kb: InlineKeyboardMarkup) -> None:
    """ویرایش امن پیام (نادیده گرفتن خطای «تغییری نکرد»)."""
    try:
        if cq.message is not None:
            await cq.message.edit_text(text, reply_markup=kb)
    except Exception as e:  # noqa: BLE001
        if "not modified" not in str(e).lower():
            log.warning("ویرایش پیام ناموفق: %s", e)
            try:
                if cq.message is not None:
                    await cq.message.answer(text, reply_markup=kb)
            except Exception as e2:  # noqa: BLE001
                log.error("ارسال جایگزین ناموفق: %s", e2)


@dp.callback_query(F.data == "acc")
async def cb_acc(cq: CallbackQuery) -> None:
    u = cq.from_user
    user = await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
    await _edit(cq, txt_account(user), kb_back("start_back"))
    await cq.answer()


@dp.callback_query(F.data == "top")
async def cb_top(cq: CallbackQuery) -> None:
    text = await asyncio.to_thread(txt_top)
    await _edit(cq, text, kb_back("start_back"))
    await cq.answer()


@dp.callback_query(F.data == "help_main")
async def cb_help_main(cq: CallbackQuery) -> None:
    await _edit(cq, txt_help_main(), kb_help_menu())
    await cq.answer()


@dp.callback_query(F.data == "help_rob")
async def cb_help_rob(cq: CallbackQuery) -> None:
    await _edit(cq, txt_help_rob(), kb_back("help_main"))
    await cq.answer()


@dp.callback_query(F.data == "help_acc")
async def cb_help_acc(cq: CallbackQuery) -> None:
    await _edit(cq, txt_help_acc(), kb_back("help_main"))
    await cq.answer()


@dp.callback_query(F.data == "help_lvl")
async def cb_help_lvl(cq: CallbackQuery) -> None:
    await _edit(cq, txt_help_lvl(), kb_back("help_main"))
    await cq.answer()


@dp.callback_query(F.data == "help_wait")
async def cb_help_wait(cq: CallbackQuery) -> None:
    await _edit(cq, txt_help_wait(), kb_back("help_main"))
    await cq.answer()


@dp.callback_query(F.data == "start_back")
async def cb_start_back(cq: CallbackQuery) -> None:
    await _edit(cq, txt_start(), kb_main())
    await cq.answer()


@dp.callback_query()
async def cb_unknown(cq: CallbackQuery) -> None:
    await cq.answer("❔ نامشخص", show_alert=False)


# ═══════════════════════════════════════════════════════════════════
# 🚀 اجرا
# ═══════════════════════════════════════════════════════════════════

def build_session() -> Optional[AiohttpSession]:
    if not USE_PROXY:
        return None
    try:
        session = AiohttpSession(proxy=PROXY_URL)
        log.info("پراکسی فعال → %s", PROXY_URL)
        return session
    except Exception as e:  # noqa: BLE001
        log.error("ساخت سشن پراکسی ناموفق (%s) — بدون پراکسی ادامه می‌دهیم", e)
        return None


async def main() -> None:
    global BOT_USERNAME

    if BOT_TOKEN in ("", "YOUR_BOT_TOKEN_HERE"):
        log.error("توکن تنظیم نشده! BOT_TOKEN را در فایل یا متغیر محیطی قرار بده.")
        return

    init_db()
    log.info("در حال راه‌اندازی ربات مافیای خیابانی...")

    session = build_session()
    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    try:
        me = await bot.get_me()
        BOT_USERNAME = me.username or ""
        log.info("ربات متصل شد → %s (@%s)", me.full_name, BOT_USERNAME)
        await bot.delete_webhook(drop_pending_updates=True)
        log.info("شروع دریافت آپدیت‌ها (polling)...")
        await dp.start_polling(bot)
    except Exception as e:  # noqa: BLE001
        log.exception("خطای بحرانی در اجرا: %s", e)
    finally:
        try:
            await bot.session.close()
        except Exception:  # noqa: BLE001
            pass
        with _db_lock:
            if _conn is not None:
                _conn.close()
        log.info("ربات خاموش شد. خداحافظ 👋")


# ═══════════════════════════════════════════════════════════════════
# 🧪 تست داخلی (بدون شبکه)
# ═══════════════════════════════════════════════════════════════════

def selftest() -> int:
    global DB_FILE, _conn
    fails: List[str] = []

    def chk(cond: bool, label: str) -> None:
        if not cond:
            fails.append(label)
        print(("  ✅ " if cond else "  ❌ ") + label)

    print("── توابع کمکی ──")
    chk(pn("1234") == "۱۲۳۴", "pn")
    chk(money(1500).startswith("۱٬۵۰۰"), f"money → {money(1500)}")
    chk(cooldown_fmt(195) == "۳:۱۵", f"cooldown_fmt(195) = {cooldown_fmt(195)}")
    chk(cooldown_fmt(9) == "۰:۰۹", f"cooldown_fmt(9) = {cooldown_fmt(9)}")
    real = [get_required_robs(i) for i in range(15)]
    print("  ℹ️  آستانه‌ها:", real)
    chk(real[:6] == [15, 22, 33, 50, 75, 113], "get_required_robs فرمول int(15×1.5^n)")
    chk(all(real[i] < real[i + 1] for i in range(14)), "آستانه‌ها صعودی")
    chk(len(LEVELS) == 15, "۱۵ سطح")
    chk(len(SCENARIOS) == 20, f"۲۰ سناریو (={len(SCENARIOS)})")
    chk(sum(_STEAL_WEIGHTS) == 100, f"جمع درصدها = {sum(_STEAL_WEIGHTS)}")
    chk(len(progress_bar(3, 8)) == 8, "طول نوار پیشرفت")
    chk(progress_bar(0, 10) == "░" * 8 and progress_bar(10, 10) == "█" * 8, "کرانه‌های نوار")
    rolls = [roll_steal() for _ in range(5000)]
    chk(min(rolls) >= 9 and max(rolls) <= 500, f"roll_steal بازه [{min(rolls)},{max(rolls)}]")
    chk(all(isinstance(steal_comment(a), str) for a in (5, 60, 150, 250, 450)), "steal_comment")

    print("── دکمه‌ها ──")
    for kb in (kb_main(), kb_help_menu(), kb_back()):
        for row in kb.inline_keyboard:
            for b in row:
                d = b.model_dump(exclude_none=True)
                if "style" in d and d["style"] not in ("primary", "success", "danger"):
                    fails.append("style نامعتبر")
    chk(True, "ساخت کیبوردها + اعتبار style")
    chk(kb_main().inline_keyboard[0][0].style == "success", "استایل دکمه افزودن")

    print("── دیتابیس ──")
    DB_FILE = "mafia_selftest.db"
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    _conn = None
    init_db()
    u = get_user(101, "علی مافیا", "ali")
    chk(u["money"] == 0 and u["level_index"] == 0, "کاربر جدید")
    u2 = update_user(101, money_add=250, rob_inc=1, set_time=True)
    chk(u2["money"] == 250 and u2["rob_count"] == 1, "update_user")
    chk(cooldown_left(u2["last_rob_time"]) > 190, f"کول‌داون = {cooldown_left(u2['last_rob_time'])}")
    r = do_rob(101, "علی مافیا", "ali")
    chk(r["ok"] is False and r["left"] > 0, "مسدودسازی کول‌داون")

    # شبیه‌سازی ۳۰ دزدی با ریست زمان → بررسی ارتقا
    ups = 0
    for _ in range(30):
        with _db_lock:
            _connect().execute("UPDATE users SET last_rob_time = NULL WHERE user_id = 101")
            _connect().commit()
        rr = do_rob(101, "علی مافیا", "ali")
        if rr["ok"] and rr["upgraded"]:
            ups += 1
    final = get_user(101)
    chk(final["rob_count"] == 31, f"تعداد دزدی = {final['rob_count']}")
    chk(final["level_index"] >= 2, f"سطح پس از ۳۱ دزدی = {final['level_index']} (ارتقا×{ups})")
    chk(final["money"] > 0, f"موجودی = {final['money']}")

    print("── متن‌ها ──")
    get_user(202, "رضا", None)
    update_user(202, money_add=9999, rob_inc=5)
    samples = {
        "start": txt_start(),
        "private_only": txt_private_only(),
        "cooldown": txt_cooldown(74),
        "account": txt_account(get_user(101)),
        "help_main": txt_help_main(),
        "help_rob": txt_help_rob(),
        "help_acc": txt_help_acc(),
        "help_lvl": txt_help_lvl(),
        "help_wait": txt_help_wait(),
        "top": txt_top(),
        "rob": txt_rob("علی مافیا", 430, SCENARIOS[0], steal_comment(430), get_user(101), ("🃏 پدرخوانده", 15000)),
    }
    for k, v in samples.items():
        chk(bool(v) and len(v) < 4096, f"{k} ({len(v)} کاراکتر)")
        chk(not re.search(r"[0-9]", re.sub(r"<[^>]+>", "", v)), f"{k}: اعداد فارسی")

    # حالت بالاترین سطح
    with _db_lock:
        _connect().execute("UPDATE users SET level_index = 14, rob_count = 5000 WHERE user_id = 101")
        _connect().commit()
    acc_max = txt_account(get_user(101))
    chk("بالاترین سطح" in acc_max, "نمایش بالاترین سطح")
    chk(progress_info(14, 5000) is None, "progress_info سطح آخر")

    print("── نمونه خروجی ──\n")
    for k in ("start", "rob", "account", "top", "help_rob"):
        print(re.sub(r"</?[^>]+>", "", samples[k]))
        print("- - - - - - - - - -")

    with _db_lock:
        if _conn is not None:
            _conn.close()
            _conn = None
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    for ext in ("-wal", "-shm"):
        p = "mafia_selftest.db" + ext
        if os.path.exists(p):
            os.remove(p)

    print(f"\n{'🎉 همه تست‌ها موفق' if not fails else '❌ خطاها: ' + str(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("توقف دستی توسط کاربر.")
