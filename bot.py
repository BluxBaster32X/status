import os
import discord
import requests
import logging
import pytz
from datetime import datetime
from dotenv import load_dotenv
import re
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('uber-eats-bot')

# Load environment variables from .env file (for local development)
load_dotenv()

BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN') or os.getenv(
    'DISCORD_BOT_TOKEN')
WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL') or os.getenv(
    'DISCORD_WEBHOOK_URL')
ALLOWED_USERS = os.environ.get('ALLOWED_USERS', '').split(',') or os.getenv(
    'ALLOWED_USERS', '').split(',')
ANNOUNCEMENT_CHANNEL_ID = os.environ.get(
    'ANNOUNCEMENT_CHANNEL_ID') or os.getenv('ANNOUNCEMENT_CHANNEL_ID')
STATUS_VOICE_CHANNEL_ID = os.environ.get(
    'STATUS_VOICE_CHANNEL_ID') or os.getenv('STATUS_VOICE_CHANNEL_ID')
TICKETS_CATEGORY_ID = os.environ.get('TICKETS_CATEGORY_ID') or os.getenv(
    'TICKETS_CATEGORY_ID')

current_status = "closed"
processed_ticket_channels = set()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True
client = discord.Client(intents=intents)


def send_webhook(status: str, triggered_by: str):
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern).strftime("%-m/%-d/%Y, %-I:%M:%S %p ET")

    if status == "open":
        title = "Shack Eats is Now Open ✅"
        description = "We are now accepting orders! Click the order button in <#order-here> to create a ticket."
        color = 5763719
    else:
        title = "Shack Eats is Now Closed ❌"
        description = "We are not accepting orders right now. Please check back later."
        color = 15548997

    payload = {
        "username":
        triggered_by,
        "embeds": [{
            "title": title,
            "description": description,
            "color": color,
            "footer": {
                "text": f"Status updated by {triggered_by} • {now}"
            }
        }]
    }

    if not WEBHOOK_URL:
        logger.warning(
            "No webhook URL configured. Skipping webhook notification.")
        return False

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        if response.status_code >= 400:
            logger.error(
                f"Error sending webhook: {response.status_code} - {response.text}"
            )
            return False
        return True
    except Exception as e:
        logger.error(f"Failed to send webhook: {str(e)}")
        return False


async def extract_group_order_link(messages):
    for message in messages:
        if "GROUP ORDER LINK" in message.content.upper():
            content = message.content
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "GROUP ORDER LINK" in line.upper():
                    link_line = line
                    if "HTTP" not in line.upper() and i + 1 < len(lines):
                        link_line = lines[i + 1]
                    match = re.search(r'https?://\S+', link_line)
                    if match:
                        return match.group(0)
    return None


async def process_ticket_channel(channel):
    global processed_ticket_channels
    if channel.id in processed_ticket_channels:
        return
    processed_ticket_channels.add(channel.id)

    try:
        messages = [message async for message in channel.history(limit=50)]
        group_order_link = await extract_group_order_link(messages)
        if group_order_link:
            command = f"/checker {group_order_link}"
            logger.info(f"Sending command in {channel.name}: {command}")
            await channel.send(command)
        else:
            logger.info(f"No group order link found in {channel.name}")
    except Exception as e:
        logger.error(f"Error processing {channel.name}: {str(e)}")


async def check_for_new_ticket_channels():
    await client.wait_until_ready()
    while not client.is_closed():
        try:
            for guild in client.guilds:
                if TICKETS_CATEGORY_ID:
                    category = discord.utils.get(guild.categories,
                                                 id=int(TICKETS_CATEGORY_ID))
                    if category:
                        for channel in category.text_channels:
                            await process_ticket_channel(channel)
                for channel in guild.text_channels:
                    if "ticket" in channel.name.lower():
                        await process_ticket_channel(channel)
        except Exception as e:
            logger.error(f"Error in ticket check: {str(e)}")
        await asyncio.sleep(5)


@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user.name}')
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="Orders CLOSED" if current_status == "closed" else "Orders OPEN")
    await client.change_presence(activity=activity)
    client.loop.create_task(check_for_new_ticket_channels())


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    username = str(message.author)
    user_id = str(message.author.id)

    if username not in ALLOWED_USERS and user_id not in ALLOWED_USERS:
        if message.content.startswith('!'):
            await message.channel.send(
                "❌ Sorry, you're not authorized to use this command.")
        return

    global current_status
    content = message.content.lower()

    if content == "!open":
        if current_status == "open":
            await message.channel.send("⚠️ Status is already set to **OPEN**.")
            return
        current_status = "open"
        await client.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, name="Orders OPEN"))
        webhook_sent = send_webhook("open", username)
        if not webhook_sent and ANNOUNCEMENT_CHANNEL_ID:
            await send_announcement(ANNOUNCEMENT_CHANNEL_ID, "open", username)
        await message.channel.send(f"✅ Status set to **OPEN** by `{username}`")

    elif content == "!close":
        if current_status == "closed":
            await message.channel.send(
                "⚠️ Status is already set to **CLOSED**.")
            return
        current_status = "closed"
        await client.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, name="Orders CLOSED"))
        webhook_sent = send_webhook("close", username)
        if not webhook_sent and ANNOUNCEMENT_CHANNEL_ID:
            await send_announcement(ANNOUNCEMENT_CHANNEL_ID, "close", username)
        await message.channel.send(
            f"❌ Status set to **CLOSED** by `{username}`")

    elif content == "!status":
        status_text = "**CLOSED** ❌" if current_status == "closed" else "**OPEN** ✅"
        await message.channel.send(f"Current status: {status_text}")

    elif content == "!help":
        embed = discord.Embed(
            title="Shack Eats Status Bot - Help",
            description="Commands available to authorized users:",
            color=discord.Color.blue())
        embed.add_field(name="!open",
                        value="Set the ordering status to OPEN",
                        inline=False)
        embed.add_field(name="!close",
                        value="Set the ordering status to CLOSED",
                        inline=False)
        embed.add_field(name="!status",
                        value="Display the current ordering status",
                        inline=False)
        embed.add_field(name="!help",
                        value="Show this help message",
                        inline=False)
        await message.channel.send(embed=embed)


def main():
    if not BOT_TOKEN:
        logger.error("Missing bot token.")
        return
    if not WEBHOOK_URL and not ANNOUNCEMENT_CHANNEL_ID:
        logger.warning("No webhook or announcement channel configured.")
    if not ALLOWED_USERS or (len(ALLOWED_USERS) == 1
                             and ALLOWED_USERS[0] == ''):
        logger.warning("No authorized users configured.")
    try:
        logger.info("Starting bot...")
        client.run(BOT_TOKEN)
    except discord.errors.LoginFailure:
        logger.error("Invalid bot token.")
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")


if __name__ == "__main__":
    main()
