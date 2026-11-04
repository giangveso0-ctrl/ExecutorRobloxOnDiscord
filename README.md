================================================================================

⚡ ROBLEX ON DISCORD - ULTIMATE WEBSOCKET BRIDGE & REMOTE EXECUTION HUB

================================================================================

Repository: https://github.com/giangveso0-ctrl/RobloxOnDiscord-Test

Author & Maintainer: Mihai Ardelean

License: MIT Open Source / Educational & Research Use Only

================================================================================



[ENGLISH VERSION]



1. ARCHITECTURAL OVERVIEW & TELEMETRY

--------------------------------------------------------------------------------

RobloxOnDiscord-Test establishes a high-performance, enterprise-grade command bridge 

between your Discord server and the local Roblox game client (RobloxPlayerBeta.exe). 

By leveraging an asynchronous Python WebSocket daemon running on `ws://localhost:8765`, 

this architecture bypasses conventional HTTP polling limitations, delivering zero-latency 

command dispatch and real-time execution telemetry.



  +------------------+         Secure WebSocket         +------------------+         Async Execution         +------------------+

  |  Discord Server  |  ============================>   |   Python Daemon  |  ============================>  | Roblox Client    |

  | (#debug channel) |    (Signed JSON / Payload)       | (ws://localhost) |    (Dynamic loadstring Eval)    | (Executor/Game)  |

  +------------------+                                  +------------------+                                 +------------------+



2. REPOSITORY FILE MANIFEST & SPECIFICATIONS

--------------------------------------------------------------------------------

- bot.py       : The core asynchronous Python application. Manages Discord Gateway 

                 events, slash command synchronization (`discord.app_commands`), 

                 `psutil` process auditing, token-based handshake verification, 

                 and robust exception handling.

- bridge.lua   : The client-side injection script. Implements automatic reconnection 

                 routines, global state preservation (`_G.ActiveWebSocket`), 

                 `StarterGui` visual feedback, and secure Lua payload compilation.

- start.bat    : A production-ready Windows batch utility designed to initialize the 

                 Python runtime environment and launch the bot server instantly.



3. ENVIRONMENT PREREQUISITES & DEPENDENCY SETUP

--------------------------------------------------------------------------------

[Phase 1] Python Runtime Environment

- Operating System: Windows 10 / 11 (Mandatory for `RobloxPlayerBeta.exe` API hooks).

- Python Version: **Python 3.8.x up to 3.12.x**.

  * Download the official binary installer from https://www.python.org/downloads/

  * IMPORTANT: Check the box **"Add Python to PATH"** during installation.



[Phase 2] Installing Core Python Libraries

Open your terminal (Command Prompt, PowerShell, or Git Bash) and install the 

required asynchronous networking and utility packages:

  pip install discord.py websockets psutil



[Phase 3] Selecting a Compatible Roblox Executor

To inject and execute the Lua bridge script inside Roblox, ensure you use an 

executor that natively supports WebSocket client socket connections (`WebSocket.connect`):

- Solara : Reliable, widely adopted free execution environment.

- Wave   : High-performance execution suite with extensive environment support.

- Zeno   : Lightweight architecture with ultra-low connection overhead.



4. DEPLOYMENT & CONFIGURATION WORKFLOW

--------------------------------------------------------------------------------

1. Clone or download this repository onto your local Windows workstation.

2. Open `bot.py` using any code editor (VS Code, Notepad++, etc.) and paste your 

   private Discord Bot Token into the configuration section:

     DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"

3. Double-click **`start.bat`** to start the Python bot daemon and open port `8765`.

4. Inside Roblox, inject and run the following auto-connect loadstring via your Executor:

     loadstring(game:HttpGet("https://raw.githubusercontent.com/giangveso0-ctrl/RobloxOnDiscord-Test/main/bridge.lua"))()



5. DISCORD COMMAND REFERENCE MANUAL (STRICTLY CONFINED TO `#debug`)

--------------------------------------------------------------------------------

- /inject : Scans active system tasks for `RobloxPlayerBeta.exe`, retrieves process 

            IDs, and tests live WebSocket socket health (🟢 Connected / 🔴 Disconnected).

- /exec   : Transmits raw Lua string parameters or parses uploaded `.lua` / `.txt` 

            file attachments (up to 2MB) directly to the game environment.

- /human  : Interacts with the local player's `Humanoid` instance to modify physics, 

            locomotion velocity, and spatial attributes dynamically.

- /fly    : Binds a custom `BodyVelocity` and `BodyGyro` physics loop mapped to the 

            `workspace.CurrentCamera` look vector for fluid 3D flight control.

- /unfly  : Safely unloads physics flight instances, resets `PlatformStand` to false, 

            and restores native character movement.

- /speed  : Instantly updates `Humanoid.WalkSpeed` properties with safety validation.

- /esp    : Spawns real-time `Highlight` instances across all players and completely 

            purges/destroys all instances from memory when toggled to `false`.

- /status : Broadcasts active client pool metrics and network socket diagnostics.



6. ADVANCED TECHNICAL DEEP DIVE: THE `/HUMAN` API

--------------------------------------------------------------------------------

The `/human` command provides deep, programmatic manipulation over the active 

`Humanoid` object of your local Roblox character.



- Command Syntax Structure:

  `/human property:<HumanoidProperty> value:<NumericalValue>`



- Supported Properties, Technical Bounds & Execution Examples:

  * WalkSpeed : Modifies movement velocity -> `/human WalkSpeed 125`

  * JumpPower : Modifies vertical leaping force -> `/human JumpPower 250`

  * HipHeight : Adjusts vertical offset from terrain -> `/human HipHeight 6`

  * Health    : Updates character vitality points -> `/human Health 100`





================================================================================

[PHIÊN BẢN TIẾNG VIỆT]



1. TỔNG QUAN KIẾN TRÚC & CƠ CHẾ HOẠT ĐỘNG

--------------------------------------------------------------------------------

RobloxOnDiscord-Test thiết lập một cầu nối lệnh thời gian thực hiệu suất cao, 

liên kết máy chủ Discord trực tiếp với tiến trình game Roblox trên máy tính 

(RobloxPlayerBeta.exe) thông qua máy chủ WebSocket nội bộ (`ws://localhost:8765`).



Hệ thống duy trì kết nối TCP song công toàn phần (persistent full-duplex socket), 

giúp truyền tải mã lệnh Lua với độ trễ tối thiểu, điều khiển nhân vật nâng cao, 

render ESP trực tiếp và ghi log hệ thống ngay từ kênh `#debug` trên Discord.



2. DANH MỤC CẤU TRÚC THƯ MỤC DỰ ÁN

--------------------------------------------------------------------------------

- bot.py       : Tệp lệnh Python bất đồng bộ chính. Quản lý sự kiện Discord Gateway, 

                 đồng bộ Slash Commands (`discord.app_commands`), kiểm soát tiến trình 

                 `psutil`, xác thực token và vận hành vòng lặp WebSocket.

- bridge.lua   : Script Lua phía client chạy trong Roblox. Xử lý cơ chế kết nối lại 

                 tự động, lưu trữ trạng thái toàn cục (`_G.ActiveWebSocket`), thông 

                 báo giao diện `StarterGui` và biên dịch payload an toàn qua `loadstring()`.

- start.bat    : File batch tiện ích trên Windows giúp khởi động môi trường Python 

                 và kích hoạt Bot Server ngay lập tức chỉ với một cú nhấp chuột.



3. YÊU CẦU HỆ THỐNG & HƯỚNG DẪN CÀI ĐẶT

--------------------------------------------------------------------------------

[Phần 1] Cài đặt Môi trường Python

- Hệ điều hành: Windows 10 / 11 (Bắt buộc để quét tiến trình `RobloxPlayerBeta.exe`).

- Phiên bản Python: **Python 3.8 đến 3.12**.

  * Tải gói cài đặt chính thức tại https://www.python.org/downloads/

  * LƯU Ý QUAN TRỌNG: Tích chọn ô **"Add Python to PATH"** trong quá trình cài đặt.



[Phần 2] Cài đặt Thư viện Python Phụ thuộc

Mở Command Prompt, PowerShell hoặc Git Bash và chạy lệnh sau để cài đặt các gói:

  pip install discord.py websockets psutil



[Phần 3] Lựa chọn Trình thực thi (Roblox Executor)

Để nạp script bridge vào trong game, cần sử dụng các executor hỗ trợ hàm WebSocket 

cục bộ (`WebSocket.connect`):

- Solara : Trình thực thi miễn phí ổn định, được sử dụng phổ biến.

- Wave   : Môi trường thực thi cao cấp với nhiều tính năng nâng cao.

- Zeno   : Giao diện tối ưu, tốc độ phản hồi kết nối cực nhanh.



4. QUY TRÌNH TRIỂN KHAI & CẤU HÌNH HỆ THỐNG

--------------------------------------------------------------------------------

1. Tải hoặc clone kho lưu trữ này về máy tính cá nhân.

2. Mở file `bot.py` bằng trình soạn thảo mã nguồn và dán Token Bot Discord của bạn:

     DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"

3. Nhấp đúp vào file **`start.bat`** để khởi chạy Bot Server tại cổng `8765`.

4. Trong game Roblox, chạy đoạn loadstring tự động kết nối qua Executor:

     loadstring(game:HttpGet("https://raw.githubusercontent.com/giangveso0-ctrl/RobloxOnDiscord-Test/main/bridge.lua"))()



5. BẢNG TRA CỨU LỆNH DISCORD (CHỈ HOẠT ĐỘNG TẠI KÊNH `#debug`)

--------------------------------------------------------------------------------

- /inject : Quét tiến trình `RobloxPlayerBeta.exe`, kiểm tra PID và trạng thái kết 

            nối WebSocket thực tế (🟢 Đã kết nối / 🔴 Mất kết nối).

- /exec   : Gửi chuỗi mã Lua trực tiếp hoặc tải file đính kèm `.lua` / `.txt` 

            (tối đa 2MB) để thực thi trong game.

- /human  : Tương tác trực tiếp với đối tượng `Humanoid` của nhân vật để thay đổi 

            thông số vật lý, tốc độ chạy hoặc sức nhảy theo thời gian thực.

- /fly    : Kích hoạt vòng lặp vật lý `BodyVelocity` và `BodyGyro` bám theo góc nhìn 

            camera (`workspace.CurrentCamera`) giúp bay mượt mà 3 chiều.

- /unfly  : Dọn dẹp an toàn các instance bay, khôi phục `PlatformStand` và đưa nhân 

            vật về trạng thái vật lý mặc định.

- /speed  : Ghi đè trực tiếp thuộc tính `Humanoid.WalkSpeed` kèm kiểm tra giới hạn.

- /esp    : Tạo các khối `Highlight` trên toàn bộ người chơi và **xóa sạch 100%** 

            khỏi bộ nhớ khi chuyển trạng thái sang `false`.

- /status : Hiển thị số lượng client WebSocket đang kết nối và thông số độ trễ mạng.



6. HƯỚNG DẪN CHUYÊN SÂU: SỬ DỤNG LỆNH API `/HUMAN`

--------------------------------------------------------------------------------

Lệnh `/human` cung cấp khả năng điều khiển chi tiết thuộc tính của lớp `Humanoid` 

trên nhân vật Roblox của bạn.



- Cú pháp lệnh chuẩn:

  `/human property:<Tên_Thuộc_Tính> value:<Giá_Trị_Số>`



- Các thuộc tính hỗ trợ & Ví dụ thực tế:

  * WalkSpeed : Điều chỉnh tốc độ di chuyển -> `/human WalkSpeed 125`

  * JumpPower : Điều chỉnh sức bật nhảy dọc -> `/human JumpPower 250`

  * HipHeight : Chỉnh độ cao khoảng cách hông so với mặt đất -> `/human HipHeight 6`

  * Health    : Quản lý chỉ số điểm máu nhân vật -> `/human Health 100`



================================================================================
