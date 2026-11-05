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
| `bot.py` | The Discord bot, slash and prefix commands, `psutil` process check and the WebSocket server. |
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
5. On the same page, scroll to **Privileged Gateway Intents** and turn **ON** **Message Content Intent**, then click **Save Changes**. The `!exec` command needs it to read your messages. Without it the bot refuses to start.

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
pip install -U discord.py websockets psutil
```

Give the bot your token in **one** of these ways:

| Option | How |
| --- | --- |
| Paste it when asked (easiest) | Just run `bot.py` (or `start.bat`). With no token saved, the console asks you to paste it, then offers to save it to `token.txt` and adds that file to `.gitignore` for you. |
| `token.txt` | Create a file named `token.txt` next to `bot.py` and paste only the token into it. |
| Edit `bot.py` | Replace `PASTE_YOUR_BOT_TOKEN_HERE` in `DISCORD_BOT_TOKEN = "..."` with your token. |
| Environment variable | Set `DISCORD_BOT_TOKEN` before running the bot. |

A real token has three parts separated by dots, like `XXXXXXXXXXXXXXXXXXXXXXXX.XXXXXX.XXXXXXXXXXXXXXXXXXXXXXXXXXX`. Don't upload `bot.py` or `token.txt` to GitHub with your real token inside (add `token.txt` to `.gitignore`).

**Optional:** to stop other people in `#debug` from running code on your PC, put your Discord user ID in `ALLOWED_USER_IDS` at the top of `bot.py`, for example `ALLOWED_USER_IDS = [123456789012345678]`. Leave it empty to allow everyone in the channel.

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

**Slash commands**

| Command | Description |
| --- | --- |
| `/help` | Shows all commands. |
| `/inject` | Checks for `RobloxPlayerBeta.exe`, shows the WebSocket state and the loadstring to run. |
| `/status` | Shows Roblox / WebSocket state, latency and uptime. |
| `/exec <code>` | Runs a short Lua snippet in the game. Syntax and runtime errors are reported in the Roblox console. |
| `/findscript <source> <keyword>` | Gives a search link on Rscripts or ScriptBlox. |
| `/esp [on/off]` | Player `Highlight` outlines. Also covers new players and respawns. |
| `/fly` / `/unfly` | Flight with WASD + Q/E (down/up). |
| `/clicktotp [on/off]` | Hold `Ctrl` and click to teleport. |
| `/autoheal [on/off]` | Keeps your health full. |
| `/fpsboost` | Lowers graphics quality for more FPS. |
| `/cre` | Credits. |

**Prefix commands** (`!` or `.`)

| Command | Description |
| --- | --- |
| `!exec <script>` | For long scripts. You can paste a ` ```lua ` code block or attach a `.lua` / `.txt` file (max 2 MB). |
| `!help` | Shows the help embed. |

The `[on/off]` commands default to **on**. Example: `/esp state:OFF`.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Slash commands don't show up | Re-invite the bot with the `applications.commands` scope, wait a minute, then refresh Discord with `Ctrl + R`. |
| Bot is offline or console says invalid token | A wrong or reset token causes a login failure. The bot offers to delete the saved `token.txt`, then run it again and paste a fresh token. |
| Console says `Used disallowed intents` | In the Developer Portal → **Bot**, turn on **Message Content Intent** and save. |
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
| `bot.py` | Bot Discord, slash command và lệnh tiền tố, kiểm tra tiến trình bằng `psutil` và máy chủ WebSocket. |
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
5. Trên cùng trang, kéo xuống **Privileged Gateway Intents** và **BẬT** **Message Content Intent**, rồi nhấn **Save Changes**. Lệnh `!exec` cần quyền này để đọc tin nhắn. Nếu không bật, bot sẽ không khởi động được.

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
pip install -U discord.py websockets psutil
```

Đưa token cho bot theo **một** trong các cách sau:

| Cách | Thực hiện |
| --- | --- |
| Dán khi được hỏi (dễ nhất) | Chỉ cần chạy `bot.py` (hoặc `start.bat`). Khi chưa có token, console sẽ yêu cầu bạn dán token, rồi hỏi có muốn lưu vào `token.txt` không và tự thêm file đó vào `.gitignore`. |
| `token.txt` | Tạo file `token.txt` cạnh `bot.py` và chỉ dán token vào trong đó. |
| Sửa `bot.py` | Thay `PASTE_YOUR_BOT_TOKEN_HERE` trong `DISCORD_BOT_TOKEN = "..."` bằng token của bạn. |
| Biến môi trường | Đặt `DISCORD_BOT_TOKEN` trước khi chạy bot. |

Token thật gồm ba phần cách nhau bởi dấu chấm, ví dụ `XXXXXXXXXXXXXXXXXXXXXXXX.XXXXXX.XXXXXXXXXXXXXXXXXXXXXXXXXXX`. Không tải `bot.py` hoặc `token.txt` lên GitHub khi bên trong có token thật (hãy thêm `token.txt` vào `.gitignore`).

**Tùy chọn:** để người khác trong `#debug` không chạy được mã trên máy bạn, điền ID Discord của bạn vào `ALLOWED_USER_IDS` ở đầu `bot.py`, ví dụ `ALLOWED_USER_IDS = [123456789012345678]`. Để trống nếu muốn cho mọi người trong kênh dùng.

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

**Slash command**

| Lệnh | Mô tả |
| --- | --- |
| `/help` | Hiển thị tất cả lệnh. |
| `/inject` | Kiểm tra `RobloxPlayerBeta.exe`, trạng thái WebSocket và loadstring cần chạy. |
| `/status` | Hiển thị trạng thái Roblox / WebSocket, độ trễ và thời gian hoạt động. |
| `/exec <code>` | Chạy đoạn Lua ngắn trong game. Lỗi cú pháp và lỗi khi chạy sẽ được báo trong console Roblox. |
| `/findscript <source> <keyword>` | Cho link tìm kiếm trên Rscripts hoặc ScriptBlox. |
| `/esp [on/off]` | Viền `Highlight` người chơi. Tự cập nhật người mới và khi hồi sinh. |
| `/fly` / `/unfly` | Bay bằng WASD + Q/E (xuống/lên). |
| `/clicktotp [on/off]` | Giữ `Ctrl` và click để dịch chuyển. |
| `/autoheal [on/off]` | Giữ máu luôn đầy. |
| `/fpsboost` | Giảm chất lượng đồ họa để tăng FPS. |
| `/cre` | Thông tin tác giả. |

**Lệnh tiền tố** (`!` hoặc `.`)

| Lệnh | Mô tả |
| --- | --- |
| `!exec <script>` | Dùng cho script dài. Có thể dán khối mã ` ```lua ` hoặc đính kèm file `.lua` / `.txt` (tối đa 2 MB). |
| `!help` | Hiển thị bảng hướng dẫn. |

Các lệnh có `[on/off]` mặc định là **bật**. Ví dụ: `/esp state:OFF`.

## Khắc phục sự cố

| Vấn đề | Cách xử lý |
| --- | --- |
| Không thấy slash command | Mời lại bot với scope `applications.commands`, đợi một phút rồi tải lại Discord bằng `Ctrl + R`. |
| Bot ngoại tuyến hoặc console báo token không hợp lệ | Token sai hoặc đã bị reset sẽ khiến đăng nhập thất bại. Bot sẽ hỏi có xóa `token.txt` đã lưu không, sau đó hãy chạy lại và dán token mới. |
| Console báo `Used disallowed intents` | Trong Developer Portal → **Bot**, bật **Message Content Intent** rồi lưu lại. |
| `/inject` báo DISCONNECTED | Chạy `bot.py` trước, rồi mới chạy `bridge.lua`. Đảm bảo không có chương trình nào khác dùng cổng `8765` và firewall cho phép kết nối cục bộ. |
| "Missing Access" hoặc bot không trả lời | Cấp cho bot quyền xem và gửi tin nhắn trong `#debug`. |
| `WebSocket` là nil trong Roblox | Executor của bạn không hỗ trợ `WebSocket.connect`. Hãy thử executor khác. |
| Không nhận lệnh `python` | Cài lại Python và tích **Add Python to PATH**. |

## Đóng góp

Hoan nghênh issue và pull request. Vui lòng giữ thay đổi tập trung.

## Giấy phép

Chưa có giấy phép được chỉ định. Hãy thêm tệp `LICENSE` (ví dụ MIT) để người khác biết cách sử dụng mã nguồn.
