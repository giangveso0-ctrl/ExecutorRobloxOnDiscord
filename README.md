# RobloxOnDiscord-Test

**English** | [Tiếng Việt](#tiếng-việt)

Control a Roblox client from Discord. A Python bot receives slash commands in a Discord channel and forwards Lua to the game through a local WebSocket connection.

> **Disclaimer:** This is a test/educational project. Running scripts through third-party executors can violate the [Roblox Terms of Use](https://en.help.roblox.com/hc/en-us/articles/115004647846) and may get your account banned. Use it only on your own account, in your own experiences or private test places, and at your own risk. Never use it to disrupt other players.

---

## How it works

```
Discord (#debug)  ──slash command──▶  bot.py  ◀──WebSocket (ws://localhost:8765)──▶  bridge.lua (in Roblox)
```

1. `bot.py` connects to Discord and starts a WebSocket server on `ws://localhost:8765`.
2. `bridge.lua`, run inside Roblox through an executor, connects back to that server and keeps the connection alive (with automatic retry).
3. When you use a slash command, the bot sends a Lua payload over the socket and the bridge executes it in the game.

## Project structure

| File | Description |
| --- | --- |
| `bot.py` | Async Python bot: Discord gateway, slash command sync, `psutil` process check, and the WebSocket server. |
| `bridge.lua` | Client-side script: connects to the bot, caches the socket in `_G.ActiveWebSocket`, shows `StarterGui` notifications, runs received code via `loadstring()`. |
| `start.bat` | Windows helper that launches the bot. |

## Requirements

- Windows 10 / 11 (the bot looks for the `RobloxPlayerBeta.exe` process)
- Python 3.8+ (tick **Add Python to PATH** when installing)
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))
- A Roblox executor that supports `WebSocket.connect` (e.g. Solara, Wave, Zeno)

## Installation

```bash
git clone https://github.com/giangveso0-ctrl/RobloxOnDiscord-Test.git
cd RobloxOnDiscord-Test
pip install discord.py websockets psutil
```

## Creating a Discord bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and log in.
2. Click **New Application**, name it, and accept the terms.
3. Open the **Bot** tab on the left.
4. Click **Reset Token** (or **Copy** if shown) and save the token somewhere safe. You will paste it into `bot.py`. Discord only shows it once.
5. Still on the **Bot** tab, scroll to **Privileged Gateway Intents**. Slash commands don't need any, so leave them off unless you later change `bot.py` to read message content.
6. Open **OAuth2 → URL Generator**:
   - Under **Scopes**, tick `bot` and `applications.commands`.
   - Under **Bot Permissions**, tick `View Channels`, `Send Messages`, `Embed Links` and `Attach Files`.
7. Copy the generated URL at the bottom, open it in your browser, pick your server and click **Authorize**.
8. In your server, create a text channel named `#debug`. Commands only work there.
9. Optional: in Discord go to **Settings → Advanced** and turn on **Developer Mode**, so you can right-click the server or channel and copy its ID if you need it.

Once the bot is invited, continue with the configuration below.

## Configuration

Open `bot.py` and set your bot token:

```python
DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"
```

> **Keep your token private.** Never commit a real token to GitHub. If you leak one, reset it immediately in the Developer Portal. Consider loading it from an environment variable instead of hardcoding it.

Also make sure the bot is invited to your server with the `applications.commands` and `bot` scopes, and that you have a channel named `#debug` (commands are restricted to it).

## Usage

1. Start the bot by double-clicking `start.bat` or running:

   ```bash
   python bot.py
   ```

2. Open Roblox and run the bridge through your executor:

   ```lua
   loadstring(game:HttpGet("https://raw.githubusercontent.com/giangveso0-ctrl/RobloxOnDiscord-Test/main/bridge.lua"))()
   ```

   > Only run scripts you have read and trust. Loading code from a URL executes whatever is at that URL, so review `bridge.lua` first (or paste its contents directly).

3. In Discord's `#debug` channel, run `/inject` to confirm the connection shows **CONNECTED**.

## Commands

All commands are restricted to the `#debug` channel.

| Command | Description |
| --- | --- |
| `/inject` | Checks for `RobloxPlayerBeta.exe` and reports the WebSocket state (connected / disconnected). |
| `/exec` | Sends a Lua string, or an uploaded `.lua` / `.txt` file (max 2 MB), to the game client. |
| `/human` | Sets a property on your character's Humanoid (see below). |
| `/fly` | Enables flight using `BodyVelocity` / `BodyGyro` following the camera direction. |
| `/unfly` | Stops flight and restores normal character physics. |
| `/speed` | Sets `Humanoid.WalkSpeed` (with validation). |
| `/esp` | Toggles `Highlight` outlines on players; turning it off removes them all. |
| `/status` | Shows connected clients and connection diagnostics. |

### `/human` properties

```
/human property:<name> value:<number>
```

| Property | Example |
| --- | --- |
| `WalkSpeed` | `/human WalkSpeed 120` |
| `JumpPower` | `/human JumpPower 200` |
| `HipHeight` | `/human HipHeight 4` |
| `Health` | `/human Health 50` |

## Troubleshooting

- **`/inject` shows DISCONNECTED:** make sure `bot.py` is running first, then execute `bridge.lua`. Check that nothing else is using port `8765` and that your firewall allows local connections.
- **Slash commands don't appear:** confirm the bot was invited with the `applications.commands` scope and give Discord a minute to sync.
- **`WebSocket` is nil in Roblox:** your executor doesn't support `WebSocket.connect`; try a different one.
- **Python not recognized:** reinstall Python with **Add Python to PATH** checked.

## Releases & Packages

- [Releases](https://github.com/giangveso0-ctrl/RobloxOnDiscord-Test/releases): tagged versions of the project (none published yet).
- [Packages](https://github.com/users/giangveso0-ctrl/packages?repo_name=RobloxOnDiscord-Test): packages published from this repository (none published yet).

## Contributing

Issues and pull requests are welcome. This is a small test project, so please keep changes focused.

## License

No license has been specified yet. Add a `LICENSE` file (e.g. MIT) to let others know how they may use the code.

---

<a name="tiếng-việt"></a>

# Tiếng Việt

[English](#robloxondiscord-test) | **Tiếng Việt**

Điều khiển client Roblox từ Discord. Một bot Python nhận slash command trong kênh Discord và chuyển mã Lua vào game thông qua kết nối WebSocket cục bộ.

> **Lưu ý:** Đây là dự án thử nghiệm/học tập. Việc chạy script qua executor bên thứ ba có thể vi phạm [Điều khoản sử dụng của Roblox](https://en.help.roblox.com/hc/en-us/articles/115004647846) và có thể khiến tài khoản bị khóa. Chỉ sử dụng trên tài khoản của bạn, trong game của chính bạn hoặc place thử nghiệm riêng tư, và tự chịu rủi ro. Không dùng để gây ảnh hưởng đến người chơi khác.

---

## Cách hoạt động

```
Discord (#debug)  ──slash command──▶  bot.py  ◀──WebSocket (ws://localhost:8765)──▶  bridge.lua (trong Roblox)
```

1. `bot.py` kết nối với Discord và mở một máy chủ WebSocket tại `ws://localhost:8765`.
2. `bridge.lua` chạy trong Roblox thông qua executor, kết nối ngược lại máy chủ đó và giữ kết nối (có tự động thử lại).
3. Khi bạn dùng slash command, bot gửi mã Lua qua socket và bridge sẽ thực thi trong game.

## Cấu trúc dự án

| Tệp | Mô tả |
| --- | --- |
| `bot.py` | Bot Python bất đồng bộ: Discord gateway, đồng bộ slash command, kiểm tra tiến trình bằng `psutil` và máy chủ WebSocket. |
| `bridge.lua` | Script phía client: kết nối tới bot, lưu socket trong `_G.ActiveWebSocket`, hiện thông báo `StarterGui`, chạy mã nhận được bằng `loadstring()`. |
| `start.bat` | File batch trên Windows để khởi động bot nhanh. |

## Yêu cầu

- Windows 10 / 11 (bot tìm tiến trình `RobloxPlayerBeta.exe`)
- Python 3.8 trở lên (nhớ tích **Add Python to PATH** khi cài đặt)
- Token bot Discord ([Discord Developer Portal](https://discord.com/developers/applications))
- Executor Roblox hỗ trợ `WebSocket.connect` (ví dụ: Solara, Wave, Zeno)

## Cài đặt

```bash
git clone https://github.com/giangveso0-ctrl/RobloxOnDiscord-Test.git
cd RobloxOnDiscord-Test
pip install discord.py websockets psutil
```

## Cách tạo bot Discord

1. Vào [Discord Developer Portal](https://discord.com/developers/applications) và đăng nhập.
2. Nhấn **New Application**, đặt tên và đồng ý điều khoản.
3. Mở tab **Bot** ở menu bên trái.
4. Nhấn **Reset Token** (hoặc **Copy** nếu có) và lưu token ở nơi an toàn. Bạn sẽ dán token này vào `bot.py`. Discord chỉ hiển thị token một lần.
5. Vẫn ở tab **Bot**, kéo xuống mục **Privileged Gateway Intents**. Slash command không cần intent nào, nên hãy để tắt trừ khi sau này bạn sửa `bot.py` để đọc nội dung tin nhắn.
6. Mở **OAuth2 → URL Generator**:
   - Ở mục **Scopes**, tích `bot` và `applications.commands`.
   - Ở mục **Bot Permissions**, tích `View Channels`, `Send Messages`, `Embed Links` và `Attach Files`.
7. Sao chép URL được tạo ở cuối trang, mở bằng trình duyệt, chọn server của bạn rồi nhấn **Authorize**.
8. Trong server, tạo một kênh văn bản tên `#debug`. Các lệnh chỉ dùng được ở kênh này.
9. Tùy chọn: vào **Settings → Advanced** trong Discord và bật **Developer Mode** để có thể nhấp chuột phải vào server hoặc kênh và sao chép ID khi cần.

Sau khi mời bot vào server, tiếp tục với phần cấu hình bên dưới.

## Cấu hình

Mở `bot.py` và điền token bot của bạn:

```python
DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"
```

> **Giữ bí mật token.** Tuyệt đối không commit token thật lên GitHub. Nếu lỡ lộ, hãy reset ngay trong Developer Portal. Nên đọc token từ biến môi trường thay vì ghi cứng trong code.

Đồng thời hãy mời bot vào server với scope `applications.commands` và `bot`, và tạo kênh tên `#debug` (các lệnh chỉ dùng được ở kênh này).

## Sử dụng

1. Khởi động bot bằng cách nhấp đúp `start.bat` hoặc chạy:

   ```bash
   python bot.py
   ```

2. Mở Roblox và chạy bridge qua executor:

   ```lua
   loadstring(game:HttpGet("https://raw.githubusercontent.com/giangveso0-ctrl/RobloxOnDiscord-Test/main/bridge.lua"))()
   ```

   > Chỉ chạy script mà bạn đã đọc và tin tưởng. Việc tải mã từ URL sẽ thực thi bất cứ thứ gì có tại URL đó, nên hãy xem `bridge.lua` trước (hoặc dán trực tiếp nội dung vào executor).

3. Trong kênh `#debug` trên Discord, chạy `/inject` để xác nhận trạng thái **CONNECTED**.

## Danh sách lệnh

Tất cả lệnh chỉ dùng được trong kênh `#debug`.

| Lệnh | Mô tả |
| --- | --- |
| `/inject` | Kiểm tra tiến trình `RobloxPlayerBeta.exe` và trạng thái WebSocket (kết nối / ngắt kết nối). |
| `/exec` | Gửi chuỗi Lua, hoặc tệp `.lua` / `.txt` tải lên (tối đa 2 MB), tới game client. |
| `/human` | Đặt thuộc tính Humanoid của nhân vật (xem bên dưới). |
| `/fly` | Bật chế độ bay bằng `BodyVelocity` / `BodyGyro` theo hướng camera. |
| `/unfly` | Tắt bay và khôi phục vật lý nhân vật bình thường. |
| `/speed` | Đặt `Humanoid.WalkSpeed` (có kiểm tra giá trị). |
| `/esp` | Bật/tắt viền `Highlight` trên người chơi; khi tắt sẽ xóa toàn bộ. |
| `/status` | Hiển thị số client đang kết nối và thông tin chẩn đoán kết nối. |

### Thuộc tính của `/human`

```
/human property:<tên> value:<số>
```

| Thuộc tính | Ví dụ |
| --- | --- |
| `WalkSpeed` | `/human WalkSpeed 120` |
| `JumpPower` | `/human JumpPower 200` |
| `HipHeight` | `/human HipHeight 4` |
| `Health` | `/human Health 50` |

## Khắc phục sự cố

- **`/inject` báo DISCONNECTED:** hãy chạy `bot.py` trước, sau đó mới chạy `bridge.lua`. Kiểm tra xem có chương trình nào khác đang dùng cổng `8765` và firewall có cho phép kết nối cục bộ không.
- **Không thấy slash command:** kiểm tra bot đã được mời với scope `applications.commands` và đợi Discord đồng bộ khoảng một phút.
- **`WebSocket` là nil trong Roblox:** executor của bạn không hỗ trợ `WebSocket.connect`; hãy thử executor khác.
- **Không nhận lệnh Python:** cài lại Python và tích chọn **Add Python to PATH**.

## Bản phát hành & Gói (Releases & Packages)

- [Releases](https://github.com/giangveso0-ctrl/RobloxOnDiscord-Test/releases): các phiên bản đã gắn tag của dự án (chưa có bản nào được phát hành).
- [Packages](https://github.com/users/giangveso0-ctrl/packages?repo_name=RobloxOnDiscord-Test): các gói được phát hành từ kho lưu trữ này (chưa có gói nào).

## Đóng góp

Hoan nghênh issue và pull request. Đây là dự án thử nghiệm nhỏ nên vui lòng giữ thay đổi tập trung.

## Giấy phép

Chưa có giấy phép được chỉ định. Hãy thêm tệp `LICENSE` (ví dụ MIT) để người khác biết cách sử dụng mã nguồn.
