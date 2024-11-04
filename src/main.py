import os
import discord
from discord import app_commands
from discord.ext import commands
from typing import List, Optional
import logging
from pathlib import Path
from dotenv import load_dotenv

# initialize the logger for this bot
logger: logging.Logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

storage_dir = Path('/data')
picture_dir = Path('/data/pictures')

picture_dir.mkdir(parents=True, exist_ok=True)

load_dotenv()  # load environment variables from .env file

# initialize the bot using .env TOKEN environment variable
token = os.getenv('TOKEN')
intents: discord.Intents = discord.Intents.all()
bot: commands.Bot = commands.Bot(command_prefix='<', intents=intents, help_command=None)


@bot.tree.context_menu(name="Download Images")
@app_commands.allowed_installs(users=True, guilds=False)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def download_images(interaction: discord.Interaction, message: discord.Message) -> None:
    # Log the execution of the command
    logger.info(f"Context menu 'Download images' used by {interaction.user.name} in {interaction.channel.name}")

    # get the message and its attachments
    attachments: List[discord.Attachment] = message.attachments
    if attachments:
        await interaction.response.send_message(  # noqa
            f"Downloading {len(attachments)} images...",
            ephemeral=True,
        )

    if not attachments:
        await interaction.response.send_message("No attachments found in the message.", ephemeral=True)  # noqa
        return

    msg = await interaction.original_response()
    files_downloaded = 0

    for attachment in attachments:
        filepath = picture_dir / f"{message.author.name}_{attachment.filename}"
        logger.info(f"Files will be saved to: {picture_dir}")


        try:
            await attachment.save(fp=filepath)

            files_downloaded += 1

        except Exception as http_err:
            await interaction.followup.send(
                f"Failed to download {attachment.filename}: {http_err}", ephemeral=True)
            logger.error(f"Failed to download {attachment.filename}: {http_err}")
            continue

        finally:
            await msg.edit(content=f"Downloaded {files_downloaded}/{len(attachments)} images.")


@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name}')
    try:
        await bot.tree.sync()
        logger.info("Synced bot.tree for all guilds.")
    except Exception as err:
        logger.error(f"Error syncing bot.tree: {err}")


bot.run(token)
