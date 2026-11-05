<div align="center">

# ⚡ ExecutorOnDiscord

**Control a Roblox client from Discord, with a desktop control panel and a button-based Discord panel.**

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Windows-10%2F11-0078D6?logo=windows&logoColor=white)
![discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2?logo=discord&logoColor=white)
![Status](https://img.shields.io/badge/status-test%20project-orange)

**English** · [Tiếng Việt](#-tiếng-việt)

</div>

> **Credits:** Made by **Videccode**, idea from **@vaehz**. This is a small test project, so expect rough edges. If you share or modify it, please keep these credits.

> **Disclaimer:** For testing and learning only. Running scripts through third-party executors can break the [Roblox Terms of Use](https://en.help.roblox.com/hc/en-us/articles/115004647846) and may get your account banned. Use it on your own account, in your own experiences or private test places, at your own risk. Never use it to disrupt other players.

---

## Contents

1. [How it works](#how-it-works)
2. [What's included](#whats-included)
3. [Requirements](#requirements)
4. [Setup](#setup)
5. [Desktop control panel](#desktop-control-panel-guipy)
6. [Discord panel](#discord-panel-uipy)
7. [Commands](#commands)
8. [Troubleshooting](#troubleshooting)

## How it works

```
Discord (#debug) ──slash command / button──▶ bot.py ◀──WebSocket ws://localhost:8765──▶ bridge.lua (in Roblox)
                                               ▲
                                  gui.py (start / stop / logs)
```

- `bot.py` logs in to Discord and opens a local WebSocket server.
- `bridge.lua` runs inside Roblox through an executor, connects to that server and reconnects automatically.
- A command in `#debug` makes the bot send Lua over the socket, and the bridge runs it.

## What's included

| File | Description |
| --- | --- |
| `bot.py` | The Discord bot: slash and prefix commands, process check, WebSocket server. |
| `bridge.lua` | Client script run in Roblox: connects to the bot, shows notifications, runs received code. |
| `gui.py` | **New.** Desktop control panel: start/stop the bot, save the token, live coloured console. |
| `ui.py` | **New.** Adds `/panel`, a Discord message with buttons and a "Run Lua" pop-up form. |
| `start.bat` | Launches the bot in a console. |
| `start_gui.bat` | **New.** Installs dependencies and opens the control panel. |

## Requirements

- Windows 10 / 11 (the bot looks for `RobloxPlayerBeta.exe`)
- [Python 3.8+](https://www.python.org/downloads/), with **Add Python to PATH** ticked
- A Discord account and a server where you can add bots
- A Roblox executor that supports `WebSocket.connect` (for example Solara, Wave or Zeno)

## Setup

### 1. Create the Discord bot

1. Open the [Discord Developer Portal](https://discord.com/developers/applications) → **New Application**.
2. **Bot** → **Reset Token** → copy it (shown only once).
3. On the same page, turn **ON** **Message Content Intent** under *Privileged Gateway Intents* and save.

> **Treat the token like a password.** Never post it or commit it. If it leaks, reset it.

### 2. Add the bot to your server

1. **OAuth2 → URL Generator**.
2. Scopes: `bot`, `applications.commands`.
3. Permissions: `View Channels`, `Send Messages`, `Embed Links`, `Attach Files`.
4. Open the generated URL, pick your server and authorize.
5. Create a text channel named **`#debug`**. All commands only work there.

### 3. Install

```bash
git clone https://github.com/giangveso0-ctrl/ExecutorRobloxOnDiscord.git
cd ExecutorRobloxOnDiscord
pip install -U discord.py websockets psutil
```

### 4. Run it

**Option A, with the control panel (recommended):** double-click `start_gui.bat`, paste your token, press **Start bot**.

**Option B, console only:** double-click `start.bat` or run `python bot.py`. The console asks for the token on first run and can save it to `token.txt`.

Then, in Roblox, run in your executor:

```lua
loadstring(game:HttpGet("https://raw.githubusercontent.com/giangveso0-ctrl/ExecutorRobloxOnDiscord/main/bridge.lua"))()
```

> Loading code from a URL runs whatever is at that URL. Read `bridge.lua` first, or paste its contents instead.
> The bridge address must match `GITHUB_RAW_SCRIPT` in `bot.py`, so check that line points to this repo.

Start the bot first, then the bridge. Type `/inject` in `#debug`: it should show **CONNECTED**.

**Optional:** put your Discord user ID in `ALLOWED_USER_IDS` at the top of `bot.py` so nobody else in `#debug` can use the bot.

## Desktop control panel (`gui.py`)

A dark window built with Python's built-in `tkinter`, so there is nothing extra to install.

- **Status cards** for the Discord bot, the Roblox process and the number of connected bridge clients.
- **Start / Stop / Restart** buttons.
- **Token box** with a show/hide switch. *Save token* writes `token.txt` and adds it to `.gitignore`.
- **Live console** with colours per message type, and tips for common errors (wrong token, missing intent).
- **Copy loadstring**, **Dev Portal** and **Folder** shortcuts.

The token is passed to `bot.py` through the `DISCORD_BOT_TOKEN` environment variable, so the bot never has to prompt.

## Discord panel (`ui.py`)

`/panel` posts one message with buttons that keep working even after the bot restarts:

| Button | Action |
| --- | --- |
| 🔄 Refresh | Updates the status embed in place |
| ⚡ Run Lua | Opens a pop-up form for Lua code (up to 4000 characters) |
| 📋 Loadstring | Shows the loadstring to run in your executor |
| 📖 Help | Shows the command list |
| 🔗 Repo | Opens this repository |

Buttons follow the same rules as slash commands: `#debug` only, and `ALLOWED_USER_IDS` is respected.

**Enable it:** put `ui.py` next to `bot.py` and add this to `bot.py` at module level, after the other commands and before the bot starts (for example just above the `/status` command):

```python
import types
import ui

ui.install(bot, types.SimpleNamespace(
    Colour=Colour, REPO_URL=REPO_URL, make_embed=make_embed, error_embed=error_embed,
    code_block=code_block, loadstring_snippet=loadstring_snippet,
    strip_code_fence=strip_code_fence, execute_script=execute_script,
    build_status_embed=build_status_embed, build_help_embed=build_help_embed,
    in_debug_channel=in_debug_channel, is_allowed_user=is_allowed_user,
    is_debug_channel=is_debug_channel, wrong_channel_embed=wrong_channel_embed,
    denied_embed=denied_embed,
))
```

Restart the bot and type `/panel` in `#debug`.

## Commands

All commands only work in `#debug`.

| Command | Description |
| --- | --- |
| `/panel` | Button control panel (needs `ui.py`) |
| `/help` | Shows all commands |
| `/inject` | Checks Roblox and the WebSocket, shows the loadstring |
| `/status` | Roblox / WebSocket state, latency, uptime |
| `/exec <code>` | Runs a short Lua snippet. Errors appear in the Roblox console |
| `/findscript <source> <keyword>` | Gives a search link on Rscripts or ScriptBlox |
| `/esp [on/off]` | Player outlines |
| `/fly` · `/unfly` | Flight with WASD + Q/E |
| `/clicktotp [on/off]` | Hold `Ctrl` and click to teleport |
| `/autoheal [on/off]` | Keeps health full |
| `/fpsboost` | Lowers graphics quality for more FPS |
| `/cre` | Credits |
| `!exec <script>` | Long scripts: a ```` ```lua ```` block or a `.lua` / `.txt` file (max 2 MB) |

`[on/off]` commands default to **on**, for example `/esp state:OFF`.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Slash commands don't show up | Re-invite with the `applications.commands` scope, wait a minute, press `Ctrl + R` in Discord |
| Invalid token / bot offline | Reset the token in the portal and paste the new one (in the panel, press *Save token*) |
| `Used disallowed intents` | Developer Portal → **Bot** → enable **Message Content Intent** |
| `/inject` says DISCONNECTED | Start the bot first, then run the bridge. Check that nothing else uses port `8765` |
| `/panel` not found | `ui.py` is missing or the 3-line hook isn't in `bot.py`. Restart the bot after adding it |
| Panel buttons say "interaction failed" | The bot was offline. Start it again, or run `/panel` for a fresh one |
| `WebSocket` is nil in Roblox | Your executor lacks `WebSocket.connect`. Try another |
| `python` is not recognized | Reinstall Python and tick **Add Python to PATH** |
| GUI says "psutil missing" | `pip install psutil` (only the Roblox indicator needs it) |

## Contributing

Issues and pull requests are welcome. Please keep changes focused.

## License

No license is specified yet. Add a `LICENSE` file (for example MIT) so others know how they may use the code.

---

## 🇻🇳 Tiếng Việt

**Điều khiển client Roblox từ Discord, có bảng điều khiển trên máy tính và bảng nút bấm trong Discord.**

> **Ghi công:** Do **Videccode** làm, ý tưởng từ **@vaehz**. Đây là dự án thử nghiệm nhỏ nên có thể còn thiếu sót. Nếu chia sẻ hoặc chỉnh sửa, vui lòng giữ lại phần ghi công này.

> **Lưu ý:** Chỉ dùng để thử nghiệm và học tập. Chạy script qua executor bên thứ ba có thể vi phạm [Điều khoản sử dụng của Roblox](https://en.help.roblox.com/hc/en-us/articles/115004647846) và có thể khiến tài khoản bị khóa. Chỉ dùng trên tài khoản của bạn, trong game của chính bạn hoặc place thử nghiệm riêng, tự chịu rủi ro. Không dùng để làm phiền người chơi khác.

### Cách hoạt động

- `bot.py` đăng nhập Discord và mở WebSocket server cục bộ `ws://localhost:8765`.
- `bridge.lua` chạy trong Roblox qua executor, kết nối tới server đó và tự kết nối lại.
- Khi bạn gõ lệnh trong `#debug`, bot gửi mã Lua qua socket và bridge sẽ chạy nó.

### Các tệp

| Tệp | Mô tả |
| --- | --- |
| `bot.py` | Bot Discord: slash command, lệnh tiền tố, kiểm tra tiến trình, WebSocket server |
| `bridge.lua` | Script chạy trong Roblox |
| `gui.py` | **Mới.** Bảng điều khiển trên máy tính: bật/tắt bot, lưu token, console có màu |
| `ui.py` | **Mới.** Thêm `/panel`: tin nhắn có nút bấm và form "Run Lua" |
| `start.bat` | Chạy bot trong console |
| `start_gui.bat` | **Mới.** Cài thư viện và mở bảng điều khiển |

### Yêu cầu

- Windows 10 / 11
- [Python 3.8+](https://www.python.org/downloads/) (tích **Add Python to PATH**)
- Tài khoản Discord và một server bạn thêm được bot
- Executor Roblox hỗ trợ `WebSocket.connect` (ví dụ Solara, Wave, Zeno)

### Cài đặt nhanh

1. **Tạo bot:** [Developer Portal](https://discord.com/developers/applications) → New Application → **Bot** → **Reset Token** và sao chép. Bật **Message Content Intent** rồi lưu.
2. **Thêm bot vào server:** OAuth2 → URL Generator → scope `bot` + `applications.commands`; quyền `View Channels`, `Send Messages`, `Embed Links`, `Attach Files`. Mở link, chọn server, Authorize.
3. **Tạo kênh** `#debug`. Mọi lệnh chỉ dùng được ở đó.
4. **Cài đặt:**

   ```bash
   git clone https://github.com/giangveso0-ctrl/ExecutorRobloxOnDiscord.git
   cd ExecutorRobloxOnDiscord
   pip install -U discord.py websockets psutil
   ```

5. **Chạy:** nhấp đúp `start_gui.bat`, dán token rồi nhấn **Start bot** (hoặc dùng `start.bat` / `python bot.py`).
6. **Trong Roblox**, chạy trong executor:

   ```lua
   loadstring(game:HttpGet("https://raw.githubusercontent.com/giangveso0-ctrl/ExecutorRobloxOnDiscord/main/bridge.lua"))()
   ```

   Hãy đọc `bridge.lua` trước khi chạy. Địa chỉ này nên khớp với `GITHUB_RAW_SCRIPT` trong `bot.py`.

Chạy bot trước, bridge sau. Gõ `/inject` trong `#debug`, sẽ thấy **CONNECTED**.

### Bảng điều khiển (`gui.py`)

Cửa sổ nền tối dùng `tkinter` có sẵn của Python:

- Thẻ trạng thái: bot Discord, tiến trình Roblox, số bridge đang kết nối
- Nút **Start / Stop / Restart**
- Ô nhập token có nút hiện/ẩn; *Save token* lưu vào `token.txt` và thêm vào `.gitignore`
- Console trực tiếp có màu, kèm gợi ý khi gặp lỗi phổ biến
- Phím tắt: **Copy loadstring**, **Dev Portal**, **Folder**

### Bảng nút bấm trong Discord (`ui.py`)

`/panel` gửi một tin nhắn có nút, vẫn dùng được sau khi bot khởi động lại:

| Nút | Tác dụng |
| --- | --- |
| 🔄 Refresh | Cập nhật trạng thái |
| ⚡ Run Lua | Mở form nhập mã Lua (tối đa 4000 ký tự) |
| 📋 Loadstring | Hiện loadstring để chạy trong executor |
| 📖 Help | Danh sách lệnh |
| 🔗 Repo | Mở kho mã nguồn |

**Bật tính năng:** đặt `ui.py` cạnh `bot.py` và thêm đoạn mã ở mục *Enable it* phía trên vào `bot.py`, rồi khởi động lại bot và gõ `/panel`.

### Danh sách lệnh

Xem bảng **Commands** ở phần tiếng Anh. Các lệnh giữ nguyên tên và cách dùng.

### Khắc phục sự cố

| Vấn đề | Cách xử lý |
| --- | --- |
| Không thấy slash command | Mời lại bot với scope `applications.commands`, chờ 1 phút, nhấn `Ctrl + R` |
| Token không hợp lệ | Reset token rồi dán token mới |
| `Used disallowed intents` | Bật **Message Content Intent** trong Developer Portal |
| `/inject` báo DISCONNECTED | Chạy bot trước, bridge sau; kiểm tra cổng `8765` |
| Không có `/panel` | Thiếu `ui.py` hoặc chưa thêm đoạn mã vào `bot.py`; khởi động lại bot |
| Không nhận lệnh `python` | Cài lại Python và tích **Add Python to PATH** |
