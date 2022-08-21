import discord
import dotenv
import os
from discord.ext import commands

client = discord.Bot()

@client.event
async def on_ready():
    print("sexo")

for file in os.listdir("commands"):
    if file.endswith(".py"):
        try:
            client.load_extension('commands.' + file[:-3])
        except Exception as e:
            print(e)

@client.event
async def on_application_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond(error)

dotenv.load_dotenv()
client.run(os.getenv("TOKEN"))
