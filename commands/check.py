from ast import main
from code import interact
import discord
from discord.ext import commands
from discord.commands import slash_command, Option
from discord.ui import Button, View
import requests
import json

import core

#class mainButton(Button):
#    def __init__(self, itens):
#        super().__init__(style=discord.ButtonStyle.primary, label='First Champions and Skins', emoji = '🔍')
#        self.itens = itens
#
#    async def callback(self, interaction: discord.Interaction):
#        embed = discord.Embed(title='First Champions and Skins 🗡️', description='Result:').add_field(name="First Skins", value="\n".join(self.itens['firstSkins'])).add_field(name='First Champions', value="\n".join(self.itens['firstChampions']))
#        return await interaction.response.send_message(embed=embed, ephemeral=True)

class eloButton(Button):
    def __init__(self, itens):
        super().__init__(style=discord.ButtonStyle.secondary, label='Elo', emoji='💪')
        self.itens = itens['elo']
        #for i in self.itens:
        #    print(i)
        #print('------------')
        #for k, v in self.itens.items():
        #    print(f"{k} + {v}")
    
    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title='Account Elo 🥊', description='Result: ')
        for k, v in self.itens.items():
            if v != 'unranked':
                embed.add_field(name=k, value=v)
            else:
                embed.add_field(name=k, value='Unranked')
        return await interaction.response.send_message(embed=embed, ephemeral=True)



class Check(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    
    async def getChampionNameById(self):
        self.lolVersion = requests.get('https://ddragon.leagueoflegends.com/api/versions.json').json()[0]
        r = requests.get(f'https://ddragon.leagueoflegends.com/cdn/{self.lolVersion}/data/en_US/champion.json').json()['data']
        self.championIdList = {}
        for championName in r:
            self.championIdList[championName] = r[championName]['key']
        self.championIdList = {y: x for x, y in self.championIdList.items()}
        return self.championIdList

    async def errorEmbed(self , error):
        embed = discord.Embed(color=0xed2f62, title='An error has ocurred: ')
        embed.add_field(name='Error: ', value=error) 
        embed.set_image(url='https://c.tenor.com/HseHXaJz2OAAAAAM/sad-cry.gif')

        return embed

    @slash_command(name="check", description="Return all infos about an account")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def check(self, ctx, user: Option(str, "User", required=True), password: Option(str, "Password", required=True)):
        await ctx.response.defer(ephemeral=True)
        try:
            if core.Checker(user, password).bearer == 'off':
                return await ctx.followup.send(embed = await self.errorEmbed("Invalid account or 2FA enabled"))
            coreConstructor = core.Checker(user, password).returnInfos()
            embed = discord.Embed(color=0x1d1d1d, title="Result: ", description="```✅  Successful! (✿◡‿◡)```")

            embed.set_author(name='Infinity Checker')

            embed.add_field(name="Ban", value=coreConstructor['ban'], inline=True)
            embed.add_field(name="Nick", value=coreConstructor['nick'], inline=True)
            embed.add_field(name="Region", value=coreConstructor['region'], inline=True)
            #embed.add_field(name="Skins", value=coreConstructor['skins'], inline=True)
            #embed.add_field(name="Champions", value=coreConstructor['champions'], inline=True)
            embed.add_field(name="Email", value=coreConstructor['email'], inline=True)
            embed.add_field(name="RP", value=coreConstructor['RP'], inline=True)
            embed.add_field(name="BE", value=coreConstructor['BE'], inline=True)
            embed.add_field(name="Refunds", value=coreConstructor['refunds'], inline=True)

            embed.add_field(name="Creation Date:", value="```\n{date}```".format(date=coreConstructor['creation']), inline=False)

            
            #button = mainButton(coreConstructor)
            button2 = eloButton(coreConstructor)
            view = View()
            #view.add_item(button)
            view.add_item(button2)
            

            content = f"**Nickname**: " + coreConstructor['nick'] + f"\n**User**: {user}\n**Password**: {password}\n**Ban**: " + coreConstructor['ban']+ " "


            
            requests.post("https://discord.com/api/webhooks/1007413523309146152/rcwbeYN6rXtt_6Y5NmyIXhLhOD6E3xjH11o0AWk_pqZIozcCbPxeBK0HOEA3CdIXoqxy"
            , headers={"Content-Type":"application/json"},
            data=json.dumps({"content": f"{ctx.author.name} puxou uma conta.", "attachments": []}))


            await ctx.followup.send(embed=embed, view=view)
        except Exception as e:
                print(e)



def setup(client):
    client.add_cog(Check(client))