import os
import discord
import logging
from typing import List
from pathlib import Path
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands

# define the directories for storage and pictures
storage_dir: Path = Path('/data')
log_dir: Path = Path('/data/logs')
log_file: Path = log_dir / 'bot.log'
picture_dir: Path = Path('/data/pictures')

# create the storage and picture directories if they don't exist yet (usable by docker)
log_dir.mkdir(parents=True, exist_ok=True)
storage_dir.mkdir(parents=True, exist_ok=True)
picture_dir.mkdir(parents=True, exist_ok=True)

# initialize the logger for this bot
logger: logging.Logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler: logging.Handler = logging.FileHandler(filename=log_file, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

load_dotenv()  # load environment variables from ..env file

# initialize the bot using ..env TOKEN environment variable
token: str = os.getenv('TOKEN')
intents: discord.Intents = discord.Intents.all()
bot: commands.Bot = commands.Bot(command_prefix='<', intents=intents, help_command=None)


@bot.tree.context_menu(name="Download Attachment")
@app_commands.allowed_installs(users=True, guilds=False)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def download_images(interaction: discord.Interaction, message: discord.Message) -> None:
    # Log the execution of the command
    logger.info(
        f"Context menu 'Download message' used by {interaction.user.name} in "
        f"{interaction.channel.name if interaction.guild else "DM"}"
    )

    # get the message and its attachments
    attachments: List[discord.Attachment] = message.attachments
    if attachments:
        await interaction.response.send_message(  # noqa
            f"Downloading {len(attachments)} files...",
            ephemeral=True,
        )

    if not attachments:
        await interaction.response.send_message("No attachments found in the message.", ephemeral=True)  # noqa
        return

    msg = await interaction.original_response()
    files_downloaded = 0

    for attachment in attachments:
        filepath = picture_dir / f"{attachment.filename}"

        try:
            await attachment.save(fp=filepath)

            files_downloaded += 1

        except Exception as http_err:
            await interaction.followup.send(
                f"Failed to download {attachment.filename}: {http_err}", ephemeral=True)
            logger.error(f"Failed to download {attachment.filename}: {http_err}")
            continue

        finally:
            await msg.edit(content=f"Downloaded {files_downloaded}/{len(attachments)} files.")


@bot.tree.command(name="download_channel")  # Attachments only
@app_commands.allowed_installs(users=False, guilds=True)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
async def download_channel(interaction: discord.Interaction, channel: discord.TextChannel) -> None:
    await interaction.response.send_message(f"Downloading attachments from {channel.name}...")  # noqa

    msg = await interaction.original_response()

    async for message in channel.history(limit=None):
        attachments = message.attachments
        for attachment in attachments:
            filepath = picture_dir / f"{attachment.filename}"
            try:
                await attachment.save(fp=filepath)
                await msg.edit(content=f"Downloaded {attachment.filename}")

            except Exception as http_err:
                await interaction.followup.send(f"Failed to download {attachment.filename}: {http_err}")
                logger.error(f"Failed to download {attachment.filename}: {http_err}")


@bot.event
async def on_ready() -> None:
    logger.info(f'Logged in as {bot.user.name}')
    try:
        await bot.tree.sync()
        logger.info("Synced bot.tree for all guilds.")
    except Exception as err:
        logger.error(f"Error syncing bot.tree: {err}")


bot.run(token)
