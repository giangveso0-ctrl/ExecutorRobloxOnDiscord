"""
ExecutorOnDiscord — control a Roblox client from Discord.

    Discord (#debug) ──commands / buttons──▶ bot.py ◀──WebSocket──▶ bridge.lua (inside Roblox)

Run:  python bot.py        (first run asks for your bot token)
Docs: see README.md
"""
import asyncio
import datetime
import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus

import discord
import psutil
import websockets
from discord import app_commands
from discord.ext import commands

# ==============================================================================
# 🔑 CONFIGURATION / CẤU HÌNH
# ==============================================================================
# Token — pick ONE way / Chọn MỘT cách:
#   1. Just run this file: the bot asks for the token and can save it to token.txt
#   2. Paste it into DISCORD_BOT_TOKEN below
#   3. Create token.txt next to bot.py containing only the token
#   4. Set the DISCORD_BOT_TOKEN environment variable
DISCORD_BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"

# Only these Discord user IDs may use the bot. Empty = ANYONE in the channel can run Lua on your PC!
# Ví dụ / Example: ALLOWED_USER_IDS = [123456789012345678]
ALLOWED_USER_IDS: List[int] = []

DEBUG_CHANNEL = "debug"   # the only channel the bot answers in
WS_HOST = "localhost"
WS_PORT = 8765
MAX_FILE_BYTES = 2 * 1024 * 1024   # limit for attached .lua / .txt files

REPO_URL = "https://github.com/giangveso0-ctrl/ExecutorRobloxOnDiscord"
GITHUB_RAW_SCRIPT = "https://raw.githubusercontent.com/giangveso0-ctrl/ExecutorRobloxOnDiscord/main/bridge.lua"

# Environment variables override the constants above.
DEBUG_CHANNEL = os.environ.get("DEBUG_CHANNEL", "").strip().lstrip("#") or DEBUG_CHANNEL
if os.environ.get("WS_PORT", "").strip().isdigit():
    WS_PORT = int(os.environ["WS_PORT"])
for _uid in os.environ.get("ALLOWED_USER_IDS", "").replace(";", ",").split(","):
    if _uid.strip().isdigit():
        ALLOWED_USER_IDS.append(int(_uid.strip()))

TOKEN_FILE = Path(__file__).with_name("token.txt")
PLACEHOLDER_TOKENS = {"", "YOUR_DISCORD_BOT_TOKEN_HERE", "PASTE_YOUR_BOT_TOKEN_HERE"}
ROBLOX_PROCESSES = {"robloxplayerbeta.exe", "robloxplayerbeta"}


class Colour:
    SUCCESS = 0x2ECC71
    ERROR = 0xE74C3C
    WARNING = 0xF39C12
    INFO = 0x3498DB
    PURPLE = 0x9B59B6
    PINK = 0xFF6B9D
    TEAL = 0x1ABC9C
    GOLD = 0xF1C40F
    DARK = 0x2C2F33


# ==============================================================================
# 🖥️ CONSOLE
# ==============================================================================
class Ansi:
    RESET, BOLD = "\033[0m", "\033[1m"
    RED, GREEN, YELLOW = "\033[91m", "\033[92m", "\033[93m"
    BLUE, MAGENTA, CYAN, GREY = "\033[94m", "\033[95m", "\033[96m", "\033[90m"


# Keep emoji / box-drawing characters from crashing older Windows consoles
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if os.name == "nt":
    os.system("")  # enables ANSI colours in CMD / PowerShell

LOG_STYLES = {
    "ok": (Ansi.GREEN, "  OK  "), "info": (Ansi.CYAN, " INFO "), "warn": (Ansi.YELLOW, " WARN "),
    "error": (Ansi.RED, "ERROR "), "roblox": (Ansi.MAGENTA, "ROBLOX"),
    "conn": (Ansi.GREEN, " CONN "), "disc": (Ansi.RED, " DISC "),
}


def log(level: str, message: str) -> None:
    colour, label = LOG_STYLES.get(level, (Ansi.RESET, " LOG  "))
    stamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"{Ansi.GREY}{stamp}{Ansi.RESET} {colour}{Ansi.BOLD}[{label}]{Ansi.RESET} {colour}{message}{Ansi.RESET}")


def print_banner() -> None:
    lines = [
        "╔══════════════════════════════════════════════════╗",
        "║          ⚡  EXECUTOR  ON  DISCORD  ⚡            ║",
        "║          WebSocket Remote Command Hub            ║",
        "╚══════════════════════════════════════════════════╝",
    ]
    print()
    for colour, line in zip((Ansi.CYAN, Ansi.BLUE, Ansi.MAGENTA, Ansi.CYAN), lines):
        print(f"{colour}{Ansi.BOLD}{line}{Ansi.RESET}")
    print(f"{Ansi.GREY}  {REPO_URL}{Ansi.RESET}\n")


def pause_and_exit(code: int = 1) -> None:
    """Keep the window open on Windows so errors can be read after a double-click."""
    if os.name == "nt" and sys.stdin and sys.stdin.isatty():
        try:
            input("\nNhấn Enter để thoát / Press Enter to exit...")
        except (EOFError, KeyboardInterrupt):
            pass
    sys.exit(code)


# ==============================================================================
# 🔐 TOKEN
# ==============================================================================
def clean_token(raw: str) -> str:
    token = (raw or "").strip().strip("\"'")
    return token[4:].strip() if token.lower().startswith("bot ") else token


def looks_like_token(token: str) -> bool:
    """Bot tokens have 3 dot-separated parts and are ~60-80 characters long."""
    return token.count(".") == 2 and len(token) >= 50 and " " not in token


def load_token() -> Optional[str]:
    """First real token found: env var > token.txt > constant."""
    from_file = ""
    if TOKEN_FILE.is_file():
        try:
            from_file = TOKEN_FILE.read_text(encoding="utf-8-sig")
        except OSError:
            pass
    for candidate in (os.environ.get("DISCORD_BOT_TOKEN", ""), from_file, DISCORD_BOT_TOKEN):
        token = clean_token(candidate)
        if token and token not in PLACEHOLDER_TOKENS:
            return token
    return None


def protect_token_file() -> None:
    """Add token.txt to .gitignore so the token is never pushed to GitHub by accident."""
    gitignore = TOKEN_FILE.with_name(".gitignore")
    try:
        existing = gitignore.read_text(encoding="utf-8") if gitignore.is_file() else ""
        if "token.txt" not in existing.splitlines():
            with gitignore.open("a", encoding="utf-8") as fh:
                fh.write(("\n" if existing and not existing.endswith("\n") else "") + "token.txt\n")
            log("info", "Đã thêm token.txt vào .gitignore / Added token.txt to .gitignore")
    except OSError:
        pass


def ask(prompt: str) -> Optional[str]:
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def prompt_for_token() -> Optional[str]:
    """Ask for the token in the console when none is configured."""
    if not (sys.stdin and sys.stdin.isatty()):
        return None  # not interactive (service, GUI launcher) — nothing to ask

    print(f"{Ansi.YELLOW}{Ansi.BOLD}  🔑 CHƯA CÓ TOKEN / NO BOT TOKEN YET{Ansi.RESET}")
    print(f"{Ansi.GREY}  Dán token bot Discord rồi nhấn Enter. / Paste your bot token and press Enter.")
    print(f"  Lấy token / Get it: https://discord.com/developers/applications → Bot → Reset Token{Ansi.RESET}\n")

    for _ in range(3):
        answer = ask(f"{Ansi.CYAN}{Ansi.BOLD}  Token › {Ansi.RESET}")
        if answer is None:
            return None
        token = clean_token(answer)
        if not token:
            continue
        if not looks_like_token(token):
            log("warn", "Token không đúng định dạng. / That doesn't look like a bot token.")
            if (ask("  Vẫn dùng? / Use it anyway? [y/N]: ") or "").strip().lower() != "y":
                continue
        save = ask("  Lưu vào token.txt cho lần sau? / Save to token.txt for next time? [Y/n]: ") or "n"
        if save.strip().lower() not in ("n", "no"):
            try:
                TOKEN_FILE.write_text(token + "\n", encoding="utf-8")
                log("ok", f"Đã lưu token / Token saved to {TOKEN_FILE.name}")
                protect_token_file()
            except OSError as exc:
                log("warn", f"Không lưu được token / Could not save token: {exc}")
        print()
        return token
    return None


# ==============================================================================
# 🔌 BRIDGE — WebSocket server that talks to Roblox
# ==============================================================================
class Bridge:
    """Tracks connected Roblox clients and which toggle features are currently on."""

    def __init__(self) -> None:
        self.clients: set = set()
        self.features: Dict[str, bool] = {}
        self.started = time.time()

    async def handler(self, websocket) -> None:
        if not self.clients:
            self.features.clear()  # a fresh game session starts with everything off
        self.clients.add(websocket)
        log("conn", f"Roblox client connected! Total active: {len(self.clients)}")
        try:
            async for message in websocket:
                log("roblox", str(message))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(websocket)
            log("disc", f"Roblox client disconnected. Total active: {len(self.clients)}")

    async def serve(self) -> None:
        try:
            async with websockets.serve(self.handler, WS_HOST, WS_PORT):
                log("ok", f"WebSocket Server running at ws://{WS_HOST}:{WS_PORT}")
                await asyncio.Future()  # run forever
        except OSError as exc:
            log("error", f"Không mở được cổng {WS_PORT} / Could not open port {WS_PORT}: {exc}")
            log("error", "Cổng đang bị dùng? / Is another program (or a second bot.py) using it?")

    async def send(self, lua: str) -> int:
        """Send Lua to every connected client; returns how many received it."""
        delivered = 0
        for ws in list(self.clients):
            try:
                await ws.send(lua)
                delivered += 1
            except Exception:
                self.clients.discard(ws)
        return delivered

    @property
    def connected(self) -> bool:
        return bool(self.clients)

    @property
    def uptime(self) -> float:
        return time.time() - self.started


bridge = Bridge()


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
    """Wrap user code so syntax AND runtime errors are reported instead of silently lost."""
    code = code.replace("\r\n", "\n").replace("\r", "\n")
    level = 0
    while f"]{'=' * level}]" in code:  # choose a long-bracket level the code doesn't contain
        level += 1
    eq = "=" * level
    return (
        f"local __src = [{eq}[\n{code}\n]{eq}]\n"
        "local __fn, __err = loadstring(__src)\n"
        "if not __fn then warn('[Discord Exec] Syntax error: ' .. tostring(__err)) return end\n"
        "local __ok, __res = pcall(__fn)\n"
        "if not __ok then warn('[Discord Exec] Runtime error: ' .. tostring(__res)) end"
    )


# ==============================================================================
# 📜 LUA FEATURE SCRIPTS  (sent to Roblox as-is; __ENABLE__ is replaced with true/false)
# ==============================================================================
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


# ==============================================================================
# 🎮 FEATURE REGISTRY — one table drives the slash commands AND the /panel buttons
# ==============================================================================
@dataclass(frozen=True)
class Feature:
    key: str
    name: str
    emoji: str
    script_on: str
    script_off: Optional[str] = None   # None -> reuse script_on with __ENABLE__ = false
    toggle: bool = True                # False = one-shot action (no ON/OFF state)
    on_title: str = ""
    on_text: str = ""
    off_title: str = ""
    off_text: str = ""
    on_colour: int = Colour.INFO
    off_colour: int = Colour.DARK

    def script(self, on: bool) -> str:
        if on:
            return self.script_on.replace("__ENABLE__", "true")
        if self.script_off is not None:
            return self.script_off
        return self.script_on.replace("__ENABLE__", "false")


ESP = Feature(
    "esp", "ESP", "👁️", ESP_SCRIPT,
    on_title="👁️ ESP ENABLED",
    on_text="Đã bật **ESP** (Highlight người chơi, tự cập nhật người mới)!\nPlayer highlights are now visible.",
    off_title="🙈 ESP DISABLED",
    off_text="Đã tắt **ESP** và xóa toàn bộ Highlight!\nAll highlights removed.",
    on_colour=Colour.PINK)
FLY = Feature(
    "fly", "Fly", "✈️", FLY_SCRIPT, UNFLY_SCRIPT,
    on_title="✈️ FLY ENABLED (Infinite Yield Core)",
    on_text="Đã bật **Fly Mode chuẩn Infinite Yield**!\nSử dụng WASD + Q/E để di chuyển.",
    off_title="🛑 FLY DISABLED",
    off_text="Đã tắt **Fly Mode** và khôi phục vật lý ban đầu!\nFlight disabled, physics restored.",
    on_colour=Colour.INFO, off_colour=Colour.ERROR)
CLICKTP = Feature(
    "clicktp", "Click-TP", "🖱️", CLICK_TP_SCRIPT,
    on_title="🖱️ CLICK-TO-TP ENABLED",
    on_text="Đã bật **Click-to-TP**!\nGiữ **Ctrl + Click chuột trái** để dịch chuyển / Hold **Ctrl + Left Click** to teleport.",
    off_title="🖱️ CLICK-TO-TP DISABLED",
    off_text="Đã tắt **Click-to-TP**!\nClick-to-TP turned off.",
    on_colour=Colour.WARNING)
AUTOHEAL = Feature(
    "autoheal", "Auto-Heal", "❤️", AUTO_HEAL_SCRIPT,
    on_title="❤️ AUTO-HEAL ENABLED",
    on_text="Đã bật **Auto-Heal** (tự động hồi đầy máu liên tục)!\nHealth will refill automatically.",
    off_title="💔 AUTO-HEAL DISABLED",
    off_text="Đã tắt **Auto-Heal**!\nAuto-Heal turned off.",
    on_colour=Colour.ERROR)
FPS = Feature(
    "fps", "FPS Boost", "🚀", FPS_BOOST_SCRIPT, toggle=False,
    on_title="🚀 FPS BOOST ENABLED",
    on_text="Đã kích hoạt **FPS Boost** (tối ưu hóa đồ họa thành công)!\nGraphics optimised for performance.",
    on_colour=Colour.TEAL)

PANEL_TOGGLES = (ESP, FLY, CLICKTP, AUTOHEAL)


async def apply_feature(feature: Feature, on: bool = True) -> bool:
    """Send a feature to Roblox. Returns False when no client is connected."""
    if not await bridge.send(feature.script(on)):
        return False
    if feature.toggle:
        bridge.features[feature.key] = on
    return True


# ==============================================================================
# 🧩 EMBEDS
# ==============================================================================
def make_embed(title: str, description: Optional[str] = None, colour: int = Colour.INFO) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, colour=colour, timestamp=discord.utils.utcnow())
    embed.set_footer(text="ExecutorOnDiscord • Bot Automation System")
    return embed


def error_embed(error) -> discord.Embed:
    return make_embed("❌ Lỗi / Error", f"```{str(error)[:1500]}```", Colour.ERROR)


def warn_embed(title: str, text: str) -> discord.Embed:
    return make_embed(title, text, Colour.WARNING)


def code_block(code: str, limit: int = 1500, lang: str = "lua") -> str:
    code = code.strip().replace("```", "`\u200b``")
    if len(code) > limit:
        code = code[:limit] + "\n-- ... (đã rút gọn / truncated)"
    return f"```{lang}\n{code}\n```"


def loadstring_snippet() -> str:
    return f'loadstring(game:HttpGet("{GITHUB_RAW_SCRIPT}"))()'


def format_uptime(seconds: float) -> str:
    hours, rest = divmod(int(seconds), 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}h {minutes}m {secs}s" if hours else f"{minutes}m {secs}s"


def roblox_running() -> bool:
    return any((p.info["name"] or "").lower() in ROBLOX_PROCESSES for p in psutil.process_iter(["name"]))


def not_connected_embed() -> discord.Embed:
    embed = make_embed("🔴 DISCONNECTED",
                       "Chưa kết nối WebSocket với Roblox!\nNo active Roblox client connected!", Colour.ERROR)
    embed.add_field(name="💡 Cách kết nối / How to connect",
                    value="Chạy lệnh `/inject` để xem hướng dẫn.\nRun `/inject` for instructions.", inline=False)
    return embed


def wrong_channel_embed() -> discord.Embed:
    return warn_embed("⚠️ Sai kênh / Wrong channel",
                      f"Lệnh này chỉ dùng trong kênh `#{DEBUG_CHANNEL}`!\n"
                      f"This command can only be used in `#{DEBUG_CHANNEL}`!")


def denied_embed() -> discord.Embed:
    return make_embed("⛔ Không có quyền / Access denied",
                      "Bạn không có trong danh sách được phép dùng bot này.\n"
                      "You are not on this bot's allowed users list.", Colour.ERROR)


async def build_status_embed(show_loadstring: bool = False) -> discord.Embed:
    running = await asyncio.to_thread(roblox_running)  # psutil scan can be slow
    clients = len(bridge.clients)

    if clients and running:
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
    embed.add_field(name="⏱️ Uptime", value=f"`{format_uptime(bridge.uptime)}`", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    if show_loadstring and running and not clients:
        embed.add_field(name="📋 Chạy trong Executor / Run in your executor",
                        value=code_block(loadstring_snippet()), inline=False)
    return embed


HELP_SECTIONS: List[Tuple[str, str, str]] = [  # (emoji, title, body)
    ("📜", "Lệnh Tiền Tố / Prefix Commands (`!` hoặc `.`)",
     "`!exec <script>` — Script dài hoặc file `.lua`/`.txt` / Long scripts & files\n"
     "`!panel` — Bảng điều khiển / Control panel\n"
     "`!help` — Xem hướng dẫn này / Show this help"),
    ("⚡", "Thực Thi / Execution",
     "`/panel` — 🎛️ Bảng điều khiển bằng nút / Button control panel\n"
     "`/exec [code]` — Gửi script (để trống = mở ô nhập lớn) / Run a script (empty = big editor box)\n"
     "`/findscript <source> <keyword>` — Tìm script Rscripts / ScriptBlox"),
    ("🎮", "Tính Năng / Features",
     "`/esp [on|off]` — 👁️ Nhìn xuyên tường / Player ESP\n"
     "`/fly` · `/unfly` — ✈️ Bay / Flight mode\n"
     "`/clicktotp [on|off]` — 🖱️ Ctrl+Click dịch chuyển / Click-to-TP\n"
     "`/autoheal [on|off]` — ❤️ Tự hồi máu / Auto-Heal\n"
     "`/fpsboost` — 🚀 Tăng FPS / Boost FPS"),
    ("🧰", "Hệ Thống / System",
     "`/inject` — 🔌 Kiểm tra & kết nối / Check & connect\n"
     "`/status` — 📊 Trạng thái / Status\n"
     "`/cre` — 🌟 Thông tin tác giả / Credits"),
]


def build_help_embed(section: Optional[int] = None) -> discord.Embed:
    embed = make_embed("📖 Executor Hub — Hướng Dẫn / Help",
                       "Hệ thống quản lý Roblox qua WebSocket\nWebSocket Management System", Colour.PURPLE)
    for index, (emoji, title, body) in enumerate(HELP_SECTIONS):
        if section is None or section == index:
            embed.add_field(name=f"{emoji} {title}", value=body, inline=False)
    return embed


def build_panel_embed() -> discord.Embed:
    embed = make_embed("🎛️ CONTROL PANEL",
                       "Nhấn nút bên dưới để điều khiển Roblox.\nTap a button below to control Roblox.",
                       Colour.SUCCESS if bridge.connected else Colour.ERROR)
    embed.add_field(
        name="🔌 Bridge",
        value=(f"🟢 Connected · `{len(bridge.clients)}` client(s)" if bridge.connected
               else "🔴 Not connected — run `/inject`"),
        inline=False)
    embed.add_field(name="Features", inline=True, value="\n".join(
        f"{'🟢' if bridge.features.get(f.key) else '⚫'} {f.emoji} **{f.name}**" for f in PANEL_TOGGLES))
    embed.add_field(name="📡 Latency", value=f"`{round(bot.latency * 1000)} ms`", inline=True)
    embed.add_field(name="⏱️ Uptime", value=f"`{format_uptime(bridge.uptime)}`", inline=True)
    return embed


def build_exec_embed(code: str, user, delivered: int, elapsed_ms: int, source: str) -> discord.Embed:
    embed = make_embed("⚡ SCRIPT EXECUTED",
                       "Đã gửi script tới Roblox thành công!\nScript delivered to Roblox successfully.",
                       Colour.SUCCESS)
    embed.set_author(name=f"{user.display_name} • Executor", icon_url=user.display_avatar.url)
    embed.add_field(name="📦 Size", value=f"`{len(code):,}` chars", inline=True)
    embed.add_field(name="📄 Lines", value=f"`{code.strip().count(chr(10)) + 1:,}`", inline=True)
    embed.add_field(name="📡 Delivered", value=f"`{delivered}` client(s)", inline=True)
    embed.add_field(name="🧭 Source", value=source, inline=True)
    embed.add_field(name="⏱️ Sent in", value=f"`{elapsed_ms} ms`", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="📜 Script preview", value=code_block(code, limit=900), inline=False)
    return embed


async def execute_script(code: str, user, source: str) -> Tuple[discord.Embed, bool]:
    """Wrap + send a script. Returns (embed to show, success)."""
    started = time.perf_counter()
    log("info", f"{user} ran a script ({len(code):,} chars) via {source}")
    delivered = await bridge.send(wrap_lua(code))
    if delivered:
        elapsed = round((time.perf_counter() - started) * 1000)
        return build_exec_embed(code, user, delivered, elapsed, source), True

    embed = not_connected_embed()
    embed.set_author(name=f"{user.display_name} • Executor", icon_url=user.display_avatar.url)
    embed.add_field(name="🧭 Source", value=source, inline=True)
    embed.add_field(name="📦 Script", value=f"`{len(code):,}` chars (chưa gửi / not sent)", inline=True)
    return embed, False


# ==============================================================================
# 🤖 BOT + GUARDS
# ==============================================================================
class ExecutorBot(commands.Bot):
    async def setup_hook(self) -> None:  # runs once per start (on_ready fires on every reconnect)
        try:
            synced = await self.tree.sync()
            log("ok", f"Synced {len(synced)} slash command(s).")
        except Exception as exc:
            log("error", f"Sync error: {exc}")

        self.add_view(PanelView())  # keeps /panel buttons alive across restarts
        if not ALLOWED_USER_IDS:
            log("warn", f"ALLOWED_USER_IDS is empty: anyone in #{DEBUG_CHANNEL} can run Lua on your PC. Add your user ID!")

        self.ws_task = asyncio.create_task(bridge.serve())
        self.ws_task.add_done_callback(
            lambda t: log("error", f"WebSocket server stopped: {t.exception()}")
            if not t.cancelled() and t.exception() else None)


intents = discord.Intents.default()
intents.message_content = True  # needed for the !exec / .exec prefix commands
bot = ExecutorBot(command_prefix=[".", "!"], intents=intents, help_command=None)


@bot.event
async def on_ready():
    log("ok", f"Bot logged in as: {bot.user} (English/Vietnamese Dual Mode)")
    try:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Roblox • /help"))
    except Exception:
        pass


def in_debug_channel(channel) -> bool:
    return getattr(channel, "name", None) == DEBUG_CHANNEL  # DMs have no .name


def is_allowed_user(user) -> bool:
    return not ALLOWED_USER_IDS or user.id in ALLOWED_USER_IDS


async def interaction_allowed(interaction: discord.Interaction) -> bool:
    """Channel + user check shared by slash commands, buttons, menus and modals."""
    if not in_debug_channel(interaction.channel):
        await interaction.response.send_message(embed=wrong_channel_embed(), ephemeral=True)
        return False
    if not is_allowed_user(interaction.user):
        await interaction.response.send_message(embed=denied_embed(), ephemeral=True)
        return False
    return True


def guarded():
    return app_commands.check(interaction_allowed)


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
        return  # already answered by the guard
    log("error", f"Command error: {error}")
    try:
        send = interaction.followup.send if interaction.response.is_done() else interaction.response.send_message
        await send(embed=error_embed(error), ephemeral=True)
    except discord.HTTPException:
        pass


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return  # a message that merely starts with "." or "!"
    log("error", f"Prefix command error: {error}")
    try:
        await ctx.send(embed=error_embed(error))
    except discord.HTTPException:
        pass


# ==============================================================================
# 🎛️ INTERACTIVE UI — modals, buttons, menus
# ==============================================================================
class GuardedView(discord.ui.View):
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await interaction_allowed(interaction)


class ExecModal(discord.ui.Modal, title="⚡ Run Lua script"):
    """Big editor box: /exec with no argument, or the panel's Run Script button."""
    code = discord.ui.TextInput(label="Lua code / Mã Lua", style=discord.TextStyle.paragraph,
                                placeholder='print("Hello from Discord!")', max_length=4000, required=True)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        code = strip_code_fence(str(self.code.value))
        embed, ok = await execute_script(code, interaction.user, "🪟 Editor box")
        await interaction.response.send_message(embed=embed, view=ExecResultView(code) if ok else None, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        log("error", f"Modal error: {error}")
        try:
            await interaction.response.send_message(embed=error_embed(error), ephemeral=True)
        except discord.HTTPException:
            pass


class ExecResultView(GuardedView):
    def __init__(self, code: str):
        super().__init__(timeout=300)
        self.code = code

    @discord.ui.button(label="Run again", emoji="🔁", style=discord.ButtonStyle.primary)
    async def run_again(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed, _ = await execute_script(self.code, interaction.user, "🔁 Run again")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label="Tất cả / Overview", value="all", emoji="📖")]
        options += [discord.SelectOption(label=title.split(" (")[0], value=str(i), emoji=emoji)
                    for i, (emoji, title, _) in enumerate(HELP_SECTIONS)]
        super().__init__(placeholder="Chọn mục / Pick a category…", options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        choice = self.values[0]
        embed = build_help_embed(None if choice == "all" else int(choice))
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(GuardedView):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(HelpSelect())
        self.add_item(discord.ui.Button(label="GitHub", emoji="🔗", url=REPO_URL))


class StatusView(GuardedView):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.secondary)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.edit_original_response(embed=await build_status_embed(show_loadstring=True), view=self)

    @discord.ui.button(label="Loadstring", emoji="📋", style=discord.ButtonStyle.primary)
    async def loadstring(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "📋 Dán vào executor / Paste into your executor:\n" + code_block(loadstring_snippet()), ephemeral=True)


class PanelView(GuardedView):
    """Persistent button panel. Every button has a fixed custom_id so it survives restarts."""

    def __init__(self):
        super().__init__(timeout=None)
        for feature in PANEL_TOGGLES:
            self._add(f"panel:{feature.key}", feature.emoji, feature.name, 0, self._toggle_callback(feature))
        self._add("panel:fps", FPS.emoji, FPS.name, 1, self._fps, discord.ButtonStyle.primary)
        self._add("panel:exec", "⚡", "Run Script", 1, self._exec, discord.ButtonStyle.primary)
        self._add("panel:status", "📊", "Status", 1, self._status)
        self._add("panel:help", "📖", "Help", 1, self._help)
        self._add("panel:refresh", "🔄", None, 1, self._refresh)
        self.refresh_styles()

    def _add(self, custom_id, emoji, label, row, callback, style=discord.ButtonStyle.secondary) -> None:
        button = discord.ui.Button(custom_id=custom_id, emoji=emoji, label=label, row=row, style=style)
        button.callback = callback
        self.add_item(button)

    def refresh_styles(self) -> None:
        for feature in PANEL_TOGGLES:
            button = next(b for b in self.children if getattr(b, "custom_id", None) == f"panel:{feature.key}")
            on = bridge.features.get(feature.key, False)
            button.label = f"{feature.name} · {'ON' if on else 'OFF'}"
            button.style = discord.ButtonStyle.success if on else discord.ButtonStyle.secondary

    def _toggle_callback(self, feature: Feature):
        async def callback(interaction: discord.Interaction) -> None:
            if not await apply_feature(feature, not bridge.features.get(feature.key, False)):
                return await interaction.response.send_message(embed=not_connected_embed(), ephemeral=True)
            self.refresh_styles()
            await interaction.response.edit_message(embed=build_panel_embed(), view=self)
        return callback

    async def _fps(self, interaction: discord.Interaction) -> None:
        await reply_feature(interaction, FPS)

    async def _exec(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(ExecModal())

    async def _status(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(embed=await build_status_embed(show_loadstring=True),
                                        view=StatusView(), ephemeral=True)

    async def _help(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(embed=build_help_embed(), view=HelpView(), ephemeral=True)

    async def _refresh(self, interaction: discord.Interaction) -> None:
        self.refresh_styles()
        await interaction.response.edit_message(embed=build_panel_embed(), view=self)


# ==============================================================================
# ⚡ SLASH COMMANDS
# ==============================================================================
STATE_CHOICES = [app_commands.Choice(name="ON · Bật", value="on"), app_commands.Choice(name="OFF · Tắt", value="off")]


async def reply_feature(interaction: discord.Interaction, feature: Feature, on: bool = True) -> None:
    if await apply_feature(feature, on):
        embed = make_embed(feature.on_title if on else feature.off_title,
                           feature.on_text if on else feature.off_text,
                           feature.on_colour if on else feature.off_colour)
    else:
        embed = not_connected_embed()
    await interaction.response.send_message(embed=embed, ephemeral=True)


def register_toggle(command: str, feature: Feature, description: str) -> None:
    @bot.tree.command(name=command, description=description)
    @app_commands.describe(state="Bật hoặc tắt / On or off (mặc định / default: on)")
    @app_commands.choices(state=STATE_CHOICES)
    @guarded()
    async def _toggle(interaction: discord.Interaction, state: str = "on"):
        await reply_feature(interaction, feature, state == "on")


def register_action(command: str, feature: Feature, on: bool, description: str) -> None:
    @bot.tree.command(name=command, description=description)
    @guarded()
    async def _action(interaction: discord.Interaction):
        await reply_feature(interaction, feature, on)


register_toggle("esp", ESP, "Bật/tắt nhìn xuyên tường (Highlight) / Toggle player ESP")
register_toggle("clicktotp", CLICKTP, "Bật/tắt Click chuột để dịch chuyển (Ctrl + Click) / Toggle Click-to-TP")
register_toggle("autoheal", AUTOHEAL, "Bật/tắt tự động hồi máu liên tục / Toggle Auto-Heal")
register_action("fly", FLY, True, "Bật chế độ bay chuẩn Infinite Yield / Enable Infinite Yield Fly mode")
register_action("unfly", FLY, False, "Tắt chế độ bay Infinite Yield / Disable Fly mode")
register_action("fpsboost", FPS, True, "Tối ưu hóa đồ họa, giảm lag và tăng FPS / Boost FPS & reduce lag")


@bot.tree.command(name="panel", description="Bảng điều khiển bằng nút bấm / Button control panel")
@guarded()
async def slash_panel(interaction: discord.Interaction):
    await interaction.response.send_message(embed=build_panel_embed(), view=PanelView())


@bot.tree.command(name="help", description="Xem danh sách lệnh / Show all commands")
@guarded()
async def slash_help(interaction: discord.Interaction):
    await interaction.response.send_message(embed=build_help_embed(), view=HelpView(), ephemeral=True)


@bot.tree.command(name="inject", description="Kiểm tra tiến trình và kết nối / Check process & connection status")
@guarded()
async def slash_inject(interaction: discord.Interaction):
    await interaction.response.send_message(
        embed=await build_status_embed(show_loadstring=True), view=StatusView(), ephemeral=True)


@bot.tree.command(name="status", description="Kiểm tra trạng thái máy chủ WebSocket / Check WebSocket server status")
@guarded()
async def slash_status(interaction: discord.Interaction):
    await interaction.response.send_message(embed=await build_status_embed(), view=StatusView(), ephemeral=True)


@bot.tree.command(name="exec", description="Thực thi mã Lua / Execute Lua code")
@app_commands.describe(code="Mã Lua / Lua code — để trống để mở ô nhập lớn / leave empty to open a big editor box")
@guarded()
async def slash_exec(interaction: discord.Interaction, code: Optional[str] = None):
    if code is None:
        return await interaction.response.send_modal(ExecModal())
    code = strip_code_fence(code)
    if not code:
        return await interaction.response.send_message(
            embed=warn_embed("⚠️ Thiếu mã / Missing code", "Vui lòng nhập mã lệnh Lua! / Please enter Lua code!"),
            ephemeral=True)
    embed, ok = await execute_script(code, interaction.user, "⚡ Slash command")
    await interaction.response.send_message(embed=embed, view=ExecResultView(code) if ok else None, ephemeral=True)


@bot.tree.command(name="findscript", description="Tìm script từ Rscripts hoặc ScriptBlox / Search Rscripts or ScriptBlox")
@app_commands.choices(source=[
    app_commands.Choice(name="Rscripts (rscripts.net)", value="rscripts"),
    app_commands.Choice(name="ScriptBlox (scriptblox.com)", value="scriptblox"),
])
@guarded()
async def slash_findscript(interaction: discord.Interaction, source: str, keyword: str):
    query = quote_plus(keyword)
    if source == "rscripts":
        site, url, colour = "Rscripts", f"https://rscripts.net/scripts?search={query}", Colour.PURPLE
    else:
        site, url, colour = "ScriptBlox", f"https://scriptblox.com/?q={query}", Colour.INFO
    embed = make_embed(f"🌐 Kết quả tìm kiếm từ {site}", f"Từ khóa / Keyword: **{keyword}**", colour)
    embed.add_field(name="🔗 Link tra cứu trực tiếp", value=f"[Bấm vào đây để xem trên {site}]({url})", inline=False)
    embed.add_field(name="💡 Gợi ý lệnh",
                    value="Lấy loadstring từ trang web rồi dùng `/exec` để chạy.", inline=False)
    embed.set_footer(text=f"Nguồn: {site} | Bot Automation System")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="cre", description="Thông tin tác giả và dự án / Credits & Information")
@guarded()
async def slash_cre(interaction: discord.Interaction):
    embed = make_embed("🌟 ExecutorOnDiscord — Credits",
                       "Cầu nối WebSocket giữa Discord Bot và Roblox Client.\n"
                       "WebSocket bridge between a Discord bot and the Roblox client.", Colour.GOLD)
    embed.add_field(name="👨‍💻 Developer / Tác giả", value="Videccode (idea: @vaehz)", inline=True)
    embed.add_field(name="🌐 Protocol", value=f"Localhost WebSocket (Port {WS_PORT})", inline=True)
    embed.add_field(name="🔗 GitHub Repository", value=f"[ExecutorRobloxOnDiscord]({REPO_URL})", inline=False)
    embed.set_footer(text="Cảm ơn bạn đã sử dụng hệ thống tự động hóa này!")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==============================================================================
# 🛠️ PREFIX COMMANDS  (!exec is best for long scripts and attached files)
# ==============================================================================
@bot.command(name="help")
async def legacy_help(ctx: commands.Context):
    if await guard_ctx(ctx):
        await ctx.send(embed=build_help_embed(), view=HelpView())


@bot.command(name="panel")
async def legacy_panel(ctx: commands.Context):
    if await guard_ctx(ctx):
        await ctx.send(embed=build_panel_embed(), view=PanelView())


@bot.command(name="exec")
async def legacy_exec(ctx: commands.Context, *, script_code: Optional[str] = None):
    """!exec <code> — or attach a .lua / .txt file."""
    if not await guard_ctx(ctx):
        return

    source = "💬 Prefix command"
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        limit_mb = MAX_FILE_BYTES // (1024 * 1024)
        if not attachment.filename.lower().endswith((".lua", ".txt")):
            return await ctx.send(embed=warn_embed(
                "⚠️ Sai định dạng / Unsupported file",
                "Chỉ hỗ trợ file `.lua` hoặc `.txt`.\nOnly `.lua` or `.txt` files are supported."))
        if attachment.size > MAX_FILE_BYTES:
            return await ctx.send(embed=warn_embed(
                "⚠️ File quá lớn / File too large", f"Tối đa {limit_mb} MB.\nMaximum size is {limit_mb} MB."))
        try:
            # utf-8-sig strips the BOM Windows Notepad adds, which would break loadstring
            script_code = (await attachment.read()).decode("utf-8-sig")
        except Exception as exc:
            return await ctx.send(embed=error_embed(exc))
        source = f"📎 File `{attachment.filename}`"
    elif script_code:
        script_code = strip_code_fence(script_code)

    if not script_code or not script_code.strip():
        return await ctx.send(embed=warn_embed(
            "⚠️ Thiếu script / Missing script",
            "Vui lòng nhập script hoặc đính kèm file `.lua`\nPlease provide script code or attach a file!"))

    embed, ok = await execute_script(script_code, ctx.author, source)
    await ctx.send(embed=embed, view=ExecResultView(script_code) if ok else None)
    try:
        await ctx.message.add_reaction("✅" if ok else "❌")
    except discord.HTTPException:
        pass


# ==============================================================================
# 🚀 START
# ==============================================================================
def main() -> None:
    print_banner()

    token = load_token() or prompt_for_token()
    if not token:
        log("error", "Chưa có token! Chạy lại và dán token, hoặc dùng token.txt / biến môi trường DISCORD_BOT_TOKEN.")
        log("error", "No bot token! Run again and paste it, or use token.txt / the DISCORD_BOT_TOKEN env var.")
        log("info", "Get one at: https://discord.com/developers/applications → Bot → Reset Token")
        pause_and_exit(1)
    if not looks_like_token(token):
        log("warn", "Token trông không đúng định dạng. / Token looks malformed.")

    log("info", "Starting bot...")
    try:
        bot.run(token, log_level=logging.WARNING)
    except discord.LoginFailure:
        log("error", "Token không hợp lệ hoặc đã bị reset. / Invalid or reset token — generate a new one.")
        try:  # if the bad token came from token.txt, offer to clear it
            if (TOKEN_FILE.is_file() and clean_token(TOKEN_FILE.read_text(encoding="utf-8-sig")) == token
                    and sys.stdin and sys.stdin.isatty()):
                answer = ask("  Xóa token đã lưu? / Delete the saved token so you can re-enter it? [Y/n]: ") or "n"
                if answer.strip().lower() not in ("n", "no"):
                    TOKEN_FILE.unlink()
                    log("ok", "Đã xóa token.txt — chạy lại để nhập token mới. / token.txt deleted — run again.")
        except OSError:
            pass
        pause_and_exit(1)
    except discord.PrivilegedIntentsRequired:
        log("error", "Bật 'Message Content Intent' trong Developer Portal → Bot → Privileged Gateway Intents.")
        log("error", "Enable 'Message Content Intent' in Developer Portal → Bot → Privileged Gateway Intents.")
        pause_and_exit(1)


if __name__ == "__main__":
    main()
