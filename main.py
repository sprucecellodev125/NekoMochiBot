import discord
from discord import app_commands
from discord.ext import commands, tasks
import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv('TOKEN')
FACTS_CHANNEL_ID = int(os.getenv('FACTS_CHANNEL_ID'))
QUOTES_CHANNEL_ID = int(os.getenv('QUOTES_CHANNEL_ID'))
FACTS_ROLE_ID = int(os.getenv('FACTS_ROLE_ID'))
QUOTES_ROLE_ID = int(os.getenv('QUOTES_ROLE_ID'))
APIKEY = os.getenv('APIKEY')
COUNT_FILE = os.getenv('COUNT_FILE')

bot = commands.Bot(command_prefix="!", intents = discord.Intents.all())

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    send_message.start()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@tasks.loop(minutes=1440)
async def send_message():
    facts_channel = bot.get_channel(FACTS_CHANNEL_ID)
    quotes_channel = bot.get_channel(QUOTES_CHANNEL_ID)

    if facts_channel and quotes_channel:
        try:
            counts = get_api_request_counts()
            counts["facts"] += 1
            counts["quotes"] += 1
            save_api_request_counts(counts)

            fact_fetch = requests.get("https://api.api-ninjas.com/v1/facts", headers={'X-Api-Key': APIKEY})
            quotes_fetch = requests.get("https://api.api-ninjas.com/v1/quotes", headers={'X-Api-Key': APIKEY})

            if fact_fetch.status_code == requests.codes.ok and quotes_fetch.status_code == requests.codes.ok:
                fact_response = json.loads(fact_fetch.text)
                quotes_response = json.loads(quotes_fetch.text)

                await facts_channel.send(f"||<@&{FACTS_ROLE_ID}>|| Fact no. {counts['facts']} - {fact_response[0]['fact']}")
                await quotes_channel.send(f"""{quotes_response[0]['quote']}
<@&{QUOTES_ROLE_ID}> """)
        except Exception as e:
            print(f"An error occurred: {e}")

@bot.tree.command(name="ping", description="Pong!")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="Ping",
        description=f"API Latency: {latency}ms",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

def get_api_request_counts():
    try:
        with open(COUNT_FILE, 'r') as file:
            counts = json.load(file)
            return counts
    except (FileNotFoundError, json.JSONDecodeError):
        return {"facts": 0, "quotes": 0}

def save_api_request_counts(counts):
    with open(COUNT_FILE, 'w') as file:
        json.dump(counts, file)

# Start the bot with the token
bot.run(TOKEN)
