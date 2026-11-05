<div align="center">

# RobloxOnDiscord-Test

**Control a Roblox client from Discord with slash commands.**

**English** | [Tiếng Việt](#tiếng-việt)

</div>

> **It's Videccode and takes the idea from @vaehz.** Thanks for downloading this project! It is a small test project, so expect rough edges. If you share or modify it, please keep these credits.

> **Disclaimer:** For testing and learning only. Running scripts through third-party executors can break the [Roblox Terms of Use](https://en.help.roblox.com/hc/en-us/articles/115004647846) and may get your account banned. Use it on your own account, in your own experiences or private test places, and at your own risk. Never use it to disrupt other players.

## Table of contents

1. [How it works](#how-it-works)
2. [Requirements](#requirements)
3. [Step 1: Create the Discord bot](#step-1-create-the-discord-bot)
4. [Step 2: Add the bot to your server](#step-2-add-the-bot-to-your-server)
5. [Step 3: Install and configure](#step-3-install-and-configure)
6. [Step 4: Run it](#step-4-run-it)
7. [Commands](#commands)
8. [Troubleshooting](#troubleshooting)

---

## How it works

```
Discord (#debug)  ──slash command──▶  bot.py  ◀──WebSocket (ws://localhost:8765)──▶  bridge.lua (inside Roblox)
```

- `bot.py` logs in to Discord and starts a local WebSocket server on `ws://localhost:8765`.
- `bridge.lua` runs inside Roblox through an executor, connects to that server and reconnects automatically if it drops.
- When you use a slash command, the bot sends Lua over the socket and the bridge runs it in the game.

| File | Description |
| --- | --- |
| `bot.py` | The Discord bot, slash commands, `psutil` process check and the WebSocket server. |
| `bridge.lua` | Client script: connects to the bot, shows `StarterGui` notifications, runs received code with `loadstring()`. |
| `start.bat` | Windows shortcut that launches the bot. |

## Requirements

- Windows 10 / 11 (the bot looks for the `RobloxPlayerBeta.exe` process)
- [Python 3.8+](https://www.python.org/downloads/) (tick **Add Python to PATH** during install)
- A Discord account, and a server where you can add bots
- A Roblox executor that supports `WebSocket.connect` (e.g. Solara, Wave, Zeno)

---

## Step 1: Create the Discord bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and log in.
2. Click **New Application**, enter a name (for example `RobloxOnDiscord`) and accept the terms.
3. In the left menu, open **Bot**.
4. Click **Reset Token**, confirm, then **Copy** the token and keep it somewhere safe. Discord only shows it once. If you lose it, just reset it again.
5. On the same page, under **Privileged Gateway Intents**, leave everything off. Slash commands don't need them (turn on **Message Content Intent** only if you later edit `bot.py` to read messages).

> **Treat the token like a password.** Anyone who has it can control your bot. Never post it or commit it to GitHub. If it leaks, reset it immediately.

## Step 2: Add the bot to your server

You need the **Manage Server** permission on the server you are adding it to (or be the owner).

1. In the Developer Portal, open your application and go to **OAuth2 → URL Generator**.
2. Under **Scopes**, tick:
   - `bot`
   - `applications.commands` (required for slash commands)
3. Under **Bot Permissions**, tick:
   - `View Channels`
   - `Send Messages`
   - `Embed Links`
   - `Attach Files`
4. Copy the **Generated URL** at the bottom of the page and open it in your browser.
5. Choose your server from the dropdown, click **Continue**, then **Authorize** and complete the captcha.
6. Open Discord: the bot should now appear in your member list (offline until you start it).
7. Create a text channel named **`#debug`**. The commands only work in this channel.
8. Make sure the bot can see and write in `#debug` (channel settings → Permissions → add the bot's role if the channel is private).

## Step 3: Install and configure

```bash
git clone https://github.com/giangveso0-ctrl/RobloxOnDiscord-Test.git
cd RobloxOnDiscord-Test
pip install discord.py websockets psutil
```

Open `bot.py` in a text editor and paste your token:

```python
DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"
```

Save the file. Don't upload `bot.py` to GitHub with your real token inside.

## Step 4: Run it

1. **Start the bot.** Double-click `start.bat`, or run:

   ```bash
   python bot.py
   ```

   Wait until the console says the bot is logged in. The bot now shows as online in Discord.

2. **Run the bridge in Roblox.** Join a game, then execute this in your executor:

   ```lua
   loadstring(game:HttpGet("https://raw.githubusercontent.com/giangveso0-ctrl/RobloxOnDiscord-Test/main/bridge.lua"))()
   ```

   Loading code from a URL runs whatever is at that URL, so read `bridge.lua` first, or paste its contents into the executor instead.

3. **Test the connection.** In `#debug`, type `/inject`. It should report that Roblox is running and the WebSocket is **CONNECTED**. Now you can use any command below.

> **Order matters:** start `bot.py` first, then run the bridge. If you close Roblox or the bot, start both again.

---

## Commands

All commands only work in `#debug`.

| Command | Description |
| --- | --- |
| `/inject` | Checks for `RobloxPlayerBeta.exe` and shows the WebSocket state. |
| `/exec` | Sends a Lua string, or an uploaded `.lua` / `.txt` file (max 2 MB), to the game. |
| `/human` | Sets a Humanoid property: `WalkSpeed`, `JumpPower`, `HipHeight` or `Health`. |
| `/fly` | Starts flying using `BodyVelocity` / `BodyGyro` in the camera direction. |
| `/unfly` | Stops flying and restores normal physics. |
| `/speed` | Sets `Humanoid.WalkSpeed` (validated). |
| `/esp` | Toggles `Highlight` outlines on players. |
| `/status` | Shows connected clients and connection diagnostics. |

Example:

```
/human property:WalkSpeed value:120
```

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Slash commands don't show up | Re-invite the bot with the `applications.commands` scope, wait a minute, then refresh Discord with `Ctrl + R`. |
| Bot is offline | Check the console for errors. A wrong or reset token causes a login failure, so paste a fresh token into `bot.py`. |
| `/inject` says DISCONNECTED | Start `bot.py` first, then run `bridge.lua`. Make sure nothing else uses port `8765` and your firewall allows local connections. |
| "Missing Access" or no reply | Give the bot permission to view and send messages in `#debug`. |
| `WebSocket` is nil in Roblox | Your executor doesn't support `WebSocket.connect`. Try another one. |
| `python` is not recognized | Reinstall Python and tick **Add Python to PATH**. |

## Contributing

Issues and pull requests are welcome. Please keep changes focused.

## License

No license has been specified yet. Add a `LICENSE` file (for example MIT) so others know how they can use the code.

---

<a name="tiếng-việt"></a>

<div align="center">

# Tiếng Việt

**Điều khiển client Roblox từ Discord bằng slash command.**

[English](#robloxondiscord-test) | **Tiếng Việt**

</div>

> **Đây là Videccode và lấy ý tưởng từ @vaehz.** Cảm ơn bạn đã tải dự án này! Đây là dự án thử nghiệm nhỏ nên có thể còn thiếu sót. Nếu bạn chia sẻ hoặc chỉnh sửa, vui lòng giữ lại phần ghi công này.

> **Lưu ý:** Chỉ dùng để thử nghiệm và học tập. Chạy script qua executor bên thứ ba có thể vi phạm [Điều khoản sử dụng của Roblox](https://en.help.roblox.com/hc/en-us/articles/115004647846) và có thể khiến tài khoản bị khóa. Chỉ dùng trên tài khoản của bạn, trong game của chính bạn hoặc place thử nghiệm riêng tư, và tự chịu rủi ro. Không dùng để gây ảnh hưởng đến người chơi khác.

## Mục lục

1. [Cách hoạt động](#cách-hoạt-động)
2. [Yêu cầu](#yêu-cầu)
3. [Bước 1: Tạo bot Discord](#bước-1-tạo-bot-discord)
4. [Bước 2: Thêm bot vào server](#bước-2-thêm-bot-vào-server)
5. [Bước 3: Cài đặt và cấu hình](#bước-3-cài-đặt-và-cấu-hình)
6. [Bước 4: Chạy](#bước-4-chạy)
7. [Danh sách lệnh](#danh-sách-lệnh)
8. [Khắc phục sự cố](#khắc-phục-sự-cố)

---

## Cách hoạt động

```
Discord (#debug)  ──slash command──▶  bot.py  ◀──WebSocket (ws://localhost:8765)──▶  bridge.lua (trong Roblox)
```

- `bot.py` đăng nhập Discord và mở máy chủ WebSocket cục bộ tại `ws://localhost:8765`.
- `bridge.lua` chạy trong Roblox thông qua executor, kết nối tới máy chủ đó và tự kết nối lại nếu bị ngắt.
- Khi bạn dùng slash command, bot gửi mã Lua qua socket và bridge sẽ chạy mã đó trong game.

| Tệp | Mô tả |
| --- | --- |
| `bot.py` | Bot Discord, slash command, kiểm tra tiến trình bằng `psutil` và máy chủ WebSocket. |
| `bridge.lua` | Script phía client: kết nối tới bot, hiện thông báo `StarterGui`, chạy mã nhận được bằng `loadstring()`. |
| `start.bat` | File Windows để khởi động bot nhanh. |

## Yêu cầu

- Windows 10 / 11 (bot tìm tiến trình `RobloxPlayerBeta.exe`)
- [Python 3.8+](https://www.python.org/downloads/) (nhớ tích **Add Python to PATH** khi cài)
- Tài khoản Discord và một server mà bạn có thể thêm bot
- Executor Roblox hỗ trợ `WebSocket.connect` (ví dụ: Solara, Wave, Zeno)

---

## Bước 1: Tạo bot Discord

1. Vào [Discord Developer Portal](https://discord.com/developers/applications) và đăng nhập.
2. Nhấn **New Application**, đặt tên (ví dụ `RobloxOnDiscord`) và đồng ý điều khoản.
3. Ở menu bên trái, mở **Bot**.
4. Nhấn **Reset Token**, xác nhận, rồi nhấn **Copy** và lưu token ở nơi an toàn. Discord chỉ hiện token một lần. Nếu mất, chỉ cần reset lại.
5. Trên cùng trang, ở mục **Privileged Gateway Intents**, để tắt hết. Slash command không cần các intent này (chỉ bật **Message Content Intent** nếu sau này bạn sửa `bot.py` để đọc tin nhắn).

> **Hãy coi token như mật khẩu.** Ai có token đều điều khiển được bot của bạn. Không đăng công khai hoặc commit lên GitHub. Nếu bị lộ, hãy reset ngay.

## Bước 2: Thêm bot vào server

Bạn cần quyền **Manage Server** trên server muốn thêm bot (hoặc là chủ server).

1. Trong Developer Portal, mở ứng dụng của bạn và vào **OAuth2 → URL Generator**.
2. Ở mục **Scopes**, tích:
   - `bot`
   - `applications.commands` (bắt buộc để dùng slash command)
3. Ở mục **Bot Permissions**, tích:
   - `View Channels`
   - `Send Messages`
   - `Embed Links`
   - `Attach Files`
4. Sao chép **Generated URL** ở cuối trang và mở bằng trình duyệt.
5. Chọn server trong danh sách, nhấn **Continue**, sau đó **Authorize** và hoàn thành captcha.
6. Mở Discord: bot sẽ xuất hiện trong danh sách thành viên (ngoại tuyến cho tới khi bạn chạy bot).
7. Tạo một kênh văn bản tên **`#debug`**. Các lệnh chỉ dùng được ở kênh này.
8. Đảm bảo bot xem và gửi được tin nhắn trong `#debug` (cài đặt kênh → Permissions → thêm role của bot nếu kênh ở chế độ riêng tư).

## Bước 3: Cài đặt và cấu hình

```bash
git clone https://github.com/giangveso0-ctrl/RobloxOnDiscord-Test.git
cd RobloxOnDiscord-Test
pip install discord.py websockets psutil
```

Mở `bot.py` bằng trình soạn thảo văn bản và dán token của bạn:

```python
DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"
```

Lưu file lại. Không tải `bot.py` lên GitHub khi bên trong có token thật.

## Bước 4: Chạy

1. **Khởi động bot.** Nhấp đúp `start.bat`, hoặc chạy:

   ```bash
   python bot.py
   ```

   Đợi đến khi console báo bot đã đăng nhập. Bot sẽ hiển thị trực tuyến trên Discord.

2. **Chạy bridge trong Roblox.** Vào một game rồi thực thi đoạn sau trong executor:

   ```lua
   loadstring(game:HttpGet("https://raw.githubusercontent.com/giangveso0-ctrl/RobloxOnDiscord-Test/main/bridge.lua"))()
   ```

   Tải mã từ URL sẽ chạy bất cứ thứ gì có tại URL đó, nên hãy đọc `bridge.lua` trước, hoặc dán trực tiếp nội dung vào executor.

3. **Kiểm tra kết nối.** Trong `#debug`, gõ `/inject`. Bot sẽ báo Roblox đang chạy và WebSocket là **CONNECTED**. Sau đó bạn có thể dùng các lệnh bên dưới.

> **Thứ tự quan trọng:** chạy `bot.py` trước, sau đó mới chạy bridge. Nếu đóng Roblox hoặc bot, hãy chạy lại cả hai.

---

## Danh sách lệnh

Tất cả lệnh chỉ dùng được trong `#debug`.

| Lệnh | Mô tả |
| --- | --- |
| `/inject` | Kiểm tra `RobloxPlayerBeta.exe` và trạng thái WebSocket. |
| `/exec` | Gửi chuỗi Lua, hoặc tệp `.lua` / `.txt` tải lên (tối đa 2 MB), vào game. |
| `/human` | Đặt thuộc tính Humanoid: `WalkSpeed`, `JumpPower`, `HipHeight` hoặc `Health`. |
| `/fly` | Bắt đầu bay bằng `BodyVelocity` / `BodyGyro` theo hướng camera. |
| `/unfly` | Dừng bay và khôi phục vật lý bình thường. |
| `/speed` | Đặt `Humanoid.WalkSpeed` (có kiểm tra giá trị). |
| `/esp` | Bật/tắt viền `Highlight` trên người chơi. |
| `/status` | Hiển thị các client đang kết nối và thông tin chẩn đoán. |

Ví dụ:

```
/human property:WalkSpeed value:120
```

## Khắc phục sự cố

| Vấn đề | Cách xử lý |
| --- | --- |
| Không thấy slash command | Mời lại bot với scope `applications.commands`, đợi một phút rồi tải lại Discord bằng `Ctrl + R`. |
| Bot ngoại tuyến | Xem lỗi trong console. Token sai hoặc đã bị reset sẽ khiến đăng nhập thất bại, hãy dán token mới vào `bot.py`. |
| `/inject` báo DISCONNECTED | Chạy `bot.py` trước, rồi mới chạy `bridge.lua`. Đảm bảo không có chương trình nào khác dùng cổng `8765` và firewall cho phép kết nối cục bộ. |
| "Missing Access" hoặc bot không trả lời | Cấp cho bot quyền xem và gửi tin nhắn trong `#debug`. |
| `WebSocket` là nil trong Roblox | Executor của bạn không hỗ trợ `WebSocket.connect`. Hãy thử executor khác. |
| Không nhận lệnh `python` | Cài lại Python và tích **Add Python to PATH**. |

## Đóng góp

Hoan nghênh issue và pull request. Vui lòng giữ thay đổi tập trung.

## Giấy phép

Chưa có giấy phép được chỉ định. Hãy thêm tệp `LICENSE` (ví dụ MIT) để người khác biết cách sử dụng mã nguồn.
