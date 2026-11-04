# RobloxOnDiscord-Test

 
 **It's Videccode and takes the idea from @vaehz.** Thanks for downloading this project! It is a small test project, so expect rough edges. If you share or modify it, please keep these credits.

 
🇬🇧 English · [🇻🇳 Tiếng Việt](#-tiếng-việt)

Control your own Roblox client from a Discord channel. A Python bot receives slash commands and forwards them over a local WebSocket to a Lua bridge script running inside Roblox.

> [!WARNING]
> This project runs scripts through a third-party Roblox executor. Using executors violates the Roblox Terms of Use and **can get your account banned**. Use it only in a test environment, at your own risk, and never share your bot token.

---

## How it works

```
Discord (#debug)  ──►  bot.py (Python)  ──ws://localhost:8765──►  bridge.lua (Roblox + executor)
   slash commands        WebSocket server                          runs the received Lua
```

1. You run a slash command in the `#debug` channel.
2. `bot.py` validates it and sends it over a persistent WebSocket connection.
3. `bridge.lua`, running in the Roblox client, receives the payload and executes it.

## Features

- Persistent two-way WebSocket connection (no HTTP polling)
- Run raw Lua or upload `.lua` / `.txt` files (up to 2 MB)
- Character tweaks: walk speed, jump power, hip height, health
- Fly mode, and player ESP using `Highlight` instances
- Connection and process status checks
- Auto-reconnect on the Lua side

## Project structure

| File | Purpose |
| --- | --- |
| `bot.py` | Discord bot and WebSocket server. Syncs slash commands, checks for the Roblox process with `psutil`, and handles the token handshake. |
| `bridge.lua` | Client script run inside Roblox. Connects to the bot, retries on failure, caches the socket in `_G.ActiveWebSocket`, and executes received code. |
| `start.bat` | Windows helper that launches the bot. |

## Requirements

- **Windows 10/11** (the bot looks for `RobloxPlayerBeta.exe`)
- **Python 3.8+**, with *Add Python to PATH* ticked during install
- A **Discord bot token** from the [Discord Developer Portal](https://discord.com/developers/applications)
- A Roblox executor that supports `WebSocket.connect`

Setup & How to Create a Discord Bot

        Create a Discord Bot:
        Go to the Discord Developer Portal and click "New Application".
        Navigate to the "Bot" tab on the left sidebar.
        Under "Privileged Gateway Intents", enable "Message Content Intent".
        Click Reset Token to generate your bot token.
        Go to OAuth2 > URL Generator, select bot and applications.commands scopes, and check Administrator permissions. Open the generated link to invite the bot to your server.

## Installation

```bash
git clone https://github.com/giangveso0-ctrl/RobloxOnDiscord-Test.git
cd RobloxOnDiscord-Test
pip install discord.py websockets psutil
```

## Setup

1. Open `bot.py` and set your token:

   ```python
   DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"
   ```

   Never commit your real token. If it leaks, reset it in the Developer Portal.

2. Start the bot by double-clicking `start.bat`, or run:

   ```bash
   python bot.py
   ```

3. In Roblox, run this through your executor:

   ```lua
   loadstring(game:HttpGet("https://raw.githubusercontent.com/giangveso0-ctrl/RobloxOnDiscord-Test/main/bridge.lua"))()
   ```

4. In Discord, run `/inject` in the `#debug` channel to confirm the connection.

## Commands

All commands only work in the `#debug` channel.

| Command | Description |
| --- | --- |
| `/inject` | Checks for the Roblox process and shows the WebSocket state (🟢 connected / 🔴 disconnected). |
| `/exec` | Sends Lua code, or an uploaded `.lua` / `.txt` file (max 2 MB), to the client. |
| `/human` | Sets a property on your character's Humanoid. See below. |
| `/fly` | Enables flight that follows the camera direction. |
| `/unfly` | Disables flight and restores normal physics. |
| `/speed` | Sets `Humanoid.WalkSpeed` with validation. |
| `/esp` | Toggles player highlights. Turning it off removes all created instances. |
| `/status` | Shows connected clients and network latency. |

### `/human`

```
/human property:<name> value:<number>
```

| Property | Effect | Example |
| --- | --- | --- |
| `WalkSpeed` | Running speed | `/human property:WalkSpeed value:120` |
| `JumpPower` | Jump strength | `/human property:JumpPower value:200` |
| `HipHeight` | Body height offset | `/human property:HipHeight value:4` |
| `Health` | Current health | `/human property:Health value:50` |

## Troubleshooting

- **`/inject` shows DISCONNECTED:** make sure `bot.py` is running *before* you execute `bridge.lua`, and that port `8765` is free.
- **Slash commands don't appear:** re-invite the bot with the `applications.commands` scope and give it a minute to sync.
- **`WebSocket` is nil in Roblox:** your executor doesn't support `WebSocket.connect`. Try a different one.
- **Bot can't find Roblox:** start Roblox first and run the bot on the same Windows machine.

## Security notes

- The WebSocket server listens on `localhost` only. Don't expose port `8765` to the internet.
- `/exec` runs arbitrary code, so restrict `#debug` to people you trust.
- Keep your token out of version control, for example by using an environment variable.

## Disclaimer

This is a test project, provided as is, with no warranty. It is not affiliated with Roblox Corporation or Discord Inc.

---

# 🇻🇳 Tiếng Việt

**Đây là Videccode và lấy ý tưởng từ @vaehz.** Cảm ơn bạn đã tải dự án này! Đây là dự án thử nghiệm nhỏ nên có thể còn thiếu sót. Nếu bạn chia sẻ hoặc chỉnh sửa, vui lòng giữ lại phần ghi công này.

> [!WARNING]
> Dự án chạy script thông qua executor của bên thứ ba. Việc dùng executor vi phạm Điều khoản sử dụng của Roblox và **có thể khiến tài khoản bị khóa**. Chỉ dùng để thử nghiệm, tự chịu rủi ro, và không bao giờ chia sẻ token bot.
>
> Điều khiển client Roblox của chính bạn từ một kênh Discord. Bot Python nhận slash command rồi chuyển qua WebSocket cục bộ tới script Lua đang chạy trong Roblox.

## Cách hoạt động

```
Discord (#debug)  ──►  bot.py (Python)  ──ws://localhost:8765──►  bridge.lua (Roblox + executor)
```

1. Bạn dùng slash command trong kênh `#debug`.
2. `bot.py` kiểm tra lệnh rồi gửi qua kết nối WebSocket liên tục.
3. `bridge.lua` trong Roblox nhận và thực thi mã.

## Cấu trúc dự án

| File | Chức năng |
| --- | --- |
| `bot.py` | Bot Discord và WebSocket server: đồng bộ slash command, quét tiến trình bằng `psutil`, xác thực token handshake. |
| `bridge.lua` | Script phía client: kết nối, tự thử lại khi lỗi, lưu socket vào `_G.ActiveWebSocket`, thực thi mã nhận được. |
| `start.bat` | File batch khởi động bot trên Windows. |

## Yêu cầu

- **Windows 10/11** (bot tìm tiến trình `RobloxPlayerBeta.exe`)
- **Python 3.8+**, nhớ tích *Add Python to PATH* khi cài
- **Token bot Discord** từ [Discord Developer Portal](https://discord.com/developers/applications)
- Executor Roblox hỗ trợ `WebSocket.connect`

Thiết lập & Hướng dẫn tạo Bot Discord

    Cách tạo Bot Discord:
        Truy cập Discord Developer Portal và bấm "New Application".
        Vào mục "Bot" ở menu bên trái.
        Tại phần "Privileged Gateway Intents", bật tùy chọn "Message Content Intent".
        Bấm Reset Token để lấy mã token của bot.
        Chuyển sang mục OAuth2 > URL Generator, tích chọn bot và applications.commands, đồng thời chọn quyền Administrator. Copy đường dẫn đó mở lên trình duyệt để mời bot vào server của bạn.


## Cài đặt

```bash
git clone https://github.com/giangveso0-ctrl/RobloxOnDiscord-Test.git
cd RobloxOnDiscord-Test
pip install discord.py websockets psutil
```

## Thiết lập

1. Mở `bot.py` và điền token:

   ```python
   DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"
   ```

   Không commit token thật lên GitHub. Nếu bị lộ, hãy reset trong Developer Portal.

2. Chạy bot bằng cách nhấp đúp `start.bat`, hoặc:

   ```bash
   python bot.py
   ```

3. Trong Roblox, chạy đoạn sau qua executor:

   ```lua
   loadstring(game:HttpGet("https://raw.githubusercontent.com/giangveso0-ctrl/RobloxOnDiscord-Test/main/bridge.lua"))()
   ```

4. Trên Discord, dùng `/inject` trong kênh `#debug` để kiểm tra kết nối.

## Danh sách lệnh

Tất cả lệnh chỉ hoạt động trong kênh `#debug`.

| Lệnh | Mô tả |
| --- | --- |
| `/inject` | Kiểm tra tiến trình Roblox và trạng thái WebSocket (🟢 đã kết nối / 🔴 mất kết nối). |
| `/exec` | Gửi mã Lua hoặc file `.lua` / `.txt` (tối đa 2 MB) tới client. |
| `/human` | Chỉnh thuộc tính Humanoid của nhân vật. |
| `/fly` | Bật chế độ bay theo hướng camera. |
| `/unfly` | Tắt bay, khôi phục vật lý bình thường. |
| `/speed` | Đặt `Humanoid.WalkSpeed` có kiểm tra giá trị. |
| `/esp` | Bật/tắt highlight người chơi; khi tắt sẽ xóa sạch mọi instance đã tạo. |
| `/status` | Hiển thị số client kết nối và độ trễ mạng. |

### `/human`

```
/human property:<tên> value:<số>
```

| Thuộc tính | Tác dụng | Ví dụ |
| --- | --- | --- |
| `WalkSpeed` | Tốc độ chạy | `/human property:WalkSpeed value:120` |
| `JumpPower` | Sức nhảy | `/human property:JumpPower value:200` |
| `HipHeight` | Độ cao hông so với mặt đất | `/human property:HipHeight value:4` |
| `Health` | Máu hiện tại | `/human property:Health value:50` |

## Xử lý sự cố

- **`/inject` báo DISCONNECTED:** hãy chạy `bot.py` *trước* khi chạy `bridge.lua`, và đảm bảo cổng `8765` đang trống.
- **Không thấy slash command:** mời lại bot với scope `applications.commands` và chờ một lúc để đồng bộ.
- **`WebSocket` bị nil trong Roblox:** executor không hỗ trợ `WebSocket.connect`, hãy thử executor khác.
- **Bot không tìm thấy Roblox:** mở Roblox trước và chạy bot trên cùng máy Windows.

## Lưu ý bảo mật

- WebSocket server chỉ lắng nghe trên `localhost`. Không mở cổng `8765` ra internet.
- `/exec` chạy mã tùy ý, nên chỉ cho người đáng tin truy cập `#debug`.
- Không để token trong mã nguồn, nên dùng biến môi trường.

## Miễn trừ trách nhiệm

Đây là dự án thử nghiệm, cung cấp nguyên trạng và không có bảo hành. Dự án không liên kết với Roblox Corporation hay Discord Inc.
