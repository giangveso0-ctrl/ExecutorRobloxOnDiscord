# RobloxOnDiscord-Test 🚀

[English](#english-version) | [Tiếng Việt](#vietnamese-version)

---

<a name="english-version"></a>
## 🌍 English Version

### 📖 Introduction
**RobloxOnDiscord-Test** is an advanced and robust bridge system designed to connect your Discord server directly to your Roblox game client via a local WebSocket server (`localhost:8765`). This tool allows you to remotely execute Lua scripts, manage player properties, and control game modifications securely and seamlessly using both traditional text prefixes (`!` or `.`) and modern Discord Slash Commands (`/`).

### 📁 Project Structure
* **`bot.py`**: The core Python script that acts as the Discord bot, manages command parsing, monitors the system process (`RobloxPlayerBeta.exe`), and hosts the background WebSocket server.
* **`bridge.lua`**: The client-side Lua script that runs inside Roblox to handle the WebSocket handshake, maintain persistent connection, and execute payloads safely.
* **`start.bat`**: A convenient Windows batch script to launch your Python bot environment instantly with a single double-click.

---

### 🛠️ Prerequisites & Installation Guide
Before running the bot, ensure you have the required software installed on your Windows system:

1. **Download & Install Python:**
   * Download the official installer from the [Python Official Website](https://www.python.org/downloads/).
   * *Important:* During installation, make sure to check the box that says **"Add Python to PATH"**.
2. **Install Required Python Libraries (`pip`):**
   Open your Command Prompt (CMD) or PowerShell and run the following command to install the necessary dependencies (`discord.py`, `websockets`, `psutil`):
   ```bash
   pip install discord.py websockets psutil
