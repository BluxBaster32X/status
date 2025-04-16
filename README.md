# Uber Eats Discord Status Bot

A Discord bot that allows authorized users to control and announce Uber Eats ordering status via commands.

## Features

- Toggle Uber Eats ordering status (open/closed)
- Role-based access control (only authorized users can change status)
- Status announcements via Discord webhooks
- Visual feedback with colored embeds
- Timestamped status updates in Eastern Time (ET)
- Bot presence indicator showing current status
- Voice channel name updates to indicate current status

## Commands

- `!open` - Set ordering status to OPEN
- `!close` - Set ordering status to CLOSED
- `!status` - Display the current ordering status
- `!help` - Show help information

## Setup Instructions

1. **Create a Discord Bot**:
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application and set up a bot
   - Enable the "Message Content" intent under Bot settings
   - Copy the bot token

2. **Create a Webhook** (optional):
   - In your Discord server, go to the channel settings
   - Select "Integrations" > "Webhooks"
   - Create a new webhook and copy the URL

3. **Install Requirements**:
   ```
   pip install discord.py requests python-dotenv
   ```

4. **Configure Environment Variables**:
   - Copy the `.env.example` file to `.env`
   - Add your Discord bot token
   - Add your webhook URL (if using)
   - Add the announcement channel ID (fallback)
   - Add authorized usernames/IDs

5. **Run the Bot**:
   ```
   python bot.py
   ```

## Environment Variables

- `DISCORD_BOT_TOKEN`: Your Discord bot token
- `DISCORD_WEBHOOK_URL`: Webhook URL for status announcements
- `ANNOUNCEMENT_CHANNEL_ID`: Channel ID for direct announcements (fallback)
- `STATUS_VOICE_CHANNEL_ID`: Voice channel ID to update with status changes
- `ALLOWED_USERS`: Comma-separated list of authorized users who can use commands

## Security Notes

- Never share your bot token or commit it to a public repository
- Use environment variables or a .env file to store sensitive information
- Regularly audit the list of authorized users

## Troubleshooting

- Ensure the bot has proper permissions in your Discord server
- If webhooks aren't working, check that the URL is correct and the webhook still exists
- For direct announcements, verify the bot has permission to send messages in the channel
