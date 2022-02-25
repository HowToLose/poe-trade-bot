import discord
from discord_components import DiscordComponents
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

# global settings
bot = commands.Bot(command_prefix=commands.when_mentioned, description='poe trade bot!')
DiscordComponents(bot)
cogs_folder = 'cogs'


@bot.event
async def on_ready():
    print('Logged in as')
    print(f'username: {bot.user.name}')
    print(f'id: {bot.user.id}')
    print('------' * 5)
    load_cogs()
    print('------' * 5)

@bot.event
async def on_command_error(ctx, error):
    await ctx.send('嘔幹！你在亂打三小拉！\n可以使用 help 指令來查看可用指令。')
    await ctx.send(f"錯誤訊息：\n{error}")

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
