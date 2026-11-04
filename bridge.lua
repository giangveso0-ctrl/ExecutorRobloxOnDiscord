-- Persistent WebSocket Bridge Client (English Version)
local AUTH_TOKEN = "FFZ_SECURE_TOKEN_2026"

-- Close existing active connections to prevent duplication
if _G.ActiveWebSocket then
    pcall(function() _G.ActiveWebSocket:Close() end)
    _G.ActiveWebSocket = nil
end

-- Helper function to trigger StarterGui notification
local function showNotification(title, text)
    pcall(function()
        game:GetService("StarterGui"):SetCore("SendNotification", {
            Title = title,
            Text = text,
            Duration = 4
        })
    end)
end

task.spawn(function()
    pcall(function()
        local wsConnect = WebSocket and WebSocket.connect or syn and syn.websocket and syn.websocket.connect
        if wsConnect then
            local ws = wsConnect("ws://localhost:8765")
            if ws then
                _G.ActiveWebSocket = ws
                
                -- Send authentication token to Python Server
                ws:Send("AUTH:" .. AUTH_TOKEN)
                
                -- Log success message and trigger green notification
                print("<font color=\"#00FF00\">[WEBSOCKET] Connected successfully to Bridge Server!</font>")
                showNotification("https://discord.gg/nfCy6jWYX", "🟢 WebSocket Connected Successfully!")
                
                -- Handle incoming execution commands from Discord
                ws.OnMessage:Connect(function(msg)
                    pcall(function()
                        local func = loadstring(msg)
                        if func then func() end
                    end)
                end)
                
                -- Handle disconnection event
                ws.OnClose:Connect(function()
                    print("<font color=\"#FF0000\">[WEBSOCKET] Disconnected from Bridge Server!</font>")
                    showNotification("https://discord.gg/nfCy6jWYX", "🔴 WebSocket Disconnected!")
                end)
            end
        else
            print("<font color=\"#FF0000\">[WEBSOCKET] WebSocket extension not supported by your Executor!</font>")
        end
    end)
end)