#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎭 ربات مافیای خیابانی — Street Mafia Bot  (نسخه ماژولار ۲.۰)
════════════════════════════════════════════════════════════════════════════
تک‌فایل | aiogram 3.x | SQLite | دکمه‌های شیشه‌ای رنگی | آماده Railway

┌────────────────────────────────────────────────────────────────────────┐
│ 📚 فهرست بخش‌ها — هر بخش مستقل است                                      │
│    می‌تونی هر بخش رو کامل برداری، جدا ویرایش کنی و سر جاش برگردونی.      │
│    مرز هر بخش با «▓▓ بخش NN … [شروع] / [پایان] ▓▓» مشخص شده.            │
├────────────────────────────────────────────────────────────────────────┤
│ ۰۱  ایمپورت‌ها            │ پایه — حذف نکن                              │
│ ۰۲  تنظیمات و لاگ         │ پایه — توکن، پراکسی، مسیر دیتابیس           │
│ ۰۳  توابع کمکی            │ پایه — pn / money / زمان / نوار پیشرفت      │
│ ۰۴  دکمه‌های شیشه‌ای رنگی  │ پایه — btn() و استایل‌ها                     │
│ ۰۵  دیتابیس               │ پایه — جدول users + مهاجرت خودکار ستون‌ها    │
│ ۰۶  سطح‌بندی (۱۵ سطح)     │ پایه                                        │
│ ۰۷  پلیس و زندان          │ قابل‌برداشت (دستگیری، وثیقه، آزادی)          │
│ ۰۸  دزدی                  │ قابل‌برداشت (هسته بازی)                      │
│ ۰۹  کیف پول               │ قابل‌برداشت                                  │
│ ۱۰  اسلحه AK-۴۷           │ قابل‌برداشت                                  │
│ ۱۱  پرونده جعلی           │ قابل‌برداشت                                  │
│ ۱۲  نوچه                  │ قابل‌برداشت                                  │
│ ۱۳  سند جعلی              │ قابل‌برداشت                                  │
│ ۱۴  فروشگاه               │ قابل‌برداشت (کاتالوگ همه آیتم‌ها)             │
│ ۱۵  قمارخونه              │ قابل‌برداشت                                  │
│ ۱۶  حساب و رتبه‌بندی      │ قابل‌برداشت                                  │
│ ۱۷  راهنما                │ قابل‌برداشت                                  │
│ ۱۸  استارت و منوی اصلی    │ پایه                                        │
│ ۱۹  اجرا (main)           │ پایه                                        │
│ ۲۰  تست داخلی             │ اختیاری — python mafia_bot.py --selftest    │
└────────────────────────────────────────────────────────────────────────┘

🔌 قواعد ماژولار بودن (مهم):
  • هر بخش قابل‌برداشت، ستون‌های دیتابیس خودش را با register_columns() ثبت می‌کند.
  • ارجاع بین بخش‌ها فقط با _opt("نام_تابع", ...) انجام می‌شود؛ اگر بخشی حذف شود
    فراخوانی بی‌صدا رد می‌شود و ربات بدون خطا اجرا می‌شود.
  • دکمه‌های منوی اصلی/راهنما هم با has() چک می‌شوند و اگر بخش نباشد نمایش داده نمی‌شوند.

نصب:  pip install -r requirements.txt
اجرا:  python mafia_bot.py            |  تست: python mafia_bot.py --selftest
"""

# ══════════════════════════════════════════════════════════════════════════
# ▓▓ بخش ۰۱ — ایمپورت‌ها (IMPORTS) ▓▓  [شروع]
# ══════════════════════════════════════════════════════════════════════════
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
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ChatType, ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# ▓▓ بخش ۰۱ — پایان ▓▓


# ══════════════════════════════════════════════════════════════════════════
# ▓▓ بخش ۰۲ — تنظیمات و لاگ (CONFIG) ▓▓  [شروع]
#    توکن، پراکسی، مسیر دیتابیس (ولوم Railway)، کول‌داون دزدی، واحد پول
# ══════════════════════════════════════════════════════════════════════════

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "8609846864:AAEibGaCVNdEMEjzlGh_BVUUSJo1f4ss7Q8")

# پراکسی: روی سیستم شخصی True، روی سرور (Railway) لازم نیست.
_env_proxy = os.getenv("USE_PROXY")
USE_PROXY: bool = (
    _env_proxy.strip().lower() in ("1", "true", "yes", "on")
    if _env_proxy is not None else False
)
PROXY_URL: str = os.getenv("PROXY_URL", "socks5://127.0.0.1:10808")


def _default_db_path() -> str:
    """
    مسیر دیتابیس: اولویت با ولوم دائمی سرور تا با هر ری‌دیپلوی داده‌ها نپرند.
      ۱) متغیر محیطی DB_PATH
      ۲) ولوم /DATA یا /data (Railway Volume)
      ۳) کنار فایل پروژه
    """
    env = os.getenv("DB_PATH")
    if env:
        return env
    for folder in ("/DATA", "/data"):
        if os.path.isdir(folder) and os.access(folder, os.W_OK):
            return os.path.join(folder, "mafia_game.db")
    return "mafia_game.db"


DB_FILE: str = _default_db_path()

CURRENCY: str = "سکه"
ROB_COOLDOWN: int = 195            # ۳ دقیقه و ۱۵ ثانیه

# دکمه‌های رنگی — Bot API 10.2+ (فقط primary / success / danger)
USE_BUTTON_STYLES: bool = True
CUSTOM_EMOJI_IDS: Dict[str, Optional[str]] = {}   # اختیاری: ایموجی پریمیوم

# لاگ ── زمان | سطح | نام | پیام
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-14s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("mafia")
logging.getLogger("aiogram.event").setLevel(logging.WARNING)

dp = Dispatcher()
BOT_USERNAME: str = ""

# ▓▓ بخش ۰۲ — پایان ▓▓


# ══════════════════════════════════════════════════════════════════════════
# ▓▓ بخش ۰۳ — توابع کمکی (HELPERS) ▓▓  [شروع]
#    pn / pn_back / money / cooldown_fmt / duration_fa / progress_bar / _opt
# ══════════════════════════════════════════════════════════════════════════

SEP = "━━━━━━━━━━━━━━━━━━━━"

# کلمات رزرو‌شده — نمی‌توانند اسم نوچه شوند (تا با دستورات تداخل نکنند)
RESERVED_WORDS: set = {
    "دزدی", "حسابم", "زندان", "وثیقه", "آزادی", "ازادی", "راهنما", "راهنما دزدی",
    "فروشگاه", "اسلحه", "پرونده", "کیف پول", "کیفم", "نوچه", "سند", "قمارخونه",
    "قمار", "رتبه", "start", "شروع",
}

_FA_DIGITS = str.maketrans("0123456789,.", "۰۱۲۳۴۵۶۷۸۹٬٫")
_EN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩٬٫", "01234567890123456789,.")


def pn(value: Any) -> str:
    """اعداد انگلیسی → فارسی."""
    return str(value).translate(_FA_DIGITS)


def pn_back(text: Any) -> str:
    """اعداد فارسی/عربی → انگلیسی + حذف جداکننده هزار."""
    return str(text).translate(_EN_DIGITS).replace(",", "").replace(" ", "")


def parse_int(text: Any) -> Optional[int]:
    """پارس عدد از ورودی کاربر (فارسی یا انگلیسی)."""
    raw = pn_back(text).strip()
    if not re.fullmatch(r"\d{1,12}", raw):
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def money(amount: Any) -> str:
    """فرمت پول فارسی + واحد."""
    return f"{pn(f'{int(amount):,}')} {CURRENCY}"


def cooldown_fmt(seconds: int) -> str:
    """زمان m:ss فارسی."""
    seconds = max(0, int(seconds))
    return f"{pn(seconds // 60)}:{pn(f'{seconds % 60:02d}')}"


def duration_fa(seconds: int) -> str:
    """مدت خوانا: «۲ ساعت و ۱۵ دقیقه» / «۴۵ ثانیه»."""
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    parts: List[str] = []
    if h:
        parts.append(f"{pn(h)} ساعت")
    if m:
        parts.append(f"{pn(m)} دقیقه")
    if s and not h:
        parts.append(f"{pn(s)} ثانیه")
    return " و ".join(parts) if parts else "چند لحظه"


def progress_bar(cur: Any, tgt: Any, width: int = 8) -> str:
    """نوار پیشرفت متنی (█░)."""
    tgt = max(1, int(tgt))
    cur = min(max(0, int(cur)), tgt)
    filled = min(width, max(0, int(round(cur / tgt * width))))
    return "█" * filled + "░" * (width - filled)


def pct(value: float) -> str:
    """درصد فارسی."""
    return f"{pn(int(round(value * 100)))}٪"


def esc(text: Any) -> str:
    """امن‌سازی متن کاربر برای parse_mode=HTML."""
    return html.escape(str(text or ""), quote=False)


def display_name(full_name: Optional[str], username: Optional[str], user_id: int) -> str:
    name = (full_name or "").strip() or (f"@{username}" if username else "") or f"کاربر {user_id}"
    return name[:48]


def now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


def iso(ts: Optional[float] = None) -> str:
    ts = now_ts() if ts is None else ts
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def parse_ts(raw: Any) -> Optional[float]:
    """رشته/عدد تایم‌استمپ → timestamp (تحمل چند فرمت)."""
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
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            continue
    return None


def has(func_name: str) -> bool:
    """آیا بخشی که این تابع را تعریف می‌کند در فایل حاضر است؟"""
    return callable(globals().get(func_name))


def _opt(func_name: str, *args: Any, default: Any = None, **kwargs: Any) -> Any:
    """
    فراخوانی نرم بین بخش‌ها: اگر بخش مربوطه حذف شده باشد، default برمی‌گردد.
    این تابع ستون فقرات ماژولار بودن است — دست نزن.
    """
    fn = globals().get(func_name)
    if not callable(fn):
        return default
    try:
        return fn(*args, **kwargs)
    except Exception as e:  # noqa: BLE001
        log.error("خطا در %s: %s", func_name, e)
        return default


# ▓▓ بخش ۰۳ — پایان ▓▓


# ══════════════════════════════════════════════════════════════════════════
# ▓▓ بخش ۰۴ — دکمه‌های شیشه‌ای رنگی (BUTTONS) ▓▓  [شروع]
#    استایل رسمی تلگرام: primary (آبی) | success (سبز) | danger (قرمز)
# ══════════════════════════════════════════════════════════════════════════

STYLE_PRIMARY = "primary"
STYLE_SUCCESS = "success"
STYLE_DANGER = "danger"
VALID_STYLES = (STYLE_PRIMARY, STYLE_SUCCESS, STYLE_DANGER)


def btn(
    text: str,
    *,
    callback_data: Optional[str] = None,
    url: Optional[str] = None,
    style: Optional[str] = None,
    emoji_key: Optional[str] = None,
) -> InlineKeyboardButton:
    """
    دکمه شیشه‌ای رنگی. اگر USE_BUTTON_STYLES=False باشد فیلدهای جدید حذف
    می‌شوند تا روی کلاینت/سرور قدیمی هم بدون خطا کار کند.
    """
    kwargs: Dict[str, Any] = {"text": text}
    if callback_data is not None:
        kwargs["callback_data"] = callback_data
    if url is not None:
        kwargs["url"] = url
    if USE_BUTTON_STYLES:
        if style in VALID_STYLES:
            kwargs["style"] = style
        emoji_id = CUSTOM_EMOJI_IDS.get(emoji_key) if emoji_key else None
        if emoji_id:
            kwargs["icon_custom_emoji_id"] = emoji_id
    return InlineKeyboardButton(**kwargs)


def rows(*button_rows: Sequence[InlineKeyboardButton]) -> InlineKeyboardMarkup:
    """ساخت کیبورد از ردیف‌ها (ردیف‌های خالی حذف می‌شوند)."""
    clean = [list(r) for r in button_rows if r]
    return InlineKeyboardMarkup(inline_keyboard=clean)


def kb_back(target: str = "help_main", label: str = "🔙 بازگشت") -> InlineKeyboardMarkup:
    return rows([btn(label, callback_data=target, style=STYLE_DANGER)])


def kb_back_row(target: str = "start_back") -> List[InlineKeyboardButton]:
    return [btn("🔙 بازگشت", callback_data=target, style=STYLE_DANGER)]


async def safe_edit(cq: CallbackQuery, text: str, kb: Optional[InlineKeyboardMarkup]) -> None:
    """ویرایش امن پیام؛ اگر نشد پیام تازه می‌فرستد."""
    try:
        if cq.message is not None:
            await cq.message.edit_text(text, reply_markup=kb)
            return
    except Exception as e:  # noqa: BLE001
        if "not modified" in str(e).lower():
            return
        log.warning("ویرایش پیام ناموفق: %s", e)
    try:
        if cq.message is not None:
            await cq.message.answer(text, reply_markup=kb)
    except Exception as e2:  # noqa: BLE001
        log.error("ارسال جایگزین ناموفق: %s", e2)


# ▓▓ بخش ۰۴ — پایان ▓▓


# ══════════════════════════════════════════════════════════════════════════
# ▓▓ بخش ۰۵ — دیتابیس (DATABASE) ▓▓  [شروع]
#    جدول users + ثبت ستون‌های اختیاری هر بخش با register_columns()
# ══════════════════════════════════════════════════════════════════════════

_db_lock = threading.RLock()
_conn: Optional[sqlite3.Connection] = None

# ستون‌های پایه
BASE_COLUMNS: Dict[str, str] = {
    "username": "TEXT",
    "full_name": "TEXT",
    "money": "INTEGER DEFAULT 0",
    "rob_count": "INTEGER DEFAULT 0",
    "level_index": "INTEGER DEFAULT 0",
    "last_rob_time": "TIMESTAMP",
}

# ستون‌هایی که بخش‌های اختیاری ثبت می‌کنند
EXTRA_COLUMNS: Dict[str, str] = {}


def register_columns(**cols: str) -> None:
    """هر بخش ستون‌های خودش را اینجا ثبت می‌کند (در زمان ایمپورت)."""
    EXTRA_COLUMNS.update(cols)


def all_columns() -> Dict[str, str]:
    return {**BASE_COLUMNS, **EXTRA_COLUMNS}


def _connect() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        folder = os.path.dirname(os.path.abspath(DB_FILE))
        if folder and not os.path.isdir(folder):
            os.makedirs(folder, exist_ok=True)
        _conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=30)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA synchronous=NORMAL")
    return _conn


def init_db() -> None:
    """ساخت جدول + مهاجرت خودکار ستون‌های جدید (بدون از دست رفتن داده)."""
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
        existing = {r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
        added = 0
        for col, ddl in all_columns().items():
            if col not in existing:
                conn.execute(f"ALTER TABLE users ADD COLUMN {col} {ddl}")
                added += 1
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_money ON users(money DESC)")
        conn.commit()
    if added:
        log.info("مهاجرت دیتابیس → %s ستون جدید اضافه شد", added)
    log.info("دیتابیس آماده شد → %s", os.path.abspath(DB_FILE))


def close_db() -> None:
    global _conn
    with _db_lock:
        if _conn is not None:
            _conn.close()
            _conn = None


def get_user(user_id: int, name: Optional[str] = None, username: Optional[str] = None) -> Dict[str, Any]:
    """دریافت یا ساخت کاربر (و بروزرسانی نام/یوزرنیم)."""
    with _db_lock:
        conn = _connect()
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
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
    """بروزرسانی افزایشی (سازگار با نسخه قبل)."""
    with _db_lock:
        conn = _connect()
        if set_time:
            conn.execute(
                "UPDATE users SET money = MAX(0, money + ?), rob_count = rob_count + ?,"
                " level_index = level_index + ?, last_rob_time = ? WHERE user_id = ?",
                (int(money_add), int(rob_inc), int(level_inc), iso(), user_id),
            )
        else:
            conn.execute(
                "UPDATE users SET money = MAX(0, money + ?), rob_count = rob_count + ?,"
                " level_index = level_index + ? WHERE user_id = ?",
                (int(money_add), int(rob_inc), int(level_inc), user_id),
            )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else {}


def set_fields(user_id: int, **fields: Any) -> Dict[str, Any]:
    """ست کردن مقدار مطلق ستون‌ها (فقط ستون‌های ثبت‌شده مجاز است)."""
    valid = set(all_columns().keys())
    sets, vals = [], []
    for key, value in fields.items():
        if key not in valid:
            raise ValueError(f"ستون ناشناس: {key}")
        sets.append(f"{key} = ?")
        vals.append(value)
    if not sets:
        return get_user(user_id)
    with _db_lock:
        conn = _connect()
        get_user(user_id)
        conn.execute(f"UPDATE users SET {', '.join(sets)} WHERE user_id = ?", (*vals, user_id))
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else {}


def add_money(user_id: int, delta: int) -> Dict[str, Any]:
    """افزودن/کاستن پول جیب (کف صفر)."""
    return update_user(user_id, money_add=int(delta))


def spend(user_id: int, amount: int) -> bool:
    """پرداخت اتمیک از جیب. True اگر پول کافی بود."""
    amount = int(amount)
    with _db_lock:
        conn = _connect()
        row = conn.execute("SELECT money FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if row is None or int(row["money"] or 0) < amount:
            return False
        conn.execute("UPDATE users SET money = money - ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        return True


def top_players(limit: int = 10) -> List[Dict[str, Any]]:
    with _db_lock:
        conn = _connect()
        rows_ = conn.execute(
            "SELECT * FROM users ORDER BY money DESC, rob_count DESC, user_id ASC LIMIT ?",
            (int(limit),),
        ).fetchall()
        return [dict(r) for r in rows_]


def num(user: Dict[str, Any], key: str, default: int = 0) -> int:
    """خواندن امن ستون عددی (اگر بخش حذف شده باشد ستون نیست)."""
    try:
        return int(user.get(key) if user.get(key) is not None else default)
    except (TypeError, ValueError):
        return default


# ▓▓ بخش ۰۵ — پایان ▓▓


# ══════════════════════════════════════════════════════════════════════════
# ▓▓ بخش ۰۶ — سطح‌بندی (LEVELS) ▓▓  [شروع]
#    ۱۵ سطح | آستانه: int(15 × 1.5^n) | پاداش ارتقا: (idx+1) × ۱۰۰۰
# ══════════════════════════════════════════════════════════════════════════

LEVELS: List[str] = [
    "🔰 نوچه", "⭐ شاگرد", "🎯 جیب‌بُر", "🔪 دزد خیابانی", "💣 سارق",
    "🔫 راهزن", "⚔️ یاغی", "🔥 تبهکار", "💎 قاچاقچی", "👑 رئیس باند",
    "🎭 مافیایی", "🏰 پادشاه زیرزمینی", "🗡️ شوالیه تاریکی", "👻 شبح شهر", "🃏 پدرخوانده",
]
MAX_LEVEL_INDEX = len(LEVELS) - 1
LEVEL_REWARD_STEP = 1000


def get_required_robs(level_idx: int) -> int:
    """تعداد دزدی لازم برای عبور از سطح level_idx."""
    if level_idx < 0:
        return 0
    return int(15 * (1.5 ** level_idx))


def level_name(level_idx: Any) -> str:
    return LEVELS[min(max(int(level_idx or 0), 0), MAX_LEVEL_INDEX)]


def progress_info(level_idx: int, total_robs: int) -> Optional[Dict[str, Any]]:
    """اطلاعات پیشرفت تا سطح بعد؛ None = بالاترین سطح."""
    level_idx = int(level_idx or 0)
    total_robs = int(total_robs or 0)
    if level_idx >= MAX_LEVEL_INDEX:
        return None
    cur_req = get_required_robs(level_idx)
    prev_req = get_required_robs(level_idx - 1) if level_idx > 0 else 0
    return {
        "next_name": level_name(level_idx + 1),
        "done": max(0, total_robs - prev_req),
        "target": max(1, cur_req - prev_req),
        "need": max(cur_req - total_robs, 0),
        "bar": progress_bar(max(0, total_robs - prev_req), max(1, cur_req - prev_req)),
    }


def apply_level_up(user_id: int, user: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[Tuple[str, int]]]:
    """
    بررسی و اعمال ارتقا (چند سطح پشت‌سرهم هم پشتیبانی می‌شود).
    خروجی: (رکورد جدید, (نام سطح, پاداش) یا None)
    """
    lvl = num(user, "level_index")
    robs = num(user, "rob_count")
    reward, steps = 0, 0
    while lvl + steps < MAX_LEVEL_INDEX and robs >= get_required_robs(lvl + steps):
        reward += (lvl + steps + 1) * LEVEL_REWARD_STEP
        steps += 1
    if not steps:
        return user, None
    user = update_user(user_id, money_add=reward, level_inc=steps)
    log.info("ارتقا → کاربر %s سطح %s پاداش %s", user_id, user.get("level_index"), reward)
    return user, (level_name(user.get("level_index")), reward)


# ▓▓ بخش ۰۶ — پایان ▓▓
# ══════════════════════════════════════════════════════════════════════════
# ▓▓ بخش ۰۷ — پلیس و زندان (JAIL) ▓▓  [شروع]
#    دستگیری تصادفی «هر از گاهی» (بدون سقف ۱۵) + وثیقه بر اساس دزدی
#    دستورات: زندان | وثیقه        کالبک: jail / bail / jail_wait / help_jail
# ══════════════════════════════════════════════════════════════════════════

register_columns(
    streak="INTEGER DEFAULT 0",              # دزدی پیاپی بدون دستگیری
    robs_since_arrest="INTEGER DEFAULT 0",   # دزدی از آخرین دستگیری
    jail_until="TIMESTAMP",
    jail_total="INTEGER DEFAULT 0",
    arrest_count="INTEGER DEFAULT 0",
    bail_count="INTEGER DEFAULT 0",
    loot_since_arrest="INTEGER DEFAULT 0",   # غنیمت از آخرین دستگیری (مبنای وثیقه)
)

# ── تنظیمات قابل تغییر ─────────────────────────────────────────────
ARREST_BASE_CHANCE: float = 0.055   # شانس پایه دستگیری
ARREST_RAMP: float = 0.009          # افزایش شانس به ازای هر دزدی بدون دستگیری
ARREST_MAX_CHANCE: float = 0.32     # سقف شانس (هیچ‌وقت قطعی نیست)
ARREST_GRACE: int = 2               # این تعداد دزدی اول بعد از آزادی، امن است

JAIL_MIN_MINUTES: int = 20
JAIL_MAX_MINUTES: int = 180         # ۳ ساعت

BAIL_BASE: int = 400                # پایه وثیقه
BAIL_PER_ROB: int = 130             # به ازای هر دزدی بعد از آخرین دستگیری
BAIL_LOOT_RATIO: float = 0.35       # درصدی از غنیمت همان دوره
BAIL_PER_MINUTE: int = 45           # به ازای هر دقیقه باقی‌مانده
BAIL_LEVEL_STEP: int = 200          # ضریب سطح

POCKET_LOSS_DIVISOR: int = 3        # بدون کیف پول: ۱/۳ پول جیب می‌سوزد

ARREST_SCENARIOS: List[str] = [
    "یه گشت پلیس سر کوچه کمین کرده بود",
    "دوربین مغازه صورتت رو گرفت",
    "صاحب‌خونه زنگ زد به ۱۱۰",
    "تو فرار خوردی به گشت ویژه",
    "یه شاهد پلاک ماشینت رو داد",
    "آلارم گاوصندوق روشن شد",
    "خبرچین محل لوت داد",
    "موتور پلیس تو کوچه بن‌بست گیرت آورد",
    "تله پلیس بود، از اول زیر نظر بودی",
    "بی‌سیم پلیس نشونیت رو پخش کرد",
]

PRISON_QUOTES: List[str] = [
    "🚬 صبر کن، مافیای واقعی زندان هم دیده.",
    "🧱 دیوار زندون بلنده، ولی تو بلندتری.",
    "🕰 وقت گذشتنیه، فقط تحمل کن.",
    "🤐 لام تا کام حرف نزدی، آفرین.",
]


def arrest_chance(user: Dict[str, Any]) -> float:
    """شانس دستگیری در این دزدی (هرگز ۱۰۰٪ نمی‌شود)."""
    done = num(user, "robs_since_arrest")
    if done < ARREST_GRACE:
        return 0.0
    raw = ARREST_BASE_CHANCE + ARREST_RAMP * (done - ARREST_GRACE)
    # پرونده جعلی قوی، ظن پلیس را کم می‌کند
    raw *= 1.0 - float(_opt("dossier_safety", user, default=0.0) or 0.0)
    return max(0.0, min(ARREST_MAX_CHANCE, raw))


def jail_duration() -> int:
    return random.randint(JAIL_MIN_MINUTES, JAIL_MAX_MINUTES) * 60


def bail_price(user: Dict[str, Any], seconds_left: int) -> int:
    """
    قیمت وثیقه بر اساس «دزدی»: تعداد دزدی و غنیمت دوره + زمان مانده + سطح.
    """
    robs = num(user, "robs_since_arrest")
    loot = num(user, "loot_since_arrest")
    minutes_left = (max(0, int(seconds_left)) + 59) // 60
    price = (
        BAIL_BASE
        + robs * BAIL_PER_ROB
        + int(loot * BAIL_LOOT_RATIO)
        + minutes_left * BAIL_PER_MINUTE
        + num(user, "level_index") * BAIL_LEVEL_STEP
    )
    return max(BAIL_BASE, int(price))


def jail_left(user: Dict[str, Any]) -> int:
    ts = parse_ts(user.get("jail_until"))
    if ts is None:
        return 0
    return max(0, int(round(ts - now_ts())))


def release_if_done(user: Dict[str, Any]) -> Dict[str, Any]:
    """آزادی خودکار پس از پایان مدت حبس."""
    if user.get("jail_until") and jail_left(user) <= 0:
        log.info("آزادی خودکار → کاربر %s", user.get("user_id"))
        return set_fields(int(user["user_id"]), jail_until=None, jail_total=0,
                          streak=0, robs_since_arrest=0, loot_since_arrest=0)
    return user


def send_to_jail(user_id: int, user: Dict[str, Any], extra_seconds: int = 0) -> Dict[str, Any]:
    """
    انتقال به زندان: مدت حبس + سوختن ۱/۳ پول جیب (کیف پول امن است).
    خروجی: {"user":…, "left":…, "burned":…, "saved":…}
    """
    duration = jail_duration() + max(0, int(extra_seconds))
    pocket = num(user, "money")
    burned = pocket // POCKET_LOSS_DIVISOR
    saved = num(user, "wallet_balance")
    user = set_fields(
        user_id,
        money=max(0, pocket - burned),
        jail_until=iso(now_ts() + duration),
        jail_total=duration,
        streak=0,
        arrest_count=num(user, "arrest_count") + 1,
        last_rob_time=iso(),
    )
    log.info("دستگیری → کاربر %s | حبس %ss | سوخت %s", user_id, duration, burned)
    return {"user": user, "left": duration, "burned": burned, "saved": saved}


def jail_status(user_id: int, name: Optional[str] = None, username: Optional[str] = None) -> Dict[str, Any]:
    with _db_lock:
        user = release_if_done(get_user(user_id, name, username))
        left = jail_left(user)
        return {"user": user, "left": left, "price": bail_price(user, left) if left else 0}


def do_bail(user_id: int, name: Optional[str] = None, username: Optional[str] = None) -> Dict[str, Any]:
    """آزادی با پرداخت وثیقه از جیب."""
    with _db_lock:
        user = release_if_done(get_user(user_id, name, username))
        left = jail_left(user)
        if left <= 0:
            return {"state": "free", "user": user}
        price = bail_price(user, left)
        pocket = num(user, "money")
        if pocket < price:
            return {"state": "poor", "user": user, "left": left,
                    "price": price, "need": price - pocket}
        user = set_fields(
            user_id,
            money=pocket - price,
            jail_until=None,
            jail_total=0,
            streak=0,
            robs_since_arrest=0,
            loot_since_arrest=0,
            bail_count=num(user, "bail_count") + 1,
        )
        log.info("آزادی با وثیقه → کاربر %s | مبلغ %s", user_id, price)
        return {"state": "paid", "user": user, "price": price}


# ── متن‌ها ─────────────────────────────────────────────────────────

def txt_arrested(name: str, scenario: str, res: Dict[str, Any]) -> str:
    user = res["user"]
    left = int(res["left"])
    lines = [
        "🚨 <b>دستگیر شدی!</b>",
        SEP,
        f"👤 {esc(name)}",
        f"🚔 {scenario}",
        f"💸 پول سوخته: <b>{money(res['burned'])}</b>",
    ]
    if int(res.get("saved") or 0) > 0:
        lines.append(f"👝 امن در کیف پول: <b>{money(res['saved'])}</b>")
    elif not has("wallet_panel_text"):
        pass
    else:
        lines.append("👝 کیف پول نداری! پول‌ها لو می‌ره.")
    lines += [
        SEP,
        f"⛓ حبس: <b>{duration_fa(left)}</b>",
        f"🔓 وثیقه: <b>{money(bail_price(user, left))}</b>",
        f"💵 جیب: <b>{money(num(user, 'money'))}</b>",
        SEP,
        "🏛 پنل آزادی: <code>زندان</code>",
    ]
    return "\n".join(lines)


def txt_jail_panel(name: str, user: Dict[str, Any], left: int, price: int,
                   note: Optional[str] = None) -> str:
    if left <= 0:
        lines = [
            "🕊 <b>تو آزادی!</b>",
            SEP,
            f"👤 {esc(name)}",
            "⛓ الان زندانی نیستی.",
            f"💵 جیب: <b>{money(num(user, 'money'))}</b>",
            f"🚔 دستگیری‌ها: <b>{pn(num(user, 'arrest_count'))}</b>",
            SEP,
            "😈 برو سر کار: <code>دزدی</code>",
        ]
    else:
        total = num(user, "jail_total") or left
        lines = [
            "⛓ <b>پنل زندان</b>",
            SEP,
            f"👤 {esc(name)}",
            "🏛 وضعیت: <b>بازداشت</b>",
            f"⏳ آزادی خودکار: <b>{duration_fa(left)}</b>",
            f"📊 {progress_bar(max(0, total - left), total)}",
            SEP,
            f"🔓 وثیقه: <b>{money(price)}</b>",
            f"💵 جیب: <b>{money(num(user, 'money'))}</b>",
        ]
        docs = num(user, "fake_docs")
        if has("use_fake_doc"):
            lines.append(f"📜 سند جعلی: <b>{pn(docs)}</b>")
        lines.append(random.choice(PRISON_QUOTES))
    if note:
        lines += [SEP, note]
    return "\n".join(lines)


def kb_jail(user: Dict[str, Any], left: int, price: int) -> InlineKeyboardMarkup:
    body: List[List[InlineKeyboardButton]] = []
    if left > 0:
        can_pay = num(user, "money") >= price
        body.append([btn(f"💵 پرداخت وثیقه ({pn(f'{price:,}')})", callback_data="bail",
                         style=STYLE_SUCCESS if can_pay else STYLE_DANGER)])
        if has("use_fake_doc") and num(user, "fake_docs") > 0:
            body.append([btn(f"📜 استفاده از سند جعلی ({pn(num(user, 'fake_docs'))})",
                             callback_data="doc_use", style=STYLE_PRIMARY)])
        body.append([
            btn("🔄 بروزرسانی", callback_data="jail", style=STYLE_PRIMARY),
            btn("⏳ صبر می‌کنم", callback_data="jail_wait", style=STYLE_DANGER),
        ])
    else:
        body.append([btn("😈 برو دزدی", callback_data="jail", style=STYLE_SUCCESS)])
    body.append([
        btn("👤 حسابم", callback_data="acc", style=STYLE_PRIMARY),
        *kb_back_row("start_back"),
    ])
    return rows(*body)


def jail_view(name: str, st: Dict[str, Any], note: Optional[str] = None
              ) -> Tuple[str, InlineKeyboardMarkup]:
    user, left, price = st["user"], int(st["left"]), int(st["price"])
    return txt_jail_panel(name, user, left, price, note), kb_jail(user, left, price)


def bail_view(name: str, res: Dict[str, Any]) -> Tuple[str, InlineKeyboardMarkup]:
    user = res.get("user") or {}
    state = res["state"]
    if state == "free":
        return jail_view(name, {"user": user, "left": 0, "price": 0}, "✅ تو زندانی نیستی!")
    if state == "poor":
        left, price = int(res["left"]), int(res["price"])
        note = (
            f"❌ پول کافی نداری!\n"
            f"🔓 وثیقه: <b>{money(price)}</b>\n"
            f"📉 کمبود: <b>{money(int(res['need']))}</b>\n"
            f"⏳ یا صبر کن: {duration_fa(left)}"
        )
        return jail_view(name, {"user": user, "left": left, "price": price}, note)
    text = "\n".join([
        "🕊 <b>آزاد شدی!</b>",
        SEP,
        f"👤 {esc(name)}",
        f"💵 وثیقه پرداخت شد: <b>{money(int(res['price']))}</b>",
        f"💰 جیب: <b>{money(num(user, 'money'))}</b>",
        f"🚔 دستگیری‌ها: <b>{pn(num(user, 'arrest_count'))}</b>",
        SEP,
        "😈 برگرد سر کار: <code>دزدی</code>",
    ])
    return text, kb_jail(user, 0, 0)


def txt_help_jail() -> str:
    return "\n".join([
        "🚔 <b>پلیس و زندان</b>",
        SEP,
        "دزدی که ادامه بدی، پلیس حساس‌تر می‌شه.",
        f"🎲 شانس دستگیری: {pct(ARREST_BASE_CHANCE)} تا {pct(ARREST_MAX_CHANCE)}",
        f"🛡 {pn(ARREST_GRACE)} دزدی اول بعد آزادی امنه.",
        SEP,
        f"⛓ حبس: {pn(JAIL_MIN_MINUTES)} دقیقه تا {pn(JAIL_MAX_MINUTES // 60)} ساعت",
        f"💸 بدون کیف پول: ۱/{pn(POCKET_LOSS_DIVISOR)} پول جیب می‌سوزه",
        "🔓 وثیقه = پایه + تعداد دزدی + غنیمت + زمان مانده",
        SEP,
        "🏛 <code>زندان</code> ← پنل آزادی",
        "📜 با سند جعلی هم می‌تونی فرار کنی (ریسک داره!)",
    ])


# ── هندلرها ────────────────────────────────────────────────────────

@dp.message(F.text.regexp(re.compile(r"^\s*(?:زندان|/jail)\s*$")))
async def h_jail(message: Message) -> None:
    u = message.from_user
    if u is None:
        return
    name = display_name(u.full_name, u.username, u.id)
    st = await asyncio.to_thread(jail_status, u.id, u.full_name, u.username)
    text, kb = jail_view(name, st)
    await message.reply(text, reply_markup=kb)


@dp.message(F.text.regexp(re.compile(r"^\s*(?:وثیقه|آزادی|ازادی|/bail)\s*$")))
async def h_bail(message: Message) -> None:
    u = message.from_user
    if u is None:
        return
    name = display_name(u.full_name, u.username, u.id)
    res = await asyncio.to_thread(do_bail, u.id, u.full_name, u.username)
    text, kb = bail_view(name, res)
    await message.reply(text, reply_markup=kb)


@dp.callback_query(F.data == "jail")
async def cb_jail(cq: CallbackQuery) -> None:
    u = cq.from_user
    st = await asyncio.to_thread(jail_status, u.id, u.full_name, u.username)
    text, kb = jail_view(display_name(u.full_name, u.username, u.id), st)
    await safe_edit(cq, text, kb)
    await cq.answer("⛓ زندانی" if st["left"] else "🕊 آزادی")


@dp.callback_query(F.data == "bail")
async def cb_bail(cq: CallbackQuery) -> None:
    u = cq.from_user
    res = await asyncio.to_thread(do_bail, u.id, u.full_name, u.username)
    text, kb = bail_view(display_name(u.full_name, u.username, u.id), res)
    await safe_edit(cq, text, kb)
    alerts = {"paid": "🕊 آزاد شدی!", "poor": "❌ پول کافی نداری!", "free": "✅ زندانی نیستی"}
    await cq.answer(alerts.get(res["state"], ""), show_alert=(res["state"] == "poor"))


@dp.callback_query(F.data == "jail_wait")
async def cb_jail_wait(cq: CallbackQuery) -> None:
    u = cq.from_user
    st = await asyncio.to_thread(jail_status, u.id, u.full_name, u.username)
    left = int(st["left"])
    await cq.answer(f"⏳ {duration_fa(left)} دیگه آزاد می‌شی." if left else "🕊 همین حالا آزادی!",
                    show_alert=True)


@dp.callback_query(F.data == "help_jail")
async def cb_help_jail(cq: CallbackQuery) -> None:
    await safe_edit(cq, txt_help_jail(), kb_back("help_main"))
    await cq.answer()


# ▓▓ بخش ۰۷ — پایان ▓▓
# ══════════════════════════════════════════════════════════════════════════
# ▓▓ بخش ۰۸ — دزدی (ROB) ▓▓  [شروع]
#    دستور: دزدی (فقط گروه)   |   هسته بازی
# ══════════════════════════════════════════════════════════════════════════

STEAL_MIN, STEAL_MAX = 9, 500

# توزیع مبلغ: (درصد شانس, کمینه, بیشینه)
STEAL_TABLE: List[Tuple[int, int, int]] = [
    (30, 9, 50),
    (30, 51, 100),
    (18, 101, 200),
    (12, 201, 350),
    (10, 351, 500),
]
_STEAL_WEIGHTS = [w for w, _, _ in STEAL_TABLE]

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

BANK_SCENARIOS: List[str] = [
    "با پرونده جعلی رفتی بانک و وام گرفتی",
    "با سند قلابی حساب بانک رو خالی کردی",
    "خودت رو بازرس بانک جا زدی",
    "با امضای جعلی چک نقد کردی",
]

COMMENTS: List[Tuple[int, List[str]]] = [
    (400, ["🍀 شانس بزرگ!", "🌟 افسانه‌ای بود!"]),
    (200, ["🔥 عالی بود!", "✋ دستت طلا!"]),
    (100, ["👍 بد نبود.", "🙂 خوب بود."]),
    (50, ["💼 خالی نموند.", "🤏 یه چیزی گیرت اومد."]),
    (0, ["😕 کم بود.", "🎲 شانست کم بود."]),
]


def roll_steal() -> int:
    """مبلغ تصادفی ۹ تا ۵۰۰ با توزیع وزنی."""
    _, lo, hi = random.choices(STEAL_TABLE, weights=_STEAL_WEIGHTS, k=1)[0]
    return random.randint(lo, hi)


def steal_comment(amount: int) -> str:
    for threshold, texts in COMMENTS:
        if amount >= threshold:
            return random.choice(texts)
    return random.choice(COMMENTS[-1][1])


def cooldown_left(last_rob_time: Any) -> int:
    ts = parse_ts(last_rob_time)
    if ts is None:
        return 0
    return max(0, min(ROB_COOLDOWN, int(round(ROB_COOLDOWN - (now_ts() - ts)))))


def do_rob(user_id: int, name: Optional[str] = None, username: Optional[str] = None,
           auto: bool = False) -> Dict[str, Any]:
    """
    یک تلاش دزدی.  auto=True ⇒ دزدی خودکار نوچه (کول‌داون بررسی نمی‌شود).
    خروجی state: jailed | cooldown | arrested | ok
    """
    with _db_lock:
        user = release_if_done(get_user(user_id, name, username))

        left_jail = jail_left(user)
        if left_jail > 0:
            return {"state": "jailed", "left": left_jail, "user": user}

        if not auto:
            cd = cooldown_left(user.get("last_rob_time"))
            if cd > 0:
                return {"state": "cooldown", "left": cd}

        # ── اسلحه: تضمین دزدی بدون دستگیری ──
        weapon = _opt("weapon_consume", user_id, user, default=None) or {}
        protected = bool(weapon.get("protected"))

        # ── پرونده جعلی: بانک‌زنی با پاداش بیشتر ──
        bank = _opt("dossier_consume", user_id, user, default=None) or {}

        # ── قرعه پلیس ──
        chance = 0.0 if protected else arrest_chance(user)
        if random.random() < chance:
            user = get_user(user_id)
            res = send_to_jail(user_id, user)
            res.update({
                "state": "arrested",
                "scenario": random.choice(ARREST_SCENARIOS),
                "chance": chance,
            })
            return res

        # ── دزدی موفق ──
        amount = roll_steal()
        bonus = int(amount * float(bank.get("bonus_ratio") or 0.0))
        total = amount + bonus
        scenario = random.choice(BANK_SCENARIOS) if bank.get("used") else random.choice(SCENARIOS)

        user = update_user(user_id, money_add=total, rob_inc=1, set_time=True)
        user = set_fields(
            user_id,
            streak=num(user, "streak") + 1,
            robs_since_arrest=num(user, "robs_since_arrest") + 1,
            loot_since_arrest=num(user, "loot_since_arrest") + total,
        )
        user, upgraded = apply_level_up(user_id, user)

        return {
            "state": "ok",
            "amount": total,
            "base": amount,
            "bonus": bonus,
            "scenario": scenario,
            "comment": steal_comment(total),
            "user": user,
            "upgraded": upgraded,
            "weapon": weapon,
            "bank": bank,
            "chance": chance,
        }


def txt_rob(name: str, res: Dict[str, Any]) -> str:
    user = res["user"]
    lvl = num(user, "level_index")
    robs = num(user, "rob_count")
    lines = [
        "😈 <b>دزدی موفق!</b>",
        SEP,
        f"👤 {esc(name)}",
        f"💰 <b>{money(res['amount'])}</b>",
        f"📝 {res['scenario']}",
        res["comment"],
    ]
    if int(res.get("bonus") or 0) > 0:
        lines.append(f"🏦 پاداش پرونده: <b>+{money(res['bonus'])}</b>")
    weapon = res.get("weapon") or {}
    if weapon.get("protected"):
        lines.append(f"🔫 AK-۴۷ پوششت داد ({pn(weapon.get('left', 0))} دزدی مانده)")
    if weapon.get("broke"):
        lines.append("💥 اسلحه خراب شد! <code>اسلحه</code> ← تعمیر")
    lines += [
        SEP,
        f"💵 جیب: <b>{money(num(user, 'money'))}</b>",
        f"🎖 {level_name(lvl)}",
        f"🔫 دزدی: <b>{pn(robs)}</b>",
    ]
    info = progress_info(lvl, robs)
    if info:
        lines.append(f"📊 {info['bar']} ({pn(info['done'])}/{pn(info['target'])})")
    else:
        lines.append("👑 <b>بالاترین سطح!</b>")
    lines.append(f"🚔 خطر دستگیری بعدی: {pct(arrest_chance(user))}")
    if res.get("upgraded"):
        new_name, reward = res["upgraded"]
        lines += [SEP, f"🎉 <b>ارتقا! {new_name}</b>", f"🎁 پاداش: <b>{money(reward)}</b>"]
    lines += [SEP, f"⏱️ بعدی: {cooldown_fmt(ROB_COOLDOWN)}"]
    return "\n".join(lines)


def txt_cooldown(left: int) -> str:
    return "\n".join([
        "⏳ <b>صبر کن رفیق!</b>",
        SEP,
        "🔒 تازه دزدی کردی!",
        "🕵️ پلیس گشت می‌زنه...",
        "",
        f"⏱️ باقی‌مانده: <b>{cooldown_fmt(left)}</b>",
    ])


def txt_group_only() -> str:
    return "\n".join([
        "⚠️ <b>این دستور فقط در گروه‌ها فعاله!</b>",
        SEP,
        "➕ ربات رو به گروهت اضافه کن.",
    ])


def kb_rob_after(user: Dict[str, Any]) -> InlineKeyboardMarkup:
    body: List[List[InlineKeyboardButton]] = [[
        btn("👤 حسابم", callback_data="acc", style=STYLE_PRIMARY),
    ]]
    if has("wallet_panel_text"):
        body[0].append(btn("👝 کیف پول", callback_data="wallet", style=STYLE_SUCCESS))
    if has("weapon_panel_text") and num(user, "has_ak") > 0:
        body.append([btn("🔫 اسلحه", callback_data="weapon", style=STYLE_DANGER)])
    return rows(*body)


def txt_help_rob() -> str:
    chances = "\n".join(
        f"  • {pn(lo)}–{pn(hi)} {CURRENCY} → {pn(w)}٪" for w, lo, hi in STEAL_TABLE
    )
    return "\n".join([
        "💰 <b>راهنمای دزدی</b>",
        SEP,
        "دستور: <code>دزدی</code>",
        f"💵 مبلغ: {pn(STEAL_MIN)} تا {pn(STEAL_MAX)} {CURRENCY}",
        f"⏱️ انتظار: {cooldown_fmt(ROB_COOLDOWN)} دقیقه",
        "📍 فقط در گروه‌ها",
        SEP,
        "🎯 <b>شانس مبالغ:</b>",
        chances,
    ])


@dp.message(F.text.regexp(re.compile(r"^\s*(?:دزدی|/rob)\s*$")))
async def h_rob(message: Message) -> None:
    u = message.from_user
    if u is None:
        return
    if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        await message.answer(txt_group_only(), reply_markup=kb_main())
        return

    name = display_name(u.full_name, u.username, u.id)
    res = await asyncio.to_thread(do_rob, u.id, u.full_name, u.username)
    state = res["state"]

    if state == "cooldown":
        await message.reply(txt_cooldown(int(res["left"])))
        return
    if state == "jailed":
        st = {"user": res["user"], "left": int(res["left"]),
              "price": bail_price(res["user"], int(res["left"]))}
        text, kb = jail_view(name, st, "🚫 زندانی نمی‌تونه دزدی کنه!")
        await message.reply(text, reply_markup=kb)
        return
    if state == "arrested":
        user, left = res["user"], int(res["left"])
        await message.reply(
            txt_arrested(name, res["scenario"], res),
            reply_markup=kb_jail(user, left, bail_price(user, left)),
        )
        return

    await message.reply(txt_rob(name, res), reply_markup=kb_rob_after(res["user"]))


@dp.callback_query(F.data == "help_rob")
async def cb_help_rob(cq: CallbackQuery) -> None:
    await safe_edit(cq, txt_help_rob(), kb_back("help_main"))
    await cq.answer()


# ▓▓ بخش ۰۸ — پایان ▓▓
# ══════════════════════════════════════════════════════════════════════════
# ▓▓ بخش ۰۹ — کیف پول (WALLET) ▓▓  [شروع]
#    دستور: کیف پول   |   پول امن از پلیس + ارتقای ظرفیت
# ══════════════════════════════════════════════════════════════════════════

register_columns(
    has_wallet="INTEGER DEFAULT 0",
    wallet_balance="INTEGER DEFAULT 0",
    wallet_level="INTEGER DEFAULT 0",
)

WALLET_PRICE: int = 1500            # قیمت خرید در فروشگاه
WALLET_BASE_CAP: int = 5000         # ظرفیت اولیه
WALLET_CAP_STEP: int = 5000         # افزایش ظرفیت هر ارتقا
WALLET_UPGRADE_BASE: int = 1200     # هزینه ارتقای اول
WALLET_UPGRADE_GROWTH: float = 1.6  # رشد هزینه ارتقا
WALLET_MAX_LEVEL: int = 8


def wallet_cap(user: Dict[str, Any]) -> int:
    return WALLET_BASE_CAP + WALLET_CAP_STEP * num(user, "wallet_level")


def wallet_upgrade_price(user: Dict[str, Any]) -> int:
    return int(WALLET_UPGRADE_BASE * (WALLET_UPGRADE_GROWTH ** num(user, "wallet_level")))


def wallet_deposit(user_id: int, amount: Optional[int] = None) -> Dict[str, Any]:
    """واریز به کیف پول (amount=None ⇒ همه جیب تا سقف ظرفیت)."""
    with _db_lock:
        user = get_user(user_id)
        if num(user, "has_wallet") <= 0:
            return {"state": "no_wallet", "user": user}
        cap = wallet_cap(user)
        free = max(0, cap - num(user, "wallet_balance"))
        pocket = num(user, "money")
        want = pocket if amount is None else max(0, int(amount))
        moved = min(want, pocket, free)
        if moved <= 0:
            reason = "full" if free <= 0 else "empty"
            return {"state": reason, "user": user, "cap": cap}
        user = set_fields(user_id, money=pocket - moved,
                          wallet_balance=num(user, "wallet_balance") + moved)
        log.info("واریز کیف پول → کاربر %s مبلغ %s", user_id, moved)
        return {"state": "ok", "user": user, "moved": moved, "cap": cap}


def wallet_withdraw(user_id: int, amount: Optional[int] = None) -> Dict[str, Any]:
    """برداشت از کیف پول به جیب."""
    with _db_lock:
        user = get_user(user_id)
        if num(user, "has_wallet") <= 0:
            return {"state": "no_wallet", "user": user}
        bal = num(user, "wallet_balance")
        want = bal if amount is None else max(0, int(amount))
        moved = min(want, bal)
        if moved <= 0:
            return {"state": "empty", "user": user}
        user = set_fields(user_id, money=num(user, "money") + moved,
                          wallet_balance=bal - moved)
        log.info("برداشت کیف پول → کاربر %s مبلغ %s", user_id, moved)
        return {"state": "ok", "user": user, "moved": moved}


def wallet_upgrade(user_id: int) -> Dict[str, Any]:
    """ارتقای ظرفیت کیف پول."""
    with _db_lock:
        user = get_user(user_id)
        if num(user, "has_wallet") <= 0:
            return {"state": "no_wallet", "user": user}
        if num(user, "wallet_level") >= WALLET_MAX_LEVEL:
            return {"state": "max", "user": user}
        price = wallet_upgrade_price(user)
        if not spend(user_id, price):
            return {"state": "poor", "user": get_user(user_id), "price": price}
        user = set_fields(user_id, wallet_level=num(user, "wallet_level") + 1)
        return {"state": "ok", "user": user, "price": price, "cap": wallet_cap(user)}


def wallet_panel_text(name: str, user: Dict[str, Any], note: Optional[str] = None) -> str:
    if num(user, "has_wallet") <= 0:
        lines = [
            "👝 <b>کیف پول</b>",
            SEP,
            "❌ کیف پول نداری!",
            f"💸 قیمت: <b>{money(WALLET_PRICE)}</b>",
            "",
            "چرا لازمه؟",
            f"🚔 وقتی دستگیر شی ۱/{pn(POCKET_LOSS_DIVISOR)} پول جیبت می‌سوزه.",
            "🕳 پول کیف پول زیر خاک مخفیه — پلیس پیداش نمی‌کنه.",
            SEP,
            "🛒 <code>فروشگاه</code> ← خرید",
        ]
    else:
        cap = wallet_cap(user)
        bal = num(user, "wallet_balance")
        lines = [
            "👝 <b>کیف پول مخفی</b>",
            SEP,
            f"👤 {esc(name)}",
            f"🕳 امن: <b>{money(bal)}</b>",
            f"📦 ظرفیت: <b>{money(cap)}</b>",
            f"📊 {progress_bar(bal, cap)} ({pct(bal / cap if cap else 0)})",
            f"💵 جیب: <b>{money(num(user, 'money'))}</b>",
            SEP,
            f"🏷 سطح کیف: <b>{pn(num(user, 'wallet_level') + 1)}</b>/{pn(WALLET_MAX_LEVEL + 1)}",
        ]
        if num(user, "wallet_level") < WALLET_MAX_LEVEL:
            lines.append(f"⬆️ ارتقا: <b>{money(wallet_upgrade_price(user))}</b>")
        else:
            lines.append("🏆 ظرفیت کامل!")
    if note:
        lines += [SEP, note]
    return "\n".join(lines)


def kb_wallet(user: Dict[str, Any]) -> InlineKeyboardMarkup:
    if num(user, "has_wallet") <= 0:
        return rows(
            [btn(f"🛒 خرید کیف پول ({pn(f'{WALLET_PRICE:,}')})",
                 callback_data="shop_buy_wallet", style=STYLE_SUCCESS)],
            kb_back_row("start_back"),
        )
    body = [
        [
            btn("📥 واریز همه", callback_data="wallet_dep", style=STYLE_SUCCESS),
            btn("📤 برداشت همه", callback_data="wallet_wd", style=STYLE_PRIMARY),
        ],
    ]
    if num(user, "wallet_level") < WALLET_MAX_LEVEL:
        body.append([btn(f"⬆️ ارتقای ظرفیت ({pn(f'{wallet_upgrade_price(user):,}')})",
                         callback_data="wallet_up", style=STYLE_DANGER)])
    body.append([
        btn("🔄 بروزرسانی", callback_data="wallet", style=STYLE_PRIMARY),
        *kb_back_row("start_back"),
    ])
    return rows(*body)


def wallet_view(name: str, user: Dict[str, Any], note: Optional[str] = None
                ) -> Tuple[str, InlineKeyboardMarkup]:
    return wallet_panel_text(name, user, note), kb_wallet(user)


def txt_help_wallet() -> str:
    return "\n".join([
        "👝 <b>راهنمای کیف پول</b>",
        SEP,
        "دستور: <code>کیف پول</code>",
        f"💸 قیمت: {money(WALLET_PRICE)}",
        f"📦 ظرفیت اولیه: {money(WALLET_BASE_CAP)}",
        f"⬆️ هر ارتقا: +{money(WALLET_CAP_STEP)} ظرفیت",
        SEP,
        "🕳 پول داخل کیف زیر خاک مخفی می‌شه.",
        f"🚔 بدون کیف پول، دستگیری = سوختن ۱/{pn(POCKET_LOSS_DIVISOR)} جیب",
        "💡 قبل از دزدی سنگین پولت رو واریز کن!",
    ])


@dp.message(F.text.regexp(re.compile(r"^\s*(?:کیف\s*پول|کیفم|/wallet)\s*$")))
async def h_wallet(message: Message) -> None:
    u = message.from_user
    if u is None:
        return
    user = await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
    text, kb = wallet_view(display_name(u.full_name, u.username, u.id), user)
    await message.reply(text, reply_markup=kb)


@dp.callback_query(F.data == "wallet")
async def cb_wallet(cq: CallbackQuery) -> None:
    u = cq.from_user
    user = await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
    text, kb = wallet_view(display_name(u.full_name, u.username, u.id), user)
    await safe_edit(cq, text, kb)
    await cq.answer()


@dp.callback_query(F.data == "wallet_dep")
async def cb_wallet_dep(cq: CallbackQuery) -> None:
    u = cq.from_user
    res = await asyncio.to_thread(wallet_deposit, u.id, None)
    notes = {
        "ok": lambda: f"✅ <b>{money(res['moved'])}</b> امن شد.",
        "empty": lambda: "❌ جیبت خالیه!",
        "full": lambda: "⚠️ کیف پر شده — ارتقا بده.",
        "no_wallet": lambda: "❌ اول کیف پول بخر.",
    }
    text, kb = wallet_view(display_name(u.full_name, u.username, u.id),
                           res["user"], notes.get(res["state"], lambda: "")())
    await safe_edit(cq, text, kb)
    await cq.answer("✅ واریز شد" if res["state"] == "ok" else "❌ انجام نشد")


@dp.callback_query(F.data == "wallet_wd")
async def cb_wallet_wd(cq: CallbackQuery) -> None:
    u = cq.from_user
    res = await asyncio.to_thread(wallet_withdraw, u.id, None)
    note = (f"✅ <b>{money(res['moved'])}</b> به جیب اومد."
            if res["state"] == "ok" else "❌ کیف خالیه!")
    text, kb = wallet_view(display_name(u.full_name, u.username, u.id), res["user"], note)
    await safe_edit(cq, text, kb)
    await cq.answer("✅ برداشت شد" if res["state"] == "ok" else "❌ خالیه")


@dp.callback_query(F.data == "wallet_up")
async def cb_wallet_up(cq: CallbackQuery) -> None:
    u = cq.from_user
    res = await asyncio.to_thread(wallet_upgrade, u.id)
    notes = {
        "ok": lambda: f"⬆️ ظرفیت شد <b>{money(res['cap'])}</b>",
        "poor": lambda: f"❌ پول کافی نداری ({money(res['price'])})",
        "max": lambda: "🏆 بالاترین ظرفیت!",
        "no_wallet": lambda: "❌ اول کیف پول بخر.",
    }
    text, kb = wallet_view(display_name(u.full_name, u.username, u.id),
                           res["user"], notes.get(res["state"], lambda: "")())
    await safe_edit(cq, text, kb)
    await cq.answer("⬆️ ارتقا شد" if res["state"] == "ok" else "❌ انجام نشد",
                    show_alert=(res["state"] == "poor"))


@dp.callback_query(F.data == "help_wallet")
async def cb_help_wallet(cq: CallbackQuery) -> None:
    await safe_edit(cq, txt_help_wallet(), kb_back("help_main"))
    await cq.answer()


# ▓▓ بخش ۰۹ — پایان ▓▓


# ══════════════════════════════════════════════════════════════════════════
# ▓▓ بخش ۱۰ — اسلحه AK-۴۷ (WEAPON) ▓▓  [شروع]
#    دستور: اسلحه   |   ۳ دزدی امن، بعد احتمال خرابی → تعمیر/ارتقا
# ══════════════════════════════════════════════════════════════════════════

register_columns(
    has_ak="INTEGER DEFAULT 0",
    ak_level="INTEGER DEFAULT 1",
    ak_uses="INTEGER DEFAULT 0",       # دزدی امن باقی‌مانده در این خشاب
    ak_health="INTEGER DEFAULT 100",
    ak_ammo="INTEGER DEFAULT 0",
    ak_broken="INTEGER DEFAULT 0",
)

AK_PRICE: int = 4000
AK_USES_BASE: int = 3               # سطح ۱ = ۳ دزدی امن
AK_USES_PER_LEVEL: int = 1          # هر ارتقا +۱ دزدی امن
AK_MAX_LEVEL: int = 6
AK_UPGRADE_BASE: int = 500          # ارتقا از ۵۰۰ شروع می‌شود
AK_UPGRADE_GROWTH: float = 1.75     # رشد عادلانه
AK_REPAIR_PRICE: int = 900          # تعمیر: ثابت در همه سطوح
AK_BREAK_CHANCE: float = 0.55       # احتمال خرابی بعد از تمام شدن خشاب
AK_HEALTH_COST: int = 22            # افت سلامت هر دزدی


def ak_max_uses(level: int) -> int:
    return AK_USES_BASE + AK_USES_PER_LEVEL * (max(1, int(level)) - 1)


def ak_upgrade_price(level: int) -> int:
    return int(AK_UPGRADE_BASE * (AK_UPGRADE_GROWTH ** (max(1, int(level)) - 1)))


def weapon_consume(user_id: int, user: Dict[str, Any]) -> Dict[str, Any]:
    """
    مصرف یک تیر در دزدی.
    خروجی: {"protected":bool, "left":int, "broke":bool, "active":bool}
    اگر اسلحه نباشد/خراب باشد/خشاب خالی باشد ⇒ روند عادی بازی (protected=False).
    """
    if num(user, "has_ak") <= 0 or num(user, "ak_broken") > 0:
        return {"active": False, "protected": False}
    uses = num(user, "ak_uses")
    if uses <= 0:
        return {"active": True, "protected": False, "left": 0, "empty": True}

    level = max(1, num(user, "ak_level", 1))
    left = uses - 1
    health = max(0, num(user, "ak_health", 100) - AK_HEALTH_COST)
    ammo = max(0, num(user, "ak_ammo") - 1)
    broke = False
    if left <= 0 and (health <= 0 or random.random() < AK_BREAK_CHANCE):
        broke = True
    set_fields(user_id, ak_uses=left, ak_health=health, ak_ammo=ammo,
               ak_broken=1 if broke else 0)
    if broke:
        log.info("اسلحه خراب شد → کاربر %s", user_id)
    return {"active": True, "protected": True, "left": left, "broke": broke,
            "health": health, "level": level}


def weapon_repair(user_id: int) -> Dict[str, Any]:
    with _db_lock:
        user = get_user(user_id)
        if num(user, "has_ak") <= 0:
            return {"state": "none", "user": user}
        if num(user, "ak_broken") <= 0 and num(user, "ak_health", 100) >= 100 \
                and num(user, "ak_uses") > 0:
            return {"state": "fine", "user": user}
        if not spend(user_id, AK_REPAIR_PRICE):
            return {"state": "poor", "user": get_user(user_id), "price": AK_REPAIR_PRICE}
        level = max(1, num(user, "ak_level", 1))
        user = set_fields(user_id, ak_broken=0, ak_health=100,
                          ak_uses=ak_max_uses(level), ak_ammo=ak_max_uses(level) * 10)
        log.info("تعمیر اسلحه → کاربر %s", user_id)
        return {"state": "ok", "user": user, "price": AK_REPAIR_PRICE}


def weapon_upgrade(user_id: int) -> Dict[str, Any]:
    with _db_lock:
        user = get_user(user_id)
        if num(user, "has_ak") <= 0:
            return {"state": "none", "user": user}
        level = max(1, num(user, "ak_level", 1))
        if level >= AK_MAX_LEVEL:
            return {"state": "max", "user": user}
        price = ak_upgrade_price(level)
        if not spend(user_id, price):
            return {"state": "poor", "user": get_user(user_id), "price": price}
        new_level = level + 1
        user = set_fields(user_id, ak_level=new_level, ak_broken=0, ak_health=100,
                          ak_uses=ak_max_uses(new_level), ak_ammo=ak_max_uses(new_level) * 10)
        log.info("ارتقای اسلحه → کاربر %s سطح %s", user_id, new_level)
        return {"state": "ok", "user": user, "price": price, "level": new_level}


def weapon_panel_text(name: str, user: Dict[str, Any], note: Optional[str] = None) -> str:
    if num(user, "has_ak") <= 0:
        lines = [
            "🔫 <b>اسلحه AK-۴۷</b>",
            SEP,
            "❌ اسلحه نداری!",
            f"💸 قیمت: <b>{money(AK_PRICE)}</b>",
            "",
            f"🛡 با AK هر خشاب <b>{pn(AK_USES_BASE)}</b> دزدی بدون دستگیری داری.",
            "🔧 بعدش باید تعمیر یا ارتقا کنی.",
            SEP,
            "🛒 <code>فروشگاه</code> ← خرید",
        ]
    else:
        level = max(1, num(user, "ak_level", 1))
        uses, mx = num(user, "ak_uses"), ak_max_uses(level)
        health = num(user, "ak_health", 100)
        broken = num(user, "ak_broken") > 0
        lines = [
            "🔫 <b>پنل اسلحه AK-۴۷</b>",
            SEP,
            f"👤 {esc(name)}",
            f"🏷 سطح: <b>{pn(level)}</b>/{pn(AK_MAX_LEVEL)}",
            f"🎯 دزدی امن باقی‌مانده: <b>{pn(uses)}</b>/{pn(mx)}",
            f"📊 {progress_bar(uses, mx)}",
            f"❤️ سلامت: <b>{pct(health / 100)}</b> {progress_bar(health, 100)}",
            f"🧨 فشنگ: <b>{pn(num(user, 'ak_ammo'))}</b>",
            f"⚙️ وضعیت: <b>{'💥 خراب' if broken else ('✅ آماده' if uses > 0 else '🈳 خشاب خالی')}</b>",
            SEP,
            f"🔧 تعمیر: <b>{money(AK_REPAIR_PRICE)}</b> (ثابت)",
        ]
        if level < AK_MAX_LEVEL:
            lines.append(f"⬆️ ارتقا: <b>{money(ak_upgrade_price(level))}</b> → {pn(ak_max_uses(level + 1))} دزدی امن")
        else:
            lines.append("🏆 بالاترین سطح اسلحه!")
        if broken or uses <= 0:
            lines.append("⚠️ تا تعمیر نکنی، دزدی عادی و پرخطره.")
    if note:
        lines += [SEP, note]
    return "\n".join(lines)


def kb_weapon(user: Dict[str, Any]) -> InlineKeyboardMarkup:
    if num(user, "has_ak") <= 0:
        return rows(
            [btn(f"🛒 خرید AK-۴۷ ({pn(f'{AK_PRICE:,}')})",
                 callback_data="shop_buy_ak", style=STYLE_SUCCESS)],
            kb_back_row("start_back"),
        )
    level = max(1, num(user, "ak_level", 1))
    body: List[List[InlineKeyboardButton]] = []
    up_row: List[InlineKeyboardButton] = []
    if level < AK_MAX_LEVEL:
        up_row.append(btn(f"⬆️ ارتقا ({pn(f'{ak_upgrade_price(level):,}')})",
                          callback_data="ak_up", style=STYLE_SUCCESS))
    up_row.append(btn(f"🔧 تعمیر ({pn(f'{AK_REPAIR_PRICE:,}')})",
                      callback_data="ak_fix", style=STYLE_PRIMARY))
    body.append(up_row)
    body.append([
        btn("🔄 بروزرسانی", callback_data="weapon", style=STYLE_PRIMARY),
        *kb_back_row("start_back"),
    ])
    return rows(*body)


def weapon_view(name: str, user: Dict[str, Any], note: Optional[str] = None
                ) -> Tuple[str, InlineKeyboardMarkup]:
    return weapon_panel_text(name, user, note), kb_weapon(user)


def txt_help_weapon() -> str:
    return "\n".join([
        "🔫 <b>راهنمای اسلحه</b>",
        SEP,
        "دستور: <code>اسلحه</code>",
        f"💸 قیمت AK-۴۷: {money(AK_PRICE)}",
        f"🛡 هر خشاب: {pn(AK_USES_BASE)} دزدی بدون دستگیری",
        f"⬆️ هر ارتقا: +{pn(AK_USES_PER_LEVEL)} دزدی امن (از {money(AK_UPGRADE_BASE)})",
        f"🔧 تعمیر: {money(AK_REPAIR_PRICE)} — در همه سطوح ثابت",
        SEP,
        f"💥 بعد از خالی شدن خشاب، {pct(AK_BREAK_CHANCE)} احتمال خرابی",
        "♻️ اگه تعمیر/ارتقا نکنی، بازی عادی ادامه پیدا می‌کنه.",
    ])


@dp.message(F.text.regexp(re.compile(r"^\s*(?:اسلحه|اسلحه‌ام|/weapon|ak|AK)\s*$")))
async def h_weapon(message: Message) -> None:
    u = message.from_user
    if u is None:
        return
    user = await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
    text, kb = weapon_view(display_name(u.full_name, u.username, u.id), user)
    await message.reply(text, reply_markup=kb)


@dp.callback_query(F.data == "weapon")
async def cb_weapon(cq: CallbackQuery) -> None:
    u = cq.from_user
    user = await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
    text, kb = weapon_view(display_name(u.full_name, u.username, u.id), user)
    await safe_edit(cq, text, kb)
    await cq.answer()


@dp.callback_query(F.data == "ak_fix")
async def cb_ak_fix(cq: CallbackQuery) -> None:
    u = cq.from_user
    res = await asyncio.to_thread(weapon_repair, u.id)
    notes = {
        "ok": lambda: "🔧 اسلحه تعمیر شد و خشاب پر شد!",
        "fine": lambda: "✅ اسلحه سالمه، تعمیر لازم نیست.",
        "poor": lambda: f"❌ پول کافی نداری ({money(res['price'])})",
        "none": lambda: "❌ اسلحه نداری.",
    }
    text, kb = weapon_view(display_name(u.full_name, u.username, u.id),
                           res["user"], notes.get(res["state"], lambda: "")())
    await safe_edit(cq, text, kb)
    await cq.answer("🔧 تعمیر شد" if res["state"] == "ok" else "❌ انجام نشد",
                    show_alert=(res["state"] == "poor"))


@dp.callback_query(F.data == "ak_up")
async def cb_ak_up(cq: CallbackQuery) -> None:
    u = cq.from_user
    res = await asyncio.to_thread(weapon_upgrade, u.id)
    notes = {
        "ok": lambda: f"⬆️ سطح {pn(res['level'])} — {pn(ak_max_uses(res['level']))} دزدی امن",
        "poor": lambda: f"❌ پول کافی نداری ({money(res['price'])})",
        "max": lambda: "🏆 بالاترین سطح!",
        "none": lambda: "❌ اسلحه نداری.",
    }
    text, kb = weapon_view(display_name(u.full_name, u.username, u.id),
                           res["user"], notes.get(res["state"], lambda: "")())
    await safe_edit(cq, text, kb)
    await cq.answer("⬆️ ارتقا شد" if res["state"] == "ok" else "❌ انجام نشد",
                    show_alert=(res["state"] == "poor"))


@dp.callback_query(F.data == "help_weapon")
async def cb_help_weapon(cq: CallbackQuery) -> None:
    await safe_edit(cq, txt_help_weapon(), kb_back("help_main"))
    await cq.answer()


# ▓▓ بخش ۱۰ — پایان ▓▓
# ══════════════════════════════════════════════════════════════════════════
# ▓▓ بخش ۱۱ — پرونده جعلی (DOSSIER) ▓▓  [شروع]
#    دستور: پرونده   |   امضا + اثر انگشت + عکس ⇒ بانک‌زنی
# ══════════════════════════════════════════════════════════════════════════

register_columns(
    has_dossier="INTEGER DEFAULT 0",
    dos_sign="INTEGER DEFAULT 0",     # کیفیت امضا (۰ تا ۳)
    dos_print="INTEGER DEFAULT 0",    # کیفیت اثر انگشت
    dos_photo="INTEGER DEFAULT 0",    # کیفیت عکس
    dos_ready="INTEGER DEFAULT 0",    # آماده برای استفاده در دزدی بعدی
    dos_used="INTEGER DEFAULT 0",     # تعداد بانک‌زنی موفق
)

DOSSIER_PRICE: int = 2500
DOS_MAX_TIER: int = 3                  # هر جزء تا کیفیت ۳
DOS_UPGRADE_PRICES: List[int] = [0, 600, 1400]   # تیر ۱ رایگان، بعد گران‌تر
DOS_SAFETY_PER_TIER: float = 0.09      # هر تیر ⇒ ۹٪ کاهش ظن پلیس
DOS_BONUS_PER_TIER: float = 0.22       # هر تیر ⇒ ۲۲٪ پاداش بیشتر بانک

DOS_PARTS: Dict[str, Tuple[str, str]] = {
    "sign": ("dos_sign", "✍️ امضای جعلی"),
    "print": ("dos_print", "🖐 اثر انگشت جعلی"),
    "photo": ("dos_photo", "🖼 عکس جعلی"),
}


def dos_tier_total(user: Dict[str, Any]) -> int:
    return sum(num(user, col) for col, _ in DOS_PARTS.values())


def dossier_complete(user: Dict[str, Any]) -> bool:
    """هر سه جزء حداقل تیر ۱ داشته باشند."""
    return all(num(user, col) >= 1 for col, _ in DOS_PARTS.values())


def dossier_safety(user: Dict[str, Any]) -> float:
    """کاهش ظن پلیس (۰ تا ~۰.۸) — بخش زندان از این استفاده می‌کند."""
    if num(user, "has_dossier") <= 0 or not dossier_complete(user):
        return 0.0
    return min(0.8, dos_tier_total(user) * DOS_SAFETY_PER_TIER)


def dossier_bonus(user: Dict[str, Any]) -> float:
    return dos_tier_total(user) * DOS_BONUS_PER_TIER


def dos_part_price(tier: int) -> int:
    """قیمت ارتقای جزء از تیر فعلی به بعدی (تیر اول رایگان)."""
    tier = max(0, int(tier))
    if tier >= DOS_MAX_TIER:
        return 0
    return DOS_UPGRADE_PRICES[tier] if tier < len(DOS_UPGRADE_PRICES) else DOS_UPGRADE_PRICES[-1]


def dossier_upgrade(user_id: int, part: str) -> Dict[str, Any]:
    """تکمیل/تقویت یک جزء پرونده."""
    if part not in DOS_PARTS:
        return {"state": "bad", "user": get_user(user_id)}
    col, label = DOS_PARTS[part]
    with _db_lock:
        user = get_user(user_id)
        if num(user, "has_dossier") <= 0:
            return {"state": "none", "user": user}
        tier = num(user, col)
        if tier >= DOS_MAX_TIER:
            return {"state": "max", "user": user, "label": label}
        price = dos_part_price(tier)
        if price > 0 and not spend(user_id, price):
            return {"state": "poor", "user": get_user(user_id), "price": price, "label": label}
        user = set_fields(user_id, **{col: tier + 1})
        if dossier_complete(user) and num(user, "dos_ready") <= 0:
            user = set_fields(user_id, dos_ready=1)
        return {"state": "ok", "user": user, "price": price, "label": label, "tier": tier + 1}


def dossier_arm(user_id: int) -> Dict[str, Any]:
    """آماده‌سازی پرونده برای دزدی بعدی (بانک‌زنی)."""
    with _db_lock:
        user = get_user(user_id)
        if num(user, "has_dossier") <= 0:
            return {"state": "none", "user": user}
        if not dossier_complete(user):
            return {"state": "incomplete", "user": user}
        user = set_fields(user_id, dos_ready=1)
        return {"state": "ok", "user": user}


def dossier_consume(user_id: int, user: Dict[str, Any]) -> Dict[str, Any]:
    """
    مصرف پرونده در دزدی. اگر آماده باشد ⇒ بانک‌زنی با پاداش.
    خروجی: {"used":bool, "bonus_ratio":float}
    """
    if num(user, "has_dossier") <= 0 or num(user, "dos_ready") <= 0 or not dossier_complete(user):
        return {"used": False, "bonus_ratio": 0.0}
    ratio = dossier_bonus(user)
    set_fields(user_id, dos_ready=0, dos_used=num(user, "dos_used") + 1)
    log.info("بانک‌زنی با پرونده → کاربر %s پاداش×%.2f", user_id, ratio)
    return {"used": True, "bonus_ratio": ratio}


def dossier_panel_text(name: str, user: Dict[str, Any], note: Optional[str] = None) -> str:
    if num(user, "has_dossier") <= 0:
        lines = [
            "📁 <b>پرونده جعلی</b>",
            SEP,
            "❌ پرونده نداری!",
            f"💸 قیمت: <b>{money(DOSSIER_PRICE)}</b>",
            "",
            "🏦 با پرونده کامل می‌تونی بانک بزنی:",
            "💰 پاداش بیشتر + ظن پلیس کمتر",
            SEP,
            "🛒 <code>فروشگاه</code> ← خرید",
        ]
    else:
        lines = [
            "📁 <b>پرونده جعلی</b>",
            SEP,
            f"👤 {esc(name)}",
        ]
        for key, (col, label) in DOS_PARTS.items():
            tier = num(user, col)
            mark = "✅" if tier >= 1 else "⬜"
            stars = "★" * tier + "☆" * (DOS_MAX_TIER - tier)
            lines.append(f"{mark} {label}: {stars}")
        lines += [
            SEP,
            f"🧪 اعتبار پرونده: <b>{pn(dos_tier_total(user))}</b>/{pn(DOS_MAX_TIER * 3)}",
            f"🕵️ کاهش ظن پلیس: <b>{pct(dossier_safety(user))}</b>",
            f"💰 پاداش بانک: <b>+{pct(dossier_bonus(user))}</b>",
            f"🏦 بانک‌زنی موفق: <b>{pn(num(user, 'dos_used'))}</b>",
        ]
        if not dossier_complete(user):
            lines.append("⚠️ هر سه جزء رو کامل کن تا فعال شه.")
        elif num(user, "dos_ready") > 0:
            lines.append("✅ آماده — دزدی بعدی روی بانک انجام می‌شه.")
        else:
            lines.append("💤 غیرفعال — دکمه «آماده‌سازی» رو بزن.")
    if note:
        lines += [SEP, note]
    return "\n".join(lines)


def kb_dossier(user: Dict[str, Any]) -> InlineKeyboardMarkup:
    if num(user, "has_dossier") <= 0:
        return rows(
            [btn(f"🛒 خرید پرونده ({pn(f'{DOSSIER_PRICE:,}')})",
                 callback_data="shop_buy_dossier", style=STYLE_SUCCESS)],
            kb_back_row("start_back"),
        )
    body: List[List[InlineKeyboardButton]] = []
    for key, (col, label) in DOS_PARTS.items():
        tier = num(user, col)
        if tier >= DOS_MAX_TIER:
            body.append([btn(f"{label} ★★★", callback_data="dos_max", style=STYLE_PRIMARY)])
        else:
            price = dos_part_price(tier)
            tag = "رایگان" if price == 0 else pn(f"{price:,}")
            body.append([btn(f"{label} ⬆️ ({tag})", callback_data=f"dos_up_{key}",
                             style=STYLE_SUCCESS if price == 0 else STYLE_PRIMARY)])
    if dossier_complete(user):
        ready = num(user, "dos_ready") > 0
        body.append([btn("✅ آماده برای بانک" if ready else "🏦 آماده‌سازی پرونده",
                         callback_data="dos_arm",
                         style=STYLE_SUCCESS if not ready else STYLE_DANGER)])
    body.append([
        btn("🔄 بروزرسانی", callback_data="dossier", style=STYLE_PRIMARY),
        *kb_back_row("start_back"),
    ])
    return rows(*body)


def dossier_view(name: str, user: Dict[str, Any], note: Optional[str] = None
                 ) -> Tuple[str, InlineKeyboardMarkup]:
    return dossier_panel_text(name, user, note), kb_dossier(user)


def txt_help_dossier() -> str:
    return "\n".join([
        "📁 <b>راهنمای پرونده جعلی</b>",
        SEP,
        "دستور: <code>پرونده</code>",
        f"💸 قیمت: {money(DOSSIER_PRICE)}",
        "",
        "سه جزء باید پر بشه:",
        "  ✍️ امضا  🖐 اثر انگشت  🖼 عکس",
        "🎁 تیر اول هر جزء رایگانه.",
        f"⬆️ تیر بعدی: {money(DOS_UPGRADE_PRICES[1])} و {money(DOS_UPGRADE_PRICES[2])}",
        SEP,
        f"🕵️ هر تیر: {pct(DOS_SAFETY_PER_TIER)} کاهش ظن کارکنان بانک",
        f"💰 هر تیر: {pct(DOS_BONUS_PER_TIER)} پاداش بیشتر",
        "🏦 هر بار مصرف می‌شه — دوباره آماده‌سازی کن.",
    ])


@dp.message(F.text.regexp(re.compile(r"^\s*(?:پرونده|پرونده\s*جعلی|/dossier)\s*$")))
async def h_dossier(message: Message) -> None:
    u = message.from_user
    if u is None:
        return
    user = await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
    text, kb = dossier_view(display_name(u.full_name, u.username, u.id), user)
    await message.reply(text, reply_markup=kb)


@dp.callback_query(F.data == "dossier")
async def cb_dossier(cq: CallbackQuery) -> None:
    u = cq.from_user
    user = await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
    text, kb = dossier_view(display_name(u.full_name, u.username, u.id), user)
    await safe_edit(cq, text, kb)
    await cq.answer()


@dp.callback_query(F.data.startswith("dos_up_"))
async def cb_dos_up(cq: CallbackQuery) -> None:
    u = cq.from_user
    part = (cq.data or "").replace("dos_up_", "", 1)
    res = await asyncio.to_thread(dossier_upgrade, u.id, part)
    notes = {
        "ok": lambda: f"✅ {res['label']} → تیر {pn(res['tier'])}",
        "poor": lambda: f"❌ پول کافی نداری ({money(res['price'])})",
        "max": lambda: f"🏆 {res.get('label', '')} کامله!",
        "none": lambda: "❌ اول پرونده بخر.",
        "incomplete": lambda: "⚠️ پرونده کامل نیست.",
        "bad": lambda: "❔ نامشخص",
    }
    text, kb = dossier_view(display_name(u.full_name, u.username, u.id),
                            res["user"], notes.get(res["state"], lambda: "")())
    await safe_edit(cq, text, kb)
    await cq.answer("✅ تقویت شد" if res["state"] == "ok" else "❌ انجام نشد",
                    show_alert=(res["state"] == "poor"))


@dp.callback_query(F.data == "dos_arm")
async def cb_dos_arm(cq: CallbackQuery) -> None:
    u = cq.from_user
    res = await asyncio.to_thread(dossier_arm, u.id)
    notes = {
        "ok": lambda: "🏦 پرونده آماده شد — دزدی بعدی روی بانک!",
        "incomplete": lambda: "⚠️ اول هر سه جزء رو پر کن.",
        "none": lambda: "❌ پرونده نداری.",
    }
    text, kb = dossier_view(display_name(u.full_name, u.username, u.id),
                            res["user"], notes.get(res["state"], lambda: "")())
    await safe_edit(cq, text, kb)
    await cq.answer("🏦 آماده شد" if res["state"] == "ok" else "❌ انجام نشد")


@dp.callback_query(F.data == "dos_max")
async def cb_dos_max(cq: CallbackQuery) -> None:
    await cq.answer("🏆 این جزء کامله!", show_alert=False)


@dp.callback_query(F.data == "help_dossier")
async def cb_help_dossier(cq: CallbackQuery) -> None:
    await safe_edit(cq, txt_help_dossier(), kb_back("help_main"))
    await cq.answer()


# ▓▓ بخش ۱۱ — پایان ▓▓


# ══════════════════════════════════════════════════════════════════════════
# ▓▓ بخش ۱۲ — نوچه (MINION) ▓▓  [شروع]
#    دستور: نوچه  یا  اسم دلخواه نوچه   |   نیاز: سطح ۳ به بالا
#    دزدی خودکار در فواصل زمانی + نام‌گذاری با ۷۰ سکه
# ══════════════════════════════════════════════════════════════════════════

register_columns(
    has_minion="INTEGER DEFAULT 0",
    minion_name="TEXT",
    minion_level="INTEGER DEFAULT 1",
    minion_last="TIMESTAMP",
    minion_earned="INTEGER DEFAULT 0",
    minion_runs="INTEGER DEFAULT 0",
    minion_await_name="INTEGER DEFAULT 0",
)

MINION_PRICE: int = 6000
MINION_MIN_LEVEL: int = 3          # سطح لازم برای استخدام (سطح ۳ به بالا)
MINION_NAME_PRICE: int = 70        # هزینه انتخاب اسم
MINION_CYCLE: int = 1800           # هر ۳۰ دقیقه یک دزدی خودکار
MINION_SHARE: float = 0.65         # سهم تو از غنیمت نوچه
MINION_UP_BASE: int = 1500
MINION_UP_GROWTH: float = 1.7
MINION_MAX_LEVEL: int = 5

_MINION_NAME_RE = re.compile(r"^[\w\u0600-\u06FF\s\-]{2,18}$", re.UNICODE)


def minion_cycle(user: Dict[str, Any]) -> int:
    """فاصله دزدی خودکار — با ارتقا کمتر می‌شود."""
    level = max(1, num(user, "minion_level", 1))
    return max(300, int(MINION_CYCLE * (0.85 ** (level - 1))))


def minion_upgrade_price(user: Dict[str, Any]) -> int:
    level = max(1, num(user, "minion_level", 1))
    return int(MINION_UP_BASE * (MINION_UP_GROWTH ** (level - 1)))


def minion_ready_in(user: Dict[str, Any]) -> int:
    ts = parse_ts(user.get("minion_last"))
    if ts is None:
        return 0
    return max(0, int(round(minion_cycle(user) - (now_ts() - ts))))


def minion_collect(user_id: int) -> Dict[str, Any]:
    """
    برداشت غنیمت نوچه. نوچه در زندان کار نمی‌کند.
    خروجی state: none | jailed | wait | ok
    """
    with _db_lock:
        user = release_if_done(get_user(user_id))
        if num(user, "has_minion") <= 0:
            return {"state": "none", "user": user}
        if jail_left(user) > 0:
            return {"state": "jailed", "user": user, "left": jail_left(user)}
        wait = minion_ready_in(user)
        if wait > 0:
            return {"state": "wait", "user": user, "left": wait}

        level = max(1, num(user, "minion_level", 1))
        haul = 0
        for _ in range(level):
            haul += roll_steal()
        share = max(1, int(haul * MINION_SHARE))
        user = update_user(user_id, money_add=share)
        user = set_fields(
            user_id,
            minion_last=iso(),
            minion_earned=num(user, "minion_earned") + share,
            minion_runs=num(user, "minion_runs") + 1,
        )
        log.info("غنیمت نوچه → کاربر %s مبلغ %s", user_id, share)
        return {"state": "ok", "user": user, "amount": share, "haul": haul}


def minion_upgrade(user_id: int) -> Dict[str, Any]:
    with _db_lock:
        user = get_user(user_id)
        if num(user, "has_minion") <= 0:
            return {"state": "none", "user": user}
        level = max(1, num(user, "minion_level", 1))
        if level >= MINION_MAX_LEVEL:
            return {"state": "max", "user": user}
        price = minion_upgrade_price(user)
        if not spend(user_id, price):
            return {"state": "poor", "user": get_user(user_id), "price": price}
        user = set_fields(user_id, minion_level=level + 1)
        return {"state": "ok", "user": user, "price": price, "level": level + 1}


def minion_request_name(user_id: int) -> Dict[str, Any]:
    """شروع فرایند نام‌گذاری (پرداخت ۷۰ سکه هنگام ثبت اسم انجام می‌شود)."""
    with _db_lock:
        user = get_user(user_id)
        if num(user, "has_minion") <= 0:
            return {"state": "none", "user": user}
        if num(user, "money") < MINION_NAME_PRICE:
            return {"state": "poor", "user": user, "price": MINION_NAME_PRICE}
        user = set_fields(user_id, minion_await_name=1)
        return {"state": "ok", "user": user}


def minion_set_name(user_id: int, raw_name: str) -> Dict[str, Any]:
    """ثبت اسم نوچه با پرداخت ۷۰ سکه."""
    name = (raw_name or "").strip()[:18]
    with _db_lock:
        user = get_user(user_id)
        if num(user, "has_minion") <= 0:
            return {"state": "none", "user": user}
        if not name or not _MINION_NAME_RE.match(name):
            return {"state": "bad", "user": user}
        if name in RESERVED_WORDS:
            return {"state": "reserved", "user": user}
        if not spend(user_id, MINION_NAME_PRICE):
            return {"state": "poor", "user": get_user(user_id), "price": MINION_NAME_PRICE}
        user = set_fields(user_id, minion_name=name, minion_await_name=0)
        log.info("نام نوچه ثبت شد → کاربر %s نام %s", user_id, name)
        return {"state": "ok", "user": user, "name": name}


def minion_panel_text(name: str, user: Dict[str, Any], note: Optional[str] = None) -> str:
    level_idx = num(user, "level_index")
    if num(user, "has_minion") <= 0:
        lines = [
            "🧑‍🦱 <b>نوچه</b>",
            SEP,
            "❌ نوچه نداری!",
            f"💸 قیمت استخدام: <b>{money(MINION_PRICE)}</b>",
            f"🎖 شرط: سطح <b>{pn(MINION_MIN_LEVEL)}</b> به بالا",
            f"📍 سطح تو: <b>{level_name(level_idx)}</b>",
            "",
            "نوچه به‌جای تو دزدی می‌کنه و سهمت رو می‌ده.",
            SEP,
            "🛒 <code>فروشگاه</code> ← استخدام",
        ]
    else:
        nick = user.get("minion_name") or "بی‌نام"
        level = max(1, num(user, "minion_level", 1))
        wait = minion_ready_in(user)
        cyc = minion_cycle(user)
        lines = [
            f"🧑‍🦱 <b>پنل نوچه — {esc(nick)}</b>",
            SEP,
            f"👤 ارباب: {esc(name)}",
            f"🏷 سطح نوچه: <b>{pn(level)}</b>/{pn(MINION_MAX_LEVEL)}",
            f"⏱ چرخه کار: <b>{duration_fa(cyc)}</b>",
            f"💰 کل درآمد: <b>{money(num(user, 'minion_earned'))}</b>",
            f"🔁 مأموریت‌ها: <b>{pn(num(user, 'minion_runs'))}</b>",
            SEP,
        ]
        if wait > 0:
            lines += [
                f"🕒 غنیمت بعدی: <b>{duration_fa(wait)}</b>",
                f"📊 {progress_bar(cyc - wait, cyc)}",
            ]
        else:
            lines.append("✅ غنیمت آماده — دکمه برداشت رو بزن!")
        if level < MINION_MAX_LEVEL:
            lines.append(f"⬆️ ارتقا: <b>{money(minion_upgrade_price(user))}</b>")
        else:
            lines.append("🏆 نوچه در بالاترین سطح!")
        if not user.get("minion_name"):
            lines.append(f"🏷 اسم دلخواه: <b>{money(MINION_NAME_PRICE)}</b> (با اسم هم صداش می‌زنی)")
    if note:
        lines += [SEP, note]
    return "\n".join(lines)


def kb_minion(user: Dict[str, Any]) -> InlineKeyboardMarkup:
    if num(user, "has_minion") <= 0:
        return rows(
            [btn(f"🛒 استخدام نوچه ({pn(f'{MINION_PRICE:,}')})",
                 callback_data="shop_buy_minion", style=STYLE_SUCCESS)],
            kb_back_row("start_back"),
        )
    body: List[List[InlineKeyboardButton]] = []
    ready = minion_ready_in(user) <= 0
    body.append([btn("💰 برداشت غنیمت" if ready else "⏳ هنوز آماده نیست",
                     callback_data="minion_get",
                     style=STYLE_SUCCESS if ready else STYLE_DANGER)])
    row2: List[InlineKeyboardButton] = []
    if num(user, "minion_level", 1) < MINION_MAX_LEVEL:
        row2.append(btn(f"⬆️ ارتقا ({pn(f'{minion_upgrade_price(user):,}')})",
                        callback_data="minion_up", style=STYLE_PRIMARY))
    row2.append(btn(f"🏷 انتخاب اسم ({pn(MINION_NAME_PRICE)})",
                    callback_data="minion_name", style=STYLE_PRIMARY))
    body.append(row2)
    body.append([
        btn("🔄 بروزرسانی", callback_data="minion", style=STYLE_PRIMARY),
        *kb_back_row("start_back"),
    ])
    return rows(*body)


def minion_view(name: str, user: Dict[str, Any], note: Optional[str] = None
                ) -> Tuple[str, InlineKeyboardMarkup]:
    return minion_panel_text(name, user, note), kb_minion(user)


def txt_help_minion() -> str:
    return "\n".join([
        "🧑‍🦱 <b>راهنمای نوچه</b>",
        SEP,
        "دستور: <code>نوچه</code> یا اسم دلخواهش",
        f"🎖 شرط استخدام: سطح {pn(MINION_MIN_LEVEL)} به بالا",
        f"💸 قیمت: {money(MINION_PRICE)}",
        f"🏷 اسم دلخواه: {money(MINION_NAME_PRICE)}",
        SEP,
        f"⏱ هر {duration_fa(MINION_CYCLE)} یک دزدی خودکار",
        f"🤝 سهم تو: {pct(MINION_SHARE)} غنیمت",
        f"⬆️ ارتقا: چرخه سریع‌تر + غنیمت بیشتر (تا سطح {pn(MINION_MAX_LEVEL)})",
        "⛓ نوچه وقتی تو زندانی باشی کار نمی‌کنه.",
    ])


@dp.callback_query(F.data == "minion")
async def cb_minion(cq: CallbackQuery) -> None:
    u = cq.from_user
    user = await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
    text, kb = minion_view(display_name(u.full_name, u.username, u.id), user)
    await safe_edit(cq, text, kb)
    await cq.answer()


@dp.callback_query(F.data == "minion_get")
async def cb_minion_get(cq: CallbackQuery) -> None:
    u = cq.from_user
    res = await asyncio.to_thread(minion_collect, u.id)
    notes = {
        "ok": lambda: f"💰 نوچه <b>{money(res['amount'])}</b> آورد!",
        "wait": lambda: f"⏳ {duration_fa(res['left'])} دیگه صبر کن.",
        "jailed": lambda: "⛓ تو زندانی — نوچه کار نمی‌کنه.",
        "none": lambda: "❌ نوچه نداری.",
    }
    text, kb = minion_view(display_name(u.full_name, u.username, u.id),
                           res["user"], notes.get(res["state"], lambda: "")())
    await safe_edit(cq, text, kb)
    await cq.answer("💰 دریافت شد" if res["state"] == "ok" else "⏳ آماده نیست")


@dp.callback_query(F.data == "minion_up")
async def cb_minion_up(cq: CallbackQuery) -> None:
    u = cq.from_user
    res = await asyncio.to_thread(minion_upgrade, u.id)
    notes = {
        "ok": lambda: f"⬆️ نوچه سطح {pn(res['level'])} شد!",
        "poor": lambda: f"❌ پول کافی نداری ({money(res['price'])})",
        "max": lambda: "🏆 بالاترین سطح!",
        "none": lambda: "❌ نوچه نداری.",
    }
    text, kb = minion_view(display_name(u.full_name, u.username, u.id),
                           res["user"], notes.get(res["state"], lambda: "")())
    await safe_edit(cq, text, kb)
    await cq.answer("⬆️ ارتقا شد" if res["state"] == "ok" else "❌ انجام نشد",
                    show_alert=(res["state"] == "poor"))


@dp.callback_query(F.data == "minion_name")
async def cb_minion_name(cq: CallbackQuery) -> None:
    u = cq.from_user
    res = await asyncio.to_thread(minion_request_name, u.id)
    if res["state"] == "poor":
        await cq.answer(f"❌ {money(MINION_NAME_PRICE)} لازمه!", show_alert=True)
        return
    if res["state"] == "none":
        await cq.answer("❌ نوچه نداری.", show_alert=True)
        return
    note = (f"🏷 اسم دلخواه نوچه رو <b>ریپلای</b> کن روی همین پیام.\n"
            f"💸 هزینه: <b>{money(MINION_NAME_PRICE)}</b>\n"
            f"✍️ ۲ تا ۱۸ حرف — بعدش با همون اسم صداش می‌زنی.")
    text, kb = minion_view(display_name(u.full_name, u.username, u.id), res["user"], note)
    await safe_edit(cq, text, kb)
    await cq.answer("✍️ اسم رو ریپلای کن")


@dp.callback_query(F.data == "help_minion")
async def cb_help_minion(cq: CallbackQuery) -> None:
    await safe_edit(cq, txt_help_minion(), kb_back("help_main"))
    await cq.answer()


# ▓▓ بخش ۱۲ — پایان ▓▓
# ══════════════════════════════════════════════════════════════════════════
# ▓▓ بخش ۱۳ — سند جعلی (FAKE DOC) ▓▓  [شروع]
#    دستور: سند   |   حداکثر ۳ سند همزمان، برای فرار از زندان (ریسک‌دار)
# ══════════════════════════════════════════════════════════════════════════

register_columns(
    fake_docs="INTEGER DEFAULT 0",          # سند موجود (حداکثر ۳)
    docs_bought="INTEGER DEFAULT 0",        # کل سند خریداری‌شده
    docs_used="INTEGER DEFAULT 0",          # کل استفاده
    docs_caught="INTEGER DEFAULT 0",        # چند بار لو رفته
)

DOC_PRICE: int = 1800
DOC_MAX_HOLD: int = 3                # حداکثر سند همزمان
DOC_CATCH_CHANCE: float = 0.28       # احتمال شناسایی جعلی بودن
DOC_PENALTY_MINUTES: int = 45        # حبس اضافه در صورت لو رفتن


def doc_can_buy(user: Dict[str, Any]) -> bool:
    return num(user, "fake_docs") < DOC_MAX_HOLD


def use_fake_doc(user_id: int) -> Dict[str, Any]:
    """
    استفاده از سند جعلی برای آزادی.
    خروجی state: none | free | escaped | caught
    """
    with _db_lock:
        user = release_if_done(get_user(user_id))
        if num(user, "fake_docs") <= 0:
            return {"state": "none", "user": user}
        left = jail_left(user)
        if left <= 0:
            return {"state": "free", "user": user}

        user = set_fields(user_id, fake_docs=num(user, "fake_docs") - 1,
                          docs_used=num(user, "docs_used") + 1)
        if random.random() < DOC_CATCH_CHANCE:
            extra = DOC_PENALTY_MINUTES * 60
            new_left = left + extra
            user = set_fields(
                user_id,
                jail_until=iso(now_ts() + new_left),
                jail_total=num(user, "jail_total") + extra,
                docs_caught=num(user, "docs_caught") + 1,
                arrest_count=num(user, "arrest_count") + 1,
            )
            log.info("سند جعلی لو رفت → کاربر %s | +%ss حبس", user_id, extra)
            return {"state": "caught", "user": user, "left": new_left, "extra": extra}

        user = set_fields(user_id, jail_until=None, jail_total=0, streak=0,
                          robs_since_arrest=0, loot_since_arrest=0)
        log.info("فرار با سند جعلی → کاربر %s", user_id)
        return {"state": "escaped", "user": user}


def doc_panel_text(name: str, user: Dict[str, Any], note: Optional[str] = None) -> str:
    held = num(user, "fake_docs")
    slots = "🟩" * held + "⬜" * (DOC_MAX_HOLD - held)
    lines = [
        "📜 <b>سند جعلی</b>",
        SEP,
        f"👤 {esc(name)}",
        f"🗂 موجودی: <b>{pn(held)}</b>/{pn(DOC_MAX_HOLD)}  {slots}",
        f"💸 قیمت هر سند: <b>{money(DOC_PRICE)}</b>",
        SEP,
        f"🎯 شانس فرار موفق: <b>{pct(1 - DOC_CATCH_CHANCE)}</b>",
        f"⚠️ اگه لو بره: <b>+{pn(DOC_PENALTY_MINUTES)} دقیقه</b> حبس",
        f"✅ استفاده‌شده: <b>{pn(num(user, 'docs_used'))}</b>",
        f"🚨 لو رفته: <b>{pn(num(user, 'docs_caught'))}</b>",
    ]
    if not doc_can_buy(user):
        lines += [SEP, "🈵 ظرفیت پره! اول یکی رو استفاده کن."]
    if jail_left(user) > 0 and held > 0:
        lines += [SEP, "⛓ تو زندانی — می‌تونی الان سند بزنی."]
    if note:
        lines += [SEP, note]
    return "\n".join(lines)


def kb_doc(user: Dict[str, Any]) -> InlineKeyboardMarkup:
    body: List[List[InlineKeyboardButton]] = []
    if doc_can_buy(user):
        body.append([btn(f"🛒 خرید سند ({pn(f'{DOC_PRICE:,}')})",
                         callback_data="shop_buy_doc", style=STYLE_SUCCESS)])
    else:
        body.append([btn("🈵 ظرفیت پره", callback_data="doc", style=STYLE_DANGER)])
    if num(user, "fake_docs") > 0 and jail_left(user) > 0:
        body.append([btn("🏃 فرار با سند جعلی", callback_data="doc_use", style=STYLE_DANGER)])
    body.append([
        btn("🔄 بروزرسانی", callback_data="doc", style=STYLE_PRIMARY),
        *kb_back_row("start_back"),
    ])
    return rows(*body)


def doc_view(name: str, user: Dict[str, Any], note: Optional[str] = None
             ) -> Tuple[str, InlineKeyboardMarkup]:
    return doc_panel_text(name, user, note), kb_doc(user)


def txt_help_doc() -> str:
    return "\n".join([
        "📜 <b>راهنمای سند جعلی</b>",
        SEP,
        "دستور: <code>سند</code>",
        f"💸 قیمت: {money(DOC_PRICE)}",
        f"🗂 حداکثر همزمان: {pn(DOC_MAX_HOLD)} سند",
        "♻️ برای گرفتن سند جدید باید یکی رو مصرف کنی.",
        SEP,
        f"🎯 فرار موفق: {pct(1 - DOC_CATCH_CHANCE)}",
        f"🚨 لو رفتن: {pct(DOC_CATCH_CHANCE)} → +{pn(DOC_PENALTY_MINUTES)} دقیقه حبس",
        "🏛 از پنل زندان هم می‌تونی استفاده کنی.",
    ])


@dp.message(F.text.regexp(re.compile(r"^\s*(?:سند|سند\s*جعلی|/doc)\s*$")))
async def h_doc(message: Message) -> None:
    u = message.from_user
    if u is None:
        return
    user = await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
    text, kb = doc_view(display_name(u.full_name, u.username, u.id), user)
    await message.reply(text, reply_markup=kb)


@dp.callback_query(F.data == "doc")
async def cb_doc(cq: CallbackQuery) -> None:
    u = cq.from_user
    user = await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
    text, kb = doc_view(display_name(u.full_name, u.username, u.id), user)
    await safe_edit(cq, text, kb)
    await cq.answer()


@dp.callback_query(F.data == "doc_use")
async def cb_doc_use(cq: CallbackQuery) -> None:
    u = cq.from_user
    name = display_name(u.full_name, u.username, u.id)
    res = await asyncio.to_thread(use_fake_doc, u.id)
    state = res["state"]
    if state == "escaped":
        text = "\n".join([
            "🏃 <b>فرار موفق!</b>",
            SEP,
            f"👤 {esc(name)}",
            "📜 سند جعلی رو باور کردن — آزاد شدی!",
            f"🗂 سند باقی‌مانده: <b>{pn(num(res['user'], 'fake_docs'))}</b>",
            SEP,
            "😈 برگرد سر کار: <code>دزدی</code>",
        ])
        await safe_edit(cq, text, kb_jail(res["user"], 0, 0))
        await cq.answer("🏃 آزاد شدی!", show_alert=True)
        return
    if state == "caught":
        user, left = res["user"], int(res["left"])
        text = "\n".join([
            "🚨 <b>سندت لو رفت!</b>",
            SEP,
            f"👤 {esc(name)}",
            "🕵️ افسر فهمید سند جعلیه.",
            f"⛓ حبس اضافه: <b>+{duration_fa(int(res['extra']))}</b>",
            f"⏳ مجموع باقی‌مانده: <b>{duration_fa(left)}</b>",
            f"🗂 سند باقی‌مانده: <b>{pn(num(user, 'fake_docs'))}</b>",
            SEP,
            "💵 یا وثیقه بده یا صبر کن.",
        ])
        await safe_edit(cq, text, kb_jail(user, left, bail_price(user, left)))
        await cq.answer("🚨 لو رفتی!", show_alert=True)
        return
    notes = {"none": "❌ سند جعلی نداری.", "free": "✅ تو زندانی نیستی."}
    text, kb = doc_view(name, res["user"], notes.get(state, ""))
    await safe_edit(cq, text, kb)
    await cq.answer(notes.get(state, ""), show_alert=True)


@dp.callback_query(F.data == "help_doc")
async def cb_help_doc(cq: CallbackQuery) -> None:
    await safe_edit(cq, txt_help_doc(), kb_back("help_main"))
    await cq.answer()


# ▓▓ بخش ۱۳ — پایان ▓▓


# ══════════════════════════════════════════════════════════════════════════
# ▓▓ بخش ۱۴ — فروشگاه (SHOP) ▓▓  [شروع]
#    دستور: فروشگاه   |   کاتالوگ آیتم‌ها با بررسی شرط سطح و موجودی
# ══════════════════════════════════════════════════════════════════════════

class ShopItem:
    """
    یک کالای فروشگاه.
      key      : شناسه کالا (در callback_data استفاده می‌شود)
      requires : نام تابعی که باید موجود باشد (بخش مربوطه فعال باشد)
    """

    def __init__(self, key: str, title: str, price_getter: Callable[[], int],
                 desc: str, requires: str, min_level: int = 0,
                 owned: Optional[Callable[[Dict[str, Any]], bool]] = None,
                 buy: Optional[Callable[[int, Dict[str, Any]], Dict[str, Any]]] = None,
                 panel_cb: Optional[str] = None) -> None:
        self.key = key
        self.title = title
        self.price_getter = price_getter
        self.desc = desc
        self.requires = requires
        self.min_level = min_level
        self.owned = owned or (lambda u: False)
        self.buy = buy
        self.panel_cb = panel_cb

    @property
    def price(self) -> int:
        return int(self.price_getter())

    def available(self) -> bool:
        return has(self.requires)


def _buy_flag(column: str, **extra: Any) -> Callable[[int, Dict[str, Any]], Dict[str, Any]]:
    """سازنده تابع خرید برای آیتم‌های پرچمی (has_x = 1)."""
    def _do(user_id: int, item_user: Dict[str, Any]) -> Dict[str, Any]:
        return set_fields(user_id, **{column: 1}, **extra)
    return _do


def _buy_doc(user_id: int, user: Dict[str, Any]) -> Dict[str, Any]:
    return set_fields(user_id, fake_docs=num(user, "fake_docs") + 1,
                      docs_bought=num(user, "docs_bought") + 1)


SHOP_ITEMS: List[ShopItem] = [
    ShopItem(
        "ak", "🔫 اسلحه AK-۴۷", lambda: AK_PRICE,
        "دزدی بدون دستگیری تا خالی شدن خشاب",
        requires="weapon_panel_text",
        owned=lambda u: num(u, "has_ak") > 0,
        buy=lambda uid, u: set_fields(uid, has_ak=1, ak_level=1, ak_broken=0,
                                     ak_health=100, ak_uses=AK_USES_BASE,
                                     ak_ammo=AK_USES_BASE * 10),
        panel_cb="weapon",
    ),
    ShopItem(
        "dossier", "📁 پرونده جعلی", lambda: DOSSIER_PRICE,
        "بانک‌زنی با امضا و اثر انگشت جعلی",
        requires="dossier_panel_text",
        owned=lambda u: num(u, "has_dossier") > 0,
        buy=_buy_flag("has_dossier"),
        panel_cb="dossier",
    ),
    ShopItem(
        "wallet", "👝 کیف پول", lambda: WALLET_PRICE,
        "پول رو از چشم پلیس مخفی کن",
        requires="wallet_panel_text",
        owned=lambda u: num(u, "has_wallet") > 0,
        buy=_buy_flag("has_wallet"),
        panel_cb="wallet",
    ),
    ShopItem(
        "minion", "🧑‍🦱 استخدام نوچه", lambda: MINION_PRICE,
        "دزدی خودکار به‌جای تو",
        requires="minion_panel_text",
        min_level=MINION_MIN_LEVEL,
        owned=lambda u: num(u, "has_minion") > 0,
        buy=lambda uid, u: set_fields(uid, has_minion=1, minion_level=1, minion_last=None),
        panel_cb="minion",
    ),
    ShopItem(
        "doc", "📜 سند جعلی", lambda: DOC_PRICE,
        f"فرار از زندان (حداکثر {pn(DOC_MAX_HOLD)} سند)",
        requires="use_fake_doc",
        owned=lambda u: False,
        buy=_buy_doc,
        panel_cb="doc",
    ),
]


def shop_item(key: str) -> Optional[ShopItem]:
    for it in SHOP_ITEMS:
        if it.key == key and it.available():
            return it
    return None


def shop_buy(user_id: int, key: str) -> Dict[str, Any]:
    """
    خرید کالا. state: bad | owned | level | full | poor | ok
    """
    item = shop_item(key)
    if item is None:
        return {"state": "bad", "user": get_user(user_id)}
    with _db_lock:
        user = get_user(user_id)
        if item.owned(user):
            return {"state": "owned", "user": user, "item": item}
        if item.min_level and num(user, "level_index") < item.min_level:
            return {"state": "level", "user": user, "item": item}
        if key == "doc" and not doc_can_buy(user):
            return {"state": "full", "user": user, "item": item}
        price = item.price
        if not spend(user_id, price):
            return {"state": "poor", "user": get_user(user_id), "item": item, "price": price}
        user = item.buy(user_id, user) if item.buy else get_user(user_id)
        log.info("خرید → کاربر %s کالا %s مبلغ %s", user_id, key, price)
        return {"state": "ok", "user": user, "item": item, "price": price}


def shop_text(name: str, user: Dict[str, Any], note: Optional[str] = None) -> str:
    lines = [
        "🛒 <b>فروشگاه زیرزمینی</b>",
        SEP,
        f"👤 {esc(name)}",
        f"💵 جیب: <b>{money(num(user, 'money'))}</b>",
        f"🎖 {level_name(num(user, 'level_index'))}",
        SEP,
    ]
    for item in SHOP_ITEMS:
        if not item.available():
            continue
        if item.owned(user):
            mark = "✅"
            tail = "خریداری شده"
        elif item.min_level and num(user, "level_index") < item.min_level:
            mark = "🔒"
            tail = f"نیاز به سطح {pn(item.min_level)}"
        elif num(user, "money") < item.price:
            mark = "💸"
            tail = money(item.price)
        else:
            mark = "🛍"
            tail = money(item.price)
        lines.append(f"{mark} {item.title} — <b>{tail}</b>")
        lines.append(f"   <i>{item.desc}</i>")
    if note:
        lines += [SEP, note]
    return "\n".join(lines)


def kb_shop(user: Dict[str, Any]) -> InlineKeyboardMarkup:
    body: List[List[InlineKeyboardButton]] = []
    for item in SHOP_ITEMS:
        if not item.available():
            continue
        if item.owned(user):
            body.append([btn(f"✅ {item.title} — پنل",
                             callback_data=item.panel_cb or "shop",
                             style=STYLE_PRIMARY)])
        elif item.min_level and num(user, "level_index") < item.min_level:
            body.append([btn(f"🔒 {item.title} (سطح {pn(item.min_level)})",
                             callback_data="shop_locked", style=STYLE_DANGER)])
        else:
            affordable = num(user, "money") >= item.price
            body.append([btn(f"🛍 {item.title} ({pn(f'{item.price:,}')})",
                             callback_data=f"shop_buy_{item.key}",
                             style=STYLE_SUCCESS if affordable else STYLE_DANGER)])
    body.append([
        btn("🔄 بروزرسانی", callback_data="shop", style=STYLE_PRIMARY),
        *kb_back_row("start_back"),
    ])
    return rows(*body)


def shop_view(name: str, user: Dict[str, Any], note: Optional[str] = None
              ) -> Tuple[str, InlineKeyboardMarkup]:
    return shop_text(name, user, note), kb_shop(user)


def txt_help_shop() -> str:
    lines = ["🛒 <b>راهنمای فروشگاه</b>", SEP, "دستور: <code>فروشگاه</code>", ""]
    for item in SHOP_ITEMS:
        if item.available():
            extra = f" (سطح {pn(item.min_level)}+)" if item.min_level else ""
            lines.append(f"• {item.title} — {money(item.price)}{extra}")
    lines += [SEP, "💡 پول از دزدی و قمار به‌دست میاد."]
    return "\n".join(lines)


@dp.message(F.text.regexp(re.compile(r"^\s*(?:فروشگاه|مغازه|/shop)\s*$")))
async def h_shop(message: Message) -> None:
    u = message.from_user
    if u is None:
        return
    user = await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
    text, kb = shop_view(display_name(u.full_name, u.username, u.id), user)
    await message.reply(text, reply_markup=kb)


@dp.callback_query(F.data == "shop")
async def cb_shop(cq: CallbackQuery) -> None:
    u = cq.from_user
    user = await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
    text, kb = shop_view(display_name(u.full_name, u.username, u.id), user)
    await safe_edit(cq, text, kb)
    await cq.answer()


@dp.callback_query(F.data == "shop_locked")
async def cb_shop_locked(cq: CallbackQuery) -> None:
    await cq.answer(f"🔒 برای این کالا سطح {pn(MINION_MIN_LEVEL)} به بالا لازمه!",
                    show_alert=True)


@dp.callback_query(F.data.startswith("shop_buy_"))
async def cb_shop_buy(cq: CallbackQuery) -> None:
    u = cq.from_user
    key = (cq.data or "").replace("shop_buy_", "", 1)
    res = await asyncio.to_thread(shop_buy, u.id, key)
    item: Optional[ShopItem] = res.get("item")
    title = item.title if item else "کالا"
    notes = {
        "ok": lambda: f"✅ <b>{title}</b> خریداری شد! (-{money(res['price'])})",
        "poor": lambda: f"❌ پول کافی نداری — {money(res['price'])} لازمه.",
        "owned": lambda: f"✅ {title} رو از قبل داری.",
        "level": lambda: f"🔒 نیاز به سطح {pn(item.min_level if item else 0)}",
        "full": lambda: f"🈵 حداکثر {pn(DOC_MAX_HOLD)} سند می‌تونی داشته باشی.",
        "bad": lambda: "❔ این کالا موجود نیست.",
    }
    note = notes.get(res["state"], lambda: "")()
    text, kb = shop_view(display_name(u.full_name, u.username, u.id), res["user"], note)
    await safe_edit(cq, text, kb)
    await cq.answer("✅ خرید موفق" if res["state"] == "ok" else "❌ انجام نشد",
                    show_alert=(res["state"] in ("poor", "level", "full")))


@dp.callback_query(F.data == "help_shop")
async def cb_help_shop(cq: CallbackQuery) -> None:
    await safe_edit(cq, txt_help_shop(), kb_back("help_main"))
    await cq.answer()


# ▓▓ بخش ۱۴ — پایان ▓▓
# ══════════════════════════════════════════════════════════════════════════
# ▓▓ بخش ۱۵ — قمارخونه (CASINO) ▓▓  [شروع]
#    دستور: قمارخونه   |   فلو تک‌پیامی با edit_text + دوئل با رفیق
# ══════════════════════════════════════════════════════════════════════════

register_columns(
    last_gamble="TIMESTAMP",
    gamble_wins="INTEGER DEFAULT 0",
    gamble_loses="INTEGER DEFAULT 0",
)

GAMBLE_COOLDOWN: int = 180          # ۵ دقیقه
ODDS_NORMAL: float = 1.8
ODDS_EXACT: float = 3.0
GAMBLE_DELAY: int = 5               # ثانیه انتظار نمایش نتیجه
GAMBLE_PRESETS: List[int] = [100, 500, 1000]

GAMES: List[Tuple[str, str]] = [
    ("foot", "⚽️ فوتبال"),
    ("basket", "🏀 بسکتبال"),
    ("slot", "🎰 اسلات"),
    ("dice", "🎲 تاس"),
    ("dart", "🎯 دارت"),
    ("bowl", "🎳 بولینگ"),
]
GAME_TITLES: Dict[str, str] = dict(GAMES)

MATCHES: List[Tuple[str, str]] = [
    ("پرسپولیس", "استقلال"),
    ("پاری‌سن‌ژرمن", "رئال"),
    ("بارسا", "منچستر"),
    ("اینتر", "یوونتوس"),
    ("بایرن", "دورتموند"),
]

# وضعیت زنده قمار: کلید = (chat_id, message_id)
gamble_states: Dict[Tuple[int, int], Dict[str, Any]] = {}
_EXACT_RE = re.compile(r"^(\d{1,2})\s*[-:]\s*(\d{1,2})$")


def roll_score() -> int:
    return random.randint(0, 100)


def gamble_cd_left(user: Dict[str, Any]) -> int:
    ts = parse_ts(user.get("last_gamble"))
    if ts is None:
        return 0
    return max(0, min(GAMBLE_COOLDOWN, int(round(GAMBLE_COOLDOWN - (now_ts() - ts)))))


def gm_key(message: Message) -> Tuple[int, int]:
    return (message.chat.id, message.message_id)


def gm_state(cq: CallbackQuery) -> Optional[Dict[str, Any]]:
    if cq.message is None:
        return None
    return gamble_states.get((cq.message.chat.id, cq.message.message_id))


def gm_teams(state: Dict[str, Any]) -> Tuple[str, str]:
    return state.get("team1", "تو"), state.get("team2", "ربات")


def gm_outcome(t1: int, t2: int) -> str:
    if t1 > t2:
        return "w1"
    if t2 > t1:
        return "w2"
    return "draw"


def gamble_settle(user_id: int, amount: int, won: bool, odds: float) -> Dict[str, Any]:
    """تسویه قمار با ربات."""
    with _db_lock:
        user = get_user(user_id)
        if won:
            profit = int(amount * odds) - amount
            user = update_user(user_id, money_add=profit)
            user = set_fields(user_id, last_gamble=iso(),
                              gamble_wins=num(user, "gamble_wins") + 1)
            return {"user": user, "delta": profit, "won": True}
        user = update_user(user_id, money_add=-amount)
        user = set_fields(user_id, last_gamble=iso(),
                          gamble_loses=num(user, "gamble_loses") + 1)
        return {"user": user, "delta": -amount, "won": False}


# ── متن‌ها ─────────────────────────────────────────────────────────

def txt_casino_home() -> str:
    return "\n".join([
        "🎰 <b>قمارخونه زیرزمینی</b>",
        SEP,
        "بازی مورد نظرت رو انتخاب کن 👇",
        f"💸 ضریب برد: <b>×{pn(ODDS_NORMAL)}</b>",
        f"🎯 نتیجه دقیق: <b>×{pn(int(ODDS_EXACT))}</b>",
    ])


def kb_casino_games() -> InlineKeyboardMarkup:
    body: List[List[InlineKeyboardButton]] = []
    for i in range(0, len(GAMES), 2):
        pair = GAMES[i:i + 2]
        body.append([btn(title, callback_data=f"gm_game_{key}",
                         style=STYLE_SUCCESS if i == 0 else STYLE_PRIMARY)
                     for key, title in pair])
    body.append([btn("🔙 بازگشت", callback_data="gm_cancel", style=STYLE_DANGER)])
    return rows(*body)


def txt_casino_match(game: str) -> str:
    return "\n".join([
        f"{GAME_TITLES.get(game, '🎲')} <b>انتخاب مسابقه</b>",
        SEP,
        "روی کدوم بازی شرط می‌بندی؟",
    ])


def kb_casino_match(game: str) -> InlineKeyboardMarkup:
    body: List[List[InlineKeyboardButton]] = []
    if game == "foot":
        for i, (t1, t2) in enumerate(MATCHES):
            body.append([btn(f"⚽️ {t1} ⚔️ {t2}", callback_data=f"gm_match_{i}",
                             style=STYLE_PRIMARY)])
    else:
        body.append([btn(f"▶️ شروع {GAME_TITLES.get(game, '')}",
                         callback_data="gm_match_other", style=STYLE_SUCCESS)])
    body.append([btn("🔙 بازگشت", callback_data="gm_home", style=STYLE_DANGER)])
    return rows(*body)


def txt_casino_amount(state: Dict[str, Any], user: Dict[str, Any]) -> str:
    t1, t2 = gm_teams(state)
    return "\n".join([
        "💰 <b>مبلغ شرط</b>",
        SEP,
        f"{GAME_TITLES.get(state['game'], '🎲')} {esc(t1)} ⚔️ {esc(t2)}",
        f"💵 جیب: <b>{money(num(user, 'money'))}</b>",
        SEP,
        "مبلغ رو انتخاب کن یا دلخواه بفرست (ریپلای).",
    ])


def kb_casino_amount() -> InlineKeyboardMarkup:
    return rows(
        [btn(f"🟢 {pn(GAMBLE_PRESETS[0])}", callback_data=f"gm_amt_{GAMBLE_PRESETS[0]}", style=STYLE_SUCCESS),
         btn(f"🔵 {pn(GAMBLE_PRESETS[1])}", callback_data=f"gm_amt_{GAMBLE_PRESETS[1]}", style=STYLE_PRIMARY),
         btn(f"🟡 {pn(GAMBLE_PRESETS[2])}", callback_data=f"gm_amt_{GAMBLE_PRESETS[2]}", style=STYLE_PRIMARY)],
        [btn("🟣 مبلغ دلخواه (ریپلای)", callback_data="gm_amt_custom", style=STYLE_PRIMARY)],
        [btn("🔙 بازگشت", callback_data="gm_home", style=STYLE_DANGER)],
    )


def txt_casino_opponent(state: Dict[str, Any]) -> str:
    t1, t2 = gm_teams(state)
    return "\n".join([
        "👥 <b>انتخاب حریف</b>",
        SEP,
        f"{GAME_TITLES.get(state['game'], '🎲')} {esc(t1)} ⚔️ {esc(t2)}",
        f"💰 مبلغ: <b>{money(state['amount'])}</b>",
        SEP,
        "با ربات بازی کنی یا رفیقت؟",
    ])


def kb_casino_opponent() -> InlineKeyboardMarkup:
    return rows(
        [btn("🤖 با ربات", callback_data="gm_opp_bot", style=STYLE_DANGER),
         btn("👥 با رفیق (دوئل)", callback_data="gm_opp_pv", style=STYLE_PRIMARY)],
        [btn("🔙 بازگشت", callback_data="gm_home", style=STYLE_DANGER)],
    )


def txt_casino_predict(state: Dict[str, Any], who: Optional[str] = None) -> str:
    t1, t2 = gm_teams(state)
    head = "🔮 <b>پیش‌بینی کن</b>" if not who else f"🔮 <b>نوبت {esc(who)}</b>"
    return "\n".join([
        head,
        SEP,
        f"{GAME_TITLES.get(state['game'], '🎲')} {esc(t1)} ⚔️ {esc(t2)}",
        f"💰 مبلغ: <b>{money(state['amount'])}</b>",
        SEP,
        f"✅ برد/مساوی: ضریب <b>×{pn(ODDS_NORMAL)}</b>",
        f"🎯 نتیجه دقیق: ضریب <b>×{pn(int(ODDS_EXACT))}</b>",
    ])


def kb_casino_predict(state: Dict[str, Any]) -> InlineKeyboardMarkup:
    t1, t2 = gm_teams(state)
    return rows(
        [btn(f"🟢 برد {t1[:12]}", callback_data="gm_pred_w1", style=STYLE_SUCCESS),
         btn(f"🔴 برد {t2[:12]}", callback_data="gm_pred_w2", style=STYLE_DANGER)],
        [btn("🟡 مساوی", callback_data="gm_pred_draw", style=STYLE_PRIMARY)],
        [btn("🔢 نتیجه دقیق (ریپلای)", callback_data="gm_pred_exact", style=STYLE_PRIMARY)],
        [btn("🔙 بازگشت", callback_data="gm_home", style=STYLE_DANGER)],
    )


def txt_casino_lobby(state: Dict[str, Any]) -> str:
    t1, t2 = gm_teams(state)
    return "\n".join([
        "👥 <b>دوئل — انتظار رفیق</b>",
        SEP,
        f"{GAME_TITLES.get(state['game'], '🎲')} {esc(t1)} ⚔️ {esc(t2)}",
        f"💰 شرط هر نفر: <b>{money(state['amount'])}</b>",
        f"🎮 سازنده: {esc(state['host_name'])}",
        SEP,
        "رفیقت دکمه «پیوستن» رو بزنه!",
    ])


def kb_casino_lobby() -> InlineKeyboardMarkup:
    return rows(
        [btn("👥 پیوستن رفیق", callback_data="gm_join", style=STYLE_SUCCESS)],
        [btn("🔙 لغو", callback_data="gm_cancel", style=STYLE_DANGER)],
    )


def txt_casino_playing() -> str:
    return "\n".join([
        "🎲 <b>در حال بازی...</b>",
        SEP,
        f"⏳ {pn(GAMBLE_DELAY)} ثانیه تا نتیجه",
        "🤞 شانس باهات باشه!",
    ])


def txt_casino_result_bot(name: str, state: Dict[str, Any], p: int, o: int,
                          res: Dict[str, Any], exact: bool) -> str:
    t1, t2 = gm_teams(state)
    return "\n".join([
        "🏁 <b>نتیجه بازی</b>",
        SEP,
        f"👤 {esc(name)}",
        f"{GAME_TITLES.get(state['game'], '🎲')} {esc(t1)} <b>{pn(p)}</b> - <b>{pn(o)}</b> {esc(t2)}",
        f"🔮 پیش‌بینی: {esc(state.get('pred_label', '-'))}",
        SEP,
        ("🎉 <b>بردی!</b>" if res["won"] else "💔 <b>باختی!</b>"),
        f"{'💰 سود' if res['won'] else '💸 ضرر'}: <b>{money(abs(res['delta']))}</b>"
        + (f" (نتیجه دقیق ×{pn(int(ODDS_EXACT))})" if exact and res["won"] else ""),
        f"💵 جیب: <b>{money(num(res['user'], 'money'))}</b>",
        SEP,
        f"⏱️ قمار بعدی: {cooldown_fmt(GAMBLE_COOLDOWN)}",
    ])


def kb_casino_again() -> InlineKeyboardMarkup:
    return rows(
        [btn("🎰 قمار دوباره", callback_data="gm_home", style=STYLE_SUCCESS),
         btn("👤 حسابم", callback_data="acc", style=STYLE_PRIMARY)],
        kb_back_row("start_back"),
    )


def txt_help_casino() -> str:
    return "\n".join([
        "🎰 <b>راهنمای قمارخونه</b>",
        SEP,
        "دستور: <code>قمارخونه</code>",
        "🎮 بازی‌ها: ⚽️ 🏀 🎰 🎲 🎯 🎳",
        "🤖 با ربات یا 👥 با رفیق (دوئل)",
        f"💰 مبلغ: {pn(100)} / {pn(500)} / {pn(1000)} یا دلخواه",
        SEP,
        f"✅ برد/مساوی: ×{pn(ODDS_NORMAL)}",
        f"🎯 نتیجه دقیق: ×{pn(int(ODDS_EXACT))}",
        f"⏱️ انتظار بین قمار: {cooldown_fmt(GAMBLE_COOLDOWN)}",
        "📍 در گروه و خصوصی فعاله.",
    ])


# ── هندلرها ────────────────────────────────────────────────────────

@dp.message(F.text.regexp(re.compile(r"^\s*(?:قمارخونه|قمار|/casino)\s*$")))
async def h_casino(message: Message) -> None:
    u = message.from_user
    if u is None:
        return
    user = await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
    left = gamble_cd_left(user)
    if left > 0:
        await message.reply("\n".join([
            "⏳ <b>صبر کن رفیق!</b>",
            SEP,
            "🎰 تازه قمار کردی.",
            f"⏱️ باقی‌مانده: <b>{cooldown_fmt(left)}</b>",
        ]))
        return
    sent = await message.reply(txt_casino_home(), reply_markup=kb_casino_games())
    gamble_states[gm_key(sent)] = {
        "step": "choose_game",
        "host_id": u.id,
        "host_name": display_name(u.full_name, u.username, u.id),
        "amount": 0,
    }


@dp.callback_query(F.data == "gm_home")
async def cb_gm_home(cq: CallbackQuery) -> None:
    state = gm_state(cq)
    if state is None:
        await cq.answer("⌛ این بازی منقضی شده — دوباره «قمارخونه» بفرست.", show_alert=True)
        return
    state.update({"step": "choose_game", "game": None, "amount": 0,
                  "team1": None, "team2": None, "pred": None, "pred_label": None,
                  "guest_id": None, "guest_name": None, "preds": {}})
    await safe_edit(cq, txt_casino_home(), kb_casino_games())
    await cq.answer()


@dp.callback_query(F.data == "gm_cancel")
async def cb_gm_cancel(cq: CallbackQuery) -> None:
    if cq.message is not None:
        gamble_states.pop((cq.message.chat.id, cq.message.message_id), None)
    await safe_edit(cq, "🎰 <b>قمارخونه بسته شد.</b>\n" + SEP + "\nهر وقت خواستی <code>قمارخونه</code> بفرست.",
                    kb_back("start_back"))
    await cq.answer("بستم")


@dp.callback_query(F.data.startswith("gm_game_"))
async def cb_gm_game(cq: CallbackQuery) -> None:
    state = gm_state(cq)
    if state is None:
        await cq.answer("⌛ منقضی شده — دوباره شروع کن.", show_alert=True)
        return
    if cq.from_user.id != state["host_id"]:
        await cq.answer("🚫 این میز مال یکی دیگه‌ست!", show_alert=True)
        return
    game = (cq.data or "").replace("gm_game_", "", 1)
    if game not in GAME_TITLES:
        await cq.answer("❔ بازی نامعتبر")
        return
    state["game"] = game
    state["step"] = "choose_match"
    await safe_edit(cq, txt_casino_match(game), kb_casino_match(game))
    await cq.answer(GAME_TITLES[game])


@dp.callback_query(F.data.startswith("gm_match_"))
async def cb_gm_match(cq: CallbackQuery) -> None:
    state = gm_state(cq)
    if state is None:
        await cq.answer("⌛ منقضی شده — دوباره شروع کن.", show_alert=True)
        return
    if cq.from_user.id != state["host_id"]:
        await cq.answer("🚫 این میز مال یکی دیگه‌ست!", show_alert=True)
        return
    tag = (cq.data or "").replace("gm_match_", "", 1)
    if tag == "other":
        state["team1"], state["team2"] = state["host_name"], "🤖 ربات"
    else:
        try:
            t1, t2 = MATCHES[int(tag)]
        except (ValueError, IndexError):
            await cq.answer("❔ مسابقه نامعتبر")
            return
        state["team1"], state["team2"] = t1, t2
    state["step"] = "set_amount"
    user = await asyncio.to_thread(get_user, cq.from_user.id)
    await safe_edit(cq, txt_casino_amount(state, user), kb_casino_amount())
    await cq.answer()


@dp.callback_query(F.data.startswith("gm_amt_"))
async def cb_gm_amt(cq: CallbackQuery) -> None:
    state = gm_state(cq)
    if state is None:
        await cq.answer("⌛ منقضی شده — دوباره شروع کن.", show_alert=True)
        return
    if cq.from_user.id != state["host_id"]:
        await cq.answer("🚫 این میز مال یکی دیگه‌ست!", show_alert=True)
        return
    tag = (cq.data or "").replace("gm_amt_", "", 1)
    user = await asyncio.to_thread(get_user, cq.from_user.id)

    if tag == "custom":
        state["step"] = "await_amount_reply"
        text = txt_casino_amount(state, user) + f"\n{SEP}\n✍️ مبلغ رو <b>ریپلای</b> کن روی همین پیام."
        await safe_edit(cq, text, kb_casino_amount())
        await cq.answer("✍️ مبلغ رو ریپلای کن")
        return

    amount = parse_int(tag) or 0
    if amount <= 0:
        await cq.answer("❔ مبلغ نامعتبر")
        return
    if num(user, "money") < amount:
        await cq.answer(f"❌ پول کافی نداری ({money(amount)})", show_alert=True)
        return
    state["amount"] = amount
    state["step"] = "choose_opponent"
    await safe_edit(cq, txt_casino_opponent(state), kb_casino_opponent())
    await cq.answer(f"💰 {money(amount)}")


@dp.callback_query(F.data == "gm_opp_bot")
async def cb_gm_opp_bot(cq: CallbackQuery) -> None:
    state = gm_state(cq)
    if state is None:
        await cq.answer("⌛ منقضی شده — دوباره شروع کن.", show_alert=True)
        return
    if cq.from_user.id != state["host_id"]:
        await cq.answer("🚫 این میز مال یکی دیگه‌ست!", show_alert=True)
        return
    state["mode"] = "bot"
    state["step"] = "predict"
    await safe_edit(cq, txt_casino_predict(state), kb_casino_predict(state))
    await cq.answer("🤖 با ربات")


@dp.callback_query(F.data == "gm_opp_pv")
async def cb_gm_opp_pv(cq: CallbackQuery) -> None:
    state = gm_state(cq)
    if state is None:
        await cq.answer("⌛ منقضی شده — دوباره شروع کن.", show_alert=True)
        return
    if cq.from_user.id != state["host_id"]:
        await cq.answer("🚫 این میز مال یکی دیگه‌ست!", show_alert=True)
        return
    state["mode"] = "duel"
    state["step"] = "duel_lobby"
    state["preds"] = {}
    await safe_edit(cq, txt_casino_lobby(state), kb_casino_lobby())
    await cq.answer("👥 منتظر رفیق")


@dp.callback_query(F.data == "gm_join")
async def cb_gm_join(cq: CallbackQuery) -> None:
    state = gm_state(cq)
    if state is None:
        await cq.answer("⌛ منقضی شده — دوباره شروع کن.", show_alert=True)
        return
    u = cq.from_user
    if u.id == state["host_id"]:
        await cq.answer("🚫 خودت که سازنده‌ای!", show_alert=True)
        return
    amount = int(state["amount"])
    host = await asyncio.to_thread(get_user, int(state["host_id"]))
    guest = await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
    if num(host, "money") < amount:
        await cq.answer("❌ سازنده پول کافی نداره!", show_alert=True)
        return
    if num(guest, "money") < amount:
        await cq.answer(f"❌ تو {money(amount)} لازم داری!", show_alert=True)
        return
    state["guest_id"] = u.id
    state["guest_name"] = display_name(u.full_name, u.username, u.id)
    # در بازی‌های غیرفوتبالی، حریف «ربات» جایش را به رفیق می‌دهد
    if state.get("team2") in ("🤖 ربات", None):
        state["team2"] = state["guest_name"]
    state["step"] = "duel_predict"
    state["preds"] = {}
    text = txt_casino_predict(state) + (
        f"\n{SEP}\n🎮 {esc(state['host_name'])} ⚔️ {esc(state['guest_name'])}"
        f"\n⏳ هر دو باید پیش‌بینی کنن."
    )
    await safe_edit(cq, text, kb_casino_predict(state))
    await cq.answer("✅ وارد دوئل شدی")


PRED_LABELS = {"w1": "برد تیم اول", "w2": "برد تیم دوم", "draw": "مساوی"}


async def _finish_bot_game(cq: CallbackQuery, state: Dict[str, Any],
                           pred: str, exact: bool) -> None:
    """اجرای بازی با ربات + نمایش نتیجه."""
    u = cq.from_user
    name = display_name(u.full_name, u.username, u.id)
    amount = int(state["amount"])
    user = await asyncio.to_thread(get_user, u.id)
    if num(user, "money") < amount:
        await safe_edit(cq, f"❌ پول کافی نداری ({money(amount)})", kb_casino_again())
        await cq.answer("❌ پول کافی نیست", show_alert=True)
        return

    await safe_edit(cq, txt_casino_playing(), None)
    await asyncio.sleep(GAMBLE_DELAY)

    if exact:
        g1, g2 = state.get("exact", (0, 0))
        p, o = int(g1), int(g2)
        real1, real2 = random.randint(0, 5), random.randint(0, 5)
        won = (p, o) == (real1, real2)
        p_show, o_show = real1, real2
        odds = ODDS_EXACT
    else:
        p_show, o_show = roll_score(), roll_score()
        won = pred == gm_outcome(p_show, o_show)
        odds = ODDS_NORMAL

    res = await asyncio.to_thread(gamble_settle, u.id, amount, won, odds)
    state["step"] = "result"
    await safe_edit(cq, txt_casino_result_bot(name, state, p_show, o_show, res, exact),
                    kb_casino_again())
    await cq.answer("🎉 بردی!" if won else "💔 باختی")


async def _finish_duel(cq: CallbackQuery, state: Dict[str, Any]) -> None:
    """تسویه دوئل دو نفره."""
    amount = int(state["amount"])
    host_id, guest_id = int(state["host_id"]), int(state["guest_id"])
    preds = state["preds"]
    await safe_edit(cq, txt_casino_playing(), None)
    await asyncio.sleep(GAMBLE_DELAY)

    t1s, t2s = roll_score(), roll_score()
    outcome = gm_outcome(t1s, t2s)
    host_ok = preds.get(host_id, {}).get("pred") == outcome
    guest_ok = preds.get(guest_id, {}).get("pred") == outcome

    if host_ok == guest_ok:
        verdict = "🤝 <b>مساوی!</b> شرط‌ها برگشت."
        host_after = await asyncio.to_thread(set_fields, host_id, last_gamble=iso())
        await asyncio.to_thread(set_fields, guest_id, last_gamble=iso())
        winner_name = "—"
        prize = 0
    else:
        winner_id = host_id if host_ok else guest_id
        loser_id = guest_id if host_ok else host_id
        winner_name = state["host_name"] if host_ok else state["guest_name"]
        await asyncio.to_thread(add_money, winner_id, amount)
        await asyncio.to_thread(add_money, loser_id, -amount)
        w = await asyncio.to_thread(get_user, winner_id)
        await asyncio.to_thread(set_fields, winner_id, last_gamble=iso(),
                                gamble_wins=num(w, "gamble_wins") + 1)
        l = await asyncio.to_thread(get_user, loser_id)
        await asyncio.to_thread(set_fields, loser_id, last_gamble=iso(),
                                gamble_loses=num(l, "gamble_loses") + 1)
        verdict = f"🏆 برنده: <b>{esc(winner_name)}</b>"
        prize = amount

    t1, t2 = gm_teams(state)
    text = "\n".join([
        "🏁 <b>نتیجه دوئل</b>",
        SEP,
        f"{GAME_TITLES.get(state['game'], '🎲')} {esc(t1)} <b>{pn(t1s)}</b> - <b>{pn(t2s)}</b> {esc(t2)}",
        f"🎮 {esc(state['host_name'])} ⚔️ {esc(state['guest_name'])}",
        SEP,
        verdict,
        (f"💰 جایزه: <b>{money(prize)}</b>" if prize else "💵 پول‌ها برگشت به جیب."),
        SEP,
        f"⏱️ قمار بعدی: {cooldown_fmt(GAMBLE_COOLDOWN)}",
    ])
    state["step"] = "result"
    await safe_edit(cq, text, kb_casino_again())
    await cq.answer("🏁 تموم شد")


@dp.callback_query(F.data.startswith("gm_pred_"))
async def cb_gm_pred(cq: CallbackQuery) -> None:
    state = gm_state(cq)
    if state is None:
        await cq.answer("⌛ منقضی شده — دوباره شروع کن.", show_alert=True)
        return
    u = cq.from_user
    pred = (cq.data or "").replace("gm_pred_", "", 1)
    mode = state.get("mode", "bot")

    allowed = {int(state["host_id"])}
    if state.get("guest_id"):
        allowed.add(int(state["guest_id"]))
    if u.id not in allowed:
        await cq.answer("🚫 تو این بازی نیستی!", show_alert=True)
        return

    if pred == "exact":
        state["step"] = "await_exact_reply"
        state["exact_for"] = u.id
        text = txt_casino_predict(state) + f"\n{SEP}\n✍️ نتیجه دقیق رو <b>ریپلای</b> کن (مثل ۲-۱)"
        await safe_edit(cq, text, kb_casino_predict(state))
        await cq.answer("✍️ نتیجه رو ریپلای کن")
        return

    if pred not in PRED_LABELS:
        await cq.answer("❔ پیش‌بینی نامعتبر")
        return

    t1, t2 = gm_teams(state)
    label = {"w1": f"برد {t1}", "w2": f"برد {t2}", "draw": "مساوی"}[pred]

    if mode == "duel":
        state.setdefault("preds", {})[u.id] = {"pred": pred, "label": label}
        need = {int(state["host_id"]), int(state["guest_id"])}
        if not need <= set(state["preds"].keys()):
            waiting = state["guest_name"] if u.id == state["host_id"] else state["host_name"]
            text = txt_casino_predict(state) + (
                f"\n{SEP}\n✅ {esc(display_name(u.full_name, u.username, u.id))} ثبت شد."
                f"\n⏳ منتظر {esc(waiting)}..."
            )
            await safe_edit(cq, text, kb_casino_predict(state))
            await cq.answer("✅ ثبت شد")
            return
        await _finish_duel(cq, state)
        return

    if u.id != int(state["host_id"]):
        await cq.answer("🚫 این میز مال یکی دیگه‌ست!", show_alert=True)
        return
    state["pred"] = pred
    state["pred_label"] = label
    await _finish_bot_game(cq, state, pred, exact=False)


@dp.callback_query(F.data == "help_casino")
async def cb_help_casino(cq: CallbackQuery) -> None:
    await safe_edit(cq, txt_help_casino(), kb_back("help_main"))
    await cq.answer()


async def casino_handle_reply(message: Message, state: Dict[str, Any],
                              target: Message) -> bool:
    """
    پردازش ریپلای‌های قمار (مبلغ دلخواه / نتیجه دقیق).
    True اگر پیام مصرف شد.
    """
    u = message.from_user
    if u is None:
        return False
    step = state.get("step")
    text = (message.text or "").strip()

    if step == "await_amount_reply":
        if u.id != int(state["host_id"]):
            return False
        amount = parse_int(text)
        user = await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
        if not amount or amount <= 0:
            await target.edit_text(
                txt_casino_amount(state, user) + f"\n{SEP}\n❌ عدد نامعتبر — دوباره ریپلای کن.",
                reply_markup=kb_casino_amount())
        elif num(user, "money") < amount:
            await target.edit_text(
                txt_casino_amount(state, user) + f"\n{SEP}\n❌ پول کافی نداری ({money(amount)})",
                reply_markup=kb_casino_amount())
        else:
            state["amount"] = amount
            state["step"] = "choose_opponent"
            await target.edit_text(txt_casino_opponent(state),
                                   reply_markup=kb_casino_opponent())
        return True

    if step == "await_exact_reply":
        if u.id != int(state.get("exact_for") or state["host_id"]):
            return False
        m = _EXACT_RE.match(pn_back(text))
        if not m:
            await target.edit_text(
                txt_casino_predict(state) + f"\n{SEP}\n❌ فرمت اشتباه — مثل <code>۲-۱</code> بفرست.",
                reply_markup=kb_casino_predict(state))
            return True
        g1, g2 = int(m.group(1)), int(m.group(2))
        state["exact"] = (g1, g2)
        label = f"نتیجه دقیق {pn(g1)}-{pn(g2)}"
        if state.get("mode") == "duel":
            state.setdefault("preds", {})[u.id] = {
                "pred": gm_outcome(g1, g2), "label": label}
            need = {int(state["host_id"]), int(state["guest_id"])}
            if not need <= set(state["preds"].keys()):
                await target.edit_text(
                    txt_casino_predict(state) + f"\n{SEP}\n✅ {esc(label)} ثبت شد.\n⏳ منتظر حریف...",
                    reply_markup=kb_casino_predict(state))
                return True
            # تسویه دوئل از مسیر پیام (بدون کالبک)
            await _duel_settle_from_message(target, state)
            return True

        state["pred_label"] = label
        amount = int(state["amount"])
        user = await asyncio.to_thread(get_user, u.id)
        if num(user, "money") < amount:
            await target.edit_text(f"❌ پول کافی نداری ({money(amount)})",
                                   reply_markup=kb_casino_again())
            return True
        await target.edit_text(txt_casino_playing())
        await asyncio.sleep(GAMBLE_DELAY)
        real1, real2 = random.randint(0, 5), random.randint(0, 5)
        won = (g1, g2) == (real1, real2)
        res = await asyncio.to_thread(gamble_settle, u.id, amount, won, ODDS_EXACT)
        name = display_name(u.full_name, u.username, u.id)
        state["step"] = "result"
        await target.edit_text(
            txt_casino_result_bot(name, state, real1, real2, res, True),
            reply_markup=kb_casino_again())
        return True

    return False


async def _duel_settle_from_message(target: Message, state: Dict[str, Any]) -> None:
    """تسویه دوئل وقتی آخرین پیش‌بینی با ریپلای ثبت شده."""
    amount = int(state["amount"])
    host_id, guest_id = int(state["host_id"]), int(state["guest_id"])
    preds = state["preds"]
    await target.edit_text(txt_casino_playing())
    await asyncio.sleep(GAMBLE_DELAY)
    t1s, t2s = roll_score(), roll_score()
    outcome = gm_outcome(t1s, t2s)
    host_ok = preds.get(host_id, {}).get("pred") == outcome
    guest_ok = preds.get(guest_id, {}).get("pred") == outcome
    if host_ok == guest_ok:
        verdict, prize, = "🤝 <b>مساوی!</b> شرط‌ها برگشت.", 0
        await asyncio.to_thread(set_fields, host_id, last_gamble=iso())
        await asyncio.to_thread(set_fields, guest_id, last_gamble=iso())
    else:
        winner_id = host_id if host_ok else guest_id
        loser_id = guest_id if host_ok else host_id
        winner_name = state["host_name"] if host_ok else state["guest_name"]
        await asyncio.to_thread(add_money, winner_id, amount)
        await asyncio.to_thread(add_money, loser_id, -amount)
        await asyncio.to_thread(set_fields, host_id, last_gamble=iso())
        await asyncio.to_thread(set_fields, guest_id, last_gamble=iso())
        verdict, prize = f"🏆 برنده: <b>{esc(winner_name)}</b>", amount
    t1, t2 = gm_teams(state)
    state["step"] = "result"
    await target.edit_text("\n".join([
        "🏁 <b>نتیجه دوئل</b>",
        SEP,
        f"{GAME_TITLES.get(state['game'], '🎲')} {esc(t1)} <b>{pn(t1s)}</b> - <b>{pn(t2s)}</b> {esc(t2)}",
        f"🎮 {esc(state['host_name'])} ⚔️ {esc(state['guest_name'])}",
        SEP,
        verdict,
        (f"💰 جایزه: <b>{money(prize)}</b>" if prize else "💵 پول‌ها برگشت به جیب."),
        SEP,
        f"⏱️ قمار بعدی: {cooldown_fmt(GAMBLE_COOLDOWN)}",
    ]), reply_markup=kb_casino_again())


# ▓▓ بخش ۱۵ — پایان ▓▓
# ══════════════════════════════════════════════════════════════════════════
# ▓▓ بخش ۱۶ — حساب و رتبه‌بندی (ACCOUNT & TOP) ▓▓  [شروع]
#    دستورات: حسابم | رتبه        کالبک: acc / top
# ══════════════════════════════════════════════════════════════════════════

TOP_LIMIT: int = 10


def txt_account(user: Dict[str, Any]) -> str:
    lvl = num(user, "level_index")
    robs = num(user, "rob_count")
    uname = user.get("username")
    lines = [
        "👤 <b>حساب شما</b>",
        SEP,
        f"🆔 <code>{pn(user.get('user_id', 0))}</code>",
        f"📛 {('@' + esc(uname)) if uname else 'ندارد'}",
        SEP,
        f"🏆 {level_name(lvl)}",
        f"💵 جیب: <b>{money(num(user, 'money'))}</b>",
    ]
    if has("wallet_panel_text") and num(user, "has_wallet") > 0:
        lines.append(f"👝 کیف پول: <b>{money(num(user, 'wallet_balance'))}</b>")
    lines.append(f"🔫 دزدی: <b>{pn(robs)}</b>")

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

    # وضعیت زندان / خطر
    if has("jail_left"):
        jl = jail_left(user)
        if jl > 0:
            lines += ["", f"⛓ <b>زندانی</b> — {duration_fa(jl)} مانده"]
        else:
            lines += ["", f"🚔 خطر دستگیری: {pct(arrest_chance(user))}"]

    # دارایی‌ها
    assets: List[str] = []
    if has("weapon_panel_text") and num(user, "has_ak") > 0:
        assets.append(f"🔫 AK سطح {pn(max(1, num(user, 'ak_level', 1)))}")
    if has("dossier_panel_text") and num(user, "has_dossier") > 0:
        assets.append("📁 پرونده")
    if has("minion_panel_text") and num(user, "has_minion") > 0:
        assets.append(f"🧑‍🦱 {esc(user.get('minion_name') or 'نوچه')}")
    if has("use_fake_doc") and num(user, "fake_docs") > 0:
        assets.append(f"📜 ×{pn(num(user, 'fake_docs'))}")
    if assets:
        lines.append("🎒 " + " | ".join(assets))
    lines.append(SEP)
    return "\n".join(lines)


def kb_account(user: Dict[str, Any]) -> InlineKeyboardMarkup:
    body: List[List[InlineKeyboardButton]] = []
    row1: List[InlineKeyboardButton] = []
    if has("wallet_panel_text"):
        row1.append(btn("👝 کیف پول", callback_data="wallet", style=STYLE_SUCCESS))
    if has("shop_text"):
        row1.append(btn("🛒 فروشگاه", callback_data="shop", style=STYLE_PRIMARY))
    if row1:
        body.append(row1)
    row2: List[InlineKeyboardButton] = []
    if has("weapon_panel_text") and num(user, "has_ak") > 0:
        row2.append(btn("🔫 اسلحه", callback_data="weapon", style=STYLE_DANGER))
    if has("minion_panel_text") and num(user, "has_minion") > 0:
        row2.append(btn("🧑‍🦱 نوچه", callback_data="minion", style=STYLE_PRIMARY))
    if row2:
        body.append(row2)
    body.append([
        btn("📊 رتبه‌بندی", callback_data="top", style=STYLE_PRIMARY),
        *kb_back_row("start_back"),
    ])
    return rows(*body)


def txt_top() -> str:
    players = top_players(TOP_LIMIT)
    if not players:
        return "\n".join(["👑 <b>بهترین بازیکنان</b>", SEP, "هنوز کسی دزدی نکرده! 🤷‍♂️"])
    medals = ["🥇", "🥈", "🥉"]
    lines = ["👑 <b>بهترین بازیکنان</b>", SEP]
    for i, p in enumerate(players):
        tag = medals[i] if i < 3 else f"#{pn(i + 1)}"
        nm = display_name(p.get("full_name"), p.get("username"), int(p.get("user_id", 0)))
        total = num(p, "money") + num(p, "wallet_balance")
        lines.append(f"{tag} {esc(nm)} ─ 💰 {money(total)} | {level_name(num(p, 'level_index'))}")
    lines.append(SEP)
    return "\n".join(lines)


def txt_help_account() -> str:
    return "\n".join([
        "👤 <b>راهنمای حساب</b>",
        SEP,
        "دستور: <code>حسابم</code>",
        "",
        "نمایش می‌ده:",
        "  🆔 آیدی عددی",
        "  🏆 سطح فعلی",
        "  💵 جیب و 👝 کیف پول",
        "  🔫 تعداد دزدی",
        "  📊 نوار پیشرفت",
        "  🎒 دارایی‌ها",
        SEP,
        "📍 در گروه و خصوصی کار می‌کنه.",
    ])


@dp.message(F.text.regexp(re.compile(r"^\s*(?:حسابم|حساب\s*من|/account)\s*$")))
async def h_account(message: Message) -> None:
    u = message.from_user
    if u is None:
        return
    user = await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
    if has("release_if_done"):
        user = await asyncio.to_thread(release_if_done, user)
    await message.reply(txt_account(user), reply_markup=kb_account(user))


@dp.message(F.text.regexp(re.compile(r"^\s*(?:رتبه|رتبه\s*بندی|رتبه‌بندی|/top)\s*$")))
async def h_top(message: Message) -> None:
    text = await asyncio.to_thread(txt_top)
    await message.reply(text, reply_markup=kb_back("start_back"))


@dp.callback_query(F.data == "acc")
async def cb_acc(cq: CallbackQuery) -> None:
    u = cq.from_user
    user = await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
    if has("release_if_done"):
        user = await asyncio.to_thread(release_if_done, user)
    await safe_edit(cq, txt_account(user), kb_account(user))
    await cq.answer()


@dp.callback_query(F.data == "top")
async def cb_top(cq: CallbackQuery) -> None:
    text = await asyncio.to_thread(txt_top)
    await safe_edit(cq, text, kb_back("start_back"))
    await cq.answer()


@dp.callback_query(F.data == "help_account")
async def cb_help_account(cq: CallbackQuery) -> None:
    await safe_edit(cq, txt_help_account(), kb_back("help_main"))
    await cq.answer()


# ▓▓ بخش ۱۶ — پایان ▓▓


# ══════════════════════════════════════════════════════════════════════════
# ▓▓ بخش ۱۷ — راهنما (HELP) ▓▓  [شروع]
#    دستور: راهنما دزدی   |   منو فقط بخش‌های موجود را نشان می‌دهد
# ══════════════════════════════════════════════════════════════════════════

# (عنوان دکمه, callback, تابعی که باید موجود باشد, استایل)
HELP_PAGES: List[Tuple[str, str, str, str]] = [
    ("💰 راهنمای دزدی", "help_rob", "txt_help_rob", STYLE_SUCCESS),
    ("👤 راهنمای حساب", "help_account", "txt_help_account", STYLE_PRIMARY),
    ("📈 سیستم سطح‌بندی", "help_lvl", "txt_help_levels", STYLE_PRIMARY),
    ("⏱️ زمان انتظار", "help_wait", "txt_help_wait", STYLE_PRIMARY),
    ("🚔 پلیس و زندان", "help_jail", "txt_help_jail", STYLE_DANGER),
    ("🛒 فروشگاه", "help_shop", "txt_help_shop", STYLE_SUCCESS),
    ("🔫 اسلحه", "help_weapon", "txt_help_weapon", STYLE_DANGER),
    ("👝 کیف پول", "help_wallet", "txt_help_wallet", STYLE_SUCCESS),
    ("📁 پرونده جعلی", "help_dossier", "txt_help_dossier", STYLE_PRIMARY),
    ("🧑‍🦱 نوچه", "help_minion", "txt_help_minion", STYLE_PRIMARY),
    ("📜 سند جعلی", "help_doc", "txt_help_doc", STYLE_DANGER),
    ("🎰 قمارخونه", "help_casino", "txt_help_casino", STYLE_SUCCESS),
]


def txt_help_main() -> str:
    return "\n".join([
        "🎭 <b>منوی راهنما</b>",
        SEP,
        "یکی از بخش‌ها رو انتخاب کن 👇",
    ])


def kb_help_menu() -> InlineKeyboardMarkup:
    available = [(t, cb, st) for t, cb, fn, st in HELP_PAGES if has(fn)]
    body: List[List[InlineKeyboardButton]] = []
    for i in range(0, len(available), 2):
        body.append([btn(t, callback_data=cb, style=st) for t, cb, st in available[i:i + 2]])
    body.append(kb_back_row("start_back"))
    return rows(*body)


def txt_help_levels() -> str:
    body = "\n".join(
        f"{pn(i)}. {LEVELS[i]} — آستانه {pn(get_required_robs(i - 1) if i else 0)}"
        for i in range(len(LEVELS))
    )
    return "\n".join([
        "📈 <b>سیستم سطح‌بندی</b>",
        SEP,
        body,
        SEP,
        "🎁 هر ارتقا = پاداش سکه!",
    ])


def txt_help_wait() -> str:
    lines = [
        "⏱️ <b>زمان انتظار</b>",
        SEP,
        f"🔫 دزدی: <b>{pn(3)} دقیقه و {pn(15)} ثانیه</b> ({pn(ROB_COOLDOWN)} ثانیه)",
    ]
    if has("txt_help_casino"):
        lines.append(f"🎰 قمار: <b>{cooldown_fmt(GAMBLE_COOLDOWN)}</b> دقیقه")
    if has("minion_panel_text"):
        lines.append(f"🧑‍🦱 نوچه: هر <b>{duration_fa(MINION_CYCLE)}</b>")
    if has("txt_help_jail"):
        lines.append(f"⛓ حبس: {pn(JAIL_MIN_MINUTES)} دقیقه تا {pn(JAIL_MAX_MINUTES // 60)} ساعت")
    lines += [SEP, "زودتر بزنی ⇒ پیام «صبر کن رفیق!» می‌گیری."]
    return "\n".join(lines)


@dp.message(F.text.regexp(re.compile(r"^\s*(?:راهنما\s*دزدی|راهنما|/help)\s*$")))
async def h_help(message: Message) -> None:
    await message.reply(txt_help_main(), reply_markup=kb_help_menu())


@dp.callback_query(F.data == "help_main")
async def cb_help_main(cq: CallbackQuery) -> None:
    await safe_edit(cq, txt_help_main(), kb_help_menu())
    await cq.answer()


@dp.callback_query(F.data == "help_lvl")
async def cb_help_lvl(cq: CallbackQuery) -> None:
    await safe_edit(cq, txt_help_levels(), kb_back("help_main"))
    await cq.answer()


@dp.callback_query(F.data == "help_wait")
async def cb_help_wait(cq: CallbackQuery) -> None:
    await safe_edit(cq, txt_help_wait(), kb_back("help_main"))
    await cq.answer()


# ▓▓ بخش ۱۷ — پایان ▓▓


# ══════════════════════════════════════════════════════════════════════════
# ▓▓ بخش ۱۸ — استارت، منوی اصلی و روتر ریپلای ▓▓  [شروع]
# ══════════════════════════════════════════════════════════════════════════

def add_group_url() -> str:
    return f"https://t.me/{BOT_USERNAME}?startgroup=true" if BOT_USERNAME else "https://t.me/"


def txt_start() -> str:
    cmds = ["💰 <code>دزدی</code>", "👤 <code>حسابم</code>"]
    if has("txt_jail_panel"):
        cmds.append("⛓ <code>زندان</code>")
    if has("shop_text"):
        cmds.append("🛒 <code>فروشگاه</code>")
    if has("txt_casino_home"):
        cmds.append("🎰 <code>قمارخونه</code>")
    extra: List[str] = []
    if has("weapon_panel_text"):
        extra.append("🔫 <code>اسلحه</code>")
    if has("wallet_panel_text"):
        extra.append("👝 <code>کیف پول</code>")
    if has("dossier_panel_text"):
        extra.append("📁 <code>پرونده</code>")
    if has("use_fake_doc"):
        extra.append("📜 <code>سند</code>")
    if has("minion_panel_text"):
        extra.append("🧑‍🦱 <code>نوچه</code>")

    lines = [
        "🎭 <b>مافیای خیابانی</b>",
        SEP,
        "سلام رفیق! به دنیای زیرزمینی خوش اومدی 🕶",
        "",
        "📌 <b>دستورات:</b>",
        " ─ ".join(cmds),
    ]
    if extra:
        lines.append(" ─ ".join(extra))
    lines += [
        SEP,
        "🚔 حواست باشه، پلیس بیکار نیست!",
        "⚡ ربات رو به گروهت اضافه کن و شروع کن!",
    ]
    return "\n".join(lines)


def kb_main() -> InlineKeyboardMarkup:
    body: List[List[InlineKeyboardButton]] = [
        [btn("➕ افزودن به گروه", url=add_group_url(), style=STYLE_SUCCESS, emoji_key="add")],
        [
            btn("👤 حسابم", callback_data="acc", style=STYLE_PRIMARY, emoji_key="acc"),
            btn("❓ راهنما دزدی", callback_data="help_main", style=STYLE_PRIMARY, emoji_key="help"),
        ],
    ]
    row: List[InlineKeyboardButton] = []
    if has("shop_text"):
        row.append(btn("🛒 فروشگاه", callback_data="shop", style=STYLE_SUCCESS))
    if has("txt_casino_home"):
        row.append(btn("🎰 قمارخونه", callback_data="gm_open", style=STYLE_PRIMARY))
    if row:
        body.append(row)
    row2: List[InlineKeyboardButton] = []
    if has("txt_jail_panel"):
        row2.append(btn("⛓ زندان", callback_data="jail", style=STYLE_DANGER))
    row2.append(btn("📊 رتبه‌بندی", callback_data="top", style=STYLE_DANGER, emoji_key="top"))
    body.append(row2)
    return rows(*body)


@dp.message(CommandStart())
async def h_start(message: Message) -> None:
    u = message.from_user
    if u:
        await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
    await message.answer(txt_start(), reply_markup=kb_main())


@dp.callback_query(F.data == "start_back")
async def cb_start_back(cq: CallbackQuery) -> None:
    await safe_edit(cq, txt_start(), kb_main())
    await cq.answer()


@dp.callback_query(F.data == "gm_open")
async def cb_gm_open(cq: CallbackQuery) -> None:
    """باز کردن قمارخونه از منوی اصلی (پیام جدید تا وضعیت مستقل بماند)."""
    u = cq.from_user
    if cq.message is None or not has("txt_casino_home"):
        await cq.answer("❌ قمارخونه فعال نیست.")
        return
    user = await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
    left = gamble_cd_left(user)
    if left > 0:
        await cq.answer(f"⏳ {cooldown_fmt(left)} تا قمار بعدی", show_alert=True)
        return
    sent = await cq.message.answer(txt_casino_home(), reply_markup=kb_casino_games())
    gamble_states[gm_key(sent)] = {
        "step": "choose_game",
        "host_id": u.id,
        "host_name": display_name(u.full_name, u.username, u.id),
        "amount": 0,
    }
    await cq.answer("🎰 قمارخونه باز شد")


# ── روتر پیام‌های آزاد: اسم نوچه + ریپلای‌های قمار ───────────────────

@dp.message(F.text)
async def h_free_text(message: Message) -> None:
    """
    آخرین هندلر متنی: فقط سه کار انجام می‌دهد و بقیه پیام‌ها را رد می‌کند.
      ۱) ریپلای روی پیام قمار (مبلغ دلخواه / نتیجه دقیق)
      ۲) ریپلای برای ثبت اسم نوچه
      ۳) صدا زدن نوچه با اسم دلخواهش
    """
    u = message.from_user
    text = (message.text or "").strip()
    if u is None or not text:
        return

    reply_to = message.reply_to_message

    # ۱) ریپلای‌های قمارخونه
    if reply_to is not None and has("casino_handle_reply"):
        state = gamble_states.get((message.chat.id, reply_to.message_id))
        if state is not None:
            done = await casino_handle_reply(message, state, reply_to)
            if done:
                try:
                    await message.delete()
                except Exception:  # noqa: BLE001
                    pass
                return

    # ۲) ثبت اسم نوچه (با ریپلای روی پنل نوچه)
    if has("minion_set_name") and reply_to is not None:
        user = await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
        if num(user, "minion_await_name") > 0:
            res = await asyncio.to_thread(minion_set_name, u.id, text)
            notes = {
                "ok": lambda: f"🏷 اسم نوچه شد: <b>{esc(res['name'])}</b>\n"
                              f"💬 از این به بعد با «{esc(res['name'])}» هم صداش می‌زنی.",
                "bad": lambda: "❌ اسم نامعتبر — ۲ تا ۱۸ حرف بدون کاراکتر خاص.",
                "reserved": lambda: "❌ این کلمه رزروه، یکی دیگه انتخاب کن.",
                "poor": lambda: f"❌ {money(MINION_NAME_PRICE)} لازمه.",
                "none": lambda: "❌ نوچه نداری.",
            }
            text_out, kb = minion_view(display_name(u.full_name, u.username, u.id),
                                       res["user"], notes.get(res["state"], lambda: "")())
            await message.reply(text_out, reply_markup=kb)
            return

    # ۳) صدا زدن نوچه با اسم دلخواه یا کلمه «نوچه»
    if has("minion_panel_text"):
        plain = text.lower()
        user = await asyncio.to_thread(get_user, u.id, u.full_name, u.username)
        nick = (user.get("minion_name") or "").strip().lower()
        if plain in ("نوچه", "/minion") or (nick and plain == nick):
            text_out, kb = minion_view(display_name(u.full_name, u.username, u.id), user)
            await message.reply(text_out, reply_markup=kb)
            return


@dp.callback_query()
async def cb_unknown(cq: CallbackQuery) -> None:
    await cq.answer("❔ نامشخص")


# ▓▓ بخش ۱۸ — پایان ▓▓


# ══════════════════════════════════════════════════════════════════════════
# ▓▓ بخش ۱۹ — اجرا (MAIN) ▓▓  [شروع]
# ══════════════════════════════════════════════════════════════════════════

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

    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        log.error("توکن تنظیم نشده! BOT_TOKEN را در فایل یا متغیر محیطی بگذار.")
        return

    init_db()
    log.info("در حال راه‌اندازی ربات مافیای خیابانی...")

    bot = Bot(
        token=BOT_TOKEN,
        session=build_session(),
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
        close_db()
        log.info("ربات خاموش شد. خداحافظ 👋")


# ▓▓ بخش ۱۹ — پایان ▓▓
# ══════════════════════════════════════════════════════════════════════════
# ▓▓ بخش ۲۰ — تست داخلی (SELFTEST) ▓▓  [شروع]
#    اجرا: python mafia_bot.py --selftest   (بدون شبکه و توکن)
# ══════════════════════════════════════════════════════════════════════════

def selftest() -> int:
    global DB_FILE, _conn
    fails: List[str] = []

    def chk(cond: bool, label: str) -> None:
        if not cond:
            fails.append(label)
        print(("  ✅ " if cond else "  ❌ ") + label)

    def clear_cd(uid: int) -> None:
        set_fields(uid, last_rob_time=None)

    def free_now(uid: int) -> None:
        set_fields(uid, jail_until=None, jail_total=0)

    print("── ۰۳ توابع کمکی ──")
    chk(pn("1234") == "۱۲۳۴", "pn")
    chk(pn_back("۱٬۲۳۴") == "1234", f"pn_back → {pn_back('۱٬۲۳۴')}")
    chk(parse_int("۵۰۰") == 500 and parse_int("abc") is None, "parse_int")
    chk(money(1500).startswith("۱٬۵۰۰"), f"money → {money(1500)}")
    chk(cooldown_fmt(195) == "۳:۱۵", f"cooldown_fmt → {cooldown_fmt(195)}")
    chk(duration_fa(4500) == "۱ ساعت و ۱۵ دقیقه", f"duration_fa → {duration_fa(4500)}")
    chk(len(progress_bar(3, 8)) == 8 and progress_bar(0, 5) == "░" * 8, "progress_bar")
    chk(pct(0.35) == "۳۵٪", f"pct → {pct(0.35)}")
    chk(_opt("تابع_ناموجود", default="fallback") == "fallback", "_opt fallback (ماژولار)")
    chk(has("do_rob") and not has("تابع_ناموجود"), "has()")

    print("── ۰۶ سطح‌بندی ──")
    thresholds = [get_required_robs(i) for i in range(15)]
    print("  ℹ️  آستانه‌ها:", thresholds)
    chk(thresholds[:6] == [15, 22, 33, 50, 75, 113], "فرمول int(15×1.5^n)")
    chk(len(LEVELS) == 15 and level_name(99) == LEVELS[14], "۱۵ سطح")
    chk(progress_info(14, 9999) is None, "سطح آخر → None")

    print("── ۰۸ دزدی ──")
    chk(len(SCENARIOS) == 20, f"۲۰ سناریو (={len(SCENARIOS)})")
    chk(sum(_STEAL_WEIGHTS) == 100, "جمع درصدها ۱۰۰")
    rolls = [roll_steal() for _ in range(5000)]
    chk(min(rolls) >= 9 and max(rolls) <= 500, f"roll_steal [{min(rolls)},{max(rolls)}]")

    print("── دیتابیس + مهاجرت ──")
    DB_FILE = "mafia_selftest.db"
    for ext in ("", "-wal", "-shm"):
        if os.path.exists(DB_FILE + ext):
            os.remove(DB_FILE + ext)
    _conn = None
    # شبیه‌سازی دیتابیس قدیمی (فقط ستون‌های پایه) برای تست ALTER TABLE
    conn0 = _connect()
    conn0.execute("CREATE TABLE users (user_id INTEGER PRIMARY KEY, username TEXT,"
                  " full_name TEXT, money INTEGER DEFAULT 0, rob_count INTEGER DEFAULT 0,"
                  " level_index INTEGER DEFAULT 0, last_rob_time TIMESTAMP)")
    conn0.execute("INSERT INTO users (user_id, full_name, money, rob_count) VALUES (7, 'قدیمی', 1234, 9)")
    conn0.commit()
    init_db()
    cols = {r["name"] for r in _connect().execute("PRAGMA table_info(users)").fetchall()}
    chk(set(all_columns().keys()) <= cols, f"مهاجرت خودکار ({len(cols)} ستون)")
    old = get_user(7)
    chk(num(old, "money") == 1234 and num(old, "rob_count") == 9, "داده کاربر قدیمی حفظ شد")
    chk(num(old, "has_ak") == 0 and num(old, "fake_docs") == 0, "ستون‌های جدید پیش‌فرض صفر")

    UID = 101
    u = get_user(UID, "علی مافیا", "ali")
    chk(num(u, "money") == 0, "کاربر جدید")
    chk(spend(UID, 10) is False, "spend بدون پول → False")
    add_money(UID, 5000)
    chk(spend(UID, 1000) and num(get_user(UID), "money") == 4000, "spend اتمیک")

    print("── ۰۷ پلیس و زندان (بدون سقف ۱۵) ──")
    chk(arrest_chance({"robs_since_arrest": 0}) == 0.0, "دزدی‌های اول امن (grace)")
    c_low = arrest_chance({"robs_since_arrest": 5})
    c_high = arrest_chance({"robs_since_arrest": 60})
    chk(0 < c_low < c_high <= ARREST_MAX_CHANCE, f"شانس صعودی {c_low:.3f} → {c_high:.3f}")
    chk(c_high < 1.0, f"هیچ‌وقت دستگیری قطعی نیست (سقف {pct(ARREST_MAX_CHANCE)})")
    b_few = bail_price({"robs_since_arrest": 2, "loot_since_arrest": 500, "level_index": 0}, 600)
    b_many = bail_price({"robs_since_arrest": 40, "loot_since_arrest": 9000, "level_index": 0}, 600)
    chk(b_many > b_few, f"وثیقه بر اساس دزدی: {b_few} → {b_many}")
    chk(JAIL_MIN_MINUTES * 60 <= jail_duration() <= JAIL_MAX_MINUTES * 60, "بازه حبس")

    # دستگیری واقعی
    set_fields(UID, money=9000, robs_since_arrest=50, loot_since_arrest=8000)
    jres = send_to_jail(UID, get_user(UID))
    chk(jres["burned"] == 9000 // POCKET_LOSS_DIVISOR, f"۱/۳ جیب سوخت = {jres['burned']}")
    chk(jail_left(jres["user"]) > 0, "زمان حبس ثبت شد")
    clear_cd(UID)
    blocked = do_rob(UID, "علی", "ali")
    chk(blocked["state"] == "jailed", f"دزدی در زندان مسدود → {blocked['state']}")
    poor = do_bail(UID)
    chk(poor["state"] in ("poor", "paid"), f"وثیقه → {poor['state']}")
    set_fields(UID, money=999999)
    paid = do_bail(UID)
    chk(paid["state"] == "paid" and jail_left(paid["user"]) == 0, "آزادی با وثیقه")
    chk(num(paid["user"], "robs_since_arrest") == 0, "شمارنده بعد از وثیقه صفر شد")
    set_fields(UID, jail_until=iso(now_ts() - 5), jail_total=600)
    chk(release_if_done(get_user(UID)).get("jail_until") is None, "آزادی خودکار")

    print("── ۰۹ کیف پول ──")
    set_fields(UID, money=8000, has_wallet=0, wallet_balance=0, wallet_level=0)
    chk(wallet_deposit(UID)["state"] == "no_wallet", "بدون کیف پول → واریز نمی‌شه")
    set_fields(UID, has_wallet=1)
    cap0 = wallet_cap(get_user(UID))
    dep = wallet_deposit(UID)
    chk(dep["state"] == "ok" and dep["moved"] == cap0,
        f"واریز تا سقف ظرفیت = {dep.get('moved')} (ظرفیت {cap0})")
    chk(num(dep["user"], "money") == 8000 - cap0, "بقیه پول در جیب موند")
    # پول کیف در دستگیری امن است، پول جیب می‌سوزد
    set_fields(UID, money=0)
    jres2 = send_to_jail(UID, get_user(UID))
    chk(jres2["burned"] == 0 and num(jres2["user"], "wallet_balance") == cap0,
        f"کیف پول از پلیس امن موند ({cap0})")
    free_now(UID)
    wd = wallet_withdraw(UID)
    chk(wd["state"] == "ok" and num(wd["user"], "money") == cap0, "برداشت از کیف به جیب")
    chk(num(wd["user"], "wallet_balance") == 0, "کیف خالی شد")
    set_fields(UID, money=50000)
    up = wallet_upgrade(UID)
    chk(up["state"] == "ok" and up["cap"] == WALLET_BASE_CAP + WALLET_CAP_STEP, "ارتقای ظرفیت")

    print("── ۱۰ اسلحه AK-۴۷ ──")
    chk(ak_max_uses(1) == 3, f"سطح ۱ = {ak_max_uses(1)} دزدی امن")
    chk(ak_upgrade_price(1) == AK_UPGRADE_BASE, f"ارتقا از {AK_UPGRADE_BASE}")
    chk(ak_upgrade_price(3) > ak_upgrade_price(2) > ak_upgrade_price(1), "رشد عادلانه ارتقا")
    set_fields(UID, money=99999, has_ak=1, ak_level=1, ak_uses=3, ak_health=100,
               ak_ammo=30, ak_broken=0)
    protected = 0
    for _ in range(3):
        w = weapon_consume(UID, get_user(UID))
        if w.get("protected"):
            protected += 1
    chk(protected == 3, f"۳ دزدی امن پشت‌سرهم = {protected}")
    after = get_user(UID)
    chk(num(after, "ak_uses") == 0, "خشاب خالی شد")
    w4 = weapon_consume(UID, get_user(UID))
    chk(not w4.get("protected"), "بعد از خشاب: پوشش نداره (بازی عادی)")
    fix = weapon_repair(UID)
    chk(fix["state"] == "ok" and num(fix["user"], "ak_uses") == 3, f"تعمیر ({AK_REPAIR_PRICE} ثابت)")
    upg = weapon_upgrade(UID)
    chk(upg["state"] == "ok" and num(upg["user"], "ak_uses") == ak_max_uses(2), "ارتقای اسلحه")
    # اسلحه ⇒ دزدی بدون دستگیری
    set_fields(UID, robs_since_arrest=99, ak_uses=4, ak_broken=0, ak_health=100)
    clear_cd(UID); free_now(UID)
    safe = do_rob(UID, "علی", "ali")
    chk(safe["state"] == "ok" and safe["weapon"].get("protected"), "AK جلوی دستگیری رو گرفت")

    print("── ۱۱ پرونده جعلی ──")
    set_fields(UID, money=99999, has_dossier=1, dos_sign=0, dos_print=0, dos_photo=0, dos_ready=0)
    chk(dossier_complete(get_user(UID)) is False, "پرونده ناقص")
    chk(dos_part_price(0) == 0, "تیر اول رایگان")
    for part in ("sign", "print", "photo"):
        r = dossier_upgrade(UID, part)
        chk(r["state"] == "ok", f"تکمیل {part}")
    duser = get_user(UID)
    chk(dossier_complete(duser), "پرونده کامل شد")
    chk(dossier_safety(duser) > 0, f"کاهش ظن پلیس = {pct(dossier_safety(duser))}")
    chk(arrest_chance({**duser, "robs_since_arrest": 10}) <
        arrest_chance({"robs_since_arrest": 10}), "پرونده ظن پلیس رو کم کرد")
    set_fields(UID, dos_ready=1, ak_uses=0, ak_broken=1, robs_since_arrest=0)
    clear_cd(UID); free_now(UID)
    bank = do_rob(UID, "علی", "ali")
    chk(bank["state"] == "ok" and bank["bonus"] > 0, f"بانک‌زنی با پاداش {bank.get('bonus')}")
    chk(num(get_user(UID), "dos_ready") == 0, "پرونده مصرف شد")

    print("── ۱۲ نوچه ──")
    set_fields(UID, money=99999, level_index=0, has_minion=0)
    lvl_block = shop_buy(UID, "minion")
    chk(lvl_block["state"] == "level", f"سطح کم → {lvl_block['state']}")
    set_fields(UID, level_index=MINION_MIN_LEVEL)
    buy_m = shop_buy(UID, "minion")
    chk(buy_m["state"] == "ok" and num(buy_m["user"], "has_minion") == 1, "استخدام نوچه سطح ۳+")
    got = minion_collect(UID)
    chk(got["state"] == "ok" and got["amount"] > 0, f"غنیمت نوچه = {got.get('amount')}")
    chk(minion_collect(UID)["state"] == "wait", "چرخه انتظار نوچه")
    nm_bad = minion_set_name(UID, "دزدی")
    chk(nm_bad["state"] == "reserved", "اسم رزرو رد شد")
    nm = minion_set_name(UID, "شکور")
    chk(nm["state"] == "ok" and nm["user"]["minion_name"] == "شکور", "ثبت اسم نوچه (۷۰ سکه)")
    mup = minion_upgrade(UID)
    chk(mup["state"] == "ok" and minion_cycle(mup["user"]) < MINION_CYCLE, "ارتقا → چرخه سریع‌تر")
    set_fields(UID, jail_until=iso(now_ts() + 600), jail_total=600, minion_last=None)
    chk(minion_collect(UID)["state"] == "jailed", "نوچه در زندان کار نمی‌کنه")
    free_now(UID)

    print("── ۱۳ سند جعلی ──")
    set_fields(UID, money=99999, fake_docs=0)
    for i in range(DOC_MAX_HOLD):
        chk(shop_buy(UID, "doc")["state"] == "ok", f"خرید سند {pn(i + 1)}")
    chk(num(get_user(UID), "fake_docs") == DOC_MAX_HOLD, f"سقف {DOC_MAX_HOLD} سند")
    chk(shop_buy(UID, "doc")["state"] == "full", "سند چهارم رد شد")
    chk(use_fake_doc(UID)["state"] == "free", "بیرون زندان سند مصرف نمی‌شه")
    outcomes = {"escaped": 0, "caught": 0}
    for _ in range(40):
        set_fields(UID, fake_docs=1, jail_until=iso(now_ts() + 1800), jail_total=1800)
        r = use_fake_doc(UID)
        outcomes[r["state"]] = outcomes.get(r["state"], 0) + 1
        if r["state"] == "caught":
            chk_extra = jail_left(r["user"]) > 1800
        free_now(UID)
    chk(outcomes["escaped"] > 0 and outcomes["caught"] > 0,
        f"فرار {outcomes['escaped']} / لو رفتن {outcomes['caught']}")

    print("── ۱۴ فروشگاه ──")
    chk(len(SHOP_ITEMS) == 5 and all(it.available() for it in SHOP_ITEMS), "۵ کالا فعال")
    set_fields(UID, money=0, has_ak=0)
    chk(shop_buy(UID, "ak")["state"] == "poor", "خرید بدون پول رد شد")
    set_fields(UID, money=AK_PRICE)
    bak = shop_buy(UID, "ak")
    chk(bak["state"] == "ok" and num(bak["user"], "ak_uses") == AK_USES_BASE, "خرید AK با خشاب پر")
    chk(shop_buy(UID, "ak")["state"] == "owned", "خرید تکراری رد شد")
    chk(shop_buy(UID, "چیز_نامعتبر")["state"] == "bad", "کالای نامعتبر")

    print("── ۱۵ قمارخونه ──")
    chk(len(GAMES) == 6 and len(MATCHES) == 5, "۶ بازی + ۵ مسابقه")
    chk(gm_outcome(5, 3) == "w1" and gm_outcome(1, 4) == "w2" and gm_outcome(2, 2) == "draw",
        "gm_outcome")
    chk(bool(_EXACT_RE.match(pn_back("۲-۱"))) and bool(_EXACT_RE.match("3:2")), "regex نتیجه دقیق")
    set_fields(UID, money=10000, last_gamble=None)
    win = gamble_settle(UID, 1000, True, ODDS_NORMAL)
    chk(win["delta"] == int(1000 * ODDS_NORMAL) - 1000, f"سود برد = {win['delta']}")
    chk(gamble_cd_left(win["user"]) > 290, "کول‌داون قمار فعال شد")
    lose = gamble_settle(UID, 500, False, ODDS_NORMAL)
    chk(lose["delta"] == -500, "ضرر باخت")
    exact_win = gamble_settle(UID, 100, True, ODDS_EXACT)
    chk(exact_win["delta"] == int(100 * ODDS_EXACT) - 100, f"سود نتیجه دقیق = {exact_win['delta']}")

    print("── دکمه‌ها (استایل رنگی در همه پنل‌ها) ──")
    demo = get_user(UID)
    keyboards = {
        "main": kb_main(), "help": kb_help_menu(), "back": kb_back(),
        "jail_in": kb_jail(demo, 600, 1700), "jail_out": kb_jail(demo, 0, 0),
        "wallet": kb_wallet(demo), "weapon": kb_weapon(demo),
        "dossier": kb_dossier(demo), "minion": kb_minion(demo),
        "doc": kb_doc(demo), "shop": kb_shop(demo),
        "casino_games": kb_casino_games(), "casino_amount": kb_casino_amount(),
        "casino_opp": kb_casino_opponent(), "casino_pred": kb_casino_predict({
            "game": "foot", "amount": 100, "team1": "الف", "team2": "ب"}),
        "casino_lobby": kb_casino_lobby(), "casino_again": kb_casino_again(),
        "account": kb_account(demo), "rob_after": kb_rob_after(demo),
    }
    styled = plain = 0
    for label, kb in keyboards.items():
        for row in kb.inline_keyboard:
            for b in row:
                d = b.model_dump(exclude_none=True)
                if not (d.get("callback_data") or d.get("url")):
                    fails.append(f"{label}: دکمه بدون اکشن ({d.get('text')})")
                st = d.get("style")
                if st is None:
                    plain += 1
                elif st in VALID_STYLES:
                    styled += 1
                else:
                    fails.append(f"{label}: style نامعتبر {st}")
    chk(plain == 0, f"همه دکمه‌ها رنگی‌اند (رنگی={styled}, بی‌رنگ={plain})")
    chk(len(keyboards) >= 19, f"{len(keyboards)} کیبورد بررسی شد")

    print("── متن‌ها (اعداد فارسی + طول مجاز) ──")
    set_fields(UID, money=7654, wallet_balance=3200, jail_until=iso(now_ts() + 4200),
               jail_total=5400, fake_docs=2, robs_since_arrest=12, loot_since_arrest=4300)
    ju = get_user(UID)
    jl = jail_left(ju)
    st = {"user": ju, "left": jl, "price": bail_price(ju, jl)}
    gstate = {"game": "foot", "amount": 500, "team1": "پرسپولیس", "team2": "استقلال",
              "host_id": UID, "host_name": "علی", "guest_name": "رضا",
              "pred_label": "برد پرسپولیس"}
    samples: Dict[str, str] = {
        "start": txt_start(),
        "group_only": txt_group_only(),
        "cooldown": txt_cooldown(74),
        "account": txt_account(ju),
        "top": txt_top(),
        "help_main": txt_help_main(),
        "help_rob": txt_help_rob(),
        "help_account": txt_help_account(),
        "help_levels": txt_help_levels(),
        "help_wait": txt_help_wait(),
        "help_jail": txt_help_jail(),
        "help_shop": txt_help_shop(),
        "help_weapon": txt_help_weapon(),
        "help_wallet": txt_help_wallet(),
        "help_dossier": txt_help_dossier(),
        "help_minion": txt_help_minion(),
        "help_doc": txt_help_doc(),
        "help_casino": txt_help_casino(),
        "jail_panel": jail_view("علی", st)[0],
        "arrested": txt_arrested("علی", ARREST_SCENARIOS[0],
                                 {"user": ju, "left": 5400, "burned": 1200, "saved": 3200}),
        "bail_paid": bail_view("علی", {"state": "paid", "price": 3400, "user": ju})[0],
        "bail_poor": bail_view("علی", {"state": "poor", "price": 99999, "need": 50000,
                                       "left": jl, "user": ju})[0],
        "wallet": wallet_panel_text("علی", ju),
        "weapon": weapon_panel_text("علی", ju),
        "dossier": dossier_panel_text("علی", ju),
        "minion": minion_panel_text("علی", ju),
        "doc": doc_panel_text("علی", ju),
        "shop": shop_text("علی", ju),
        "casino_home": txt_casino_home(),
        "casino_amount": txt_casino_amount(gstate, ju),
        "casino_opp": txt_casino_opponent(gstate),
        "casino_predict": txt_casino_predict(gstate),
        "casino_lobby": txt_casino_lobby(gstate),
        "casino_playing": txt_casino_playing(),
        "casino_result": txt_casino_result_bot("علی", gstate, 3, 1,
                                               {"won": True, "delta": 900, "user": ju}, False),
        "rob": txt_rob("علی", {"user": ju, "amount": 430, "bonus": 90,
                               "scenario": SCENARIOS[0], "comment": steal_comment(430),
                               "upgraded": ("🃏 پدرخوانده", 15000),
                               "weapon": {"protected": True, "left": 2}}),
    }
    for key, val in samples.items():
        chk(bool(val) and len(val) < 4000, f"{key} ({len(val)} کاراکتر)")
        stripped = re.sub(r"<[^>]+>", "", val)
        chk(not re.search(r"[0-9]", stripped), f"{key}: اعداد فارسی")
    chk(len(samples) >= 36, f"{len(samples)} متن بررسی شد")

    print("\n── نمونه خروجی ──\n")
    for key in ("start", "rob", "arrested", "jail_panel", "shop", "weapon",
                "wallet", "dossier", "minion", "doc", "casino_home", "help_jail"):
        print(re.sub(r"</?[^>]+>", "", samples[key]))
        print("- - - - - - - - - - - - - -")

    close_db()
    for ext in ("", "-wal", "-shm"):
        p = "mafia_selftest.db" + ext
        if os.path.exists(p):
            os.remove(p)

    print(f"\n{'🎉 همه تست‌ها موفق' if not fails else '❌ خطاها (' + str(len(fails)) + '):'}")
    for f in fails:
        print("   •", f)
    return 0 if not fails else 1


# ▓▓ بخش ۲۰ — پایان ▓▓


# ══════════════════════════════════════════════════════════════════════════
# 🚀 نقطه ورود
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("توقف دستی توسط کاربر.")
