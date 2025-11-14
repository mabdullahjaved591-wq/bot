import os
import discord
from discord.ext import commands
import google.generativeai as genai
from flask import Flask
from threading import Thread

print("🔧 Starting Discord AI Bot...")

# Get environment variables from Replit Secrets
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

print(f"🔑 Token check: {'✅ Found' if DISCORD_TOKEN else '❌ Missing'}")

if not DISCORD_TOKEN:
    print("❌ ERROR: DISCORD_BOT_TOKEN not found in Secrets!")
    print("💡 Please add DISCORD_BOT_TOKEN to Replit Secrets")
    exit()

# Initialize Gemini AI
model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        print("✅ Gemini AI configured successfully!")
    except Exception as e:
        print(f"❌ Gemini setup failed: {e}")
        model = None
else:
    print("⚠️  No Gemini API key - AI features disabled")

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ===== WEB SERVER FOR KEEP-ALIVE =====
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
    <head>
        <title>Discord Bot Status</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { 
                font-family: Arial, sans-serif; 
                text-align: center; 
                padding: 50px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                margin: 0;
            }
            .container {
                background: rgba(255,255,255,0.1);
                padding: 30px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
                max-width: 600px;
                margin: 0 auto;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }
            code {
                background: rgba(0,0,0,0.3);
                padding: 10px;
                border-radius: 5px;
                display: block;
                margin: 10px 0;
                word-break: break-all;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Discord Bot is Online!</h1>
            <p><strong>Status:</strong> ✅ Running</p>
            <p><strong>URL for UptimeRobot:</strong></p>
            <code>https://bot.abdullahjavedi1.repl.co</code>
            <p><em>Bot will stay online 24/7 with UptimeRobot</em></p>
            <p style="font-size: 12px; opacity: 0.8;">Server time: <span id="time"></span></p>
        </div>
        <script>
            document.getElementById('time').textContent = new Date().toLocaleString();
        </script>
    </body>
    </html>
    """

# Get the port from Replit environment or use default
port = int(os.environ.get("PORT", 5000))

def run_web_server():
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    server = Thread(target=run_web_server)
    server.daemon = True
    server.start()
    print(f"✅ Web server started on port {port}")

class AIAssistant:
    def ask_ai(self, question):
        if model is None:
            return "🤖 AI service is currently unavailable. Please check the API configuration."

        try:
            prompt = f"""You are a helpful AI assistant in a Discord server. A user asked: {question}

Provide a helpful, conversational response. Be knowledgeable but friendly. Keep your response under 1500 characters."""

            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"🔄 I'm having trouble thinking right now. Error: {str(e)}"

assistant = AIAssistant()

def split_message(message, max_length=2000):
    """Split long messages into chunks under Discord's limit"""
    if len(message) <= max_length:
        return [message]

    chunks = []
    while len(message) > max_length:
        # Find the last space within the limit
        split_index = message.rfind(' ', 0, max_length)
        if split_index == -1:
            split_index = max_length

        chunks.append(message[:split_index])
        message = message[split_index:].strip()

    if message:
        chunks.append(message)

    return chunks

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is now online!')
    print(f'📊 Connected to {len(bot.guilds)} servers')

    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening,
        name="!ask or mention me"
    ))

@bot.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author == bot.user:
        return

    # Check if bot is mentioned
    if bot.user in message.mentions:
        # Remove mentions from the message
        content = message.content
        for mention in message.mentions:
            content = content.replace(f'<@{mention.id}>', '').replace(f'<@!{mention.id}>', '')

        question = content.strip()

        if question:
            async with message.channel.typing():
                response = assistant.ask_ai(question)
                # Split long responses
                chunks = split_message(response)
                for chunk in chunks:
                    await message.reply(chunk)
        else:
            await message.reply("Hello! How can I help you today?")

    # Process commands
    await bot.process_commands(message)

@bot.command()
async def ask(ctx, *, question):
    """Ask the AI a question"""
    async with ctx.typing():
        response = assistant.ask_ai(question)
        # Split long responses
        chunks = split_message(response)
        for i, chunk in enumerate(chunks):
            if i == 0:
                await ctx.send(f"**Answer:** {chunk}")
            else:
                await ctx.send(chunk)

@bot.command()
async def ping(ctx):
    """Check bot latency"""
    latency = round(bot.latency * 1000)
    await ctx.send(f'🏓 Pong! {latency}ms')

@bot.command()
async def helpme(ctx):
    """Show help message"""
    help_text = """
**🤖 AI Bot Commands:**
`!ask <question>` - Ask the AI a question
`!ping` - Check bot latency  
`!helpme` - Show this message

**Or mention me with your question!**
"""
    await ctx.send(help_text)

# Start web server for keep-alive
keep_alive()

# Run the bot with error handling
try:
    print("🚀 Starting Discord bot connection...")
    bot.run(DISCORD_TOKEN)
except Exception as e:
    print(f"❌ Bot failed to start: {e}")
    print(f"🔧 Error type: {type(e).__name__}")
