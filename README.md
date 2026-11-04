================================================================================

⚡ ROBLEX ON DISCORD - ULTIMATE WEBSOCKET BRIDGE & REMOTE EXECUTION HUB

================================================================================

Repository: https://github.com/giangveso0-ctrl/RobloxOnDiscord-Test

Author / Maintainer: Mihai Ardelean

================================================================================



[ENGLISH VERSION]



1. SYSTEM ARCHITECTURE & OVERVIEW

--------------------------------------------------------------------------------

RobloxOnDiscord-Test is an enterprise-grade, real-time command bridge designed 

to link Discord servers directly to the Roblox game client (RobloxPlayerBeta.exe) 

via a secure local WebSocket server running on ws://localhost:8765.



Unlike traditional webhook or HTTP-poll architectures, this system maintains a 

persistent, full-duplex TCP socket connection, enabling zero-latency execution 

of Lua scripts, advanced character manipulation, real-time ESP rendering, and 

telemetry logging directly from a designated Discord #debug channel.



  +------------------+         WebSocket         +------------------+         Local Client         +------------------+

  |  Discord Server  |  =======================>  |   Python Bot     |  =========================>  | Roblox Client    |

  | (#debug channel) |    (Secure Payload)      | (ws://localhost) |    (Async Lua Execution)     | (Executor / Game)|

  +------------------+                          +------------------+                            +------------------+



2. DETAILED PROJECT FILE STRUCTURE

--------------------------------------------------------------------------------

- bot.py       : The core asynchronous event-driven Python daemon. Handles Discord 

                 Gateway events, slash command syncing (discord.app_commands), 

                 process monitoring via psutil, token-based handshake authorization, 

                 and the underlying websockets server loop.

- bridge.lua   : The client-side execution script injected into Roblox. Implements 

                 connection retry logic, persistent global state caching (_G.ActiveWebSocket), 

                 automated StarterGui notifications, and secure string compilation via loadstring().

- start.bat    : A robust Windows batch helper script designed to initialize the 

                 Python runtime environment and launch the bot daemon seamlessly.



3. STEP-BY-STEP INSTALLATION & ENVIRONMENT SETUP

--------------------------------------------------------------------------------

[Step 1] System Requirements & Python Installation

- Operating System: Windows 10 / 11 (Required for RobloxPlayerBeta.exe process scanning).

- Python: Version 3.8 or higher.

  * Download the official binary from https://www.python.org/downloads/

  * CRITICAL: Check the box "Add Python to PATH" during the setup wizard.



[Step 2] Installing Required Python Dependencies

Open your terminal (CMD, PowerShell, or Git Bash) and run:

  pip install discord.py websockets psutil



[Step 3] Choosing a Roblox Executor

To inject and execute the Lua bridge script inside Roblox, use an executor 

supporting native WebSocket client functions (WebSocket.connect):

- Solara : Free, reliable, and widely adopted for general script execution.

- Wave   : Advanced execution suite with robust environment support.

- Zeno   : Lightweight, ultra-fast connection overhead.



4. DEPLOYMENT & CONFIGURATION GUIDE

--------------------------------------------------------------------------------

1. Clone or download the repository files into your local directory.

2. Open bot.py in your text editor and insert your private Discord Bot Token:

     DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"

3. Launch the system by double-clicking start.bat (or running `python bot.py`).

4. Inside Roblox, execute the following auto-connect loadstring via your Executor:

     loadstring(game:HttpGet("https://raw.githubusercontent.com/giangveso0-ctrl/RobloxOnDiscord-Test/main/bridge.lua"))()



5. COMMAND REFERENCE MANUAL (RESTRICTED TO #DEBUG)

--------------------------------------------------------------------------------

- /inject : Scans system processes for RobloxPlayerBeta.exe, checks PID, and 

            evaluates live WebSocket state (CONNECTED in green / DISCONNECTED in red).

- /exec   : Transmits raw Lua string parameters or reads uploaded .lua / .txt 

            file attachments (up to 2MB) directly to the game client.

- /human  : Interacts directly with the local player's Humanoid instance to 

            modify physics, walk speeds, or jump heights dynamically.

- /fly    : Attaches a custom BodyVelocity and BodyGyro loop synced to the 

            workspace.CurrentCamera look vector for smooth 3D flight.

- /unfly  : Safely cleans up flight instances, restores PlatformStand to false, 

            and returns normal character physics.

- /speed  : Directly overwrites Humanoid.WalkSpeed values with safety validation.

- /esp    : Spawns dynamic Highlight instances on all players and completely 

            purges/destroys all instances from memory when toggled to false.

- /status : Broadcasts active client pool statistics and network diagnostic latency.



6. DEEP DIVE: USING THE /HUMAN API COMMAND

--------------------------------------------------------------------------------

The /human command provides granular control over the Humanoid object of your 

active Roblox character instance.



- Syntax Structure:

  /human property:<HumanoidProperty> value:<NumericalValue>



- Supported Properties & Practical Examples:

  * WalkSpeed : Adjust running velocity -> /human WalkSpeed 120

  * JumpPower : Modify vertical leaping capability -> /human JumpPower 200

  * HipHeight : Adjust body elevation offset -> /human HipHeight 4

  * Health    : Manage player vitality parameters -> /human Health 50





================================================================================

[PHIÊN BẢN TIẾNG VIỆT]



1. KIẾN TRÚC HỆ THỐNG & TỔNG QUAN

--------------------------------------------------------------------------------

RobloxOnDiscord-Test là hệ thống cầu nối lệnh thời gian thực cấp độ doanh nghiệp 

(enterprise-grade), liên kết máy chủ Discord trực tiếp với tiến trình game Roblox 

(RobloxPlayerBeta.exe) thông qua máy chủ WebSocket cục bộ ws://localhost:8765.



Hệ thống duy trì kết nối TCP song công toàn phần (full-duplex persistent connection), 

cho phép thực thi mã lệnh Lua với độ trễ bằng 0, tùy biến nhân vật nâng cao, render ESP 

trực tiếp và ghi log hệ thống ngay từ kênh #debug trên Discord.



2. CHI TIẾT CẤU TRÚC THƯ MỤC DỰ ÁN

--------------------------------------------------------------------------------

- bot.py       : Daemon Python bất đồng bộ quản lý Discord Gateway, đồng bộ slash 

                 commands (discord.app_commands), quét tiến trình psutil, xác thực 

                 handshake token và websocket server loop.

- bridge.lua   : Script Lua phía client chạy trong Roblox, quản lý cơ chế tự động 

                 kết nối lại, lưu trữ _G.ActiveWebSocket, thông báo StarterGui và 

                 biên dịch loadstring().

- start.bat    : File batch tiện ích trên Windows khởi động môi trường Python nhanh chóng.



3. HƯỚNG DẪN CÀI ĐẶT & THIẾT LẬP MÔI TRƯỜNG

--------------------------------------------------------------------------------

[Bước 1] Yêu cầu Hệ thống & Cài đặt Python

- Hệ điều hành: Windows 10 / 11 (Bắt buộc để quét PID tiến trình game).

- Python: Phiên bản 3.8 trở lên.

  * Tải tại https://www.python.org/downloads/

  * LƯU Ý: Tích chọn "Add Python to PATH" trong trình cài đặt.



[Bước 2] Cài đặt Thư viện Python Phụ thuộc

Mở Command Prompt hoặc PowerShell và chạy lệnh:

  pip install discord.py websockets psutil



[Bước 3] Giới thiệu Trình thực thi (Roblox Executor)

Sử dụng các executor hỗ trợ WebSocket (WebSocket.connect):

- Solara : Miễn phí, ổn định và được cộng đồng sử dụng rộng rãi.

- Wave   : Môi trường thực thi mạnh mẽ với nhiều tính năng nâng cao.

- Zeno   : Giao diện nhẹ, tốc độ phản hồi kết nối cực nhanh.



4. HƯỚNG DẪN VẬN HÀNH & CẤU HÌNH

--------------------------------------------------------------------------------

1. Tải kho lưu trữ về máy tính.

2. Mở bot.py và điền Token Bot Discord của bạn vào biến:

     DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"

3. Nhấp đúp vào start.bat để chạy bot.

4. Trong Roblox, chạy đoạn loadstring kết nối tự động qua Executor:

     loadstring(game:HttpGet("https://raw.githubusercontent.com/giangveso0-ctrl/RobloxOnDiscord-Test/main/bridge.lua"))()



5. BẢNG TRA CỨU LỆNH (CHỈ DÙNG TẠI KÊNH #DEBUG)

--------------------------------------------------------------------------------

- /inject : Kiểm tra tiến trình RobloxPlayerBeta.exe và WebSocket (Xanh/Đỏ).

- /exec   : Gửi chuỗi Lua trực tiếp hoặc tải file .lua / .txt (tối đa 2MB).

- /human  : Tương tác trực tiếp với đối tượng Humanoid của nhân vật.

- /fly    : Bật vòng lặp BodyVelocity và BodyGyro bám theo hướng nhìn camera.

- /unfly  : Dọn dẹp instance bay, khôi phục vật lý nhân vật bình thường.

- /speed  : Ghi đè trực tiếp giá trị Humanoid.WalkSpeed kèm kiểm tra an toàn.

- /esp    : Tạo Highlight trên người chơi và xóa sạch 100% khi tắt (false).

- /status : Hiển thị thống kê client kết nối và độ trễ mạng.



6. HƯỚNG DẪN CHUYÊN SÂU: SỬ DỤNG LỆNH API /HUMAN

--------------------------------------------------------------------------------

Lệnh /human cung cấp khả năng điều khiển chi tiết thuộc tính lớp Humanoid.



- Cú pháp chuẩn:

  /human property:<Tên_Thuộc_Tính> value:<Giá_Trị_Số>



- Các thuộc tính hỗ trợ & Ví dụ thực tế:

  * WalkSpeed : Thay đổi tốc độ di chuyển -> /human WalkSpeed 120

  * JumpPower : Tăng sức nhảy dọc -> /human JumpPower 200

  * HipHeight : Chỉnh độ cao khoảng cách hông so với mặt đất -> /human HipHeight 4

  * Health    : Quản lý chỉ số máu nhân vật -> /human Health 50



================================================================================
