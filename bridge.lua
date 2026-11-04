import os
import psutil
import asyncio
import websockets
import discord
from discord.ext import commands
from discord import app_commands

# ==============================================================================
# 🔑 CONFIGURATION (Điền Token Bot Discord của bạn vào đây)
# ==============================================================================
DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"
GITHUB_RAW_SCRIPT = "https://raw.githubusercontent.com/giangveso0-ctrl/RobloxOnDiscord-Test/main/bridge.lua"

# Khởi tạo Bot Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=['.', '!'], intents=intents)
bot.remove_command('help')

# Danh sách lưu trữ các Roblox Client đang kết nối WebSocket
connected_clients = set()

# ==============================================================================
# 🌐 WEBSOCKET SERVER (Nhận kết nối từ Roblox)
# ==============================================================================
async def ws_handler(websocket):
    connected_clients.add(websocket)
    print(f"🟢 Roblox client connected! Total clients: {len(connected_clients)}")
    try:
        async for message in websocket:
            print(f"[RECV FROM ROBLOX]: {message}")
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)
        print(f"🔴 Roblox client disconnected. Total clients: {len(connected_clients)}")

async def start_websocket_server():
    async with websockets.serve(ws_handler, "localhost", 8765):
        print("WebSocket Server is running on ws://localhost:8765")
        await asyncio.Future()

@bot.event
async def on_ready():
    print(f"Bot logged in successfully as: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} Slash Command(s).")
    except Exception as e:
        print(f"Sync error: {e}")
    
    # Khởi động WebSocket server chạy ngầm
    bot.loop.create_task(start_websocket_server())

# Hàm gửi script Lua sang Roblox
async def send_to_roblox(script_code: str) -> bool:
    if not connected_clients:
        return False
    
    dead_sockets = set()
    for ws in connected_clients:
        try:
            await ws.send(script_code)
        except Exception:
            dead_sockets.add(ws)
            
    for ws in dead_sockets:
        connected_clients.remove(ws)
        
    return len(connected_clients) > 0

# Kiểm tra lệnh chỉ được chạy trong kênh #debug
def is_debug_channel():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.channel and interaction.channel.name == "debug":
            return True
        await interaction.response.send_message("⚠️ This command can only be used in `#debug`!", ephemeral=True)
        return False
    return app_commands.check(predicate)

# ==============================================================================
# 🛠️ TRADITIONAL COMMANDS (Lệnh tiền tố ! hoặc .)
# ==============================================================================

@bot.command(name="help")
async def legacy_help(ctx):
    if ctx.channel.name != "debug":
        return await ctx.send("⚠️ This command can only be used in `#debug`!")
    
    embed = discord.Embed(title="📖 Free Fire Zone - Help", color=0x3498DB)
    embed.add_field(name="Commands", value="• `!inject` - Check game & connection status\n• `!exec <code/>` - Send script to Roblox\n• `!status` - View active connections", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="inject")
async def legacy_inject(ctx):
    if ctx.channel.name != "debug":
        return await ctx.send("⚠️ This command can only be used in `#debug`!")
        
    running = any(p.info['name'] and p.info['name'].lower() == "robloxplayerbeta.exe" for p in psutil.process_iter(['name']))
    is_connected = len(connected_clients) > 0

    if is_connected and running:
        await ctx.send("🟢 **CONNECTED**: Roblox process found and WebSocket is active!")
    elif running and not is_connected:
        msg = f"🔴 **DISCONNECTED**: Game running, but script not loaded!\nRun this in your executor:\n```lua\nloadstring(game:HttpGet(\"{GITHUB_RAW_SCRIPT}\"))()\n```"
        await ctx.send(msg)
    else:
        await ctx.send("🔴 **DISCONNECTED**: Roblox process not found!")

@bot.command(name="exec")
async def legacy_exec(ctx, *, script_code: str = None):
    if ctx.channel.name != "debug":
        return await ctx.send("⚠️ This command can only be used in `#debug`!")
        
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if attachment.filename.endswith(('.lua', '.txt')):
            script_code = (await attachment.read()).decode('utf-8')
            
    if not script_code:
        return await ctx.send("⚠️ Please provide code or attach a `.lua` file!")
        
    success = await send_to_roblox(script_code)
    if success:
        await ctx.send(f"⚡ **Executed successfully!**\n```lua\n{script_code[:300]}\n```")
    else:
        await ctx.send("🔴 **DISCONNECTED**: No active Roblox client connected!")

# ==============================================================================
# ⚡ SLASH COMMANDS (Lệnh giao diện /)
# ==============================================================================

@bot.tree.command(name="inject", description="Check Roblox process and connection status")
@is_debug_channel()
async def slash_inject(interaction: discord.Interaction):
    running = any(p.info['name'] and p.info['name'].lower() == "robloxplayerbeta.exe" for p in psutil.process_iter(['name']))
    is_connected = len(connected_clients) > 0

    if is_connected and running:
        await interaction.response.send_message("🟢 **CONNECTED**: Roblox bridge is active!", ephemeral=True)
    elif running and not is_connected:
        code_text = f'loadstring(game:HttpGet("{GITHUB_RAW_SCRIPT}"))()'
        await interaction.response.send_message(f"🔴 **DISCONNECTED**: Run this in your executor:\n```lua\n{code_text}\n```", ephemeral=True)
    else:
        await interaction.response.send_message("🔴 **DISCONNECTED**: Roblox process not found!", ephemeral=True)

@bot.tree.command(name="exec", description="Execute Lua code or upload .lua file")
@is_debug_channel()
async def slash_exec(interaction: discord.Interaction, code: str = None, file: discord.Attachment = None):
    script_to_run = None
    if file and file.filename.endswith(('.lua', '.txt')):
        script_to_run = (await file.read()).decode('utf-8')
    elif code:
        script_to_run = code
        
    if not script_to_run:
        return await interaction.response.send_message("⚠️ Please enter code or attach a file!", ephemeral=True)

    success = await send_to_roblox(script_to_run)
    if success:
        await interaction.response.send_message(f"⚡ **Sent to Roblox!**\n```lua\n{script_to_run[:300]}\n```")
    else:
        await interaction.response.send_message("🔴 **DISCONNECTED**: No Roblox clients connected!", ephemeral=True)

@bot.tree.command(name="human", description="Modify LocalPlayer Humanoid properties (e.g. WalkSpeed 100)")
@is_debug_channel()
async def slash_human(interaction: discord.Interaction, property: str, value: str):
    # Tự động tạo đoạn script Lua thay đổi thuộc tính Humanoid
    script = f"""
    pcall(function()
        local plr = game.Players.LocalPlayer
        local char = plr.Character
        if char then
            local hum = char:FindFirstChildOfClass("Humanoid")
            if hum then
                local numVal = tonumber("{value}") or "{value}"
                hum["{property}"] = numVal
            end
        end
    end)
    """
    success = await send_to_roblox(script)
    if success:
        await interaction.response.send_message(f"👤 Successfully set Humanoid **{property}** to **{value}**!", ephemeral=True)
    else:
        await interaction.response.send_message("🔴 **DISCONNECTED**: No active connection to Roblox!", ephemeral=True)

@bot.tree.command(name="fly", description="Enable flight mode")
@is_debug_channel()
async def slash_fly(interaction: discord.Interaction):
    script = """
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
    success = await send_to_roblox(script)
    if success:
        await interaction.response.send_message("✈️ **Fly Mode Enabled!**", ephemeral=True)
    else:
        await interaction.response.send_message("🔴 **DISCONNECTED**: Not connected to Roblox!", ephemeral=True)

@bot.tree.command(name="unfly", description="Disable flight mode")
@is_debug_channel()
async def slash_unfly(interaction: discord.Interaction):
    script = """
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
    await send_to_roblox(script)
    await interaction.response.send_message("🛑 **Fly Mode Disabled!**", ephemeral=True)

@bot.tree.command(name="status", description="Check active clients")
@is_debug_channel()
async def slash_status(interaction: discord.Interaction):
    count = len(connected_clients)
    status = "🟢 CONNECTED" if count > 0 else "🔴 DISCONNECTED"
    await interaction.response.send_message(f"📊 **Status:** {status} (`{count} active client(s)`)", ephemeral=True)

# Chạy bot
if __name__ == "__main__":
    if DISCORD_BOT_TOKEN == "YOUR_DISCORD_BOT_TOKEN_HERE":
        print("❌ ERROR: Please replace 'YOUR_DISCORD_BOT_TOKEN_HERE' with your actual Discord Bot Token!")
    else:
        bot.run(DISCORD_BOT_TOKEN)
