# Mobile Search Bot Setup Guide

## For Render Hosting

1. **Fork/Upload this code** to a GitHub repository

2. **Go to Render.com** and create account

3. **Create New Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository

4. **Configure Service**
   - **Name:** `mobile-search-bot`
   - **Environment:** `Python 3`
   - **Region:** Choose nearest
   - **Branch:** `main` (or your branch)
   - **Root Directory:** (leave empty)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`

5. **Environment Variables**
   - `BOT_TOKEN` = your_discord_bot_token
   - `API_URL` = https://lostingness.site/osintx/mobile/api.php?key=c365a7d9-1c91-43c9-933d-da0ac38827ad&number={number}

6. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete

## For Local Development

1. **Install Python 3.8+**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt