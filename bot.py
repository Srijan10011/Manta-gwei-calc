import requests
from decimal import Decimal, getcontext
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# 🔐 Your Telegram Bot Token here
BOT_TOKEN = "Your bot token"

# Decimal precision
getcontext().prec = 20

# RPC endpoints for Manta Pacific
RPC_ENDPOINTS = [
    "https://manta-pacific.rpc.thirdweb.com",
    "https://manta-pacific.blockpi.network/v1/rpc/public",
    "https://1rpc.io/manta"
]

MAX_TX_COUNT = 50


async def get_minimum_gwei_from_transactions():
    """Fetch minimum gas price from latest 50 transactions (ignoring zero gas price)"""
    for endpoint in RPC_ENDPOINTS:
        try:
            # Get latest block number
            block_num_response = requests.post(
                endpoint,
                json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1},
                timeout=5,
            )
            latest_block = int(block_num_response.json()['result'], 16)

            gas_prices = []
            checked_blocks = 0

            # Loop backward through blocks until 50 gas prices collected
            while len(gas_prices) < MAX_TX_COUNT and latest_block - checked_blocks >= 0:
                block_number = latest_block - checked_blocks

                block_response = requests.post(
                    endpoint,
                    json={"jsonrpc": "2.0", "method": "eth_getBlockByNumber",
                          "params": [hex(block_number), True], "id": 1},
                    timeout=5,
                )
                block_data = block_response.json().get('result')

                if block_data and block_data.get('transactions'):
                    for tx in block_data['transactions']:
                        if 'gasPrice' in tx:
                            gas_price_wei = Decimal(int(tx['gasPrice'], 16))
                            if gas_price_wei == 0:
                                continue  # skip zero gas price tx
                            gas_price_gwei = gas_price_wei / Decimal(10**9)
                            gas_prices.append(gas_price_gwei)

                            if len(gas_prices) >= MAX_TX_COUNT:
                                break

                checked_blocks += 1

            if gas_prices:
                return min(gas_prices)

        except Exception as e:
            print(f"[ERROR] RPC {endpoint} failed: {e}")
            continue

    return None


async def gwei_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Scanning latest 50 transactions for minimum gas price...")

    min_gwei = await get_minimum_gwei_from_transactions()

    if min_gwei is not None:
        # Format with 10 decimals, preserving trailing zeros as needed
        formatted_price = f"{min_gwei:.10f}"

        message = (
            f"⛽ Minimum Gas Price (10 decimals):\n"
            f"┌─────────────────────────────┐\n"
            f"│ {formatted_price.ljust(15)} Gwei │\n"
            f"└─────────────────────────────┘\n\n"
            f"📊 Based on latest 50 transactions\n"
            f"🔢 10-decimal precision"
        )
    else:
        message = "⚠️ Could not fetch gas data. All RPC endpoints failed."

    await update.message.reply_text(message)


def main():
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN is not set.")
        return

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("gwei", gwei_command))

    print("🤖 Manta Gas Tracker Bot is running...")
    application.run_polling()


if __name__ == '__main__':
    main()
