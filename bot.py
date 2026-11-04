import os
import sys
import psutil
import asyncio
import logging
import websockets
import discord
from discord.ext import commands
from discord import app_commands

# ==============================================================================
# 🔑 SECURITY & CONFIGURATION
# ==============================================================================
DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"
SECRET_WS_TOKEN = "FFZ_SECURE_TOKEN_2026"
GITHUB_RAW_SCRIPT = "https://raw.githubusercontent.com/giangveso0-ctrl/RobloxOnDiscord-Test/main/bridge.lua"

# Configure logging output
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BridgeBot")

# Initialize Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=['.', '!'], intents=intents)
bot.remove_command('help')  # Remove default help command

# Set to store connected Roblox WebSocket clients
connected_clients = set()

# ==============================================================================
# 🌐 WEBSOCKET SERVER (ROBLOX BRIDGE)
# ==============================================================================
async def ws_handler(websocket):
    try:
        # Wait for initial auth message from client
        auth_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        connected_clients.add(websocket)
        logger.info(f"🟢 Roblox client connected! Active clients: {len(connected_clients)}")
        
        async for message in websocket:
            pass
    except Exception:
        pass
    finally:
        connected_clients.discard(websocket)
        logger.info(f"🔴 Roblox client disconnected. Active clients: {len(connected_clients)}")

async def start_websocket_server():
    async with websockets.serve(ws_handler, "localhost", 8765, ping_interval=20, ping_timeout=10):
        logger.info("WebSocket Server listening on: ws://localhost:8765")
        await asyncio.Future()

@bot.event
async def on_ready():
    logger.info(f"Bot logged in as: {bot.user}")
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} Slash Commands.")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")
        
    bot.loop.create_task(start_websocket_server())

# Helper function to broadcast Lua scripts to Roblox via WebSocket
async def send_to_roblox(script_code: str) -> bool:
    if not connected_clients:
        return False
        
    dead_sockets = set()
    for ws in list(connected_clients):
        try:
            await ws.send(script_code)
        except Exception:
            dead_sockets.add(ws)
            
    connected_clients.difference_update(dead_sockets)
    return len(connected_clients) > 0

# Check channel permissions for #debug
def is_debug_channel():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.channel and interaction.channel.name == "debug":
            return True
        await interaction.response.send_message("⚠️ This command can only be used in the `#debug` channel!", ephemeral=True)
        return False
    return app_commands.check(predicate)

# ==============================================================================
# 🛠️ LEGACY COMMANDS (! or .)
# ==============================================================================

@bot.command(name="help")
async def legacy_help(ctx):
    if ctx.channel.name != "debug":
        return await ctx.send("⚠️ This command can only be used in `#debug`!")
        
    embed = discord.Embed(
        title="📖 Free Fire Zone Hub - Help Center",
        description="Remote Roblox control bridge via Discord & WebSocket.",
        color=0x3498DB
    )
    embed.add_field(
        name="🛠️ Legacy Commands (`!` or `.`)",
        value=(
            "• `!help` - Display this help manual.\n"
            "• `!inject` - Check Roblox process & connection status.\n"
            "• `!exec <script>` - Execute Lua code via WebSocket.\n"
            "• `!status` - Check server connection status.\n"
            "• `!ping` - Measure bot latency."
        ),
        inline=False
    )
    embed.add_field(
        name="⚡ Slash Commands (`/`)",
        value=(
            "• `/inject` - Check process and WebSocket status.\n"
            "• `/exec` - Execute code or attach `.lua` script file.\n"
            "• `/fly` - Enable directional flight mode.\n"
            "• `/unfly` - Disable flight mode.\n"
            "• `/speed` - Adjust character movement speed.\n"
            "• `/esp` - Toggle player ESP highlight."
        ),
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command(name="inject")
async def legacy_inject(ctx):
    if ctx.channel.name != "debug":
        return await ctx.send("⚠️ This command can only be used in `#debug`!")
        
    target_process = "RobloxPlayerBeta.exe"
    running = False
    pid = None
    
    for proc in psutil.process_iter(['name', 'pid']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == target_process.lower():
                running = True
                pid = proc.info['pid']
                break
        except Exception:
            continue

    is_connected = len(connected_clients) > 0

    if is_connected and running:
        embed = discord.Embed(
            title="🎯 Roblox Connected",
            description=f"Process **{target_process}** detected (PID: `{pid}`).",
            color=0x00FF8C
        )
        embed.add_field(name="Status", value="🟢 **CONNECTED (Bridge Active)**", inline=False)
        embed.add_field(name="Active Clients", value=f"`{len(connected_clients)} Roblox Client(s)`", inline=True)
        await ctx.send(embed=embed)
    elif running and not is_connected:
        embed = discord.Embed(
            title="🎯 Roblox Detected (Pending Injection)",
            description=f"Process **{target_process}** running (PID: `{pid}`), but **script is not loaded**!",
            color=0xFF0000
        )
        embed.add_field(name="Status", value="🔴 **DISCONNECTED (Awaiting Script Execution)**", inline=False)
        embed.add_field(
            name="🚀 Run this loadstring in your Executor:",
            value=f'```lua\nloadstring(game:HttpGet("{GITHUB_RAW_SCRIPT}"))()\n```',
            inline=False
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="⚠️ Process Not Found",
            description=f"**{target_process}** is not running on the system!",
            color=0xFF0000
        )
        embed.add_field(name="Status", value="🔴 **DISCONNECTED**", inline=False)
        await ctx.send(embed=embed)

@bot.command(name="exec")
async def legacy_exec(ctx, *, script_code: str = None):
    if ctx.channel.name != "debug":
        return await ctx.send("⚠️ This command can only be used in `#debug`!")
        
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if attachment.filename.endswith(('.lua', '.txt')):
            script_code = (await attachment.read()).decode('utf-8')
            
    if not script_code:
        return await ctx.send("⚠️ Please provide code text or attach a `.lua` file!")
        
    success = await send_to_roblox(script_code)
    if success:
        embed = discord.Embed(
            title="⚡ [EXECUTE] - Script Sent to Roblox",
            description=f"```lua\n{script_code[:400]}\n```",
            color=0x00FF8C
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send("🔴 **DISCONNECTED**: No active Roblox WebSocket clients found!")

@bot.command(name="status")
async def legacy_status(ctx):
    if ctx.channel.name != "debug":
        return await ctx.send("⚠️ This command can only be used in `#debug`!")
        
    is_connected = len(connected_clients) > 0
    color = 0x00FF8C if is_connected else 0xFF0000
    status_text = "🟢 **CONNECTED**" if is_connected else "🔴 **DISCONNECTED**"
    
    embed = discord.Embed(title="📊 Server Status", color=color)
    embed.add_field(name="Connection", value=status_text, inline=True)
    embed.add_field(name="Active Clients", value=f"`{len(connected_clients)}`", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="ping")
async def legacy_ping(ctx):
    if ctx.channel.name != "debug":
        return await ctx.send("⚠️ This command can only be used in `#debug`!")
    await ctx.send(f"🏓 Pong! Latency: **{round(bot.latency * 1000)}ms**")

# ==============================================================================
# ⚡ SLASH COMMANDS (/)
# ==============================================================================

@bot.tree.command(name="inject", description="Check Roblox process & WebSocket connection status")
@is_debug_channel()
async def slash_inject(interaction: discord.Interaction):
    target_process = "RobloxPlayerBeta.exe"
    running = False
    pid = None
    
    for proc in psutil.process_iter(['name', 'pid']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == target_process.lower():
                running = True
                pid = proc.info['pid']
                break
        except Exception:
            continue

    is_connected = len(connected_clients) > 0

    if is_connected and running:
        embed = discord.Embed(
            title="🎯 Roblox Connected",
            description=f"Process **{target_process}** detected (PID: `{pid}`).",
            color=0x00FF8C
        )
        embed.add_field(name="Status", value="🟢 **CONNECTED (Bridge Active)**", inline=False)
        embed.add_field(name="Active Clients", value=f"`{len(connected_clients)} Roblox Client(s)`", inline=True)
        await interaction.response.send_message(embed=embed)
    elif running and not is_connected:
        embed = discord.Embed(
            title="🎯 Roblox Detected (Pending Injection)",
            description=f"Process **{target_process}** running (PID: `{pid}`), but **script is not loaded**!",
            color=0xFF0000
        )
        embed.add_field(name="Status", value="🔴 **DISCONNECTED (Awaiting Script Execution)**", inline=False)
        embed.add_field(
            name="🚀 Run this loadstring in your Executor:",
            value=f'```lua\nloadstring(game:HttpGet("{GITHUB_RAW_SCRIPT}"))()\n```',
            inline=False
        )
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(
            title="⚠️ Process Not Found",
            description=f"**{target_process}** is not running!",
            color=0xFF0000
        )
        embed.add_field(name="Status", value="🔴 **DISCONNECTED**", inline=False)
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="exec", description="Execute Lua code or upload long .lua script files")
@is_debug_channel()
async def slash_exec(interaction: discord.Interaction, code: str = None, file: discord.Attachment = None):
    script_to_run = None
    if file:
        if file.filename.endswith(('.lua', '.txt')):
            script_to_run = (await file.read()).decode('utf-8')
    elif code:
        script_to_run = code
        
    if not script_to_run:
        return await interaction.response.send_message("⚠️ Please provide code or attach a script file!", ephemeral=True)

    success = await send_to_roblox(script_to_run)
    if success:
        embed = discord.Embed(
            title="⚡ [SLASH EXEC] - Sent to Roblox",
            description=f"```lua\n{script_to_run[:350]}\n```",
            color=0x00FF8C
        )
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("🔴 **DISCONNECTED**: No Roblox clients connected to WebSocket!", ephemeral=True)

@bot.tree.command(name="fly", description="Enable camera-directional flight mode")
@is_debug_channel()
async def slash_fly(interaction: discord.Interaction):
    fly_script = """
    pcall(function()
        if _G.FlyLoop then _G.FlyLoop:Disconnect() end
        local plr = game.Players.LocalPlayer
        local char = plr.Character or plr.CharacterAdded:Wait()
        local hrp = char:FindFirstChild("HumanoidRootPart")
        local hum = char:FindFirstChildOfClass("Humanoid")
        if not hrp or not hum then return end
        local camera = workspace.CurrentCamera
        hum.PlatformStand = true
        local bg = hrp:FindFirstChild("FlyBG") or Instance.new("BodyGyro", hrp)
        bg.Name = "FlyBG" bg.P = 9e4 bg.maxTorque = Vector3.new(9e9, 9e9, 9e9) bg.cframe = hrp.CFrame
        local bv = hrp:FindFirstChild("FlyBV") or Instance.new("BodyVelocity", hrp)
        bv.Name = "FlyBV" bv.maxForce = Vector3.new(9e9, 9e9, 9e9) bv.velocity = Vector3.zero
        _G.FlyLoop = game:GetService("RunService").RenderStepped:Connect(function()
            if not char or not hrp or not hum.PlatformStand then if _G.FlyLoop then _G.FlyLoop:Disconnect() end return end
            bg.cframe = camera.CFrame
            local moveDir = hum.MoveDirection
            if moveDir.Magnitude > 0 then
                bv.velocity = camera.CFrame:VectorToWorldSpace(camera.CFrame:VectorToObjectSpace(CFrame.new(Vector3.zero, camera.CFrame.LookVector):VectorToObjectSpace(moveDir)) * 50)
            else
                bv.velocity = Vector3.zero
            end
        end)
    end)
    """
    success = await send_to_roblox(fly_script)
    if success:
        await interaction.response.send_message("✈️ Activated **Fly Mode**!", ephemeral=True)
    else:
        await interaction.response.send_message("🔴 **DISCONNECTED**: Please connect the script to Roblox first!", ephemeral=True)

@bot.tree.command(name="unfly", description="Disable flight mode")
@is_debug_channel()
async def slash_unfly(interaction: discord.Interaction):
    unfly_script = """
    pcall(function()
        if _G.FlyLoop then _G.FlyLoop:Disconnect() _G.FlyLoop = nil end
        local plr = game.Players.LocalPlayer
        local char = plr.Character
        if char then
            local hum = char:FindFirstChildOfClass("Humanoid")
            local hrp = char:FindFirstChild("HumanoidRootPart")
            if hum then hum.PlatformStand = false end
            if hrp then
                if hrp:FindFirstChild("FlyBG") then hrp.FlyBG:Destroy() end
                if hrp:FindFirstChild("FlyBV") then hrp.FlyBV:Destroy() end
            end
        end
    end)
    """
    await send_to_roblox(unfly_script)
    await interaction.response.send_message("🛑 Disabled **Fly Mode**!", ephemeral=True)

@bot.tree.command(name="speed", description="Adjust character WalkSpeed")
@is_debug_channel()
async def slash_speed(interaction: discord.Interaction, value: int):
    script = f'pcall(function() game.Players.LocalPlayer.Character.Humanoid.WalkSpeed = {value} end)'
    success = await send_to_roblox(script)
    if success:
        await interaction.response.send_message(f"⚡ Set WalkSpeed to: **{value}**", ephemeral=True)
    else:
        await interaction.response.send_message("🔴 **DISCONNECTED**: No WebSocket connection!", ephemeral=True)

@bot.tree.command(name="esp", description="Toggle wallhack ESP")
@is_debug_channel()
async def slash_esp(interaction: discord.Interaction, state: bool):
    if state:
        esp_script = """
        pcall(function()
            if _G.ESP_CleanUp then _G.ESP_CleanUp() end
            _G.ESP_Active = true
            local function createESP(plr)
                if plr == game.Players.LocalPlayer then return end
                local highlight = Instance.new("Highlight")
                highlight.Name = "BridgeESP_" .. plr.Name
                highlight.FillColor = Color3.fromRGB(255, 0, 0)
                highlight.OutlineColor = Color3.fromRGB(255, 255, 255)
                highlight.FillTransparency = 0.5
                local function apply(char) if char then highlight.Adornee = char highlight.Parent = char end end
                apply(plr.Character) plr.CharacterAdded:Connect(apply)
            end
            for _, p in pairs(game.Players:GetPlayers()) do createESP(p) end
            _G.ESP_Conn = game.Players.PlayerAdded:Connect(createESP)
            _G.ESP_CleanUp = function()
                _G.ESP_Active = false
                if _G.ESP_Conn then _G.ESP_Conn:Disconnect() _G.ESP_Conn = nil end
                for _, p in pairs(game.Players:GetPlayers()) do
                    if p.Character then
                        local hl = p.Character:FindFirstChild("BridgeESP_" .. p.Name)
                        if hl then hl:Destroy() end
                    end
                end
            end
        end)
        """
        success = await send_to_roblox(esp_script)
        if success:
            await interaction.response.send_message("👁️ ESP Status: **ON**", ephemeral=True)
        else:
            await interaction.response.send_message("🔴 **DISCONNECTED**: Inject script into Roblox first!", ephemeral=True)
    else:
        esp_off_script = """
        pcall(function()
            if _G.ESP_CleanUp then _G.ESP_CleanUp() _G.ESP_CleanUp = nil end
            for _, v in pairs(workspace:GetDescendants()) do
                if v.Name:find("BridgeESP_") then pcall(function() v:Destroy() end) end
            end
        end)
        """
        await send_to_roblox(esp_off_script)
        await interaction.response.send_message("👁️ ESP Status: **OFF**", ephemeral=True)

@bot.tree.command(name="status", description="Check bridge server status")
@is_debug_channel()
async def slash_status(interaction: discord.Interaction):
    is_connected = len(connected_clients) > 0
    color = 0x00FF8C if is_connected else 0xFF0000
    status_text = "🟢 **CONNECTED**" if is_connected else "🔴 **DISCONNECTED**"
    
    embed = discord.Embed(title="📊 Server Status", color=color)
    embed.add_field(name="Connection", value=status_text, inline=True)
    embed.add_field(name="Active Clients", value=f"`{len(connected_clients)}`", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Start Discord Bot
if __name__ == "__main__":
    if DISCORD_BOT_TOKEN == "YOUR_DISCORD_BOT_TOKEN_HERE":
        print("❌ ERROR: Please edit bot.py and set DISCORD_BOT_TOKEN on line 14!")
    else:
        bot.run(DISCORD_BOT_TOKEN)