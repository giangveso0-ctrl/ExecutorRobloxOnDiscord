<div align="center">

# ⚡ ExecutorOnDiscord

### Control a Roblox client from Discord.
Slash commands, a button panel inside Discord, and a desktop control window.

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Windows](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D6?logo=windows&logoColor=white)
![discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2?logo=discord&logoColor=white)
![WebSocket](https://img.shields.io/badge/WebSocket-localhost%3A8765-2ECC71)
![Status](https://img.shields.io/badge/status-test%20project-orange)

**English** · [Tiếng Việt](#-tiếng-việt)

</div>

> **Credits:** Made by **Videccode**, idea from **@vaehz**. If you share or modify this project, please keep these credits.

> **⚠️ Disclaimer:** For testing and learning only. Running scripts through third-party executors can break the [Roblox Terms of Use](https://en.help.roblox.com/hc/en-us/articles/115004647846) and can get your account banned. Use it on your own account, in your own experiences or private test places, at your own risk. Never use it to disrupt other players.

---

## Contents

- [Overview](#overview)
- [Quick start](#quick-start)
- [Detailed setup](#detailed-setup)
- [Desktop control panel](#desktop-control-panel-guipy)
- [Discord button panel](#discord-button-panel-uipy)
- [Commands](#commands)
- [Configuration](#configuration)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Project files](#project-files)

---

## Overview

```
 Discord  ──── slash command / button ────▶  bot.py  ◀──── WebSocket ────▶  bridge.lua
 (you)                                              │          ws://localhost:8765   (inside Roblox,
                                                    │                                 via an executor)
                                         gui.py ────┘ start · stop · logs
```

1. `bot.py` logs in to Discord and opens a WebSocket server on your own PC.
2. `bridge.lua` runs inside Roblox through an executor, connects to that server and reconnects on its own if the link drops.
3. When you use a command in `#debug`, the bot sends Lua over the socket and the bridge runs it in the game.

Everything stays on `localhost`. Nothing is exposed to the internet except the normal Discord connection.

## Quick start

> You need Python 3.8+, a Discord bot token and an executor with `WebSocket.connect` support.

```bash
git clone https://github.com/giangveso0-ctrl/ExecutorRobloxOnDiscord.git
cd ExecutorRobloxOnDiscord
```

1. Double-click **`start_gui.bat`**. It installs the dependencies and opens the control panel.
2. Paste your bot token and press **Start bot**. *(No token yet? See [Step 1](#1-create-the-discord-bot).)*
3. In Roblox, run this in your executor:

   ```lua
   loadstring(game:HttpGet("https://raw.githubusercontent.com/giangveso0-ctrl/ExecutorRobloxOnDiscord/main/bridge.lua"))()
   ```

4. In `#debug`, type **`/inject`**. When it shows 🟢 **CONNECTED**, you're done.

Prefer a plain console? Use `start.bat` or `python bot.py` instead of step 1–2.

## Detailed setup

### 1. Create the Discord bot

1. Open the [Discord Developer Portal](https://discord.com/developers/applications) and choose **New Application**.
2. Go to **Bot** → **Reset Token** → **Copy**. Discord shows the token only once.
3. On the same page, under **Privileged Gateway Intents**, turn **ON** **Message Content Intent** and press **Save Changes**. The `!exec` command needs it, and the bot will not start without it.

### 2. Add the bot to your server

You need the **Manage Server** permission (or be the owner).

1. Go to **OAuth2 → URL Generator**.
2. **Scopes:** `bot` and `applications.commands`.
3. **Bot permissions:** `View Channels`, `Send Messages`, `Embed Links`, `Attach Files`.
4. Open the generated URL, pick your server, then **Authorize**.
5. Create a text channel named **`#debug`**. Every command works only there. If the channel is private, give the bot's role access to it.

### 3. Install

```bash
pip install -U discord.py websockets psutil
```

`start_gui.bat` does this for you.

### 4. Give the bot your token

Pick **one** way. The bot checks them in this order:

| Order | Method | How |
| --- | --- | --- |
| 1 | Environment variable | Set `DISCORD_BOT_TOKEN`. The control panel uses this. |
| 2 | `token.txt` | A file next to `bot.py` containing only the token. |
| 3 | Edit `bot.py` | Replace `PASTE_YOUR_BOT_TOKEN_HERE` in `DISCORD_BOT_TOKEN`. |
| 4 | Ask in console | If nothing is found, `bot.py` asks you and can save it to `token.txt`. |

A real token has three parts separated by dots. `token.txt` is added to `.gitignore` automatically.

> **Never commit or post your token.** If it leaks, reset it in the Developer Portal right away.

### 5. Point the bot at your repo (only if you forked it)

In `bot.py`, check these two lines so the loadstring shown by `/inject` matches your copy:

```python
GITHUB_RAW_SCRIPT = "https://raw.githubusercontent.com/<you>/<repo>/main/bridge.lua"
REPO_URL = "https://github.com/<you>/<repo>"
```

### 6. Run it

Start the **bot first**, then run the **bridge** in Roblox. If you close either one, start both again.

> Loading code from a URL runs whatever is at that URL. Read `bridge.lua` first, or paste its contents into the executor instead.

---

## Desktop control panel (`gui.py`)

A dark window built on Python's own `tkinter`, so there is nothing extra to install.

| Feature | What it does |
| --- | --- |
| Status cards | Shows the Discord bot, the Roblox process and how many bridge clients are connected |
| Start / Stop / Restart | Runs `bot.py` in the background, with no console window |
| Token box | Show/hide switch. **Save token** writes `token.txt` and updates `.gitignore` |
| Live console | Coloured output with tips for common errors (wrong token, missing intent) |
| Shortcuts | **Copy loadstring**, **Dev Portal**, **Folder** |

The panel gives the token to `bot.py` through `DISCORD_BOT_TOKEN`, so the bot never needs to prompt. Closing the window stops the bot.

## Discord button panel (`ui.py`)

`/panel` posts one message with buttons. They keep working after the bot restarts.

| Button | Action |
| --- | --- |
| 🔄 **Refresh** | Updates the status in place |
| ⚡ **Run Lua** | Opens a pop-up form for Lua code (up to 4000 characters) |
| 📋 **Loadstring** | Shows the loadstring to run in your executor |
| 📖 **Help** | Shows the command list |
| 🔗 **Repo** | Opens this repository |

Buttons follow the same rules as slash commands: only in `#debug`, and only for `ALLOWED_USER_IDS` if you set it.

### Enable it

1. Put `ui.py` in the same folder as `bot.py`.
2. In `bot.py`, find the section titled **`🚀 KHỞI CHẠY BOT / START`** (just above `def main()`), and paste this **right above it**:

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

3. Restart the bot and type `/panel` in `#debug`.

---

## Commands

All commands work **only in `#debug`**. Slash command replies are private (only you see them), except `/panel`.

### Slash commands

| Command | Description |
| --- | --- |
| `/panel` | Button control panel *(needs [`ui.py`](#enable-it))* |
| `/help` | Shows all commands |
| `/inject` | Checks Roblox and the WebSocket, and shows the loadstring if the bridge isn't connected |
| `/status` | Roblox / WebSocket state, latency, uptime and endpoint |
| `/exec <code>` | Runs a short Lua snippet. Syntax and runtime errors are reported in the Roblox console |
| `/findscript <source> <keyword>` | Gives a search link on Rscripts or ScriptBlox |
| `/esp [on/off]` | Player outlines. Covers new players and respawns |
| `/fly` · `/unfly` | Flight with `WASD` + `Q`/`E` |
| `/clicktotp [on/off]` | Hold `Ctrl` and click to teleport |
| `/autoheal [on/off]` | Keeps your health full |
| `/fpsboost` | Lowers graphics quality for more FPS |
| `/cre` | Credits |

`[on/off]` commands default to **on**. Example: `/esp state:OFF`.

### Prefix commands (`!` or `.`)

| Command | Description |
| --- | --- |
| `!exec <script>` | For long scripts. Paste a ```` ```lua ```` code block, or attach a `.lua` / `.txt` file (max 2 MB) |
| `!help` | Shows the help embed |

The bot reacts with ✅ when the script was delivered and ❌ when no Roblox client is connected.

## Configuration

Settings at the top of `bot.py`:

| Setting | Default | Meaning |
| --- | --- | --- |
| `DEBUG_CHANNEL` | `"debug"` | Name of the only channel where commands work |
| `WS_HOST` / `WS_PORT` | `localhost` / `8765` | Where the WebSocket server listens. If you change the port, change it in `bridge.lua` too |
| `ALLOWED_USER_IDS` | `[]` | Discord user IDs allowed to use the bot. Empty means **everyone in `#debug`** |
| `MAX_FILE_BYTES` | `2 MB` | Size limit for attached `.lua` / `.txt` files |
| `GITHUB_RAW_SCRIPT` | this repo's `bridge.lua` | Loadstring URL shown by `/inject` and the panel |

To find your user ID: Discord → Settings → Advanced → turn on **Developer Mode**, then right-click your name → **Copy User ID**.

## Security

This bot runs code on your PC and in your game. Keep it private.

- **Set `ALLOWED_USER_IDS`.** With the default empty list, anyone who can type in `#debug` can run Lua in your game. Put your own ID there, for example `ALLOWED_USER_IDS = [123456789012345678]`.
- **Keep the server private.** Do not invite people you don't trust, and keep `#debug` hidden from them.
- **Protect the token.** Anyone with it controls your bot. Don't upload `bot.py` with a real token inside, or `token.txt`.
- **Read before you run.** `loadstring(game:HttpGet(...))()` executes whatever is at the URL. Only use a URL you control or have read.
- **Local only.** The WebSocket server listens on `localhost`, so other computers cannot connect to it.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Slash commands don't show up | Re-invite the bot with the `applications.commands` scope, wait a minute, then press `Ctrl + R` in Discord |
| Bot is offline / invalid token | The token is wrong or was reset. Reset it in the portal and paste the new one |
| `Used disallowed intents` | Developer Portal → **Bot** → enable **Message Content Intent** and save |
| `/inject` says DISCONNECTED | Start the bot first, then run the bridge. Make sure nothing else uses port `8765` |
| 🟠 WAITING FOR SCRIPT | Roblox is running but the bridge isn't loaded. Run the loadstring in your executor |
| "Missing Access" or no reply | Give the bot permission to view and send messages in `#debug` |
| `/panel` not found | `ui.py` is missing or the hook isn't in `bot.py`. Restart the bot after adding it |
| Panel buttons say "interaction failed" | The bot was offline. Start it again, or run `/panel` for a fresh message |
| `WebSocket` is nil in Roblox | Your executor doesn't support `WebSocket.connect`. Try another one |
| `python` is not recognized | Reinstall Python and tick **Add Python to PATH** |
| Control panel says "psutil missing" | Run `pip install psutil`. Only the Roblox indicator needs it |

## Project files

| File | Description |
| --- | --- |
| `bot.py` | The Discord bot: commands, process check, WebSocket server |
| `bridge.lua` | Client script that runs inside Roblox and executes what the bot sends |
| `gui.py` | Desktop control panel |
| `ui.py` | Button panel and Run Lua form for Discord |
| `start.bat` | Starts the bot in a console |
| `start_gui.bat` | Installs dependencies and opens the control panel |

## Contributing

Issues and pull requests are welcome. Please keep changes focused.

## License

No license is set yet. Add a `LICENSE` file (for example MIT) so others know how they may use the code.

---

<a id="-tiếng-việt"></a>

## 🇻🇳 Tiếng Việt

### Giới thiệu

**Điều khiển client Roblox từ Discord.** Có slash command, bảng nút bấm ngay trong Discord và cửa sổ điều khiển trên máy tính.

> **Ghi công:** Do **Videccode** làm, ý tưởng từ **@vaehz**. Nếu chia sẻ hoặc chỉnh sửa, vui lòng giữ lại phần ghi công này.

> **⚠️ Lưu ý:** Chỉ dùng để thử nghiệm và học tập. Chạy script qua executor bên thứ ba có thể vi phạm [Điều khoản sử dụng của Roblox](https://en.help.roblox.com/hc/en-us/articles/115004647846) và có thể khiến tài khoản bị khóa. Chỉ dùng trên tài khoản của bạn, trong game của chính bạn hoặc place thử nghiệm riêng, tự chịu rủi ro. Không dùng để làm phiền người chơi khác.

### Cách hoạt động

1. `bot.py` đăng nhập Discord và mở WebSocket server ngay trên máy bạn (`ws://localhost:8765`).
2. `bridge.lua` chạy trong Roblox qua executor, kết nối tới server đó và tự kết nối lại nếu bị ngắt.
3. Khi bạn gõ lệnh trong `#debug`, bot gửi mã Lua qua socket và bridge sẽ chạy trong game.

Mọi thứ chỉ chạy trên `localhost`.

### Bắt đầu nhanh

Cần: Python 3.8+, token bot Discord và executor hỗ trợ `WebSocket.connect`.

```bash
git clone https://github.com/giangveso0-ctrl/ExecutorRobloxOnDiscord.git
cd ExecutorRobloxOnDiscord
```

1. Nhấp đúp **`start_gui.bat`**. File này cài thư viện và mở bảng điều khiển.
2. Dán token rồi nhấn **Start bot**.
3. Trong Roblox, chạy trong executor:

   ```lua
   loadstring(game:HttpGet("https://raw.githubusercontent.com/giangveso0-ctrl/ExecutorRobloxOnDiscord/main/bridge.lua"))()
   ```

4. Trong `#debug`, gõ **`/inject`**. Khi thấy 🟢 **CONNECTED** là xong.

Muốn dùng console thường? Chạy `start.bat` hoặc `python bot.py`.

### Cài đặt chi tiết

**1. Tạo bot.** Vào [Developer Portal](https://discord.com/developers/applications) → **New Application** → **Bot** → **Reset Token** và sao chép (chỉ hiện một lần). Ở mục **Privileged Gateway Intents**, **BẬT** **Message Content Intent** rồi lưu. Không bật thì bot không khởi động được.

**2. Thêm bot vào server.** Cần quyền **Manage Server**. Vào **OAuth2 → URL Generator**, chọn scope `bot` và `applications.commands`, quyền `View Channels`, `Send Messages`, `Embed Links`, `Attach Files`. Mở link, chọn server, **Authorize**. Tạo kênh văn bản tên **`#debug`**. Mọi lệnh chỉ dùng được ở kênh này.

**3. Cài thư viện.**

```bash
pip install -U discord.py websockets psutil
```

**4. Đưa token cho bot.** Chọn **một** cách (bot kiểm tra theo thứ tự này):

| Thứ tự | Cách | Thực hiện |
| --- | --- | --- |
| 1 | Biến môi trường | Đặt `DISCORD_BOT_TOKEN` (bảng điều khiển dùng cách này) |
| 2 | `token.txt` | File cạnh `bot.py`, chỉ chứa token |
| 3 | Sửa `bot.py` | Thay `PASTE_YOUR_BOT_TOKEN_HERE` |
| 4 | Nhập trong console | Nếu chưa có, `bot.py` sẽ hỏi và có thể lưu vào `token.txt` |

> **Không bao giờ đăng token lên mạng hoặc GitHub.** Nếu bị lộ, hãy reset ngay.

**5. Nếu bạn fork repo,** hãy sửa `GITHUB_RAW_SCRIPT` và `REPO_URL` trong `bot.py` cho khớp.

**6. Chạy.** Chạy **bot trước**, sau đó chạy **bridge** trong Roblox. Nếu đóng một trong hai, hãy chạy lại cả hai. Hãy đọc `bridge.lua` trước khi chạy loadstring.

### Bảng điều khiển trên máy tính (`gui.py`)

Cửa sổ nền tối dùng `tkinter` có sẵn của Python:

- Thẻ trạng thái: bot Discord, tiến trình Roblox, số bridge đang kết nối
- Nút **Start / Stop / Restart**, chạy bot nền không hiện cửa sổ console
- Ô token có nút hiện/ẩn; **Save token** lưu vào `token.txt` và cập nhật `.gitignore`
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

**Cách bật:** đặt `ui.py` cạnh `bot.py`. Trong `bot.py`, tìm mục **`🚀 KHỞI CHẠY BOT / START`** (ngay trên `def main()`), rồi dán **ngay phía trên** đoạn mã ở phần *Enable it* bên trên. Khởi động lại bot và gõ `/panel` trong `#debug`.

### Danh sách lệnh

Chỉ dùng được trong `#debug`.

| Lệnh | Mô tả |
| --- | --- |
| `/panel` | Bảng nút bấm (cần `ui.py`) |
| `/help` | Xem tất cả lệnh |
| `/inject` | Kiểm tra Roblox và WebSocket, hiện loadstring nếu chưa kết nối |
| `/status` | Trạng thái, độ trễ, thời gian hoạt động |
| `/exec <code>` | Chạy đoạn Lua ngắn; lỗi hiện trong console Roblox |
| `/findscript <nguồn> <từ khóa>` | Link tìm kiếm trên Rscripts / ScriptBlox |
| `/esp [on/off]` | Viền người chơi |
| `/fly` · `/unfly` | Bay bằng `WASD` + `Q`/`E` |
| `/clicktotp [on/off]` | Giữ `Ctrl` và click để dịch chuyển |
| `/autoheal [on/off]` | Giữ máu luôn đầy |
| `/fpsboost` | Giảm đồ họa để tăng FPS |
| `/cre` | Thông tin tác giả |
| `!exec <script>` | Script dài: khối ```` ```lua ```` hoặc file `.lua` / `.txt` (tối đa 2 MB) |

Lệnh có `[on/off]` mặc định là **bật**, ví dụ `/esp state:OFF`.

### Bảo mật

Bot này chạy mã trên máy bạn và trong game của bạn, hãy giữ riêng tư.

- **Hãy đặt `ALLOWED_USER_IDS`.** Để trống thì bất kỳ ai gõ được trong `#debug` đều chạy được Lua trong game của bạn. Ví dụ: `ALLOWED_USER_IDS = [123456789012345678]`. Lấy ID: Discord → Settings → Advanced → bật **Developer Mode**, chuột phải vào tên bạn → **Copy User ID**.
- Không mời người lạ vào server và giữ kênh `#debug` ẩn với họ.
- Không đăng `bot.py` (có token thật) hoặc `token.txt` lên mạng.
- `loadstring(game:HttpGet(...))()` chạy bất cứ thứ gì ở URL đó; chỉ dùng URL bạn đã đọc hoặc tự quản lý.
- WebSocket chỉ lắng nghe trên `localhost` nên máy khác không kết nối được.

### Khắc phục sự cố

| Vấn đề | Cách xử lý |
| --- | --- |
| Không thấy slash command | Mời lại bot với scope `applications.commands`, chờ 1 phút, nhấn `Ctrl + R` |
| Bot ngoại tuyến / token không hợp lệ | Token sai hoặc đã reset. Tạo token mới và dán lại |
| `Used disallowed intents` | Bật **Message Content Intent** trong Developer Portal |
| `/inject` báo DISCONNECTED | Chạy bot trước, bridge sau; kiểm tra cổng `8765` |
| 🟠 WAITING FOR SCRIPT | Roblox đã chạy nhưng chưa nạp bridge. Chạy loadstring trong executor |
| "Missing Access" hoặc không trả lời | Cấp quyền xem và gửi tin nhắn cho bot trong `#debug` |
| Không có `/panel` | Thiếu `ui.py` hoặc chưa thêm đoạn mã vào `bot.py`; khởi động lại bot |
| `WebSocket` là nil | Executor không hỗ trợ `WebSocket.connect`; thử cái khác |
| Không nhận lệnh `python` | Cài lại Python và tích **Add Python to PATH** |
