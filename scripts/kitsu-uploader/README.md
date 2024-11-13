# Kitsu Video Preview Uploader

This script uploads a video file as a preview to Kitsu using either a "shot" or an "edit" file path. 
Only one of these options can be specified at a time.

## Requirements

- Python 3.x
- `requests`
- `.env.local` configuration file in the script’s directory for Kitsu API credentials and settings

## Installation

1. Clone this repository or download the script file.
2. Create a `.env.local` file in the same directory as the script, following the format specified in [Configuration Setup](#configuration-setup).
3. Install any required dependencies:

   ```bash
   pip install requests
   ```
## Configuration Setup

The script uses the Config class to load configuration details for connecting to the Kitsu API. 
The configuration is loaded from a .env.local file placed in the same directory as the script. 
Make a copy of .env.example to get started.


## Usage

```
./main.py --shot /path/to/shot/01_010_1020-anim-v001.mp4
```
