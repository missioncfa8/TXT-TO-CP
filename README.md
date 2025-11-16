# TXT-TO-CP Telegram Bot

A Telegram bot for downloading and converting text files to various formats.

## Deployment

### Render Deployment

1. Fork this repository
2. Go to [Render](https://render.com/)
3. Create a new Web Service
4. Connect your forked repository
5. Set the following environment variables:
   - `API_ID` - Your Telegram API ID
   - `API_HASH` - Your Telegram API Hash
   - `BOT_TOKEN` - Your Telegram Bot Token
   - `OWNER` - Your Telegram User ID
   - `CREDIT` - Credit name for the bot

6. Deploy the service

## Environment Variables

- `API_ID` - Telegram API ID (required)
- `API_HASH` - Telegram API Hash (required)
- `BOT_TOKEN` - Telegram Bot Token (required)
- `OWNER` - Telegram User ID of the bot owner (required)
- `CREDIT` - Credit name for the bot (required)

## Commands

- `/start` - Start the bot
- `/drm` - Extract from .txt file
- `/y2t` - YouTube to .txt converter
- `/ytm` - YouTube .txt to .mp3 downloader
- `/yt2m` - YouTube link to .mp3 downloader
- `/t2t` - Text to .txt generator

## Features

- Download videos from various platforms
- Convert YouTube playlists to text files
- Extract audio from YouTube videos
- Handle DRM-protected content
- Batch processing capabilities

## License

This project is licensed under the MIT License.