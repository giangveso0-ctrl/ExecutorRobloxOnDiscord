-- Persistent WebSocket Bridge Client (RobloxOnDiscord-Test)
local AUTH_TOKEN = "FFZ_SECURE_TOKEN_2026"

if _G.ActiveWebSocket then
    pcall(function() _G.ActiveWebSocket:Close() end)
    _G.ActiveWebSocket = nil
end

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
        local wsConnect = (typeof(WebSocket) == "table" and WebSocket.connect) 
            or (typeof(syn) == "table" and syn.websocket and syn.websocket.connect)
            or (typeof(krnl) == "table" and krnl.websocket and krnl.websocket.connect)

        if wsConnect then
            local success, ws = pcall(function()
                return wsConnect("ws://localhost:8765")
            end)

            if success and ws then
                _G.ActiveWebSocket = ws
                pcall(function() ws:Send("AUTH:" .. AUTH_TOKEN) end)
                
                print("[WEBSOCKET] Connected successfully to Bridge Server!")
                showNotification("Roblox Bridge", "🟢 WebSocket Connected Successfully!")
                
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
                
                ws.OnClose:Connect(function()
                    print("[WEBSOCKET] Disconnected from Bridge Server!")
                    showNotification("Roblox Bridge", "🔴 WebSocket Disconnected!")
                end)
            end
        else
            print("[WEBSOCKET] Your Executor does not support WebSocket functions!")
            showNotification("Roblox Bridge", "⚠️ Unsupported Executor!")
        end
    end)
end)
