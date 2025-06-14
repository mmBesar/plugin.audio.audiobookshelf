# NOT READY YET

# Audiobookshelf Kodi Add-on

A Kodi add-on for streaming podcasts from your self-hosted [Audiobookshelf](https://github.com/advplyr/audiobookshelf) server with full progress synchronization.

## Features

- 🎧 Stream podcasts from your Audiobookshelf server
- 🔄 Full progress synchronization across devices
- 📱 Resume episodes where you left off
- 🆕 Browse recent episodes across all podcasts
- ⏯️ View and continue in-progress episodes
- 🎨 Rich metadata display with cover art
- ⚙️ Configurable sync intervals and playback settings

## Installation

### Method 1: From Repository (Recommended)

1. Download the latest `plugin.audio.audiobookshelf-X.X.X.zip` from the [Releases](../../releases) page
2. In Kodi, go to **Settings** → **Add-ons** → **Install from zip file**
3. Select the downloaded zip file
4. The add-on will be installed and available in **Add-ons** → **Music add-ons**

### Method 2: Manual Installation

1. Clone or download this repository
2. Copy the entire folder to your Kodi add-ons directory:
   - **Windows**: `%APPDATA%\Kodi\addons\`
   - **macOS**: `~/Library/Application Support/Kodi/addons/`
   - **Linux**: `~/.kodi/addons/`
3. Restart Kodi

## Setup

1. **Install and Configure Audiobookshelf Server**
   - Follow the [Audiobookshelf installation guide](https://www.audiobookshelf.org/docs)
   - Make sure your server is accessible from your Kodi device

2. **Get Your API Token**
   - Log into your Audiobookshelf web interface
   - Go to **Settings** → **Users** → Your user → **API Tokens**
   - Generate a new token and copy it

3. **Configure the Kodi Add-on**
   - Open the add-on settings in Kodi
   - Enter your Audiobookshelf server URL (e.g., `http://192.168.1.100:13378`)
   - Enter your API token
   - Click "Test Connection" to verify everything works

## Usage

### Main Menu
- **Podcasts**: Browse all your podcasts
- **Recent Episodes**: View the latest episodes across all podcasts
- **In Progress**: Continue episodes you've started but haven't finished

### Playback Features
- Episodes automatically resume from where you left off
- Progress is synced to your Audiobookshelf server every 30 seconds (configurable)
- Episodes are marked as finished when you reach the end
- Seeking is supported and synced immediately

### Settings

#### Server Settings
- **Server URL**: Your Audiobookshelf server address
- **API Token**: Your personal API token for authentication

#### Playback Settings
- **Progress Sync Interval**: How often to sync progress (10-300 seconds)
- **Auto Resume**: Automatically resume episodes from last position
- **Mark Finished Threshold**: Seconds remaining when episode is marked complete

#### Interface Settings
- **Show Descriptions**: Display episode descriptions
- **Episodes Per Page**: Number of episodes to display at once
- **Sort Episodes**: Sort by newest or oldest first

## Supported Formats

The add-on supports all audio formats that your Audiobookshelf server can stream:
- MP3
- M4A/M4B
- FLAC
- OGG
- WAV
- And more...

## Troubleshooting

### Connection Issues
1. Verify your server URL is correct and includes the port (usually 13378)
2. Ensure your Kodi device can reach the Audiobookshelf server
3. Check that your API token is valid and hasn't expired
4. Use the "Test Connection" feature in settings

### Playback Issues
1. Check that the podcast episodes exist on your server
2. Verify your Audiobookshelf server has the latest updates
3. Check Kodi logs for specific error messages

### Progress Sync Issues
1. Ensure your API token has the necessary permissions
2. Check your internet connection
3. Verify the sync interval setting isn't too low

## Development

### Requirements
- Python 3.8+
- Kodi 19+ (Matrix)

### Testing
1. Clone the repository
2. Create a symbolic link in your Kodi add-ons directory
3. Enable debug logging in Kodi
4. Check logs for any issues

### Building
The repository includes GitHub Actions that automatically:
- Validate the add-on structure
- Create release packages
- Generate checksums for repository distribution

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Audiobookshelf](https://github.com/advplyr/audiobookshelf) - The excellent self-hosted audiobook and podcast server
- The Kodi development community for their excellent documentation
- All contributors and testers

## Support

For issues and feature requests, please use the [GitHub Issues](../../issues) page.

For general Audiobookshelf support, visit their [Discord server](https://discord.gg/HQgCbd6E75).
