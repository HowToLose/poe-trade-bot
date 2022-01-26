import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

# global settings
bot = commands.Bot(command_prefix=commands.when_mentioned, description='poe trade bot!')
cogs_folder = 'cogs'


@bot.event
async def on_ready():
    print('Logged in as')
    print(f'username: {bot.user.name}')
    print(f'id: {bot.user.id}')
    print('------' * 5)
    load_cogs()
    print('------' * 5)


def load_cogs():

    for filename in os.listdir(cogs_folder):

        if filename.endswith('.py'):

            extension = filename[:-3]

            try:
                bot.load_extension(f'cogs.{extension}')
                print('Success to load extension {}'.format(extension))
            except Exception as e:
                exc = '{}: {}'.format(type(e).__name__, e)
                print('Failed to load extension {}\n{}'.format(extension, exc))


bot.run(os.getenv("TOKEN"))
