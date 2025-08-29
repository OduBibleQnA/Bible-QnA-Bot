import discord
from discord.ext import commands, tasks
from googleapiclient.discovery import build
import logging
from dotenv import load_dotenv
import os
import aiohttp
import asyncio
import signal

# === Load environment variables ===
load_dotenv()

token = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
# ANNOUNCEMENT_CHANNEL_ID = int(os.getenv("ANNOUNCEMENT_CHANNEL_ID"))
# YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
# YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
# SITE_UP = os.getenv("SITE_UP", "false").lower() == "true"
# DISCORD_API_KEY_URL = os.getenv("DISCORD_API_KEY_URL")
# DISCORD_INVITE_UPDATE_URL = os.getenv("DISCORD_INVITE_UPDATE_URL")

VIDEO_ID_FILE = "last_video.txt"

# === Logging Setup ===
logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# === Load/Save last video ID ===
# def load_last_video_id():
#     if os.path.exists(VIDEO_ID_FILE):
#         with open(VIDEO_ID_FILE, "r") as f:
#             return f.read().strip()
#     try:
#         request = youtube.search().list(
#             part="id",
#             channelId=YOUTUBE_CHANNEL_ID,
#             maxResults=1,
#             order="date",
#             type="video"
#         )
#         response = request.execute()
#         latest_id = response["items"][0]["id"]["videoId"]
#         save_last_video_id(latest_id)
#         logger.info(f"Initialized last video ID to: {latest_id}")
#         return latest_id
#     except Exception as e:
#         logger.error(f"Failed to initialize last video ID: {e}")
#         return None

# def save_last_video_id(video_id):
#     with open(VIDEO_ID_FILE, "w") as f:
#         f.write(video_id)
#     logger.info(f"Saved new last video ID: {video_id}")

# # === YouTube Setup ===
# youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
# last_video_id = load_last_video_id()

# === Discord Setup ===
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="$", intents=intents, help_command=None)

# === Graceful Shutdown ===
def shutdown():
    logger.info("Shutting down gracefully...")
    asyncio.get_event_loop().create_task(bot.close())

signal.signal(signal.SIGTERM, lambda *_: shutdown())

# === Events ===
@bot.event
async def on_ready():
    logger.info(f"Bot ready: {bot.user.name}")
    # check_new_youtube_video.start()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    mod_role = discord.utils.get(message.guild.roles, name__iexact="Moderator")
    podcaster_role = discord.utils.get(message.guild.roles, name__iexact="Podcasters")

    with open("curse_words.txt", "r") as f:
        curse_words = [line.strip().lower() for line in f]

    for word in curse_words:
        if word in message.content.lower():
            await message.delete()
            await message.channel.send(f"{message.author.mention} Don't use that word.")
            if mod_role and podcaster_role:
                await message.channel.send(f"{mod_role.mention} and {podcaster_role.mention} {message.author} has cursed. !warn {message.author} Cursed")
            await message.channel.send(f"!mute {message.author.mention} Cursed")
            logger.info(f"Deleted message from {message.author} containing banned word: {word}")
            break

    await bot.process_commands(message)

# === Commands ===
@bot.command()
@commands.has_any_role('Podcasters', 'Moderator')
async def ban(ctx, member: discord.Member, *, reason=None):
    channel = discord.utils.get(ctx.guild.channels, name="rules")
    if member.guild_permissions.administrator:
        await ctx.channel.send(f"{ctx.author.name}, that member is an admin. Don't do that!")
        logger.warning(f"{ctx.author} tried to ban admin {member}")
        return

    try:
        await member.send(f"You were banned from {ctx.guild.name}. Reason: {reason or 'Not specified'}")
    except discord.Forbidden:
        logger.warning(f"Could not DM {member.name} before banning.")

    await ctx.channel.send(f"{member.name} has been banned. Reason: {reason or 'Not specified'}")
    await member.ban(reason=reason)
    logger.info(f"{member.name} was banned. Reason: {reason or 'Not specified'}")

# === Tasks ===
# @tasks.loop(minutes=45)
# async def check_new_youtube_video():
#     global last_video_id
#     try:
#         request = youtube.search().list(
#             part="snippet",
#             channelId=YOUTUBE_CHANNEL_ID,
#             maxResults=1,
#             order="date",
#             type="video"
#         )
#         response = request.execute()
#         latest_video = response["items"][0]
#         video_id = latest_video["id"]["videoId"]
#         video_title = latest_video["snippet"]["title"]
#         video_url = f"https://youtu.be/{video_id}"

#         if video_id != last_video_id:
#             last_video_id = video_id
#             save_last_video_id(video_id)

#             channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
#             if channel:
#                 await channel.send(
#                     f"!feeds announce announcements A new video uploaded: **{video_title}**\nWatch here: {video_url}"
#                 )
#                 logger.info(f"Announced new video: {video_title} ({video_url})")
#         else:
#             logger.debug("No new video found.")
#     except Exception as e:
#         logger.error(f"YouTube check failed: {e}")

# === Start Bot ===
if __name__ == "__main__":
    bot.run(token, log_handler=file_handler, log_level=logging.DEBUG)
