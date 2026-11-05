"""
ui.py - interactive Discord UI for the bridge bot.

Adds a `/panel` command: one message with buttons that stays usable
(persistent view), so you don't have to type a slash command for every action.

    [ 🔄 Refresh ] [ ⚡ Run Lua ] [ 📋 Loadstring ] [ 📖 Help ] [ 🔗 Repo ]

It only re-uses things bot.py already has (status embed, /exec logic, help
embed, channel + user guards). Nothing here adds new in-game features.

Hook it up with 3 lines in bot.py - see README ("Discord panel").
"""
from __future__ import annotations

import discord


class ExecModal(discord.ui.Modal, title="⚡ Run Lua"):
    code = discord.ui.TextInput(
        label="Lua code",
        style=discord.TextStyle.paragraph,
        placeholder='print("hello from Discord")',
        max_length=4000,
        required=True,
    )

    def __init__(self, h) -> None:
        super().__init__()
        self.h = h

    async def on_submit(self, interaction: discord.Interaction) -> None:
        code = self.h.strip_code_fence(str(self.code.value))
        if not code:
            await interaction.response.send_message(
                embed=self.h.make_embed("⚠️ Thiếu mã / Missing code",
                                        "Vui lòng nhập mã Lua!\nPlease enter Lua code!",
                                        self.h.Colour.WARNING),
                ephemeral=True,
            )
            return
        embed, _ = await self.h.execute_script(code, interaction.user, "🧩 Panel (modal)")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        embed = self.h.error_embed(error)
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def panel_embed(h, interaction: discord.Interaction) -> discord.Embed:
    """Status embed restyled as a dashboard: coloured by state, with a quick-guide footer."""
    embed = await h.build_status_embed()
    state = embed.title or ""
    embed.set_author(name="Roblox Bridge · Control Panel",
                     icon_url=interaction.client.user.display_avatar.url)
    embed.title = state
    embed.set_thumbnail(url=interaction.client.user.display_avatar.url)
    embed.add_field(
        name="⌨️ Phím tắt / Quick guide",
        value="⚡ **Run Lua** · chạy mã / execute code\n"
              "📋 **Loadstring** · lấy mã kết nối / get the connect snippet\n"
              "🔄 **Refresh** · cập nhật trạng thái / update status",
        inline=False,
    )
    embed.set_footer(text="Chỉ trong #debug · #debug only  •  RobloxOnDiscord Bridge")
    return embed


class PanelView(discord.ui.View):
    """Persistent control panel (timeout=None + fixed custom_id on every button)."""

    def __init__(self, h) -> None:
        super().__init__(timeout=None)
        self.h = h
        self.add_item(discord.ui.Button(
            label="Repo", emoji="🔗", style=discord.ButtonStyle.link, url=h.REPO_URL, row=1))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        h = self.h
        if not h.in_debug_channel(interaction.channel):
            await interaction.response.send_message(embed=h.wrong_channel_embed(), ephemeral=True)
            return False
        if not h.is_allowed_user(interaction.user):
            await interaction.response.send_message(embed=h.denied_embed(), ephemeral=True)
            return False
        return True

    async def on_error(self, interaction: discord.Interaction, error: Exception,
                       item: discord.ui.Item) -> None:
        embed = self.h.error_embed(error)
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.secondary,
                       custom_id="rod:refresh", row=1)
    async def refresh(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        embed = await panel_embed(self.h, interaction)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Run Lua", emoji="⚡", style=discord.ButtonStyle.success,
                       custom_id="rod:exec", row=0)
    async def run_lua(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.send_modal(ExecModal(self.h))

    @discord.ui.button(label="Loadstring", emoji="📋", style=discord.ButtonStyle.primary,
                       custom_id="rod:loadstring")
    async def loadstring(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        h = self.h
        embed = h.make_embed(
            "📋 Chạy trong Executor / Run in your executor",
            h.code_block(h.loadstring_snippet()),
            h.Colour.INFO,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Help", emoji="📖", style=discord.ButtonStyle.secondary,
                       custom_id="rod:help", row=1)
    async def help(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.send_message(embed=self.h.build_help_embed(), ephemeral=True)


def install(bot, h) -> None:
    """Register /panel and the persistent view. `h` carries bot.py's helpers."""

    bot.add_view(PanelView(h))  # keeps the buttons working after a bot restart

    @bot.tree.command(name="panel",
                      description="Mở bảng điều khiển có nút bấm / Open the button control panel")
    @h.is_debug_channel()
    async def slash_panel(interaction: discord.Interaction) -> None:
        embed = await panel_embed(h, interaction)
        await interaction.response.send_message(embed=embed, view=PanelView(h))
