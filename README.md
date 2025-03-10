# kostats_downloader
Download game logs from kostats.com

# KOStats Scraper

A Python script to automatically download sports statistics files from KOStats.com on a regular schedule.

## Features

- Logs in to KOStats.com using credentials stored in environment variables
- Downloads statistics files for multiple sports (CBK, CFB, MLB, NBA, NFL, NHL)
- Organizes downloads into sport-specific folders
- Keeps track of previously downloaded files to avoid duplicates
- Runs on a schedule via cron job

## Requirements

- Python 3.7+
- Required packages: requests, beautifulsoup4, python-dotenv

## Setup Instructions

### 1. Install Required Packages

```bash
pip install requests beautifulsoup4 python-dotenv
```

### 2. Configure Environment Variables

Create a `.env` file in the same directory as the script with the following variables:

```
KOSTATS_USERNAME=your_username
KOSTATS_PASSWORD=your_password
DOWNLOAD_DIR=~/kostats_downloads
```

Replace `your_username` and `your_password` with your actual KOStats login credentials.

### 3. Make the Script Executable

```bash
chmod +x /path/to/kostats_scraper.py
```

### 4. Set Up Cron Job (for daily execution)

Open your crontab for editing:

```bash
crontab -e
```

## How It Works

1. **Login**: The script logs into KOStats.com using your credentials
2. **File Discovery**: For each sport, it visits the subscription page and finds all available data files
3. **Smart Downloads**: It checks which files are new (not previously downloaded) and downloads only those
4. **Organization**: Files are saved in separate folders by sport
5. **History Tracking**: A JSON file keeps track of all downloaded files to prevent duplicates

## Troubleshooting

Check the `kostats_scraper.log` file for detailed logs of the script's operation. This will show any errors during login, file access, or downloads.

If the script fails to run via cron, check the `cron_output.log` file for error messages.

## Customization

- To change the download frequency, modify the cron schedule
- To add or remove sports, edit the `SPORT_PAGES` dictionary in the script