import asyncio
import datetime
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

import discord
import psutil
import websockets
from discord import app_commands
from discord.ext import commands

# ==============================================================================
# 🔑 CONFIGURATION / CẤU HÌNH BOT
# ==============================================================================
# Cách đặt token (chọn 1) / Ways to set your token (pick one):
#   1. Chỉ cần mở file này — bot sẽ hỏi token và lưu vào token.txt giúp bạn
#      Just run this file — the bot asks for your token and can save it to token.txt for you
#   2. Dán trực tiếp vào DISCORD_BOT_TOKEN bên dưới / Paste it into DISCORD_BOT_TOKEN below
#   3. Tạo file token.txt cạnh bot.py và dán token vào / Create token.txt next to bot.py
#   4. Đặt biến môi trường DISCORD_BOT_TOKEN / Set the DISCORD_BOT_TOKEN environment variable
# Token thật có dạng / A real token looks like:  XXXXXXXXXXXXXXXXXXXXXXXX.XXXXXX.XXXXXXXXXXXXXXXXXXXXXXXXXXX
DISCORD_BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"

GITHUB_RAW_SCRIPT = "https://raw.githubusercontent.com/giangveso0-ctrl/RobloxOnDiscord-Test/main/bridge.lua"
REPO_URL = "https://github.com/giangveso0-ctrl/RobloxOnDiscord-Test"
WS_HOST = "localhost"
WS_PORT = 8765
DEBUG_CHANNEL = "debug"

# Chỉ những ID này mới dùng được bot. Để trống = ai trong #debug cũng dùng được.
# Only these user IDs may use the bot. Leave empty = anyone in #debug can use it.
# Ví dụ / Example: ALLOWED_USER_IDS = [123456789012345678]
ALLOWED_USER_IDS = []

MAX_FILE_BYTES = 2 * 1024 * 1024  # 2 MB limit for attached .lua / .txt files

PLACEHOLDER_TOKENS = {"", "YOUR_DISCORD_BOT_TOKEN_HERE", "PASTE_YOUR_BOT_TOKEN_HERE"}


TOKEN_FILE = Path(__file__).with_name("token.txt")


def load_token() -> Optional[str]:
    """Return the first real token found (env var > token.txt > constant)."""
    from_file = ""
    if TOKEN_FILE.is_file():
        try:
            from_file = TOKEN_FILE.read_text(encoding="utf-8-sig")
        except OSError:
            from_file = ""

    for candidate in (os.environ.get("DISCORD_BOT_TOKEN", ""), from_file, DISCORD_BOT_TOKEN):
        candidate = (candidate or "").strip().strip("\"'")
        if candidate and candidate not in PLACEHOLDER_TOKENS:
            return candidate
    return None


# (token prompt helpers are defined below, after the console log helpers)

# ==============================================================================
# 🎨 COLOURS / BẢNG MÀU
# ==============================================================================
class Colour:
    SUCCESS = 0x2ECC71   # green
    ERROR = 0xE74C3C     # red
    WARNING = 0xF39C12   # orange
    INFO = 0x3498DB      # blue
    PURPLE = 0x9B59B6
    PINK = 0xFF6B9D
    TEAL = 0x1ABC9C
    GOLD = 0xF1C40F
    DARK = 0x2C2F33


class Ansi:
    """ANSI colour codes for the console."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    GREY = "\033[90m"


# Keep emoji / box-drawing characters from crashing older Windows consoles
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Makes ANSI colours work in Windows CMD / PowerShell
if os.name == "nt":
    os.system("")

LOG_STYLES = {
    "ok":     (Ansi.GREEN,   "  OK  "),
    "info":   (Ansi.CYAN,    " INFO "),
    "warn":   (Ansi.YELLOW,  " WARN "),
    "error":  (Ansi.RED,     "ERROR "),
    "roblox": (Ansi.MAGENTA, "ROBLOX"),
    "conn":   (Ansi.GREEN,   " CONN "),
    "disc":   (Ansi.RED,     " DISC "),
}


def log(level: str, message: str) -> None:
    colour, label = LOG_STYLES.get(level, (Ansi.RESET, " LOG  "))
    stamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"{Ansi.GREY}{stamp}{Ansi.RESET} {colour}{Ansi.BOLD}[{label}]{Ansi.RESET} {colour}{message}{Ansi.RESET}")


def print_banner() -> None:
    lines = [
        "╔══════════════════════════════════════════════════╗",
        "║        ⚡  ROBLOX  ON  DISCORD  BRIDGE  ⚡        ║",
        "║          WebSocket Remote Command Hub            ║",
        "╚══════════════════════════════════════════════════╝",
    ]
    colours = [Ansi.CYAN, Ansi.BLUE, Ansi.MAGENTA, Ansi.CYAN]
    print()
    for colour, line in zip(colours, lines):
        print(f"{colour}{Ansi.BOLD}{line}{Ansi.RESET}")
    print(f"{Ansi.GREY}  {REPO_URL}{Ansi.RESET}\n")


def looks_like_token(token: str) -> bool:
    """Discord bot tokens have 3 dot-separated parts and are ~60-80 characters long."""
    return token.count(".") == 2 and len(token) >= 50 and " " not in token


def protect_token_file() -> None:
    """Add token.txt to .gitignore so the token is not pushed to GitHub by accident."""
    gitignore = TOKEN_FILE.with_name(".gitignore")
    try:
        existing = gitignore.read_text(encoding="utf-8") if gitignore.is_file() else ""
        if "token.txt" not in existing.splitlines():
            with gitignore.open("a", encoding="utf-8") as fh:
                if existing and not existing.endswith("\n"):
                    fh.write("\n")
                fh.write("token.txt\n")
            log("info", "Đã thêm token.txt vào .gitignore / Added token.txt to .gitignore")
    except OSError:
        pass


def prompt_for_token() -> Optional[str]:
    """Ask for the bot token in the console when the file is opened without one."""
    if not (sys.stdin and sys.stdin.isatty()):
        return None  # not an interactive console (e.g. run as a service) — nothing to ask

    print(f"{Ansi.YELLOW}{Ansi.BOLD}  🔑 CHƯA CÓ TOKEN / NO BOT TOKEN YET{Ansi.RESET}")
    print(f"{Ansi.GREY}  Dán token bot Discord của bạn bên dưới rồi nhấn Enter.")
    print(f"  Paste your Discord bot token below and press Enter.")
    print(f"  Lấy token / Get it: https://discord.com/developers/applications → Bot → Reset Token{Ansi.RESET}\n")

    for _ in range(3):
        try:
            token = input(f"{Ansi.CYAN}{Ansi.BOLD}  Token › {Ansi.RESET}").strip().strip("\"'")
        except (EOFError, KeyboardInterrupt):
            print()
            return None

        if token.lower().startswith("bot "):
            token = token[4:].strip()
        if not token:
            continue
        if not looks_like_token(token):
            log("warn", "Token không đúng định dạng (cần 2 dấu chấm, ~60-80 ký tự). / That doesn't look like a bot token.")
            try:
                if input("  Vẫn dùng? / Use it anyway? [y/N]: ").strip().lower() != "y":
                    continue
            except (EOFError, KeyboardInterrupt):
                print()
                return None

        try:
            save = input("  Lưu vào token.txt để lần sau không phải nhập lại? / Save to token.txt for next time? [Y/n]: ")
        except (EOFError, KeyboardInterrupt):
            print()
            save = "n"
        if save.strip().lower() not in ("n", "no"):
            try:
                TOKEN_FILE.write_text(token + "\n", encoding="utf-8")
                log("ok", f"Đã lưu token vào / Token saved to {TOKEN_FILE.name}")
                protect_token_file()
            except OSError as e:
                log("warn", f"Không lưu được token / Could not save token: {e}")
        print()
        return token

    return None


def pause_and_exit(code: int = 1) -> None:
    """Keep the window open on Windows so the error can be read when the file was double-clicked."""
    if os.name == "nt" and sys.stdin and sys.stdin.isatty():
        try:
            input("\nNhấn Enter để thoát / Press Enter to exit...")
        except (EOFError, KeyboardInterrupt):
            pass
    sys.exit(code)


# ==============================================================================
# 🤖 BOT SETUP
# ==============================================================================
# Roblox clients currently connected over WebSocket
connected_clients = set()
START_TIME = time.time()


async def ws_handler(websocket):
    connected_clients.add(websocket)
    log("conn", f"Roblox client connected! Total active: {len(connected_clients)}")
    try:
        async for message in websocket:
            log("roblox", str(message))
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.discard(websocket)
        log("disc", f"Roblox client disconnected. Total active: {len(connected_clients)}")


async def start_websocket_server() -> None:
    try:
        async with websockets.serve(ws_handler, WS_HOST, WS_PORT):
            log("ok", f"WebSocket Server running at ws://{WS_HOST}:{WS_PORT}")
            await asyncio.Future()  # run forever
    except OSError as e:
        log("error", f"Không mở được cổng {WS_PORT} / Could not open port {WS_PORT}: {e}")
        log("error", "Cổng đang bị chương trình khác dùng? / Is another program (or a second bot.py) using it?")


def _ws_task_done(task: asyncio.Task) -> None:
    if not task.cancelled() and task.exception():
        log("error", f"WebSocket server stopped: {task.exception()}")


class RobloxBot(commands.Bot):
    async def setup_hook(self) -> None:
        # Runs once per start (unlike on_ready, which fires on every reconnect)
        try:
            synced = await self.tree.sync()
            log("ok", f"Synced {len(synced)} slash command(s).")
        except Exception as e:
            log("error", f"Sync error: {e}")

        self.ws_task = asyncio.create_task(start_websocket_server())
        self.ws_task.add_done_callback(_ws_task_done)


intents = discord.Intents.default()
intents.message_content = True  # required for the !exec / .exec prefix command
bot = RobloxBot(command_prefix=[".", "!"], intents=intents, help_command=None)


@bot.event
async def on_ready():
    log("ok", f"Bot logged in as: {bot.user} (English/Vietnamese Dual Mode)")
    try:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Roblox • /help"))
    except Exception:
        pass


# ==============================================================================
# 🧩 EMBED HELPERS
# ==============================================================================
def make_embed(title: str, description: str = None, colour: int = Colour.INFO) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        colour=colour,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_footer(text="RobloxOnDiscord Bridge • Bot Automation System")
    return embed


def error_embed(error) -> discord.Embed:
    return make_embed("❌ Lỗi / Error", f"```{str(error)[:1500]}```", Colour.ERROR)


def code_block(code: str, limit: int = 1500, lang: str = "lua") -> str:
    """Wrap code in a block, truncating it and escaping stray backticks."""
    code = code.strip().replace("```", "`\u200b``")
    if len(code) > limit:
        code = code[:limit] + "\n-- ... (đã rút gọn / truncated)"
    return f"```{lang}\n{code}\n```"


def loadstring_snippet() -> str:
    return f'loadstring(game:HttpGet("{GITHUB_RAW_SCRIPT}"))()'


def format_uptime(seconds: float) -> str:
    seconds = int(seconds)
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}h {minutes}m {secs}s" if hours else f"{minutes}m {secs}s"


def roblox_running() -> bool:
    return any(
        p.info["name"] and p.info["name"].lower() == "robloxplayerbeta.exe"
        for p in psutil.process_iter(["name"])
    )


def not_connected_embed() -> discord.Embed:
    embed = make_embed(
        "🔴 DISCONNECTED",
        "Chưa kết nối WebSocket với Roblox!\nNo active Roblox client connected!",
        Colour.ERROR,
    )
    embed.add_field(
        name="💡 Cách kết nối / How to connect",
        value="Chạy lệnh `/inject` để xem hướng dẫn.\nRun `/inject` for instructions.",
        inline=False,
    )
    return embed


def wrong_channel_embed() -> discord.Embed:
    return make_embed(
        "⚠️ Sai kênh / Wrong channel",
        f"Lệnh này chỉ được phép dùng trong kênh `#{DEBUG_CHANNEL}`!\n"
        f"This command can only be used in `#{DEBUG_CHANNEL}`!",
        Colour.WARNING,
    )


def denied_embed() -> discord.Embed:
    return make_embed(
        "⛔ Không có quyền / Access denied",
        "Bạn không có trong danh sách được phép dùng bot này.\n"
        "You are not on this bot's allowed users list.",
        Colour.ERROR,
    )


async def build_status_embed(show_loadstring: bool = False) -> discord.Embed:
    running = await asyncio.to_thread(roblox_running)  # psutil scan can be slow
    clients = len(connected_clients)

    if clients > 0 and running:
        title, colour = "🟢 CONNECTED", Colour.SUCCESS
        desc = "Roblox bridge đang hoạt động hoàn hảo!\nBridge is active and ready."
    elif running:
        title, colour = "🟠 WAITING FOR SCRIPT", Colour.WARNING
        desc = "Game đang chạy nhưng chưa nạp script!\nGame running but script not injected!"
    else:
        title, colour = "🔴 DISCONNECTED", Colour.ERROR
        desc = "Không tìm thấy tiến trình Roblox!\nRoblox process not found!"

    embed = make_embed(title, desc, colour)
    embed.add_field(name="🎮 Roblox", value="🟢 Running" if running else "🔴 Not found", inline=True)
    embed.add_field(name="🔌 WebSocket", value=f"`{clients}` client(s)", inline=True)
    embed.add_field(name="📡 Latency", value=f"`{round(bot.latency * 1000)} ms`", inline=True)
    embed.add_field(name="🌐 Endpoint", value=f"`ws://{WS_HOST}:{WS_PORT}`", inline=True)
    embed.add_field(name="⏱️ Uptime", value=f"`{format_uptime(time.time() - START_TIME)}`", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)

    if show_loadstring and running and clients == 0:
        embed.add_field(
            name="📋 Chạy trong Executor / Run in your executor",
            value=code_block(loadstring_snippet()),
            inline=False,
        )
    return embed


def build_help_embed() -> discord.Embed:
    embed = make_embed(
        "📖 Roblox Bridge Hub — Hướng Dẫn / Help",
        "Hệ thống quản lý Roblox qua WebSocket\nWebSocket Management System",
        Colour.PURPLE,
    )
    embed.add_field(
        name="📜 Lệnh Tiền Tố / Prefix Commands (`!` hoặc `.`)",
        value=(
            "`!exec <script>` — Chạy script dài hoặc file đính kèm `.lua`/`.txt` / Long scripts & files\n"
            "`!help` — Xem hướng dẫn này / Show this help"
        ),
        inline=False,
    )
    embed.add_field(
        name="⚡ Thực Thi / Execution",
        value=(
            "`/exec <code>` — Gửi script ngắn / Quick short script\n"
            "`/findscript <source> <keyword>` — Tìm script Rscripts / ScriptBlox"
        ),
        inline=False,
    )
    embed.add_field(
        name="🎮 Tính Năng / Features",
        value=(
            "`/esp [on|off]` — 👁️ Nhìn xuyên tường / Player ESP\n"
            "`/fly` · `/unfly` — ✈️ Bay / Flight mode\n"
            "`/clicktotp [on|off]` — 🖱️ Ctrl+Click dịch chuyển / Click-to-TP\n"
            "`/autoheal [on|off]` — ❤️ Tự hồi máu / Auto-Heal\n"
            "`/fpsboost` — 🚀 Tăng FPS / Boost FPS"
        ),
        inline=False,
    )
    embed.add_field(
        name="🧰 Hệ Thống / System",
        value=(
            "`/inject` — 🔌 Kiểm tra & kết nối / Check & connect\n"
            "`/status` — 📊 Trạng thái / Status\n"
            "`/cre` — 🌟 Thông tin tác giả / Credits"
        ),
        inline=False,
    )
    return embed


# ==============================================================================
# 🧪 LUA HELPERS
# ==============================================================================
def strip_code_fence(text: str) -> str:
    """Remove a surrounding ```lua ... ``` fence if the user pasted one."""
    text = text.strip()
    if len(text) >= 6 and text.startswith("```") and text.endswith("```"):
        inner = text[3:-3]
        first, sep, rest = inner.partition("\n")
        if sep and first.strip().lower() in ("", "lua", "luau"):
            inner = rest
        return inner.strip()
    return text


def wrap_lua(code: str) -> str:
    """Wrap user code so syntax AND runtime errors are caught instead of silently lost."""
    code = code.replace("\r\n", "\n").replace("\r", "\n")
    level = 0
    while f"]{'=' * level}]" in code:  # pick a long-bracket level the code doesn't contain
        level += 1
    eq = "=" * level
    return (
        f"local __src = [{eq}[\n{code}\n]{eq}]\n"
        "local __fn, __err = loadstring(__src)\n"
        "if not __fn then warn('[Discord Exec] Syntax error: ' .. tostring(__err)) return end\n"
        "local __ok, __res = pcall(__fn)\n"
        "if not __ok then warn('[Discord Exec] Runtime error: ' .. tostring(__res)) end"
    )


def toggle_script(template: str, enabled: bool) -> str:
    return template.replace("__ENABLE__", "true" if enabled else "false")


async def send_to_roblox(script_code: str) -> int:
    """Send Lua to every connected client. Returns how many clients received it."""
    delivered = 0
    for ws in list(connected_clients):
        try:
            await ws.send(script_code)
            delivered += 1
        except Exception:
            connected_clients.discard(ws)
    return delivered


# ==============================================================================
# ⚡ EXECUTOR EMBEDS
# ==============================================================================
def build_exec_embed(code: str, user, delivered: int, elapsed_ms: int, source: str) -> discord.Embed:
    lines = code.strip().count("\n") + 1
    embed = make_embed(
        "⚡ SCRIPT EXECUTED",
        "Đã gửi script tới Roblox thành công!\nScript delivered to Roblox successfully.",
        Colour.SUCCESS,
    )
    embed.set_author(name=f"{user.display_name} • Executor", icon_url=user.display_avatar.url)
    embed.add_field(name="📦 Size", value=f"`{len(code):,}` chars", inline=True)
    embed.add_field(name="📄 Lines", value=f"`{lines:,}`", inline=True)
    embed.add_field(name="📡 Delivered", value=f"`{delivered}` client(s)", inline=True)
    embed.add_field(name="🧭 Source", value=source, inline=True)
    embed.add_field(name="⏱️ Sent in", value=f"`{elapsed_ms} ms`", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="📜 Script preview", value=code_block(code, limit=900), inline=False)
    return embed


def build_exec_failed_embed(code: str, user, source: str) -> discord.Embed:
    embed = not_connected_embed()
    embed.set_author(name=f"{user.display_name} • Executor", icon_url=user.display_avatar.url)
    embed.add_field(name="🧭 Source", value=source, inline=True)
    embed.add_field(name="📦 Script", value=f"`{len(code):,}` chars (chưa gửi / not sent)", inline=True)
    return embed


async def execute_script(code: str, user, source: str) -> "tuple[discord.Embed, bool]":
    """Wrap + send a script and return (embed, success)."""
    started = time.perf_counter()
    delivered = await send_to_roblox(wrap_lua(code))
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    if delivered:
        return build_exec_embed(code, user, delivered, elapsed_ms, source), True
    return build_exec_failed_embed(code, user, source), False


# ==============================================================================
# 🔒 CHANNEL / USER GUARDS
# ==============================================================================
def in_debug_channel(channel) -> bool:
    # DM channels have no .name, so use getattr instead of crashing
    return getattr(channel, "name", None) == DEBUG_CHANNEL


def is_allowed_user(user) -> bool:
    return not ALLOWED_USER_IDS or user.id in ALLOWED_USER_IDS


def is_debug_channel():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not in_debug_channel(interaction.channel):
            await interaction.response.send_message(embed=wrong_channel_embed(), ephemeral=True)
            return False
        if not is_allowed_user(interaction.user):
            await interaction.response.send_message(embed=denied_embed(), ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)


async def guard_ctx(ctx: commands.Context) -> bool:
    if not in_debug_channel(ctx.channel):
        await ctx.send(embed=wrong_channel_embed())
        return False
    if not is_allowed_user(ctx.author):
        await ctx.send(embed=denied_embed())
        return False
    return True


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        return  # already answered by the channel check
    log("error", f"Command error: {error}")
    embed = error_embed(error)
    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except discord.HTTPException:
        pass


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return  # a message that merely starts with "." or "!" — ignore
    log("error", f"Prefix command error: {error}")
    try:
        await ctx.send(embed=error_embed(error))
    except discord.HTTPException:
        pass


async def run_feature(interaction: discord.Interaction, script: str, *, title: str, description: str, colour: int):
    """Send a Lua feature script to Roblox and answer with a coloured embed."""
    if await send_to_roblox(script):
        embed = make_embed(title, description, colour)
    else:
        embed = not_connected_embed()
    await interaction.response.send_message(embed=embed, ephemeral=True)


STATE_CHOICES = [
    app_commands.Choice(name="ON · Bật", value="on"),
    app_commands.Choice(name="OFF · Tắt", value="off"),
]


# ==============================================================================
# 🛠️ PREFIX COMMANDS (!exec chuyên dụng cho script dài & file đính kèm)
# ==============================================================================
@bot.command(name="help")
async def legacy_help(ctx: commands.Context):
    if not await guard_ctx(ctx):
        return
    await ctx.send(embed=build_help_embed())


@bot.command(name="exec")
async def legacy_exec(ctx: commands.Context, *, script_code: str = None):
    """Lệnh !exec tối ưu cho script dài và file đính kèm .lua/.txt"""
    if not await guard_ctx(ctx):
        return

    source = "💬 Prefix command"

    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if not attachment.filename.lower().endswith((".lua", ".txt")):
            return await ctx.send(embed=make_embed(
                "⚠️ Sai định dạng / Unsupported file",
                "Chỉ hỗ trợ file `.lua` hoặc `.txt`.\nOnly `.lua` or `.txt` files are supported.",
                Colour.WARNING))
        if attachment.size > MAX_FILE_BYTES:
            return await ctx.send(embed=make_embed(
                "⚠️ File quá lớn / File too large",
                f"Tối đa {MAX_FILE_BYTES // (1024 * 1024)} MB.\nMaximum size is {MAX_FILE_BYTES // (1024 * 1024)} MB.",
                Colour.WARNING))
        try:
            # utf-8-sig strips the BOM that Windows Notepad adds, which would break loadstring
            script_code = (await attachment.read()).decode("utf-8-sig")
        except Exception as e:
            return await ctx.send(embed=make_embed(
                "❌ Lỗi đọc file / File read error", f"```{str(e)[:1500]}```", Colour.ERROR))
        source = f"📎 File `{attachment.filename}`"
    elif script_code:
        script_code = strip_code_fence(script_code)

    if not script_code or not script_code.strip():
        return await ctx.send(embed=make_embed(
            "⚠️ Thiếu script / Missing script",
            "Vui lòng nhập nội dung script hoặc đính kèm file `.lua`\n"
            "Please provide script code or attach a file!",
            Colour.WARNING))

    embed, ok = await execute_script(script_code, ctx.author, source)
    await ctx.send(embed=embed)
    try:
        await ctx.message.add_reaction("✅" if ok else "❌")
    except discord.HTTPException:
        pass


# ==============================================================================
# ⚡ SLASH COMMANDS
# ==============================================================================
@bot.tree.command(name="help", description="Xem danh sách lệnh / Show all commands")
@is_debug_channel()
async def slash_help(interaction: discord.Interaction):
    await interaction.response.send_message(embed=build_help_embed(), ephemeral=True)


@bot.tree.command(name="inject", description="Kiểm tra trạng thái tiến trình và kết nối / Check process & connection status")
@is_debug_channel()
async def slash_inject(interaction: discord.Interaction):
    embed = await build_status_embed(show_loadstring=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="exec", description="Thực thi nhanh mã Lua ngắn / Quick execute short Lua code")
@app_commands.describe(code="Mã Lua cần chạy / Lua code to run (dùng !exec cho script dài / use !exec for long scripts)")
@is_debug_channel()
async def slash_exec(interaction: discord.Interaction, code: str):
    code = strip_code_fence(code)
    if not code:
        return await interaction.response.send_message(embed=make_embed(
            "⚠️ Thiếu mã / Missing code", "Vui lòng nhập mã lệnh Lua! / Please enter Lua code!",
            Colour.WARNING), ephemeral=True)

    embed, _ = await execute_script(code, interaction.user, "⚡ Slash command")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="findscript", description="Tìm kiếm script từ Rscripts hoặc ScriptBlox / Search scripts from Rscripts or ScriptBlox")
@app_commands.choices(source=[
    app_commands.Choice(name="Rscripts (rscripts.net)", value="rscripts"),
    app_commands.Choice(name="ScriptBlox (scriptblox.com)", value="scriptblox"),
])
@is_debug_channel()
async def slash_findscript(interaction: discord.Interaction, source: str, keyword: str):
    query = quote_plus(keyword)
    if source == "rscripts":
        site, url, colour = "Rscripts", f"https://rscripts.net/scripts?search={query}", Colour.PURPLE
    else:
        site, url, colour = "ScriptBlox", f"https://scriptblox.com/?q={query}", Colour.INFO

    embed = make_embed(f"🌐 Kết quả tìm kiếm từ {site}", f"Từ khóa / Keyword: **{keyword}**", colour)
    embed.add_field(name="🔗 Link tra cứu trực tiếp",
                    value=f"[Bấm vào đây để xem trên {site}]({url})", inline=False)
    embed.add_field(name="💡 Gợi ý lệnh",
                    value="Truy cập trang web trên để lấy loadstring và dùng lệnh `/exec` để chạy.",
                    inline=False)
    embed.set_footer(text=f"Nguồn: {site} | Bot Automation System")
    await interaction.response.send_message(embed=embed, ephemeral=True)


ESP_SCRIPT = """
pcall(function()
    local Players = game:GetService("Players")
    local LocalPlayer = Players.LocalPlayer
    local TAG = "DiscordESP"

    -- remove the old listeners and highlights first, so re-running never stacks them
    if _G.DiscordESPConns then
        for _, c in ipairs(_G.DiscordESPConns) do c:Disconnect() end
    end
    _G.DiscordESPConns = {}
    for _, plr in ipairs(Players:GetPlayers()) do
        if plr.Character then
            local old = plr.Character:FindFirstChild(TAG)
            if old then old:Destroy() end
        end
    end

    if not __ENABLE__ then return end

    local function track(plr)
        if plr == LocalPlayer then return end
        local function onCharacter(char)
            if not char or char:FindFirstChild(TAG) then return end
            local highlight = Instance.new("Highlight")
            highlight.Name = TAG
            highlight.Adornee = char
            highlight.FillColor = Color3.fromRGB(255, 0, 0)
            highlight.OutlineColor = Color3.fromRGB(255, 255, 255)
            highlight.FillTransparency = 0.5
            highlight.Parent = char
        end
        onCharacter(plr.Character)
        table.insert(_G.DiscordESPConns, plr.CharacterAdded:Connect(onCharacter))
    end

    for _, plr in ipairs(Players:GetPlayers()) do track(plr) end
    table.insert(_G.DiscordESPConns, Players.PlayerAdded:Connect(track))
end)
"""


@bot.tree.command(name="esp", description="Bật/tắt nhìn xuyên tường (Highlight) / Toggle player ESP")
@app_commands.describe(state="Bật hoặc tắt / On or off (mặc định / default: on)")
@app_commands.choices(state=STATE_CHOICES)
@is_debug_channel()
async def slash_esp(interaction: discord.Interaction, state: str = "on"):
    on = state == "on"
    await run_feature(
        interaction, toggle_script(ESP_SCRIPT, on),
        title="👁️ ESP ENABLED" if on else "🙈 ESP DISABLED",
        description=("Đã bật **ESP** (Highlight người chơi, tự cập nhật người mới)!\nPlayer highlights are now visible."
                     if on else "Đã tắt **ESP** và xóa toàn bộ Highlight!\nAll highlights removed."),
        colour=Colour.PINK if on else Colour.DARK)


FPS_BOOST_SCRIPT = """
pcall(function()
    local lighting = game:GetService("Lighting")
    lighting.GlobalShadows = false
    lighting.FogEnd = 9e9
    for _, v in ipairs(workspace:GetDescendants()) do
        if v:IsA("BasePart") then
            v.Material = Enum.Material.SmoothPlastic
            v.Reflectance = 0
        elseif v:IsA("Decal") or v:IsA("Texture") then
            v.Transparency = 1
        end
    end
    settings().Rendering.QualityLevel = Enum.QualityLevel.Level01
end)
"""


@bot.tree.command(name="fpsboost", description="Tối ưu hóa đồ họa, giảm lag và tăng FPS / Boost FPS & reduce lag")
@is_debug_channel()
async def slash_fpsboost(interaction: discord.Interaction):
    await run_feature(
        interaction, FPS_BOOST_SCRIPT,
        title="🚀 FPS BOOST ENABLED",
        description="Đã kích hoạt **FPS Boost** (tối ưu hóa đồ họa thành công)!\nGraphics optimised for performance.",
        colour=Colour.TEAL)


FLY_SCRIPT = """
pcall(function()
    local Players = game:GetService("Players")
    local LocalPlayer = Players.LocalPlayer
    local UserInputService = game:GetService("UserInputService")
    local RunService = game:GetService("RunService")
    local Workspace = game:GetService("Workspace")

    if _G.IYNOFLY then _G.IYNOFLY() end

    _G.FLYING = true
    local flySpeed = 1
    local SPEED = 50
    local CONTROL = {F = 0, B = 0, L = 0, R = 0, Q = 0, E = 0}

    local char = LocalPlayer.Character or LocalPlayer.CharacterAdded:Wait()
    local torso = char:FindFirstChild("Torso") or char:FindFirstChild("HumanoidRootPart")
    local humanoid = char:FindFirstChildOfClass("Humanoid")
    if not torso or not humanoid then return end

    local BG = Instance.new("BodyGyro")
    BG.Name = "IY_BodyGyro"
    BG.P = 9e4
    BG.MaxTorque = Vector3.new(9e9, 9e9, 9e9)
    BG.CFrame = torso.CFrame
    BG.Parent = torso

    local BV = Instance.new("BodyVelocity")
    BV.Name = "IY_BodyVelocity"
    BV.Velocity = Vector3.new(0, 0, 0)
    BV.MaxForce = Vector3.new(9e9, 9e9, 9e9)
    BV.Parent = torso

    humanoid.PlatformStand = true

    local keyDown = UserInputService.InputBegan:Connect(function(input, gpe)
        if gpe then return end
        if input.KeyCode == Enum.KeyCode.W then CONTROL.F = flySpeed
        elseif input.KeyCode == Enum.KeyCode.S then CONTROL.B = -flySpeed
        elseif input.KeyCode == Enum.KeyCode.A then CONTROL.L = -flySpeed
        elseif input.KeyCode == Enum.KeyCode.D then CONTROL.R = flySpeed
        elseif input.KeyCode == Enum.KeyCode.E then CONTROL.Q = flySpeed * 2
        elseif input.KeyCode == Enum.KeyCode.Q then CONTROL.E = -flySpeed * 2
        end
    end)

    -- no gpe check on release, otherwise a key let go while typing would stay "stuck"
    local keyUp = UserInputService.InputEnded:Connect(function(input)
        if input.KeyCode == Enum.KeyCode.W then CONTROL.F = 0
        elseif input.KeyCode == Enum.KeyCode.S then CONTROL.B = 0
        elseif input.KeyCode == Enum.KeyCode.A then CONTROL.L = 0
        elseif input.KeyCode == Enum.KeyCode.D then CONTROL.R = 0
        elseif input.KeyCode == Enum.KeyCode.E then CONTROL.Q = 0
        elseif input.KeyCode == Enum.KeyCode.Q then CONTROL.E = 0
        end
    end)

    local diedConn = humanoid.Died:Connect(function()
        if _G.IYNOFLY then _G.IYNOFLY() end
    end)

    _G.IYNOFLY = function()
        _G.FLYING = false
        if keyDown then keyDown:Disconnect() end
        if keyUp then keyUp:Disconnect() end
        if diedConn then diedConn:Disconnect() end
        if _G.FlyLoopConn then _G.FlyLoopConn:Disconnect() _G.FlyLoopConn = nil end

        local c = LocalPlayer.Character
        if c then
            local hum = c:FindFirstChildOfClass("Humanoid")
            if hum then hum.PlatformStand = false end
        end
        if BG then BG:Destroy() end
        if BV then BV:Destroy() end
    end

    _G.FlyLoopConn = RunService.RenderStepped:Connect(function()
        if not _G.FLYING then return end
        local cam = Workspace.CurrentCamera
        local cf = cam.CFrame

        if (CONTROL.L + CONTROL.R) ~= 0 or (CONTROL.F + CONTROL.B) ~= 0 or (CONTROL.Q + CONTROL.E) ~= 0 then
            local move = (cf.LookVector * (CONTROL.F + CONTROL.B))
                + ((cf * CFrame.new(CONTROL.L + CONTROL.R, (CONTROL.F + CONTROL.B + CONTROL.Q + CONTROL.E) * 0.2, 0).p) - cf.p)
            BV.Velocity = move * SPEED
        else
            BV.Velocity = Vector3.new(0, 0, 0)
        end

        BG.CFrame = cf
    end)
end)
"""

UNFLY_SCRIPT = """
pcall(function()
    if _G.IYNOFLY then
        _G.IYNOFLY()
        _G.IYNOFLY = nil
    else
        local char = game:GetService("Players").LocalPlayer.Character
        if char then
            local hum = char:FindFirstChildOfClass("Humanoid")
            local root = char:FindFirstChild("Torso") or char:FindFirstChild("HumanoidRootPart")
            if hum then hum.PlatformStand = false end
            if root then
                if root:FindFirstChild("IY_BodyGyro") then root.IY_BodyGyro:Destroy() end
                if root:FindFirstChild("IY_BodyVelocity") then root.IY_BodyVelocity:Destroy() end
            end
        end
    end
end)
"""


@bot.tree.command(name="fly", description="Bật chế độ bay chuẩn Infinite Yield / Enable Infinite Yield Fly mode")
@is_debug_channel()
async def slash_fly(interaction: discord.Interaction):
    await run_feature(
        interaction, FLY_SCRIPT,
        title="✈️ FLY ENABLED (Infinite Yield Core)",
        description="Đã bật **Fly Mode chuẩn Infinite Yield**!\nSử dụng WASD + Q/E để di chuyển.",
        colour=Colour.INFO)


@bot.tree.command(name="unfly", description="Tắt chế độ bay Infinite Yield / Disable Fly mode")
@is_debug_channel()
async def slash_unfly(interaction: discord.Interaction):
    await run_feature(
        interaction, UNFLY_SCRIPT,
        title="🛑 FLY DISABLED",
        description="Đã tắt **Fly Mode** và khôi phục vật lý ban đầu!\nFlight disabled, physics restored.",
        colour=Colour.ERROR)


CLICK_TP_SCRIPT = """
pcall(function()
    local plr = game:GetService("Players").LocalPlayer
    local mouse = plr:GetMouse()
    local uis = game:GetService("UserInputService")
    if _G.ClickTPConn then _G.ClickTPConn:Disconnect() _G.ClickTPConn = nil end
    if not __ENABLE__ then return end

    _G.ClickTPConn = mouse.Button1Down:Connect(function()
        if uis:IsKeyDown(Enum.KeyCode.LeftControl) or uis:IsKeyDown(Enum.KeyCode.RightControl) then
            local char = plr.Character
            if char and char:FindFirstChild("HumanoidRootPart") and mouse.Target then
                char.HumanoidRootPart.CFrame = CFrame.new(mouse.Hit.Position + Vector3.new(0, 3, 0))
            end
        end
    end)
end)
"""


@bot.tree.command(name="clicktotp", description="Bật/tắt Click chuột để dịch chuyển (Ctrl + Click) / Toggle Click-to-TP")
@app_commands.describe(state="Bật hoặc tắt / On or off (mặc định / default: on)")
@app_commands.choices(state=STATE_CHOICES)
@is_debug_channel()
async def slash_clicktotp(interaction: discord.Interaction, state: str = "on"):
    on = state == "on"
    await run_feature(
        interaction, toggle_script(CLICK_TP_SCRIPT, on),
        title="🖱️ CLICK-TO-TP ENABLED" if on else "🖱️ CLICK-TO-TP DISABLED",
        description=("Đã bật **Click-to-TP**!\nGiữ **Ctrl + Click chuột trái** để dịch chuyển / Hold **Ctrl + Left Click** to teleport."
                     if on else "Đã tắt **Click-to-TP**!\nClick-to-TP turned off."),
        colour=Colour.WARNING if on else Colour.DARK)


AUTO_HEAL_SCRIPT = """
pcall(function()
    if _G.AutoHealConn then _G.AutoHealConn:Disconnect() _G.AutoHealConn = nil end
    if not __ENABLE__ then return end

    _G.AutoHealConn = game:GetService("RunService").Stepped:Connect(function()
        local char = game:GetService("Players").LocalPlayer.Character
        if char then
            local hum = char:FindFirstChildOfClass("Humanoid")
            if hum and hum.Health > 0 and hum.Health < hum.MaxHealth then
                hum.Health = hum.MaxHealth
            end
        end
    end)
end)
"""


@bot.tree.command(name="autoheal", description="Bật/tắt tự động hồi máu liên tục / Toggle Auto-Heal")
@app_commands.describe(state="Bật hoặc tắt / On or off (mặc định / default: on)")
@app_commands.choices(state=STATE_CHOICES)
@is_debug_channel()
async def slash_autoheal(interaction: discord.Interaction, state: str = "on"):
    on = state == "on"
    await run_feature(
        interaction, toggle_script(AUTO_HEAL_SCRIPT, on),
        title="❤️ AUTO-HEAL ENABLED" if on else "💔 AUTO-HEAL DISABLED",
        description=("Đã bật **Auto-Heal** (tự động hồi đầy máu liên tục)!\nHealth will refill automatically."
                     if on else "Đã tắt **Auto-Heal**!\nAuto-Heal turned off."),
        colour=Colour.ERROR if on else Colour.DARK)


@bot.tree.command(name="cre", description="Hiển thị thông tin tác giả và dự án / Credits & Information")
@is_debug_channel()
async def slash_cre(interaction: discord.Interaction):
    embed = make_embed(
        "🌟 RobloxOnDiscord Bridge — Credits",
        "Hệ thống cầu nối WebSocket tương tác giữa Discord Bot và Roblox Client.\n"
        "WebSocket bridge between a Discord bot and the Roblox client.",
        Colour.GOLD)
    embed.add_field(name="👨‍💻 Developer / Tác giả", value="Videccode (idea: @vaehz)", inline=True)
    embed.add_field(name="🌐 Protocol", value=f"Localhost WebSocket (Port {WS_PORT})", inline=True)
    embed.add_field(name="🔗 GitHub Repository", value=f"[RobloxOnDiscord-Test]({REPO_URL})", inline=False)
    embed.set_footer(text="Cảm ơn bạn đã sử dụng hệ thống tự động hóa này!")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="status", description="Kiểm tra trạng thái máy chủ WebSocket / Check WebSocket server status")
@is_debug_channel()
async def slash_status(interaction: discord.Interaction):
    embed = await build_status_embed()
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==============================================================================
# 🚀 KHỞI CHẠY BOT / START
# ==============================================================================
def main() -> None:
    print_banner()

    token = load_token()
    if not token:
        token = prompt_for_token()
    if not token:
        log("error", "Chưa có token! Mở lại file và dán token, hoặc dùng token.txt / biến môi trường DISCORD_BOT_TOKEN.")
        log("error", "No bot token! Run the file again and paste it, or use token.txt / the DISCORD_BOT_TOKEN env var.")
        log("info", "Lấy token tại / Get one at: https://discord.com/developers/applications  →  Bot  →  Reset Token")
        pause_and_exit(1)

    if not looks_like_token(token):
        log("warn", "Token trông không đúng định dạng. / Token looks malformed.")

    log("info", "Starting bot...")
    try:
        bot.run(token, log_level=logging.WARNING)
    except discord.LoginFailure:
        log("error", "Token không hợp lệ hoặc đã bị reset. Hãy tạo token mới trong Developer Portal.")
        log("error", "Invalid or reset token. Generate a fresh one in the Developer Portal.")
        # If the bad token came from token.txt, offer to clear it so the next launch asks again
        try:
            if TOKEN_FILE.is_file() and TOKEN_FILE.read_text(encoding="utf-8-sig").strip() == token \
                    and sys.stdin and sys.stdin.isatty():
                answer = input("  Xóa token đã lưu để nhập lại lần sau? / Delete the saved token so you can re-enter it? [Y/n]: ")
                if answer.strip().lower() not in ("n", "no"):
                    TOKEN_FILE.unlink()
                    log("ok", "Đã xóa token.txt — mở lại file để nhập token mới. / token.txt deleted — run the file again.")
        except (OSError, EOFError, KeyboardInterrupt):
            pass
        pause_and_exit(1)
    except discord.PrivilegedIntentsRequired:
        log("error", "Hãy bật 'Message Content Intent' trong Developer Portal → Bot → Privileged Gateway Intents.")
        log("error", "Enable 'Message Content Intent' in Developer Portal → Bot → Privileged Gateway Intents.")
        pause_and_exit(1)


if __name__ == "__main__":
    main()
