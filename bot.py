import os
import psutil
import asyncio
import websockets
import discord
from discord.ext import commands
from discord import app_commands

# ==============================================================================
# 🔑 CONFIGURATION / CẤU HÌNH BOT
# ==============================================================================
DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"
GITHUB_RAW_SCRIPT = "https://raw.githubusercontent.com/giangveso0-ctrl/RobloxOnDiscord-Test/main/bridge.lua"

# Khởi tạo Bot Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=['.', '!'], intents=intents)
bot.remove_command('help')

# Lưu danh sách các Roblox Client đang kết nối WebSocket
connected_clients = set()

# ==============================================================================
# 🌐 WEBSOCKET SERVER (CẦU NỐI ROBLOX)
# ==============================================================================
async def ws_handler(websocket):
    connected_clients.add(websocket)
    print(f"🟢 [CONNECTED] Roblox client connected! Total active: {len(connected_clients)}")
    try:
        async for message in websocket:
            print(f"[ROBLOX LOG]: {message}")
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)
        print(f"🔴 [DISCONNECTED] Roblox client disconnected. Total active: {len(connected_clients)}")

async def start_websocket_server():
    async with websockets.serve(ws_handler, "localhost", 8765):
        print("🚀 WebSocket Server running successfully at ws://localhost:8765")
        await asyncio.Future()

@bot.event
async def on_ready():
    print(f"✅ Bot logged in as: {bot.user} (English/Vietnamese Dual Mode)")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} Slash Command(s).")
    except Exception as e:
        print(f"Sync error: {e}")
    
    bot.loop.create_task(start_websocket_server())

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

def is_debug_channel():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.channel and interaction.channel.name == "debug":
            return True
        await interaction.response.send_message("⚠️ Lệnh này chỉ được phép sử dụng trong kênh `#debug` / This command can only be used in `#debug`!", ephemeral=True)
        return False
    return app_commands.check(predicate)

# ==============================================================================
# 🛠️ TRADITIONAL COMMANDS (!exec chuyên dụng cho script dài & file đính kèm)
# ==============================================================================

@bot.command(name="help")
async def legacy_help(ctx):
    if ctx.channel.name != "debug":
        return await ctx.send("⚠️ Vui lòng dùng trong kênh `#debug`!")
    
    embed = discord.Embed(
        title="📖 Roblox Bridge Hub - Hướng Dẫn / Help", 
        description="Hệ thống quản lý Roblox qua WebSocket / WebSocket Management System",
        color=0x3498DB
    )
    embed.add_field(
        name="📜 Lệnh Tiền Tố (Prefix Commands)",
        value="• `!inject` - Kiểm tra trạng thái / Check status\n• `!exec <script>` hoặc đính kèm file - Thực thi script dài / Execute long scripts & files\n• `!status` - Xem kết nối / View connections",
        inline=False
    )
    embed.add_field(
        name="⚡ Slash Commands (/)",
        value="• `/exec <code/>` - Gửi script ngắn nhanh chóng / Quick short script execution\n• `/findscript <source> <keyword>` - Tìm kiếm script từ Rscripts hoặc ScriptBlox\n• `/esp` - Bật/tắt tính năng nhìn xuyên tường ESP / Toggle ESP\n• `/fpsboost` - Tối ưu hóa đồ họa, tăng FPS / Boost game performance\n• `/fly` / `/unfly` - Bật tắt bay mượt mà / Toggle flight mode\n• `/clicktotp` - Bật dịch chuyển click chuột (Ctrl+Click) / Toggle Click-to-TP\n• `/autoheal` - Bật tự động hồi máu liên tục / Toggle Auto-Heal\n• `/cre` - Thông tin tác giả & nhà phát triển / Credits",
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command(name="inject")
async def legacy_inject(ctx):
    if ctx.channel.name != "debug":
        return await ctx.send("⚠️ Vui lòng dùng trong kênh `#debug`!")
        
    running = any(p.info['name'] and p.info['name'].lower() == "robloxplayerbeta.exe" for p in psutil.process_iter(['name']))
    is_connected = len(connected_clients) > 0

    if is_connected and running:
        await ctx.send("🟢 **CONNECTED**: Đã tìm thấy game và WebSocket đang hoạt động! / Game found & WebSocket active!")
    elif running and not is_connected:
        msg = f"🔴 **DISCONNECTED**: Game đang chạy nhưng chưa nạp script! / Game running but script not injected!\nCopy lệnh này vào Executor của bạn / Run this in your executor:\n```lua\nloadstring(game:HttpGet(\"{GITHUB_RAW_SCRIPT}\"))()\n```"
        await ctx.send(msg)
    else:
        await ctx.send("🔴 **DISCONNECTED**: Không tìm thấy tiến trình Roblox! / Roblox process not found!")

@bot.command(name="exec")
async def legacy_exec(ctx, *, script_code: str = None):
    """Lệnh !exec tối ưu chuyên sâu cho việc nhận script dài và file đính kèm .lua/.txt"""
    if ctx.channel.name != "debug":
        return await ctx.send("⚠️ Vui lòng dùng trong kênh `#debug`!")
        
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if attachment.filename.endswith(('.lua', '.txt')):
            try:
                script_code = (await attachment.read()).decode('utf-8')
            except Exception as e:
                return await ctx.send(f"❌ Lỗi đọc file / File read error: `{e}`")
            
    if not script_code:
        return await ctx.send("⚠️ Vui lòng nhập nội dung script hoặc đính kèm file `.lua` / Please provide script code or attach a file!")
        
    success = await send_to_roblox(script_code)
    if success:
        display_code = script_code[:800] + "\n... (đã rút gọn / truncated)" if len(script_code) > 800 else script_code
        await ctx.send(f"⚡ **[LONG SCRIPT EXECUTED] - Đã gửi script dài tới Roblox successfully!**\n```lua\n{display_code}\n```")
    else:
        await ctx.send("🔴 **DISCONNECTED**: Chưa kết nối WebSocket với Roblox! / No active Roblox client connected!")

# ==============================================================================
# ⚡ SLASH COMMANDS (Tính năng nâng cao, Tìm kiếm Rscripts/ScriptBlox, ESP, FPS Boost, Credits)
# ==============================================================================

@bot.tree.command(name="inject", description="Kiểm tra trạng thái tiến trình và kết nối / Check process & connection status")
@is_debug_channel()
async def slash_inject(interaction: discord.Interaction):
    running = any(p.info['name'] and p.info['name'].lower() == "robloxplayerbeta.exe" for p in psutil.process_iter(['name']))
    is_connected = len(connected_clients) > 0

    if is_connected and running:
        await interaction.response.send_message("🟢 **CONNECTED**: Roblox bridge đang hoạt động hoàn hảo / Bridge is active!", ephemeral=True)
    elif running and not is_connected:
        code_text = f'loadstring(game:HttpGet("{GITHUB_RAW_SCRIPT}"))()'
        await interaction.response.send_message(f"🔴 **DISCONNECTED**: Chạy loadstring này trong Executor của bạn / Run this in your executor:\n```lua\n{code_text}\n```", ephemeral=True)
    else:
        await interaction.response.send_message("🔴 **DISCONNECTED**: Không tìm thấy tiến trình Roblox! / Process not found!", ephemeral=True)

@bot.tree.command(name="exec", description="Thực thi nhanh mã Lua ngắn / Quick execute short Lua code")
@is_debug_channel()
async def slash_exec(interaction: discord.Interaction, code: str):
    if not code:
        return await interaction.response.send_message("⚠️ Vui lòng nhập mã lệnh Lua! / Please enter Lua code!", ephemeral=True)

    success = await send_to_roblox(code)
    if success:
        await interaction.response.send_message(f"⚡ **[QUICK EXEC] - Đã gửi thành công! / Sent successfully!**\n```lua\n{code}\n```", ephemeral=True)
    else:
        await interaction.response.send_message("🔴 **DISCONNECTED**: Chưa kết nối WebSocket! / No clients connected!", ephemeral=True)

@bot.tree.command(name="findscript", description="Tìm kiếm script từ Rscripts hoặc ScriptBlox / Search scripts from Rscripts or ScriptBlox")
@app_commands.choices(source=[
    app_commands.Choice(name="Rscripts (rscripts.net)", value="rscripts"),
    app_commands.Choice(name="ScriptBlox (scriptblox.com)", value="scriptblox")
])
@is_debug_channel()
async def slash_findscript(interaction: discord.Interaction, source: str, keyword: str):
    keyword_lower = keyword.lower()
    
    # Dữ liệu mẫu hoặc tích hợp đường dẫn tra cứu nhanh từ Rscripts và ScriptBlox
    if source == "rscripts":
        search_url = f"https://rscripts.net/?q={keyword.replace(' ', '+')}"
        embed = discord.Embed(
            title=f"🌐 Kết quả tìm kiếm từ Rscripts",
            description=f"Từ khóa: **{keyword}**",
            color=0x9B59B6
        )
        embed.add_field(name="🔗 Link tra cứu trực tiếp", value=f"[Bấm vào đây để xem trên Rscripts]({search_url})", inline=False)
        embed.add_field(name="💡 Gợi ý lệnh", value=f"Bạn có thể truy cập trang web trên để lấy loadstring và dùng lệnh `/exec` để chạy.", inline=False)
    else:
        search_url = f"https://scriptblox.com/search?q={keyword.replace(' ', '+')}"
        embed = discord.Embed(
            title=f"🌐 Kết quả tìm kiếm từ ScriptBlox",
            description=f"Từ khóa: **{keyword}**",
            color=0x3498DB
        )
        embed.add_field(name="🔗 Link tra cứu trực tiếp", value=f"[Bấm vào đây để xem trên ScriptBlox]({search_url})", inline=False)
        embed.add_field(name="💡 Gợi ý lệnh", value=f"Bạn có thể truy cập trang web trên để lấy loadstring và dùng lệnh `/exec` để chạy.", inline=False)
        
    embed.set_footer(text=fNguồn: {source.capitalize()} | Bot Automation System")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="esp", description="Bật tính năng nhìn xuyên tường (ESP Box/Name) / Enable player ESP")
@is_debug_channel()
async def slash_esp(interaction: discord.Interaction):
    script = """
    pcall(function()
        for _, plr in ipairs(game.Players:GetPlayers()) do
            if plr ~= game.Players.LocalPlayer then
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
    success = await send_to_roblox(script)
    if success:
        await interaction.response.send_message("👁️ Đã bật **ESP** (Highlight người chơi)! / ESP Enabled!", ephemeral=True)
    else:
        await interaction.response.send_message("🔴 **DISCONNECTED**: Chưa kết nối game! / Not connected!", ephemeral=True)

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
    success = await send_to_roblox(script)
    if success:
        await interaction.response.send_message("🚀 Đã kích hoạt **FPS Boost** (Tối ưu hóa đồ họa thành công)! / FPS Boost Enabled!", ephemeral=True)
    else:
        await interaction.response.send_message("🔴 **DISCONNECTED**: Chưa kết nối game! / Not connected!", ephemeral=True)

@bot.tree.command(name="fly", description="Bật chế độ bay mượt mà / Enable smooth flight mode")
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
        await interaction.response.send_message("✈️ Đã bật **Fly Mode**! / Flight enabled!", ephemeral=True)
    else:
        await interaction.response.send_message("🔴 **DISCONNECTED**: Chưa kết nối game! / Not connected!", ephemeral=True)

@bot.tree.command(name="unfly", description="Tắt chế độ bay và khôi phục vật lý / Disable flight & restore physics")
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
    await interaction.response.send_message("🛑 Đã tắt **Fly Mode**! / Flight disabled!", ephemeral=True)

@bot.tree.command(name="clicktotp", description="Bật tính năng Click chuột để dịch chuyển (Ctrl + Click) / Enable Click-to-TP")
@is_debug_channel()
async def slash_clicktotp(interaction: discord.Interaction):
    script = """
    pcall(function()
        local mouse = game.Players.LocalPlayer:GetMouse()
        local uis = game:GetService("UserInputService")
        if _G.ClickTPConn then _G.ClickTPConn:Disconnect() end
        _G.ClickTPConn = mouse.Button1Down:Connect(function()
            if uis:IsKeyDown(Enum.KeyCode.LeftControl) or uis:IsKeyDown(Enum.KeyCode.RightControl) then
                local char = game.Players.LocalPlayer.Character
                if char and char:FindFirstChild("HumanoidRootPart") then
                    if mouse.Target then
                        char.HumanoidRootPart.CFrame = CFrame.new(mouse.Hit.Position + Vector3.new(0, 3, 0))
                    end
                end
            end
        end)
    end)
    """
    success = await send_to_roblox(script)
    if success:
        await interaction.response.send_message("🖱️ Đã bật **Click-to-TP** (Giữ Ctrl + Click chuột trái để dịch chuyển)! / Click-to-TP Enabled!", ephemeral=True)
    else:
        await interaction.response.send_message("🔴 **DISCONNECTED**: Chưa kết nối game!", ephemeral=True)

@bot.tree.command(name="autoheal", description="Tự động hồi máu tối đa liên tục / Enable Auto-Heal")
@is_debug_channel()
async def slash_autoheal(interaction: discord.Interaction):
    script = """
    pcall(function()
        if _G.AutoHealConn then _G.AutoHealConn:Disconnect() end
        _G.AutoHealConn = game:GetService("RunService").Stepped:Connect(function()
            local char = game.Players.LocalPlayer.Character
            if char then
                local hum = char:FindFirstChildOfClass("Humanoid")
                if hum and hum.Health > 0 and hum.Health < hum.MaxHealth then
                    hum.Health = hum.MaxHealth
                end
            end
        end)
    end)
    """
    success = await send_to_roblox(script)
    if success:
        await interaction.response.send_message("❤️ Đã bật **Auto-Heal** (Tự động hồi đầy máu liên tục)! / Auto-Heal Enabled!", ephemeral=True)
    else:
        await interaction.response.send_message("🔴 **DISCONNECTED**: Chưa kết nối game!", ephemeral=True)

@bot.tree.command(name="cre", description="Hiển thị thông tin tác giả và dự án / Credits & Information")
@is_debug_channel()
async def slash_cre(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌟 RobloxOnDiscord Bridge - Credits",
        description="Hệ thống cầu nối WebSocket tương tác giữa Discord Bot và Roblox Client.",
        color=0xF1C40F
    )
    embed.add_field(name="👨‍💻 Developer / Tác giả", value="giangveso0-ctrl", inline=True)
    embed.add_field(name="🔗 GitHub Repository", value="[RobloxOnDiscord-Test](https://github.com/giangveso0-ctrl/RobloxOnDiscord-Test)", inline=False)
    embed.add_field(name="🌐 Protocol", value="Localhost WebSocket (Port 8765)", inline=True)
    embed.set_footer(text="Cảm ơn bạn đã sử dụng hệ thống tự động hóa này!")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="status", description="Kiểm tra trạng thái máy chủ WebSocket / Check WebSocket server status")
@is_debug_channel()
async def slash_status(interaction: discord.Interaction):
    count = len(connected_clients)
    if count > 0:
        status = "🟢 CONNECTED (Đang hoạt động)"
    else:
        status = "🔴 DISCONNECTED (Chưa kết nối)"
        
    await interaction.response.send_message(f"📊 **Trạng thái / Status:** {status} (`{count} client active`)", ephemeral=True)

# Khởi chạy Bot
if __name__ == "__main__":
    if DISCORD_BOT_TOKEN == "YOUR_DISCORD_BOT_TOKEN_HERE":
        print("❌ ERROR: Vui lòng thay thế 'YOUR_DISCORD_BOT_TOKEN_HERE' bằng Token Discord thực tế của bạn!")
    else:
        bot.run(DISCORD_BOT_TOKEN)
