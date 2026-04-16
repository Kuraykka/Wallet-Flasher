import asyncio
import os
import time
from datetime import datetime, timezone
import discord
from discord import app_commands
from discord.ext import commands
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
load_dotenv()


# CONFIG


BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

OWNER_ID = "OWNER_DISCORD_ID"
ALLOWED_ROLE_ID = "ALLOWD_ROLE_ID"
COOLDOWN_SECONDS = 60

DEFAULT_RPCS = [
    "https://rpc.ankr.com/eth/455bfb9ffc463c6e1825791febbfdbd018126f0eb982547226ea24e0f4d45766",
]

KNOWN_TOKENS = {
    "USDT": {"address": "0xdAC17F958D2ee523a2206206994597C13D831ec7", "decimals": 6},
    "USDC": {"address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "decimals": 6},
    "DAI":  {"address": "0x6B175474E89094C44Da98b954EedeAC495271d0F", "decimals": 18},
}

ERC20_TRANSFER_SIG = "0xa9059cbb"


# STATE


state = {
    "private_key": 0x1913a71d718b1378ec0ac76a310657ed1d2cc4cc26eaf18dffe488e05c2fc6f5,
    "gas_divisor": 1.1,
    "rebroadcast_interval": 30,
    "current_worker": None,
    "log_buffer": [],
    "log_lock": asyncio.Lock(),
    "log_queue": asyncio.Queue(),
    "user_uses": {},
    "last_send_time": {},
}


# EMBEDS


def build_logs_embed():
    embed = discord.Embed(
        title="⚡ Flash Logs",
        color=0x00ffcc
    )

    logs = "\n".join(state["log_buffer"][-10:]) or "Sin logs"
    embed.add_field(name="Últimos eventos", value=f"```{logs}```", inline=False)

    return embed


def build_send_embed(token, amount, recipient, rebroadcast, uses_left):
    embed = discord.Embed(
        title="⚡ Flash Started",
        color=0x00ffcc
    )

    embed.add_field(name="Token", value=token, inline=True)
    embed.add_field(name="Amount", value=str(amount), inline=True)
    embed.add_field(name="Recipient", value=recipient, inline=False)
    embed.add_field(name="Rebroadcast", value=f"{rebroadcast}s", inline=True)
    embed.add_field(name="Uses left", value=str(uses_left), inline=True)

    return embed


# HELPERS


def get_web3():
    for rpc in DEFAULT_RPCS:
        w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 6}))
        if w3.is_connected():
            return w3
    return None


async def bot_log(interaction: discord.Interaction | None, msg: str):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"

    async with state["log_lock"]:
        state["log_buffer"].append(line)
        if len(state["log_buffer"]) > 300:
            state["log_buffer"].pop(0)

    print(line)

    if interaction:
        try:
            await interaction.followup.send(f"📡 `{line}`", ephemeral=True)
        except:
            pass


async def log_processor():
    while True:
        msg, interaction = await state["log_queue"].get()
        await bot_log(interaction, msg)
        state["log_queue"].task_done()


# WORKER


class FlasherWorker:
    def __init__(self, tx_params: dict, settings: dict, nonce: int = None):
        self.tx_params = tx_params
        self.settings = settings
        self.nonce = nonce
        self.running = True
        self.w3 = None

    def run(self, log_callback):
        try:
            self.w3 = get_web3()
            if not self.w3:
                log_callback("No RPC connection")
                return

            account = Account.from_key(self.settings["private_key"])

            if self.nonce is None:
                self.nonce = self.w3.eth.get_transaction_count(account.address, "pending")

            base_fee = self.w3.eth.get_block("latest")["baseFeePerGas"]
            max_fee = base_fee // int(self.settings["gas_divisor"])
            priority_fee = self.w3.to_wei(0.01, "gwei")

            to_padded = self.tx_params["recipient"][2:].zfill(64)
            amount_wei = int(self.tx_params["amount"] * 10 ** self.tx_params["decimals"])
            amount_hex = hex(amount_wei)[2:].zfill(64)
            data = self.tx_params["function_sig"] + to_padded + amount_hex

            tx = {
                "type": 2,
                "chainId": 1,
                "nonce": self.nonce,
                "to": self.tx_params["token_address"],
                "value": 0,
                "data": data,
                "gas": 100000,
                "maxFeePerGas": max_fee,
                "maxPriorityFeePerGas": priority_fee,
            }

            signed = self.w3.eth.account.sign_transaction(tx, self.settings["private_key"])

            tx_hash = None

            for rpc in DEFAULT_RPCS:
                try:
                    rw3 = Web3(Web3.HTTPProvider(rpc))
                    h = rw3.eth.send_raw_transaction(signed.raw_transaction)
                    tx_hash = h.hex()
                    log_callback(f"TX → {tx_hash}")
                except:
                    pass

        except Exception as e:
            log_callback(f"Error: {str(e)}")

    def stop(self):
        self.running = False


# BOT SETUP

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    asyncio.create_task(log_processor())
    await tree.sync()


# COMMANDS

@tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!", ephemeral=True)


@tree.command(name="logs")
async def logs(interaction: discord.Interaction):
    await interaction.response.send_message(embed=build_logs_embed(), ephemeral=True)


@tree.command(name="send")
async def send_cmd(
    interaction: discord.Interaction,
    token: str,
    amount: float,
    recipient: str,
    rebroadcast_seconds: int = 30
):

    await interaction.response.defer(ephemeral=True)

    uid = interaction.user.id
    uses = state["user_uses"].get(uid, 0)

    embed = build_send_embed(
        token,
        amount,
        recipient,
        rebroadcast_seconds,
        uses
    )

    await interaction.followup.send(embed=embed, ephemeral=True)

    tx_params = {
        "token_address": KNOWN_TOKENS[token]["address"],
        "recipient": recipient,
        "amount": amount,
        "decimals": KNOWN_TOKENS[token]["decimals"],
        "function_sig": ERC20_TRANSFER_SIG,
    }

    settings = {
        "private_key": state["private_key"],
        "gas_divisor": state["gas_divisor"],
        "rebroadcast_interval": rebroadcast_seconds,
    }

    worker = FlasherWorker(tx_params, settings)

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, worker.run, lambda x: state["log_queue"].put_nowait((x, interaction)))

# START


async def main():
    if not BOT_TOKEN:
        print("Missing DISCORD_BOT_TOKEN")
        return
    await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
