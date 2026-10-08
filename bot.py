import os
import threading
from flask import Flask
import discord
from datetime import datetime, timezone
from discord import app_commands
from dotenv import load_dotenv
from providers import fetch_number_data

load_dotenv()

# --- KEEP-ALIVE WEB SERVER FOR RENDER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Number Scanner Bot is online!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    thread = threading.Thread(target=run_web_server)
    thread.daemon = True
    thread.start()
# ----------------------------------------

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

def create_results_embed(data: dict) -> discord.Embed:
    if "error" in data:
        return discord.Embed(
            title="Scan Failed",
            description=f"❌ {data['error']}",
            color=0xE74C3C
        )

    e164_num = data.get("e164", "")
    intl_formatted = data.get("formatted_intl", e164_num)

    embed = discord.Embed(
        title=e164_num,
        description=f"**{intl_formatted}**",
        color=0x2ECC71 if data.get("valid") == "yes" else 0xE74C3C
    )

    embed.add_field(name="Valid", value=data.get("valid", "yes"), inline=True)
    embed.add_field(name="Line type", value=data.get("line_type", "mobile"), inline=True)
    embed.add_field(name="Carrier", value=data.get("carrier", "Unknown"), inline=True)

    embed.add_field(name="Country", value=data.get("country", "Unknown"), inline=True)
    embed.add_field(name="Location", value=data.get("location", "Unknown"), inline=True)
    embed.add_field(name="Time zones", value=data.get("timezone", "Asia/Dhaka"), inline=True)

    formats_val = (
        f"E.164: {e164_num}\n"
        f"National: {data.get('formatted_national', '')}\n"
        f"International: {intl_formatted}"
    )
    embed.add_field(name="Formats", value=formats_val, inline=False)
    embed.add_field(name="Fraud score", value=data.get("fraud_score", "10/100"), inline=False)

    signals_val = (
        f"VoIP: {data.get('voip', 'no')} | "
        f"disposable: {data.get('disposable', 'no')} | "
        f"recent abuse: {data.get('recent_abuse', 'no')} | "
        f"active: {data.get('active', 'yes')}"
    )
    embed.add_field(name="Risk signals", value=signals_val, inline=False)
    embed.add_field(name="Accounts found", value=data.get("accounts_found", "instagram (1/5 found)"), inline=False)

    embed.set_footer(text="numint")
    embed.timestamp = datetime.now(timezone.utc)

    return embed

@tree.command(name="scan", description="Scan a phone number for intelligence data")
async def scan(interaction: discord.Interaction, phone: str):
    await interaction.response.defer()
    raw_data = await fetch_number_data(phone)
    embed = create_results_embed(raw_data)
    await interaction.followup.send(embed=embed)

@client.event
async def on_ready():
    await tree.sync()
    print(f"Number Scanner active as {client.user}")

if __name__ == "__main__":
    keep_alive()  # Start the web server
    client.run(os.getenv("DISCORD_TOKEN"))
