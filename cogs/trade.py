from discord.ext import commands
import requests
import json
import os
import re


class searchOptions():
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

        config = searchOptions(req.text)

        headers = {
            'Content-Type': 'application/json'
        }

        r = requests.post(
            f'{os.getenv("POE_API_BASE")}/trade/search/{config.get_league()}', headers=headers, data=config.get_config())
        search_result = r.json()

        r = requests.get(
            f'{os.getenv("POE_API_BASE")}/trade/fetch/{str.join(",", search_result["result"][:5])}?query={search_result["id"]}', headers=headers)
        items = r.json()["result"]

        names = [f'{o["item"]["name"]} {o["item"]["typeLine"]} : {o["listing"]["price"]["amount"]:>10.1f} {o["listing"]["price"]["currency"]}' for o in items]

        await ctx.send(str.join('\n', names))


def setup(bot):
    bot.add_cog(Trade(bot))
