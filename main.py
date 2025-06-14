import discord
from discord.ext import commands, tasks
from googleapiclient.discovery import build
import logging
from dotenv import load_dotenv
import os
import aiohttp


load_dotenv()


token = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID"))
ANNOUNCEMENT_CHANNEL_ID = int(os.getenv("ANNOUNCEMENT_CHANNEL_ID"))

YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

SITE_UP = os.getenv("SITE_UP").lower() == "true"
DISCORD_API_KEY_URL = os.getenv("DISCORD_API_KEY_URL")
DISCORD_INVITE_UPDATE_URL = os.getenv("DISCORD_INVITE_UPDATE_URL")

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
last_video_id = None


handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="#", intents=intents, help_command=None)


@bot.event
async def on_ready():
    print(f"We are ready to start using {bot.user.name}")
    rotate_invite.start()


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    mod_role = discord.utils.get(message.guild.roles, name__iexact="Podcasters")

    curse_words = []
    with open("curse_words.txt", "r") as f:
        curse_words = f.readlines()

    for word in curse_words:
        if word in message.content.lower:
            await message.delete()
            await message.channel.send(f"{message.author.mention} Don't use that word.")
            await message.channel.send(
                f"{mod_role.mention if mod_role else ''} {message.author} has cursed. !warn {message.author} Cursed"
            )
            await message.channel.send(
                f"!mute {message.author.mention} Cursed"
            )
            break

    await bot.process_commands(message)


@bot.command()
@commands.has_role("Podcasters")
async def ban(ctx, member: discord.Member, *, reason=None):
    channel = discord.utils.get(ctx.guild.channels, name="rules")

    if (
        member.guild_permissions.administrator
    ):  # To check if the member we are trying to mute is an admin or not.
        await ctx.channel.send(
            f"Hi {ctx.author.name}! The member you are trying to ban is a server Administrator. Please don't try this on them else they can get angry! :person_shrugging:"
        )

    else:
        if reason is None:  # If the moderator did not enter any reason.
            # This command sends DM to the user about the BAN!
            await member.send(
                f"Hi {member.name}! You have been banned from {ctx.channel.guild.name}. You must have done something wrong. VERY BAD! :angry: :triumph: \n \nReason: Not Specified"
            )
            # This command sends message in the channel for confirming BAN!
            await ctx.channel.send(
                f"{member.name} flew too close to the sun and got banned. Maybe they should have followed the {channel.mention} \n \nReason: Not Specified"
            )
            await member.ban()  # Bans the member.

        else:  # If the moderator entered a reason.
            # This command sends DM to the user about the BAN!
            await member.send(
                f"Hi {member.name}! You have been banned from {ctx.channel.guild.name}. You must have done something wrong. VERY BAD! :angry: :triumph: \n \nReason: {reason}"
            )
            # This command sends message in the channel for confirming BAN!
            await ctx.channel.send(
                f"{member.name} flew too close to the sun and got banned. Maybe they should have followed the {channel.mention} \n \nReason: {reason}"
            )
            await member.ban()

@tasks.loop(hours=72)
async def rotate_invite():
    guild = bot.get_guild(GUILD_ID)
    channel = guild.get_channel(WELCOME_CHANNEL_ID)

    invites = await guild.invites()
    for invite in invites:
        if invite.channel.id == WELCOME_CHANNEL_ID:
            await invite.delete()

    new_invite = await channel.create_invite(max_age=72*60*60, unique=True)
    if not SITE_UP: return
    async with aiohttp.ClientSession() as session:
        # Step 1: Get API key
        async with session.get(DISCORD_API_KEY_URL) as key_resp:
            if key_resp.status != 200:
                print("Failed to get API key")
                return
            
            data = await key_resp.json()
            
            api_key = data.get("DISCORD-BOT-APP-KEY")
            if not api_key:
                print("API key not found in response")
                return

        # Step 2: Send invite to Django API
        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
        payload = {"url": new_invite.url}

        async with session.post(
            DISCORD_INVITE_UPDATE_URL, headers=headers, json=payload
        ) as resp:
            if resp.status == 201:
                print("Invite saved to Django")
            else:
                print(f"Failed to save invite (status {resp.status})")

@tasks.loop(minutes=45)
async def check_new_youtube_video():
    global last_video_id
    request = youtube.search().list(
        part="snippet",
        channelId=YOUTUBE_CHANNEL_ID,
        maxResults=1,
        order="date",
        type="video"
    )
    response = request.execute()
    latest_video = response['items'][0]
    video_id = latest_video['id']['videoId']

    if video_id != last_video_id:
        last_video_id = video_id
        video_title = latest_video['snippet']['title']
        video_url = f"https://youtu.be/{video_id}"
        channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
        if channel:
            await channel.send(f"!feeds announce announcements A new video uploaded: **{video_title}**\nWatch here: {video_url}")



if __name__ == "__main__":
    bot.run(token, log_handler=handler, log_level=logging.DEBUG)
