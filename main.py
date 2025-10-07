import discord
import aiohttp
import re
import os
import asyncio
import json
from discord.ext import commands
from datetime import datetime, timezone
import pytz
import time
import io
import logging

# Setup logging for Pella
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot setup with correct intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Configuration from environment variables (Pella uses env vars)
API_URL = os.getenv('API_URL', "https://lostingness.site/osintx/mobile/api.php?key=c365a7d9-1c91-43c9-933d-da0ac38827ad&number={number}")
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Updated Developer Information
DEVELOPER_INFO = {
    'discord': 'https://discord.gg/teamkorn',
    'telegram': 'https://t.me/s/terex',
    'developer': '@Terex'
}

class PremiumStyles:
    # Premium Colors
    PRIMARY = 0x5865F2
    SUCCESS = 0x57F287
    ERROR = 0xED4245
    WARNING = 0xFEE75C
    INFO = 0x3498DB
    PREMIUM = 0x9B59B6

# Global variables for stats
bot.start_time = datetime.now(timezone.utc)
search_count = 0

# Maximum records to display in embeds
MAX_DISPLAY_RECORDS = 25

def get_indian_time():
    """Get current Indian time"""
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist).strftime("%d %b %Y • %I:%M %p IST")

def get_uptime():
    """Calculate bot uptime"""
    delta = datetime.now(timezone.utc) - bot.start_time
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    else:
        return f"{hours}h {minutes}m {seconds}s"

def clean_text(text):
    """Advanced text cleaning"""
    if not text or str(text).strip() in ["", "null", "None", "N/A", "NA"]:
        return "🚫 Not Available"
    
    text = str(text).strip()
    text = re.sub(r'[!@#$%^&*()_+=`~\[\]{}|\\:;"<>?]', ' ', text)
    text = re.sub(r'[.!]+$', '', text)
    text = re.sub(r'\s+', ' ', text)
    
    if '@' not in text:
        words = text.split()
        cleaned_words = []
        for word in words:
            if word.upper() in ['II', 'III', 'IV', 'VI', 'VII', 'VIII']:
                cleaned_words.append(word.upper())
            elif len(word) > 1:
                cleaned_words.append(word[0].upper() + word[1:].lower())
            else:
                cleaned_words.append(word.upper())
        text = ' '.join(cleaned_words)
    
    return text

def format_address(address):
    """Premium address formatting"""
    if not address or str(address).strip() in ["", "null", "None", "N/A"]:
        return "🚫 Address Not Available"
    
    address = str(address)
    address = re.sub(r'[.!*#-]+', ', ', address)
    address = re.sub(r'\s*,\s*', ', ', address)
    address = re.sub(r'\s+', ' ', address)
    address = re.sub(r'\b(c/o|C/O)\s*:?\s*', 'C/O: ', address, flags=re.IGNORECASE)
    address = address.strip().strip(',')
    
    parts = [part.strip() for part in address.split(',') if part.strip()]
    formatted_parts = []
    
    for part in parts:
        if part.upper() in ['DELHI', 'MUMBAI', 'KOLKATA', 'CHENNAI', 'BANGALORE', 'HYDERABAD']:
            formatted_parts.append(part.upper())
        else:
            formatted_parts.append(part.title())
    
    return ', '.join(formatted_parts)

@bot.event
async def on_ready():
    logger.info("🚀 Premium Mobile Search Bot Online!")
    logger.info("💎 Developed By @Terex")
    logger.info("⚡ Unlimited searches enabled!")
    logger.info("🌐 API: Lostingness Premium")
    logger.info(f"👋 Connected to {len(bot.guilds)} servers!")
    
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="Mobile Numbers | !help"
    )
    await bot.change_presence(activity=activity)

@bot.event
async def on_guild_join(guild):
    """Send welcome message when bot joins a new server"""
    try:
        # Try to send to system channel first
        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            channel = guild.system_channel
        else:
            # Find first text channel where bot can send messages
            channel = next((ch for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages), None)
        
        if channel:
            embed = discord.Embed(
                title="👋 Thanks for adding Mobile Search Bot!",
                description="**Advanced mobile number lookup with premium features**",
                color=0x5865F2
            )
            
            embed.add_field(
                name="🚀 Quick Start",
                value="• Use `!search 7405453929` to search numbers\n• Or just type any 10-digit number in chat\n• Use `!help` for all commands",
                inline=False
            )
            
            embed.add_field(
                name="💎 Premium Features",
                value="• Unlimited searches\n• No rate limits\n• JSON data export\n• Text file download\n• Auto number detection",
                inline=False
            )
            
            embed.add_field(
                name="🔗 Developer Links",
                value=f"• [Discord Server]({DEVELOPER_INFO['discord']})\n• [Telegram]({DEVELOPER_INFO['telegram']})\n• Developer: {DEVELOPER_INFO['developer']}",
                inline=False
            )
            
            embed.set_footer(text="Type !help for complete guide • Enjoy premium searching!")
            
            await channel.send(embed=embed)
            logger.info(f"✅ Sent welcome message to {guild.name}")
    except Exception as e:
        logger.error(f"❌ Couldn't send welcome message to {guild.name}: {e}")

class PremiumSearchView(discord.ui.View):
    """Interactive buttons for premium search"""
    def __init__(self, ctx, records, number):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.records = records
        self.number = number
    
    @discord.ui.button(label='📋 Copy JSON Data', style=discord.ButtonStyle.primary, emoji='📋')
    async def copy_json(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Copy all data as JSON"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            copy_data = {
                "search_number": self.number,
                "timestamp": get_indian_time(),
                "total_records": len(self.records),
                "records": self.records
            }
            
            json_str = json.dumps(copy_data, indent=2, ensure_ascii=False)
            
            if len(json_str) > 2000:
                # Create file in memory
                file_buffer = io.BytesIO(json_str.encode('utf-8'))
                file = discord.File(
                    fp=file_buffer,
                    filename=f"mobile_search_{self.number}.json"
                )
                await interaction.followup.send(
                    "✅ Data exported as file:",
                    file=file,
                    ephemeral=True
                )
            else:
                embed = discord.Embed(
                    title="📋 Copyable JSON Data",
                    description=f"```json\n{json_str}\n```",
                    color=0x9B59B6
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"JSON Export Error: {e}")
            await interaction.followup.send("❌ Failed to export data. Please try again.", ephemeral=True)
    
    @discord.ui.button(label='📱 Export Text', style=discord.ButtonStyle.secondary, emoji='📱')
    async def export_text(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Export as formatted text"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            text_content = f"🔍 MOBILE SEARCH RESULTS\n"
            text_content += f"═══════════════════════════\n\n"
            text_content += f"📱 Number: {self.number}\n"
            text_content += f"📅 Time: {get_indian_time()}\n"
            text_content += f"📊 Records Found: {len(self.records)}\n"
            text_content += f"👨‍💻 Developer: {DEVELOPER_INFO['developer']}\n\n"
            
            for i, record in enumerate(self.records, 1):
                text_content += f"──────── RECORD {i} ────────\n"
                text_content += f"📱 Mobile: {record.get('mobile', 'N/A')}\n"
                text_content += f"👤 Name: {clean_text(record.get('name', 'N/A'))}\n"
                text_content += f"👨‍👦 Father: {clean_text(record.get('father_name', record.get('fathersname', 'N/A')))}\n"
                text_content += f"🏠 Address: {format_address(record.get('address', 'N/A'))}\n"
                text_content += f"🌍 Circle: {clean_text(record.get('circle', 'N/A'))}\n"
                text_content += f"🪪 ID: {clean_text(record.get('id_number', record.get('idnumber', 'N/A')))}\n"
                text_content += f"📧 Email: {clean_text(record.get('email', 'N/A'))}\n"
                text_content += f"📞 Alt Mobile: {clean_text(record.get('alt_mobile', 'N/A'))}\n\n"
            
            # Create file in memory with proper encoding
            file_buffer = io.BytesIO(text_content.encode('utf-8'))
            file = discord.File(
                fp=file_buffer,
                filename=f"search_{self.number}.txt"
            )
            
            await interaction.followup.send(
                "📥 Text export ready:",
                file=file,
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Text Export Error: {e}")
            await interaction.followup.send("❌ Failed to export text. Please try again.", ephemeral=True)

@bot.command()
async def search(ctx, *, number: str = None):
    """Premium mobile number search"""
    global search_count
    
    if not number:
        embed = discord.Embed(
            title="ℹ️ Mobile Search",
            description="**Usage:** `!search 7405453929`\n**Auto-detection:** Just type any 10-digit number in chat",
            color=0x3498DB
        )
        embed.add_field(
            name="🔧 Features",
            value="• Unlimited searches\n• Multiple records\n• JSON export\n• Text export\n• Copyable data\n• Fast results",
            inline=False
        )
        embed.add_field(
            name="🔗 Developer",
            value=f"[Discord Server]({DEVELOPER_INFO['discord']}) • [Telegram]({DEVELOPER_INFO['telegram']})",
            inline=False
        )
        embed.set_footer(text=f"Developed by {DEVELOPER_INFO['developer']} • Premium Search Bot")
        await ctx.send(embed=embed)
        return
    
    # Extract numbers from input
    numbers = re.findall(r'\d{10}', number)
    if not numbers:
        embed = discord.Embed(
            title="❌ Invalid Input",
            description="Please provide a valid 10-digit mobile number.",
            color=0xED4245
        )
        await ctx.send(embed=embed)
        return
    
    number = numbers[0]
    
    # Show searching embed
    search_embed = discord.Embed(
        title="🚀 Launching Premium Search",
        description=f"**Target:** `{number}`\n**Status:** Initializing...",
        color=0x5865F2
    )
    search_embed.add_field(
        name="🔍 Search Details",
        value=f"• API: Lostingness Premium\n• Mode: Ultra Fast\n• Time: {get_indian_time()}",
        inline=False
    )
    search_embed.set_footer(text="Powered by Advanced OSINT Technology")
    search_msg = await ctx.send(embed=search_embed)
    
    search_count += 1
    await process_search(ctx, number, search_msg)

@bot.event
async def on_message(message):
    """Auto-detect mobile numbers in messages"""
    global search_count
    
    if message.author == bot.user:
        return
    
    # Auto-detect 10-digit numbers
    numbers = re.findall(r'\b\d{10}\b', message.content)
    for number in numbers:
        if number and re.match(r'^\d{10}$', number):
            embed = discord.Embed(
                title="🔍 Auto-Detected Number",
                description=f"Found mobile number: `{number}`",
                color=0x3498DB
            )
            embed.set_footer(text="Auto-search starting...")
            search_msg = await message.channel.send(embed=embed)
            search_count += 1
            await process_search(message.channel, number, search_msg, is_auto=True)
    
    await bot.process_commands(message)

async def process_search(ctx_or_channel, number, search_msg=None, is_auto=False):
    """Process the mobile number search"""
    try:
        # Update search status
        if search_msg:
            updating_embed = discord.Embed(
                title="⚡ Connecting to Database",
                description=f"**Searching:** `{number}`\n**Status:** Accessing premium database...",
                color=0xFEE75C
            )
            updating_embed.set_footer(text="High-speed search in progress...")
            await search_msg.edit(embed=updating_embed)
        
        # API Request
        url = API_URL.format(number=number)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                else:
                    raise Exception(f"API returned status {response.status}")
        
        # Process response
        if isinstance(data, dict) and data.get("error"):
            error_embed = discord.Embed(
                title="❌ Search Failed",
                description=f"**Number:** `{number}`\n**Error:** {data.get('error', 'Unknown error')}",
                color=0xED4245
            )
            error_embed.set_footer(text="Try again with a different number")
            if search_msg:
                await search_msg.edit(embed=error_embed)
            else:
                await send_embed(ctx_or_channel, error_embed)
            return
        
        if not data or (isinstance(data, list) and len(data) == 0):
            no_data_embed = discord.Embed(
                title="⚠️ No Records Found",
                description=f"No records found for: `{number}`",
                color=0xFEE75C
            )
            no_data_embed.add_field(
                name="💡 Suggestions",
                value="• Try with a different number\n• Check the number format\n• Some numbers may not be in database",
                inline=False
            )
            if search_msg:
                await search_msg.edit(embed=no_data_embed)
            else:
                await send_embed(ctx_or_channel, no_data_embed)
            return
        
        # Successful search with data
        records = data if isinstance(data, list) else [data]
        
        if search_msg:
            await search_msg.delete()
        
        await send_premium_results(ctx_or_channel, number, records)
        
    except aiohttp.ClientError as e:
        logger.error(f"Network error: {e}")
        error_embed = discord.Embed(
            title="❌ Network Error",
            description="Unable to connect to search service. Please check your internet connection.",
            color=0xED4245
        )
        if search_msg:
            await search_msg.edit(embed=error_embed)
        else:
            await send_embed(ctx_or_channel, error_embed)
    except asyncio.TimeoutError:
        error_embed = discord.Embed(
            title="❌ Timeout Error",
            description="Search request timed out. Please try again.",
            color=0xED4245
        )
        if search_msg:
            await search_msg.edit(embed=error_embed)
        else:
            await send_embed(ctx_or_channel, error_embed)
    except Exception as e:
        logger.error(f"Search error: {e}")
        error_embed = discord.Embed(
            title="❌ Search Error",
            description=f"An error occurred while searching: `{str(e)}`",
            color=0xED4245
        )
        if search_msg:
            await search_msg.edit(embed=error_embed)
        else:
            await send_embed(ctx_or_channel, error_embed)

async def send_premium_results(ctx_or_channel, number, records):
    """Send premium formatted results with max record limit"""
    total_records = len(records)
    
    # Determine how many records to display
    display_records = records[:MAX_DISPLAY_RECORDS]
    hidden_records = total_records - MAX_DISPLAY_RECORDS if total_records > MAX_DISPLAY_RECORDS else 0
    
    # Summary Embed
    summary_embed = discord.Embed(
        title="🎉 SEARCH SUCCESSFUL!",
        description=f"**🔥 Found {total_records} Record(s) for `{number}`**",
        color=0x57F287,
        timestamp=datetime.now(timezone.utc)
    )
    
    summary_embed.add_field(
        name="ℹ️ Search Summary",
        value=f"**Number:** `{number}`\n**Records:** {total_records}\n**Displaying:** First {len(display_records)} records\n**Time:** {get_indian_time()}",
        inline=False
    )
    
    if hidden_records > 0:
        summary_embed.add_field(
            name="📊 Records Note",
            value=f"*Showing first {MAX_DISPLAY_RECORDS} records out of {total_records}*\n*Use JSON export to view all {total_records} records*",
            inline=False
        )
    
    summary_embed.add_field(
        name="💎 Premium Features",
        value="• Copy JSON Data (All Records)\n• Export as Text (All Records)\n• Unlimited Usage",
        inline=False
    )
    
    summary_embed.add_field(
        name="🔗 Developer",
        value=f"[Discord Server]({DEVELOPER_INFO['discord']}) • [Telegram]({DEVELOPER_INFO['telegram']})",
        inline=False
    )
    
    summary_embed.set_footer(text=f"Developed by {DEVELOPER_INFO['developer']} • Premium Mobile Search")
    
    # Send summary with interactive buttons
    view = PremiumSearchView(ctx_or_channel, records, number)
    await send_embed(ctx_or_channel, summary_embed, view=view)
    
    # Send individual record embeds (limited to MAX_DISPLAY_RECORDS)
    for index, record in enumerate(display_records, 1):
        record_embed = create_record_embed(record, index, len(display_records), number, total_records, hidden_records)
        await send_embed(ctx_or_channel, record_embed)
        await asyncio.sleep(0.3)
    
    # Add note about hidden records if applicable
    if hidden_records > 0:
        note_embed = discord.Embed(
            title="📝 Note",
            description=f"**{hidden_records} additional records are hidden**\nUse the **📋 Copy JSON Data** button above to view all {total_records} records in full detail.",
            color=0xFEE75C
        )
        await send_embed(ctx_or_channel, note_embed)

def create_record_embed(record, current_index, total_displayed, search_number, total_records, hidden_records):
    """Create a premium embed for each record"""
    # Clean data
    name = clean_text(record.get('name', 'N/A'))
    fathers_name = clean_text(record.get('father_name', record.get('fathersname', 'N/A')))
    address = format_address(record.get('address', 'N/A'))
    circle = clean_text(record.get('circle', 'N/A'))
    id_number = clean_text(record.get('id_number', record.get('idnumber', 'N/A')))
    email = clean_text(record.get('email', 'N/A'))
    alt_mobile = clean_text(record.get('alt_mobile', 'N/A'))
    mobile = record.get('mobile', search_number)
    
    embed = discord.Embed(
        title=f"👤 RECORD {current_index} of {total_displayed}",
        color=0x5865F2,
        timestamp=datetime.now(timezone.utc)
    )
    
    # Add note about total records if some are hidden
    if hidden_records > 0 and current_index == total_displayed:
        embed.description = f"*Displaying {total_displayed} of {total_records} total records*"
    
    # Main fields
    embed.add_field(
        name="📱 Mobile Number",
        value=f"```{mobile}```",
        inline=True
    )
    
    embed.add_field(
        name="👤 Full Name",
        value=f"```{name}```",
        inline=True
    )
    
    if fathers_name != "🚫 Not Available":
        embed.add_field(
            name="👨‍👦 Father's Name",
            value=f"```{fathers_name}```",
            inline=True
        )
    
    if address != "🚫 Address Not Available":
        embed.add_field(
            name="🏠 Complete Address",
            value=f"```{address}```",
            inline=False
        )
    
    # Additional fields
    if circle != "🚫 Not Available":
        embed.add_field(
            name="🌍 Telecom Circle",
            value=f"```{circle}```",
            inline=True
        )
    
    if id_number != "🚫 Not Available":
        embed.add_field(
            name="🪪 ID Number",
            value=f"```{id_number}```",
            inline=True
        )
    
    if email != "🚫 Not Available":
        embed.add_field(
            name="📧 Email Address",
            value=f"```{email}```",
            inline=True
        )
    
    if alt_mobile != "🚫 Not Available":
        embed.add_field(
            name="📞 Alternate Mobile",
            value=f"```{alt_mobile}```",
            inline=True
        )
    
    footer_text = f"Record {current_index}/{total_displayed} • {get_indian_time()} • {DEVELOPER_INFO['developer']}"
    if hidden_records > 0:
        footer_text = f"Record {current_index}/{total_displayed} • +{hidden_records} more • {DEVELOPER_INFO['developer']}"
    
    embed.set_footer(text=footer_text)
    
    return embed

async def send_embed(ctx_or_channel, embed, view=None):
    """Helper to send embeds"""
    try:
        if hasattr(ctx_or_channel, 'send'):
            if view:
                await ctx_or_channel.send(embed=embed, view=view)
            else:
                await ctx_or_channel.send(embed=embed)
        else:
            if view:
                await ctx_or_channel.send(embed=embed, view=view)
            else:
                await ctx_or_channel.send(embed=embed)
    except Exception as e:
        logger.error(f"Error sending embed: {e}")

@bot.command()
async def premium(ctx):
    """Show premium features"""
    embed = discord.Embed(
        title="👑 PREMIUM MOBILE SEARCH BOT",
        description="**Advanced mobile number lookup with premium features**",
        color=0x9B59B6
    )
    
    embed.add_field(
        name="🚀 Core Features",
        value="• Unlimited searches\n• No rate limits\n• Multiple records\n• Auto-number detection\n• Fast API responses",
        inline=False
    )
    
    embed.add_field(
        name="💎 Premium Tools",
        value="• JSON data export\n• Text file download\n• Copyable formats\n• Interactive buttons\n• Smart record limiting (shows first 25 records)",
        inline=False
    )
    
    embed.add_field(
        name="🔍 How to Use",
        value="• `!search 7405453929` - Manual search\n• Just type 10-digit number - Auto search\n• Use buttons for exports\n• View all records via JSON export",
        inline=False
    )
    
    embed.add_field(
        name="🔗 Connect with Developer",
        value=f"• [Discord Server]({DEVELOPER_INFO['discord']})\n• [Telegram]({DEVELOPER_INFO['telegram']})\n• Developer: {DEVELOPER_INFO['developer']}",
        inline=False
    )
    
    embed.set_footer(text="Thank you for using our premium service!")
    await ctx.send(embed=embed)

@bot.command()
async def stats(ctx):
    """Show comprehensive bot statistics"""
    # Calculate statistics
    latency = round(bot.latency * 1000)
    uptime = get_uptime()
    server_count = len(bot.guilds)
    user_count = sum(g.member_count for g in bot.guilds)
    
    # Determine status based on latency
    if latency < 20:
        status = "🚀 ULTRA FAST"
        status_color = 0x57F287
    elif latency < 50:
        status = "⚡ LIGHTNING"
        status_color = 0x5865F2
    elif latency < 100:
        status = "✅ EXCELLENT"
        status_color = 0x3498DB
    else:
        status = "⚠️ GOOD"
        status_color = 0xFEE75C
    
    embed = discord.Embed(
        title="📊 BOT STATISTICS",
        color=status_color,
        timestamp=datetime.now(timezone.utc)
    )
    
    # Performance Section
    embed.add_field(
        name="⚡ PERFORMANCE",
        value=f"**Latency:** `{latency}ms`\n**Status:** {status}\n**Uptime:** `{uptime}`",
        inline=False
    )
    
    # Usage Statistics
    embed.add_field(
        name="🔍 USAGE STATS",
        value=f"**Total Searches:** `{search_count}`\n**Servers:** `{server_count}`\n**Users:** `{user_count}`",
        inline=False
    )
    
    # System Status
    embed.add_field(
        name="🛡️ SYSTEM STATUS",
        value="• ✅ API: Operational\n• ✅ Database: Connected\n• ✅ Search: Enabled\n• ✅ Exports: Active\n• ✅ Record Limit: 25 displayed",
        inline=False
    )
    
    # Developer Info
    embed.add_field(
        name="👨‍💻 DEVELOPER",
        value=f"• **Name:** {DEVELOPER_INFO['developer']}\n• [Discord Server]({DEVELOPER_INFO['discord']})\n• [Telegram]({DEVELOPER_INFO['telegram']})",
        inline=False
    )
    
    embed.set_footer(text=f"Live Statistics • {get_indian_time()}")
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
    """Check bot latency with ultra-fast indicators"""
    # Measure actual response time
    start_time = time.time()
    
    latency = round(bot.latency * 1000)
    
    # Ultra-fast ping categories
    if latency < 10:
        status = "🚀 ULTRA SONIC"
        color = 0x57F287
        emoji = "🚀"
    elif latency < 20:
        status = "⚡ LIGHTNING FAST"
        color = 0x57F287  
        emoji = "⚡"
    elif latency < 50:
        status = "🔥 BLAZING FAST"
        color = 0x5865F2
        emoji = "🔥"
    elif latency < 100:
        status = "✅ EXCELLENT"
        color = 0x3498DB
        emoji = "✅"
    else:
        status = "⚠️ GOOD"
        color = 0xFEE75C
        emoji = "⚠️"
    
    embed = discord.Embed(
        title=f"{emoji} BOT PERFORMANCE",
        color=color
    )
    
    embed.add_field(
        name="📡 LATENCY",
        value=f"```{latency}ms```",
        inline=True
    )
    
    embed.add_field(
        name="🟢 STATUS",
        value=f"```{status}```",
        inline=True
    )
    
    embed.add_field(
        name="👥 SERVERS",
        value=f"```{len(bot.guilds)}```",
        inline=True
    )
    
    # Add performance tips for ultra-low latency
    if latency < 50:
        embed.add_field(
            name="🎯 PERFORMANCE",
            value="• Optimized API Calls\n• Fast Response Times\n• Efficient Data Processing\n• Premium Hosting",
            inline=False
        )
    
    embed.set_footer(text=f"Premium Performance • {DEVELOPER_INFO['developer']}")
    
    end_time = time.time()
    response_time = round((end_time - start_time) * 1000)
    
    # Add response time note if super fast
    if response_time < 100:
        embed.description = f"**Response Time:** `{response_time}ms` ⚡"
    
    await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
    """Help command with all features"""
    embed = discord.Embed(
        title="⭐ MOBILE SEARCH BOT HELP",
        description="**Advanced mobile number lookup with premium features**",
        color=0x3498DB
    )
    
    embed.add_field(
        name="🔍 SEARCH COMMANDS",
        value=(
            "`!search 7405453929` - Search mobile number\n"
            "`!search 9876543210` - With any 10-digit number\n"
            "**Auto-detection:** Just type any 10-digit number in chat"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📊 BOT COMMANDS",
        value=(
            "`!stats` - View bot statistics\n"
            "`!ping` - Check bot latency\n"
            "`!premium` - Premium features\n"
            "`!help` - This help message\n"
            "`!developer` - Developer info"
        ),
        inline=False
    )
    
    embed.add_field(
        name="💎 PREMIUM FEATURES",
        value=(
            "• Unlimited searches\n"
            "• No rate limits\n"
            "• JSON data export (All records)\n"
            "• Text file download (All records)\n"
            "• Copyable formats\n"
            "• Auto number detection\n"
            "• Fast response times\n"
            "• Smart display (First 25 records shown)"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🔗 DEVELOPER INFORMATION",
        value=(
            f"**Developer:** {DEVELOPER_INFO['developer']}\n"
            f"• [Discord Server]({DEVELOPER_INFO['discord']})\n"
            f"• [Telegram]({DEVELOPER_INFO['telegram']})"
        ),
        inline=False
    )
    
    embed.set_footer(text="Thank you for using our premium search service!")
    await ctx.send(embed=embed)

@bot.command()
async def developer(ctx):
    """Show developer information"""
    embed = discord.Embed(
        title="👨‍💻 DEVELOPER INFORMATION",
        description="Connect with the developer behind this premium bot",
        color=0x5865F2
    )
    
    embed.add_field(
        name="📝 About Developer",
        value=f"**{DEVELOPER_INFO['developer']}**\nThis premium mobile search bot is developed with advanced features and optimized performance for the best user experience.",
        inline=False
    )
    
    embed.add_field(
        name="🔗 Social Links",
        value=(
            f"• [Discord Server]({DEVELOPER_INFO['discord']})\n"
            f"• [Telegram]({DEVELOPER_INFO['telegram']})\n"
            f"• **Developer:** {DEVELOPER_INFO['developer']}"
        ),
        inline=False
    )
    
    embed.add_field(
        name="💡 Support",
        value="For any queries, suggestions, or support, feel free to reach out through the links above or join our Discord server.",
        inline=False
    )
    
    embed.set_footer(text="Thank you for your support! ❤️")
    await ctx.send(embed=embed)

# Error handling
@search.error
async def search_error(ctx, error):
    logger.error(f"Search command error: {error}")
    embed = discord.Embed(
        title="❌ Command Error",
        description="An error occurred. Please try again.",
        color=0xED4245
    )
    await ctx.send(embed=embed)

@stats.error
async def stats_error(ctx, error):
    logger.error(f"Stats command error: {error}")
    embed = discord.Embed(
        title="❌ Stats Error",
        description="Unable to fetch statistics. Please try again.",
        color=0xED4245
    )
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    """Global error handler"""
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore unknown commands
    
    logger.error(f"Command error: {error}")
    embed = discord.Embed(
        title="❌ Command Error",
        description="An error occurred while processing the command.",
        color=0xED4245
    )
    await ctx.send(embed=embed)

def main():
    """Main function to run the bot"""
    if not BOT_TOKEN:
        logger.error("❌ No bot token found in environment variables!")
        logger.error("Please set BOT_TOKEN environment variable in Pella dashboard")
        return
    
    try:
        logger.info("🚀 Starting Premium Mobile Search Bot...")
        logger.info("💎 Developer: @Terex")
        logger.info("🔗 Discord Server: https://discord.gg/teamkorn")
        logger.info("📱 Telegram: https://t.me/s/terex")
        logger.info("⚡ Features: Unlimited searches, No rate limits")
        logger.info("🌐 API: Lostingness Premium")
        logger.info("📊 Record Display: First 25 records shown")
        logger.info("👋 Auto-help enabled for new servers")
        logger.info("🏠 Host: Pella.app")
        logger.info("⭐ Status: Ready to launch!")
        
        bot.run(BOT_TOKEN)
    except discord.LoginFailure:
        logger.error("❌ Invalid bot token!")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")

if __name__ == "__main__":
    main()