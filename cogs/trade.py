from asyncio import tasks, sleep
from glob import glob
from time import sleep
import discord
from discord.ext import tasks, commands
from discord_components import DiscordComponents, ComponentsBot, Button, ButtonStyle, SelectOption, Select
import requests
import base64
import json
import os
import re
from uuid import uuid4


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


class Task():
    def __init__(self, bot, ctx, user, name, link):
        self.id = str(uuid4())
        self.bot = bot
        self.ctx = ctx
        self.user = user
        self.name = name
        self.link = link
        self.reply = None

        self.batch_size = 5

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_user(self):
        return self.user

    def get_items(self):

        req = requests.get(self.link)

        config = SearchOptions(req.text)

        headers = {
            'Content-Type': 'application/json'
        }

        try:

            r = requests.post(
                f'{os.getenv("POE_API_BASE")}/trade/search/{config.get_league()}', headers=headers, data=config.get_config())
            search_result = r.json()

        except:
            
            return [], "機器人在搜尋物品時出了一些問題。"

        if (search_result["total"] == 0):

            return [], None

        try:

            r = requests.get(
                f'{os.getenv("POE_API_BASE")}/trade/fetch/{str.join(",", search_result["result"][:self.batch_size])}?query={search_result["id"]}', headers=headers)

            items = r.json()

            return [Item(item) for item in items["result"]], None
        
        except:

            return [], "機器人在取得物品資訊的時候出了些問題。"
        

    async def run(self):
        if (self.reply is not None):
            try:

                await self.reply.delete()

            except:

                await self.ctx.send("刪除前次結果發生錯誤。")

        items, err =  self.get_items()

        if err is not None:

            self.reply = await self.ctx.send(f"{self.user.mention} 搜尋 {self.name} 時 {err}。")

        elif (len(items) == 0):

            self.reply = await self.ctx.send(f"{self.user.mention} {self.name} 的搜尋沒有結果。")

        else:

            self.reply = await self.ctx.send(
                f"{self.user.mention} {self.name} 的搜尋的結果如下：",
                components=[
                    self.bot.components_manager.add_callback(
                        item.get_button(), item.get_callback()
                    ) for item in items
                ],
            )

    def validate(self):

        req = requests.get(self.link)

        try:
            SearchOptions(req.text)
            return True

        except:
            return False


class Trade(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # for search
        self.items = []

        # for task
        self.tasks = []
        self.index = 0
        self.max_tasks = 30

        # for timer
        self.timer.start()

    @commands.command()
    async def search(self, ctx, link):

        new_task = Task(self.bot, ctx, ctx.author, "", link)

        if (new_task.validate()):
            await new_task.run()
        
        else:
            await ctx.send(f"{ctx.author.mention} 你給的連結似乎有點問題。")

    @commands.command()
    async def task(self, ctx, task_name, link):

        new_task = Task(self.bot, ctx, ctx.author, task_name, link)

        if (len(self.tasks) + 1 > self.max_tasks):
            await ctx.send(f"{ctx.author.mention} 目前佇列已滿（上限：{self.max_tasks})，請先刪除部分任務後再新增。")

        elif (new_task.validate()):

            self.tasks.append(Task(self.bot, ctx, ctx.author, task_name, link))
            await ctx.send(f"{ctx.author.mention} 已註冊搜尋： {task_name}。")
        
        else:

            await ctx.send(f"{ctx.author.mention} {task_name} 的註冊出了些問題，你確定你的搜尋條件是這季的嗎？")


        

    @commands.command()
    async def list(self, ctx):

        def get_list():

            components = []

            for task in self.tasks:
                button = Button(style=ButtonStyle.red,
                         label=f'刪除 {task.get_name()} ({task.get_user().name})', custom_id=task.get_id())
                
                async def callback(interaction):

                    for (idx, item) in enumerate(self.tasks):
                        if item.get_id() == interaction.custom_id:
                            del self.tasks[idx]

                    updated_components = get_list()

                    if len(updated_components) == 0:
                        await interaction.edit_origin(
                            "目前佇列中沒有任務。",
                            components = []
                        )
                    else:
                        await interaction.edit_origin(
                            components = updated_components
                        )

                components.append(self.bot.components_manager.add_callback(button, callback))


            # Button to remove list message

            removeBtn = Button(style=ButtonStyle.blue,
                        label=f'關閉此列表', custom_id=str(uuid4()))

            async def removeCb(interaction):
                await interaction.edit_origin(
                    "*此訊息已被刪除。*",
                    components = []
                )

            components.append(self.bot.components_manager.add_callback(removeBtn, removeCb))

            return components

        if len(self.tasks) == 0:
            await ctx.send("目前佇列中沒有任務。")
        else:
            await ctx.send("已註冊的任務如下：", components=get_list())


    @tasks.loop(minutes=1.0)
    async def timer(self):

        self.index = (self.index + 1) % self.max_tasks

        if (len(self.tasks) > 0 and len(self.tasks) > self.index):
            await self.tasks[self.index].run()
            


def setup(bot):
    bot.add_cog(Trade(bot))
