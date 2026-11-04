# RobloxOnDiscord-Test

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

## Contributing

Issues and pull requests are welcome. This is a small test project, so please keep changes focused.

## License

No license has been specified yet. Add a `LICENSE` file (e.g. MIT) to let others know how they may use the code.
