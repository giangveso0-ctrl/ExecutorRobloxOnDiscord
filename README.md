<a id="top"></a>

<div align="center">

# ⚡ ExecutorOnDiscord

**Control your Roblox client from Discord — slash commands, buttons and a live control panel.**
**Điều khiển Roblox từ Discord — slash command, nút bấm và bảng điều khiển.**

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2?logo=discord&logoColor=white)
![Platform](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D6?logo=windows&logoColor=white)

**English** · [Tiếng Việt](#-tiếng-việt)

</div>

> **Credits:** made by **Videccode**, idea from **@vaehz**. Please keep the credits if you share or modify this project.
>
> **Disclaimer:** for testing and learning only. Running scripts through third-party executors can break the [Roblox Terms of Use](https://en.help.roblox.com/hc/en-us/articles/115004647846) and may get your account banned. Use it on your own account and in your own or private test places, at your own risk. Never use it to disrupt other players.

---

## ✨ Features

| | |
|---|---|
| 🎛️ **Control panel** | `/panel` posts a button panel: ESP, Fly, Click-TP, Auto-Heal, FPS Boost. Buttons turn green when a feature is on. |
| ⚡ **Script runner** | `/exec` opens a large editor box (4,000 chars). `!exec` takes long code blocks or `.lua` / `.txt` files up to 2 MB. **Run again** re-sends the last script. |
| 📖 **Smart help** | `/help` with a category dropdown. |
| 📊 **Live status** | `/status` and `/inject` with **Refresh** and **Loadstring** buttons. |
| 🔒 **Locked down** | Works only in `#debug`, and only for the user IDs you allow — buttons and menus included. |

## 🧩 How it works

```
Discord (#debug) ──commands / buttons──▶ bot.py ◀──WebSocket ws://localhost:8765──▶ bridge.lua (in Roblox)
```

`bot.py` logs in to Discord and runs a local WebSocket server. `bridge.lua` runs inside Roblox through your executor, connects to it, and executes whatever Lua the bot sends.

| File | Purpose |
|------|---------|
| `bot.py` | Discord bot + WebSocket server |
| `bridge.lua` | Roblox-side client |
| `start.bat` | Windows one-click launcher |
| `requirements.txt` | Python dependencies |

## 📦 Requirements

- Windows 10 / 11 (the bot checks for `RobloxPlayerBeta.exe`)
- [Python 3.8+](https://www.python.org/downloads/) — tick **Add Python to PATH**
- A Discord server where you can add bots
- A Roblox executor with `WebSocket.connect` support

## 🚀 Quick start

**1. Install**

```bash
git clone https://github.com/giangveso0-ctrl/ExecutorRobloxOnDiscord.git
cd ExecutorRobloxOnDiscord
pip install -r requirements.txt
```

**2. Create the Discord bot**

1. [Developer Portal](https://discord.com/developers/applications) → **New Application** → **Bot** → **Reset Token** → copy it.
2. Same page → **Privileged Gateway Intents** → enable **Message Content Intent** → save.
3. **OAuth2 → URL Generator** → scopes `bot` + `applications.commands` → permissions `View Channels`, `Send Messages`, `Embed Links`, `Attach Files`.
4. Open the generated URL and add the bot to your server.
5. Create a text channel named **`#debug`**.

> 🔑 The token is a password. Never post it or commit it. If it leaks, reset it.

**3. Allow yourself**

Enable Discord **Developer Mode** (Settings → Advanced), right-click your name → **Copy User ID**, then in `bot.py`:

```python
ALLOWED_USER_IDS = [123456789012345678]
```

**4. Run the bot**

```bash
python bot.py        # or double-click start.bat
```

Paste the token when asked (it can be saved to `token.txt`, which is git-ignored).

**5. Run the bridge in Roblox** (in your executor)

```lua
loadstring(game:HttpGet("https://raw.githubusercontent.com/giangveso0-ctrl/ExecutorRobloxOnDiscord/main/bridge.lua"))()
```

> Loading from a URL runs whatever is there — read `bridge.lua` first, or paste its contents instead.

**6. Test** — in `#debug` type `/inject`. When it says **CONNECTED**, type `/panel`.

> ⚠️ Start the bot **before** the bridge. If you close either, start both again.

## 🎮 Commands

All commands work only in `#debug`. Prefix commands accept `!` or `.`.

| Command | What it does |
|---------|--------------|
| `/panel` · `!panel` | Button control panel |
| `/exec [code]` | Run Lua (empty = open the editor box) |
| `!exec <script>` | Long script or attached `.lua` / `.txt` |
| `/help` · `!help` | Help with category dropdown |
| `/inject` | Check Roblox + WebSocket, get the loadstring |
| `/status` | Roblox / WebSocket state, latency, uptime |
| `/esp [on/off]` | Player highlights |
| `/fly` · `/unfly` | Flight (WASD + Q/E) |
| `/clicktotp [on/off]` | `Ctrl` + click to teleport |
| `/autoheal [on/off]` | Keep health full |
| `/fpsboost` | Lower graphics for more FPS |
| `/findscript <source> <keyword>` | Search link for Rscripts / ScriptBlox |
| `/cre` | Credits |

## ⚙️ Configuration

Edit the constants at the top of `bot.py`, or set environment variables:

| Variable | Default | Meaning |
|----------|---------|---------|
| `DISCORD_BOT_TOKEN` | — | Bot token (or `token.txt`) |
| `ALLOWED_USER_IDS` | empty | Comma-separated IDs allowed to use the bot |
| `DEBUG_CHANNEL` | `debug` | Channel the bot listens in |
| `WS_PORT` | `8765` | Local WebSocket port (must match `bridge.lua`) |

## 🛡️ Security

This bot lets people in your channel **run Lua inside your Roblox client**.

- **Always set `ALLOWED_USER_IDS`** — ideally just your own ID. The bot warns you when it is empty.
- Keep `#debug` private and only add the bot to servers you control.
- Never commit `token.txt`.
- The WebSocket server listens on `localhost` only.

## 🔧 Troubleshooting

| Problem | Fix |
|---------|-----|
| Slash commands missing | Re-invite with `applications.commands`, wait a minute, press `Ctrl + R` in Discord. |
| Invalid token | Reset it in the Developer Portal and paste the new one. |
| `Used disallowed intents` | Enable **Message Content Intent** in the Developer Portal. |
| `/inject` says DISCONNECTED | Start the bot first, then the bridge; make sure port `8765` is free. |
| "Access denied" on buttons | Your ID is not in `ALLOWED_USER_IDS`. |
| Old panel buttons do nothing | Run `/panel` again. |
| `WebSocket` is nil | Your executor lacks `WebSocket.connect`; try another. |
| `python` not recognized | Reinstall Python with **Add Python to PATH**. |

## 🤝 Contributing & License

Issues and pull requests are welcome — please keep changes focused. No license is set yet; add a `LICENSE` file (e.g. MIT) so others know how they may use the code.

---

<a id="-tiếng-việt"></a>

<div align="center">

# 🇻🇳 Tiếng Việt

[English](#top) · **Tiếng Việt**

</div>

> **Ghi công:** do **Videccode** làm, ý tưởng từ **@vaehz**. Vui lòng giữ phần ghi công khi chia sẻ hoặc chỉnh sửa.
>
> **Lưu ý:** chỉ dùng để thử nghiệm và học tập. Chạy script qua executor bên thứ ba có thể vi phạm [Điều khoản sử dụng của Roblox](https://en.help.roblox.com/hc/en-us/articles/115004647846) và có thể khiến tài khoản bị khóa. Chỉ dùng trên tài khoản của bạn, trong game của chính bạn hoặc place thử nghiệm riêng tư, tự chịu rủi ro. Không dùng để gây ảnh hưởng đến người chơi khác.

## ✨ Tính năng

| | |
|---|---|
| 🎛️ **Bảng điều khiển** | `/panel` đăng bảng nút: ESP, Fly, Click-TP, Auto-Heal, FPS Boost. Nút chuyển xanh khi tính năng đang bật. |
| ⚡ **Chạy script** | `/exec` mở ô nhập lớn (4.000 ký tự). `!exec` nhận script dài hoặc file `.lua` / `.txt` tới 2 MB. Nút **Run again** gửi lại script vừa chạy. |
| 📖 **Trợ giúp** | `/help` có menu chọn mục. |
| 📊 **Trạng thái** | `/status`, `/inject` có nút **Refresh** và **Loadstring**. |
| 🔒 **Bảo mật** | Chỉ dùng trong `#debug` và chỉ với ID được phép — gồm cả nút và menu. |

## 🧩 Cách hoạt động

```
Discord (#debug) ──lệnh / nút──▶ bot.py ◀──WebSocket ws://localhost:8765──▶ bridge.lua (trong Roblox)
```

`bot.py` đăng nhập Discord và mở máy chủ WebSocket cục bộ. `bridge.lua` chạy trong Roblox qua executor, kết nối tới đó và chạy mã Lua mà bot gửi.

## 📦 Yêu cầu

- Windows 10 / 11 (bot tìm tiến trình `RobloxPlayerBeta.exe`)
- [Python 3.8+](https://www.python.org/downloads/) — nhớ tích **Add Python to PATH**
- Một server Discord mà bạn thêm được bot
- Executor Roblox hỗ trợ `WebSocket.connect`

## 🚀 Bắt đầu nhanh

**1. Cài đặt**

```bash
git clone https://github.com/giangveso0-ctrl/ExecutorRobloxOnDiscord.git
cd ExecutorRobloxOnDiscord
pip install -r requirements.txt
```

**2. Tạo bot Discord**

1. [Developer Portal](https://discord.com/developers/applications) → **New Application** → **Bot** → **Reset Token** → sao chép token.
2. Cùng trang → **Privileged Gateway Intents** → bật **Message Content Intent** → lưu.
3. **OAuth2 → URL Generator** → scope `bot` + `applications.commands` → quyền `View Channels`, `Send Messages`, `Embed Links`, `Attach Files`.
4. Mở URL vừa tạo và thêm bot vào server.
5. Tạo kênh chat tên **`#debug`**.

> 🔑 Token như mật khẩu. Không đăng công khai hay commit lên GitHub. Nếu bị lộ, hãy reset.

**3. Cho phép bản thân**

Bật **Chế độ nhà phát triển** trong Discord (Cài đặt → Nâng cao), chuột phải vào tên bạn → **Sao chép ID người dùng**, rồi điền vào `bot.py`:

```python
ALLOWED_USER_IDS = [123456789012345678]
```

**4. Chạy bot**

```bash
python bot.py        # hoặc nhấp đúp start.bat
```

Dán token khi được hỏi (có thể lưu vào `token.txt`, file này đã được git bỏ qua).

**5. Chạy bridge trong Roblox** (trong executor)

```lua
loadstring(game:HttpGet("https://raw.githubusercontent.com/giangveso0-ctrl/ExecutorRobloxOnDiscord/main/bridge.lua"))()
```

> Tải mã từ URL sẽ chạy bất cứ thứ gì có ở đó — hãy đọc `bridge.lua` trước hoặc dán trực tiếp nội dung.

**6. Kiểm tra** — trong `#debug` gõ `/inject`. Khi báo **CONNECTED**, gõ `/panel`.

> ⚠️ Chạy bot **trước**, rồi mới chạy bridge. Nếu đóng một trong hai, hãy chạy lại cả hai.

## 🎮 Lệnh

Tất cả lệnh chỉ dùng trong `#debug`. Lệnh tiền tố dùng `!` hoặc `.`.

| Lệnh | Chức năng |
|------|-----------|
| `/panel` · `!panel` | Bảng điều khiển bằng nút |
| `/exec [code]` | Chạy Lua (để trống = mở ô nhập lớn) |
| `!exec <script>` | Script dài hoặc file `.lua` / `.txt` đính kèm |
| `/help` · `!help` | Trợ giúp có menu chọn mục |
| `/inject` | Kiểm tra Roblox + WebSocket, lấy loadstring |
| `/status` | Trạng thái, độ trễ, thời gian chạy |
| `/esp [on/off]` | Viền người chơi |
| `/fly` · `/unfly` | Bay (WASD + Q/E) |
| `/clicktotp [on/off]` | `Ctrl` + click để dịch chuyển |
| `/autoheal [on/off]` | Giữ máu luôn đầy |
| `/fpsboost` | Giảm đồ họa để tăng FPS |
| `/findscript <source> <keyword>` | Link tìm kiếm Rscripts / ScriptBlox |
| `/cre` | Thông tin tác giả |

## ⚙️ Cấu hình

Sửa các hằng số đầu `bot.py`, hoặc đặt biến môi trường:

| Biến | Mặc định | Ý nghĩa |
|------|----------|---------|
| `DISCORD_BOT_TOKEN` | — | Token bot (hoặc `token.txt`) |
| `ALLOWED_USER_IDS` | trống | ID được phép dùng bot, cách nhau bằng dấu phẩy |
| `DEBUG_CHANNEL` | `debug` | Kênh bot lắng nghe |
| `WS_PORT` | `8765` | Cổng WebSocket cục bộ (phải khớp `bridge.lua`) |

## 🛡️ Bảo mật

Bot này cho phép người trong kênh **chạy mã Lua trong client Roblox của bạn**.

- **Luôn đặt `ALLOWED_USER_IDS`** — tốt nhất chỉ ID của bạn. Bot sẽ cảnh báo nếu để trống.
- Giữ `#debug` riêng tư và chỉ thêm bot vào server bạn kiểm soát.
- Không commit `token.txt`.
- Máy chủ WebSocket chỉ lắng nghe trên `localhost`.

## 🔧 Khắc phục sự cố

| Vấn đề | Cách xử lý |
|--------|------------|
| Không thấy slash command | Mời lại bot với `applications.commands`, đợi một phút, nhấn `Ctrl + R` trong Discord. |
| Token không hợp lệ | Reset trong Developer Portal rồi dán token mới. |
| `Used disallowed intents` | Bật **Message Content Intent** trong Developer Portal. |
| `/inject` báo DISCONNECTED | Chạy bot trước, rồi bridge; đảm bảo cổng `8765` còn trống. |
| Nút báo "Không có quyền" | ID của bạn chưa có trong `ALLOWED_USER_IDS`. |
| Nút ở panel cũ không phản hồi | Gõ `/panel` lại. |
| `WebSocket` là nil | Executor không hỗ trợ `WebSocket.connect`; thử cái khác. |
| Không nhận lệnh `python` | Cài lại Python và tích **Add Python to PATH**. |

## 🤝 Đóng góp & Giấy phép

Hoan nghênh issue và pull request — vui lòng giữ thay đổi tập trung. Chưa có giấy phép; hãy thêm tệp `LICENSE` (ví dụ MIT) để người khác biết cách sử dụng mã nguồn.
