import discord
from discord import app_commands
from datetime import timedelta

def is_admin(interaction):
    return interaction.user.guild_permissions.administrator

class ModerationView(discord.ui.View):
    def __init__(self, member, author):
        super().__init__(timeout=60)
        self.member = member
        self.author = author

    async def interaction_check(self, interaction):
        return interaction.user.id == self.author.id

    @discord.ui.button(label="警告", style=discord.ButtonStyle.secondary)
    async def warn(self, interaction, _):
        await interaction.response.send_message(f"{self.member.mention} 被警告", ephemeral=True)

    @discord.ui.button(label="禁言 60 秒", style=discord.ButtonStyle.primary)
    async def timeout(self, interaction, _):
        try:
            await self.member.timeout_for(timedelta(seconds=60))
            await interaction.response.send_message(f"{self.member.mention} 被禁言", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"禁言失敗：{e}", ephemeral=True)

    @discord.ui.button(label="踢出", style=discord.ButtonStyle.danger)
    async def kick(self, interaction, _):
        try:
            await self.member.kick()
            await interaction.response.send_message(f"{self.member.mention} 被踢出", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"踢出失敗：{e}", ephemeral=True)

    @discord.ui.button(label="封鎖", style=discord.ButtonStyle.danger)
    async def ban(self, interaction, _):
        try:
            await self.member.ban()
            await interaction.response.send_message(f"{self.member.mention} 被封鎖", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"封鎖失敗：{e}", ephemeral=True)

def add_moderate_commands(bot):
    @bot.tree.command(name="moderate", description="打開管理面板")
    @app_commands.describe(member="要管理的成員")
    async def moderate(interaction: discord.Interaction, member: discord.Member):
        if not is_admin(interaction):
            return await interaction.response.send_message("你沒有權限。", ephemeral=True)
        view = ModerationView(member, interaction.user)
        await interaction.response.send_message(f"請選擇對 {member.mention} 的操作：", view=view, ephemeral=True)
