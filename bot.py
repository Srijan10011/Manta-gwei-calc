import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("7201934999:AAGRDXyDTFmVDTu6U3MziCMxxy_R4ELmd4o")
MANTA_RPC_URL = os.getenv("MANTA_RPC_URL", "https://pacific-rpc.manta.network/http")

async def get_manta_gas_price():
    """Fetch current gas price from Manta Pacific network"""
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_gasPrice",
        "params": [],
        "id": 1
    }
    
    try:
        response = requests.post(MANTA_RPC_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Convert hex gas price to gwei
        gas_price_wei = int(data['result'], 16)
        gas_price_gwei = gas_price_wei / 10**9
        return gas_price_gwei
    except Exception as e:
        print(f"Error fetching gas price: {e}")
        return None

async def gwei_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /gwei command"""
    gas_price = await get_manta_gas_price()
    if gas_price is not None:
        message = f"⛽ Current Manta Pacific gas price: {gas_price:.2f} gwei"
    else:
        message = "⚠️ Could not fetch current gas price. Please try again later."
    
    await update.message.reply_text(message)

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handler
    application.add_handler(CommandHandler("gwei", gwei_command))
    
    # Run the bot until Ctrl-C is pressed
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
