from glob import glob
import discord
from discord.ext import commands
from discord_components import DiscordComponents, ComponentsBot, Button, ButtonStyle, SelectOption, Select
import requests
import base64
import json
import os
import re


class SearchOptions():
    def __init__(self, html) -> None:

        tmp = re.search(r'"league":"([^"]+)"', html)
        tmp = json.loads('{' + tmp.group(0) + '}')

        self.league = tmp["league"]

        tmp = re.search(r'"state":\{(.*?)\},"loggedIn"', html)
        tmp = json.loads('{' + tmp.group(0)[:-11] + '}')

        self.query = tmp["state"]


    def get_config(self):
        return json.dumps({
            "query": self.query,
            "sort": {"price": "asc"}
        })

    def get_league(self):
        return self.league


class Item():
    def __init__(self, details):
        self.id = details["id"]
        self.icon = details["item"]["icon"]
        self.name = details["item"]["name"]
        self.type = details["item"]["typeLine"]
        self.description = base64.b64decode(
            details["item"]["extended"]["text"])
        self.description = self.description.decode('utf-8')[:-1]
        self.whisper = details["listing"]["whisper"]
        self.price = details["listing"]["price"]

    def get_reply_text(self):

        return f'{self.name} {self.type} : {self.price["amount"]:.1f} {self.price["currency"]}'

    async def get_detail_reply(self, interaction):

        description = self.description
        description = description.split('--------\r\n')[1:]
        description = str.join('', description)
        description = description.replace('\r', '\n')

        embed = discord.Embed(
            title=f'{self.name} {self.type}', description=description)
        embed.set_thumbnail(url=self.icon)
        embed.add_field(
            name="價格", value=f'{self.price["amount"]:.1f} {self.price["currency"]}\n', inline=False)
        embed.add_field(name="密語", value=f'{self.whisper}', inline=False)
        await interaction.send(embed=embed)

    def get_button(self):

        return Button(style=ButtonStyle.gray, label=f'{self.get_reply_text()}', custom_id=self.id)

    def get_callback(self):

        return self.get_detail_reply


class Trade(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.items = []

    @commands.command()
    async def search(self, ctx, link):

        req = requests.get(link)

        config = SearchOptions(req.text)

        headers = {
            'Content-Type': 'application/json'
        }

        r = requests.post(
            f'{os.getenv("POE_API_BASE")}/trade/search/{config.get_league()}', headers=headers, data=config.get_config())
        search_result = r.json()

        r = requests.get(
            f'{os.getenv("POE_API_BASE")}/trade/fetch/{str.join(",", search_result["result"][:5])}?query={search_result["id"]}', headers=headers)

        self.items = r.json()["result"]
        self.items = [Item(item) for item in self.items]

        await ctx.send(
            "搜尋的結果如下：",
            components=[
                self.bot.components_manager.add_callback(
                    item.get_button(), item.get_callback()
                ) for item in self.items
            ],
        )

def setup(bot):
    bot.add_cog(Trade(bot))
