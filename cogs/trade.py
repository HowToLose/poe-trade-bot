from discord.ext import commands
from discord_components import DiscordComponents, ComponentsBot, Button, SelectOption, Select
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


class Trade(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
            f'{os.getenv("POE_API_BASE")}/trade/fetch/{str.join(",", search_result["result"][:10])}?query={search_result["id"]}', headers=headers)
        items = r.json()["result"]

        selection = await ctx.send("Select", components=[
            Select(
                placeholder="Select a item.",
                options=[
                    SelectOption(label=f'{o["item"]["name"]} {o["item"]["typeLine"]} : {o["listing"]["price"]["amount"]:>10.1f} {o["listing"]["price"]["currency"]}', value=o["item"]["id"]) for o in items
                ]
            )
        ])

        try:
            select_interaction = await self.bot.wait_for("select_option")
            target_item = next((x for x in items if x["id"] == select_interaction.values[0]), None)
            details = base64.b64decode(target_item["item"]["extended"]["text"])
            details = details.decode('utf-8')[:-1]
            details = f'{details}\n--------\n價格： {target_item["listing"]["price"]["amount"]:.1f} {target_item["listing"]["price"]["currency"]}\n--------\n{target_item["listing"]["whisper"]}'
            await select_interaction.send(content=details, ephemeral=False)
            await selection.delete()

        except:
            await ctx.send("Something wrong.")


def setup(bot):
    bot.add_cog(Trade(bot))
