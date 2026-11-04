-- Persistent WebSocket Bridge Client (RobloxOnDiscord-Test)
local AUTH_TOKEN = "FFZ_SECURE_TOKEN_2026"

-- Close existing active WebSocket connection to prevent duplication
if _G.ActiveWebSocket then
    pcall(function() _G.ActiveWebSocket:Close() end)
    _G.ActiveWebSocket = nil
end

-- Notification helper function safely checking StarterGui
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
        -- Safe check for WebSocket support across different executors
        local wsConnect = (typeof(WebSocket) == "table" and WebSocket.connect) 
            or (typeof(syn) == "table" and syn.websocket and syn.websocket.connect)
            or (typeof(krnl) == "table" and krnl.websocket and krnl.websocket.connect)

        if wsConnect then
            local success, ws = pcall(function()
                return wsConnect("ws://localhost:8765")
            end)

            if success and ws then
                _G.ActiveWebSocket = ws
                
                -- Send handshake authorization token
                pcall(function() ws:Send("AUTH:" .. AUTH_TOKEN) end)
                
                print("[WEBSOCKET] Connected successfully to Bridge Server!")
                showNotification("Roblox Bridge", "🟢 WebSocket Connected Successfully!")
                
                -- Handle incoming execution commands from Discord
                ws.OnMessage:Connect(function(msg)
                    pcall(function()
                        local func, err = loadstring(msg)
                        if func then 
                            task.spawn(func)
                        else
                            warn("[BRIDGE EXEC ERROR]: " .. tostring(err))
                        end
                    end)
                end)
                
                -- Handle disconnection event
                ws.OnClose:Connect(function()
                    print("[WEBSOCKET] Disconnected from Bridge Server!")
                    showNotification("Roblox Bridge", "🔴 WebSocket Disconnected!")
                end)
            else
                print("[WEBSOCKET] Failed to establish connection to localhost:8765")
            end
        else
            print("[WEBSOCKET] Your Executor does not support WebSocket functions!")
            showNotification("Roblox Bridge", "⚠️ Unsupported Executor!")
        end
    end)
end)
