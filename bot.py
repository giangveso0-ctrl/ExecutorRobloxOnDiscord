import os
import time
import asyncio
import datetime
from urllib.parse import quote_plus

import psutil
import websockets
import discord
from discord.ext import commands
from discord import app_commands

# ==============================================================================
# 🔑 CONFIGURATION / CẤU HÌNH BOT
# ==============================================================================
DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"  # Thay token của bạn vào đây
GITHUB_RAW_SCRIPT = "https://raw.githubusercontent.com/giangveso0-ctrl/RobloxOnDiscord-Test/main/bridge.lua"
REPO_URL = "https://github.com/giangveso0-ctrl/RobloxOnDiscord-Test"
WS_HOST = "localhost"
WS_PORT = 8765
DEBUG_CHANNEL = "debug"

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


# Makes ANSI colours work in Windows CMD / PowerShell
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


# ==============================================================================
# 🤖 BOT SETUP
# ==============================================================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=['.', '!'], intents=intents)
bot.remove_command('help')

# Roblox clients currently connected over WebSocket
connected_clients = set()
START_TIME = time.time()
_ws_started = False


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
        p.info['name'] and p.info['name'].lower() == "robloxplayerbeta.exe"
        for p in psutil.process_iter(['name'])
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


def build_status_embed(show_loadstring: bool = False) -> discord.Embed:
    running = roblox_running()
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
            "`!exec <script>` — Chạy script dài hoặc file đính kèm / Long scripts & files\n"
            "`!status` — Xem kết nối / View connections"
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
            "`/esp` — 👁️ Nhìn xuyên tường / Player ESP\n"
            "`/fly` · `/unfly` — ✈️ Bay / Flight mode\n"
            "`/clicktotp` — 🖱️ Ctrl+Click dịch chuyển / Click-to-TP\n"
            "`/autoheal` — ❤️ Tự hồi máu / Auto-Heal\n"
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
# 🌐 WEBSOCKET SERVER (CẦU NỐI ROBLOX)
# ==============================================================================
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


async def start_websocket_server():
    async with websockets.serve(ws_handler, WS_HOST, WS_PORT):
        log("ok", f"WebSocket Server running at ws://{WS_HOST}:{WS_PORT}")
        await asyncio.Future()


@bot.event
async def on_ready():
    global _ws_started
    log("ok", f"Bot logged in as: {bot.user} (English/Vietnamese Dual Mode)")
    try:
        synced = await bot.tree.sync()
        log("ok", f"Synced {len(synced)} Slash Command(s).")
    except Exception as e:
        log("error", f"Sync error: {e}")

    if not _ws_started:
        _ws_started = True
        bot.loop.create_task(start_websocket_server())


async def send_to_roblox(script_code: str) -> bool:
    if not connected_clients:
        return False

    dead_sockets = set()
    for ws in list(connected_clients):
        try:
            await ws.send(script_code)
        except Exception:
            dead_sockets.add(ws)

    for ws in dead_sockets:
        connected_clients.discard(ws)

    return len(connected_clients) > 0


def is_debug_channel():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.channel and interaction.channel.name == DEBUG_CHANNEL:
            return True
        await interaction.response.send_message(embed=wrong_channel_embed(), ephemeral=True)
        return False
    return app_commands.check(predicate)


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        return  # already answered by the channel check
    log("error", f"Command error: {error}")
    embed = make_embed("❌ Lỗi / Error", f"```{error}```", Colour.ERROR)
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def run_feature(interaction: discord.Interaction, script: str, *, title: str, description: str, colour: int):
    """Send a Lua feature script to Roblox and answer with a coloured embed."""
    if await send_to_roblox(script):
        embed = make_embed(title, description, colour)
    else:
        embed = not_connected_embed()
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==============================================================================
# 🛠️ TRADITIONAL COMMANDS (!exec chuyên dụng cho script dài & file đính kèm)
# ==============================================================================

@bot.command(name="help")
async def legacy_help(ctx):
    if ctx.channel.name != DEBUG_CHANNEL:
        return await ctx.send(embed=wrong_channel_embed())
    await ctx.send(embed=build_help_embed())


@bot.command(name="status")
async def legacy_status(ctx):
    if ctx.channel.name != DEBUG_CHANNEL:
        return await ctx.send(embed=wrong_channel_embed())
    await ctx.send(embed=build_status_embed())


@bot.command(name="exec")
async def legacy_exec(ctx, *, script_code: str = None):
    """Lệnh !exec tối ưu chuyên sâu cho việc nhận script dài và file đính kèm .lua/.txt"""
    if ctx.channel.name != DEBUG_CHANNEL:
        return await ctx.send(embed=wrong_channel_embed())

    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if attachment.filename.endswith(('.lua', '.txt')):
            try:
                script_code = (await attachment.read()).decode('utf-8')
            except Exception as e:
                return await ctx.send(embed=make_embed(
                    "❌ Lỗi đọc file / File read error", f"```{e}```", Colour.ERROR))

    if not script_code:
        return await ctx.send(embed=make_embed(
            "⚠️ Thiếu script / Missing script",
            "Vui lòng nhập nội dung script hoặc đính kèm file `.lua`\n"
            "Please provide script code or attach a file!",
            Colour.WARNING))

    wrapped_code = f"pcall(function()\n{script_code}\nend)"

    if await send_to_roblox(wrapped_code):
        embed = make_embed(
            "⚡ LONG SCRIPT EXECUTED",
            "Đã gửi script dài tới Roblox thành công!\nScript sent to Roblox successfully!",
            Colour.SUCCESS)
        embed.add_field(name=f"📜 Script ({len(script_code)} ký tự / chars)",
                        value=code_block(script_code, limit=900), inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send(embed=not_connected_embed())


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
    await interaction.response.send_message(embed=build_status_embed(show_loadstring=True), ephemeral=True)


@bot.tree.command(name="exec", description="Thực thi nhanh mã Lua ngắn / Quick execute short Lua code")
@is_debug_channel()
async def slash_exec(interaction: discord.Interaction, code: str):
    if not code:
        return await interaction.response.send_message(embed=make_embed(
            "⚠️ Thiếu mã / Missing code", "Vui lòng nhập mã lệnh Lua! / Please enter Lua code!",
            Colour.WARNING), ephemeral=True)

    wrapped_code = f"pcall(function()\n{code}\nend)"

    if await send_to_roblox(wrapped_code):
        embed = make_embed(
            "⚡ QUICK EXEC",
            "Đã gửi thành công!\nSent successfully!",
            Colour.SUCCESS)
        embed.add_field(name="📜 Script", value=code_block(code, limit=900), inline=False)
    else:
        embed = not_connected_embed()
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="findscript", description="Tìm kiếm script từ Rscripts hoặc ScriptBlox / Search scripts from Rscripts or ScriptBlox")
@app_commands.choices(source=[
    app_commands.Choice(name="Rscripts (rscripts.net)", value="rscripts"),
    app_commands.Choice(name="ScriptBlox (scriptblox.com)", value="scriptblox")
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


@bot.tree.command(name="esp", description="Bật tính năng nhìn xuyên tường (ESP Box/Name) / Enable player ESP")
@is_debug_channel()
async def slash_esp(interaction: discord.Interaction):
    script = """
    pcall(function()
        local Players = game:GetService("Players")
        for _, plr in ipairs(Players:GetPlayers()) do
            if plr ~= Players.LocalPlayer then
                local char = plr.Character
                if char and not char:FindFirstChild("DiscordESP") then
                    local highlight = Instance.new("Highlight")
                    highlight.Name = "DiscordESP"
                    highlight.Adornee = char
                    highlight.FillColor = Color3.fromRGB(255, 0, 0)
                    highlight.OutlineColor = Color3.fromRGB(255, 255, 255)
                    highlight.FillTransparency = 0.5
                    highlight.Parent = char
                end
            end
        end
    end)
    """
    await run_feature(interaction, script,
                      title="👁️ ESP ENABLED",
                      description="Đã bật **ESP** (Highlight người chơi)!\nPlayer highlights are now visible.",
                      colour=Colour.PINK)


@bot.tree.command(name="fpsboost", description="Tối ưu hóa đồ họa, giảm lag và tăng FPS / Boost FPS & reduce lag")
@is_debug_channel()
async def slash_fpsboost(interaction: discord.Interaction):
    script = """
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
        settings().Rendering.QualityLevel = Enum.QualityLevel.Level0
    end)
    """
    await run_feature(interaction, script,
                      title="🚀 FPS BOOST ENABLED",
                      description="Đã kích hoạt **FPS Boost** (tối ưu hóa đồ họa thành công)!\nGraphics optimised for performance.",
                      colour=Colour.TEAL)


@bot.tree.command(name="fly", description="Bật chế độ bay chuẩn Infinite Yield / Enable Infinite Yield Fly mode")
@is_debug_channel()
async def slash_fly(interaction: discord.Interaction):
    script = """
    pcall(function()
        local Players = game:GetService("Players")
        local LocalPlayer = Players.LocalPlayer
        local UserInputService = game:GetService("UserInputService")
        local Workspace = game:GetService("Workspace")

        if _G.IYNOFLY then _G.IYNOFLY() end

        _G.FLYING = true
        local iyflyspeed = 1
        local CONTROL = {F = 0, B = 0, L = 0, R = 0, Q = 0, E = 0}
        local lCONTROL = {F = 0, B = 0, L = 0, R = 0, Q = 0, E = 0}
        local SPEED = 0

        local char = LocalPlayer.Character or LocalPlayer.CharacterAdded:Wait()
        local torso = char:FindFirstChild("Torso") or char:FindFirstChild("HumanoidRootPart")
        local humanoid = char:FindFirstChildOfClass("Humanoid")
        if not torso or not humanoid then return end

        local BG = Instance.new("BodyGyro")
        local BV = Instance.new("BodyVelocity")
        
        BG.Name = "IY_BodyGyro"
        BG.P = 9e4
        BG.maxTorque = Vector3.new(9e9, 9e9, 9e9)
        BG.cframe = torso.CFrame
        BG.Parent = torso

        BV.Name = "IY_BodyVelocity"
        BV.velocity = Vector3.new(0, 0, 0)
        BV.maxForce = Vector3.new(9e9, 9e9, 9e9)
        BV.Parent = torso

        humanoid.PlatformStand = true

        local flyKeyDown = UserInputService.InputBegan:Connect(function(input, gpe)
            if gpe then return end
            if input.KeyCode == Enum.KeyCode.W then CONTROL.F = iyflyspeed
            elseif input.KeyCode == Enum.KeyCode.S then CONTROL.B = -iyflyspeed
            elseif input.KeyCode == Enum.KeyCode.A then CONTROL.L = -iyflyspeed
            elseif input.KeyCode == Enum.KeyCode.D then CONTROL.R = iyflyspeed
            elseif input.KeyCode == Enum.KeyCode.E then CONTROL.Q = iyflyspeed*2
            elseif input.KeyCode == Enum.KeyCode.Q then CONTROL.E = -iyflyspeed*2
            end
        end)

        local flyKeyUp = UserInputService.InputEnded:Connect(function(input, gpe)
            if gpe then return end
            if input.KeyCode == Enum.KeyCode.W then CONTROL.F = 0
            elseif input.KeyCode == Enum.KeyCode.S then CONTROL.B = 0
            elseif input.KeyCode == Enum.KeyCode.A then CONTROL.L = 0
            elseif input.KeyCode == Enum.KeyCode.D then CONTROL.R = 0
            elseif input.KeyCode == Enum.KeyCode.E then CONTROL.Q = 0
            elseif input.KeyCode == Enum.KeyCode.Q then CONTROL.E = 0
            end
        end)

        _G.IYNOFLY = function()
            _G.FLYING = false
            if flyKeyDown then flyKeyDown:Disconnect() end
            if flyKeyUp then flyKeyUp:Disconnect() end
            if _G.FlyLoopConn then _G.FlyLoopConn:Disconnect() end
            
            local c = LocalPlayer.Character
            if c then
                local hum = c:FindFirstChildOfClass("Humanoid")
                if hum then hum.PlatformStand = false end
                local root = c:FindFirstChild("Torso") or c:FindFirstChild("HumanoidRootPart")
                if root then
                    if root:FindFirstChild("IY_BodyGyro") then root.IY_BodyGyro:Destroy() end
                    if root:FindFirstChild("IY_BodyVelocity") then root.IY_BodyVelocity:Destroy() end
                end
            end
        end

        _G.FlyLoopConn = game:GetService("RunService").RenderStepped:Connect(function()
            if not _G.FLYING then return end
            
            if CONTROL.L + CONTROL.R ~= 0 or CONTROL.F + CONTROL.B ~= 0 or CONTROL.Q + CONTROL.E ~= 0 then
                SPEED = 50
            elseif not (CONTROL.L + CONTROL.R ~= 0 or CONTROL.F + CONTROL.B ~= 0 or CONTROL.Q + CONTROL.E ~= 0) and SPEED ~= 0 then
                SPEED = 0
            end
            
            if (CONTROL.L + CONTROL.R) ~= 0 or (CONTROL.F + CONTROL.B) ~= 0 or (CONTROL.Q + CONTROL.E) ~= 0 then
                BV.velocity = ((Workspace.CurrentCamera.CFrame.LookVector * (CONTROL.F + CONTROL.B)) + ((Workspace.CurrentCamera.CFrame * CFrame.new(CONTROL.L + CONTROL.R, (CONTROL.F + CONTROL.B + CONTROL.Q + CONTROL.E) * 0.2, 0).p) - Workspace.CurrentCamera.CFrame.p)) * SPEED
                lCONTROL = {F = CONTROL.F, B = CONTROL.B, L = CONTROL.L, R = CONTROL.R, Q = CONTROL.Q, E = CONTROL.E}
            elseif SPEED ~= 0 then
                BV.velocity = ((Workspace.CurrentCamera.CFrame.LookVector * (lCONTROL.F + lCONTROL.B)) + ((Workspace.CurrentCamera.CFrame * CFrame.new(lCONTROL.L + lCONTROL.R, (lCONTROL.F + lCONTROL.B + lCONTROL.Q + lCONTROL.E) * 0.2, 0).p) - Workspace.CurrentCamera.CFrame.p)) * SPEED
            else
                BV.velocity = Vector3.new(0, 0, 0)
            end
            
            BG.cframe = Workspace.CurrentCamera.CFrame
        end)
    end)
    """
    await run_feature(interaction, script,
                      title="✈️ FLY ENABLED (Infinite Yield Core)",
                      description="Đã bật **Fly Mode chuẩn Infinite Yield**!\nSử dụng WASD + Q/E để di chuyển.",
                      colour=Colour.INFO)


@bot.tree.command(name="unfly", description="Tắt chế độ bay Infinite Yield / Disable Fly mode")
@is_debug_channel()
async def slash_unfly(interaction: discord.Interaction):
    script = """
    pcall(function()
        if _G.IYNOFLY then
            _G.IYNOFLY()
            _G.IYNOFLY = nil
        else
            local LocalPlayer = game:GetService("Players").LocalPlayer
            local char = LocalPlayer.Character
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
    await send_to_roblox(script)
    await interaction.response.send_message(embed=make_embed(
        "🛑 FLY DISABLED",
        "Đã tắt **Fly Mode** và khôi phục vật lý ban đầu!",
        Colour.ERROR), ephemeral=True)


@bot.tree.command(name="clicktotp", description="Bật tính năng Click chuột để dịch chuyển (Ctrl + Click) / Enable Click-to-TP")
@is_debug_channel()
async def slash_clicktotp(interaction: discord.Interaction):
    script = """
    pcall(function()
        local plr = game:GetService("Players").LocalPlayer
        local mouse = plr:GetMouse()
        local uis = game:GetService("UserInputService")
        if _G.ClickTPConn then _G.ClickTPConn:Disconnect() end
        
        _G.ClickTPConn = mouse.Button1Down:Connect(function()
            if uis:IsKeyDown(Enum.KeyCode.LeftControl) or uis:IsKeyDown(Enum.KeyCode.RightControl) then
                local char = plr.Character
                if char and char:FindFirstChild("HumanoidRootPart") then
                    if mouse.Target then
                        char.HumanoidRootPart.CFrame = CFrame.new(mouse.Hit.Position + Vector3.new(0, 3, 0))
                    end
                end
            end
        end)
    end)
    """
    await run_feature(interaction, script,
                      title="🖱️ CLICK-TO-TP ENABLED",
                      description="Đã bật **Click-to-TP**!\nGiữ **Ctrl + Click chuột trái** để dịch chuyển / Hold **Ctrl + Left Click** to teleport.",
                      colour=Colour.WARNING)


@bot.tree.command(name="autoheal", description="Tự động hồi máu tối đa liên tục / Enable Auto-Heal")
@is_debug_channel()
async def slash_autoheal(interaction: discord.Interaction):
    script = """
    pcall(function()
        if _G.AutoHealConn then _G.AutoHealConn:Disconnect() end
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
    await run_feature(interaction, script,
                      title="❤️ AUTO-HEAL ENABLED",
                      description="Đã bật **Auto-Heal** (tự động hồi đầy máu liên tục)!\nHealth will refill automatically.",
                      colour=Colour.ERROR)


@bot.tree.command(name="cre", description="Hiển thị thông tin tác giả và dự án / Credits & Information")
@is_debug_channel()
async def slash_cre(interaction: discord.Interaction):
    embed = make_embed(
        "🌟 RobloxOnDiscord Bridge — Credits",
        "Hệ thống cầu nối WebSocket tương tác giữa Discord Bot và Roblox Client.\n"
        "WebSocket bridge between a Discord bot and the Roblox client.",
        Colour.GOLD)
    embed.add_field(name="👨‍💻 Developer / Tác giả", value="giangveso0-ctrl", inline=True)
    embed.add_field(name="🌐 Protocol", value=f"Localhost WebSocket (Port {WS_PORT})", inline=True)
    embed.add_field(name="🔗 GitHub Repository", value=f"[RobloxOnDiscord-Test]({REPO_URL})", inline=False)
    embed.set_footer(text="Cảm ơn bạn đã sử dụng hệ thống tự động hóa này!")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="status", description="Kiểm tra trạng thái máy chủ WebSocket / Check WebSocket server status")
@is_debug_channel()
async def slash_status(interaction: discord.Interaction):
    await interaction.response.send_message(embed=build_status_embed(), ephemeral=True)


# ==============================================================================
# 🚀 KHỞI CHẠY BOT / START
# ==============================================================================
if __name__ == "__main__":
    print_banner()
    if DISCORD_BOT_TOKEN == "YOUR_DISCORD_BOT_TOKEN_HERE":
        log("error", "Vui lòng thay 'YOUR_DISCORD_BOT_TOKEN_HERE' bằng Token Discord thực tế của bạn!")
        log("error", "Please replace 'YOUR_DISCORD_BOT_TOKEN_HERE' with your real Discord bot token!")
    else:
        log("info", "Starting bot...")
        bot.run(DISCORD_BOT_TOKEN)
