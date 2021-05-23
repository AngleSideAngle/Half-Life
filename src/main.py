import discord
#from discord import guild
#from discord.channel import DMChannel, TextChannel
from discord.errors import HTTPException
from discord.ext import commands
from discord.utils import get

import os

from secrets import token, link
from permissions import perm_check, trusted
from settings import color, playing, command_prefix, comment_prefix

intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix = command_prefix, intents = intents)

#activates all cogs on startup
for file in os.listdir("./src/cogs"):
    if file.endswith(".py"):
        client.load_extension(f"cogs.{file[:-3]}")

@client.event
async def on_ready():
    game = discord.Game(playing)
    await client.change_presence(activity = game)
    print(f"logged in as: {client.user}\ndisplaying the status: {game}")

@client.event
async def on_guild_join(guild):
    print(f"Joined {guild.name}")

@client.command()
async def test(ctx, user):
    test = commands.MemberConverter()
    member = await test.convert(ctx = ctx, argument = user)
    await ctx.send(member.mention)

@client.event
async def on_command_error(ctx, error):
    title = None
    msg = None

    if isinstance(error, commands.CommandNotFound):
        title = "Command Not Found"
        msg = f"the command \"{ctx.message.content}\" does not exist"

    if isinstance(error, commands.BotMissingPermissions):
        title = "Missing Permissions"
        msg = f"{client.user.name} lacks the required permissions"

    if isinstance(error, commands.MissingRequiredArgument):
        title = "Missing Required Arguments"
        msg = f"you did not input the command's arguments correctly, refer to {client.command_prefix}help for information on how to use the command"

    if isinstance(error, commands.CheckFailure):
        title = "Check Failure"
        msg = "you do not have the required permissions to run this command"
    
    if msg and title:
        embed = discord.Embed(title = title, color = color, description = msg)
        embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
        await ctx.send(embed = embed)
    else:
        print(error)

@client.command()
async def invite(ctx):
    await ctx.send(link)

@client.command()
@perm_check()
async def status(ctx, *, status = None):
    if status:
        game = discord.Game(status)
        await client.change_presence(activity = game)
    else:
        await client.change_presence(activity = None)

@client.command()
@perm_check()
async def nick(ctx, guild : discord.Guild, *, bot_nick):
    
    #me = get(guild.members, id = client.user.id)
    
    await guild.me.edit(nick = bot_nick)

@client.command()
@perm_check()
async def reload(ctx):
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            client.reload_extension(f"cogs.{file[:-3]}")
    await ctx.send("reloaded cogs")

@client.event
async def on_message(message):
    # runs ctx commands
    await client.process_commands(message)

    if message.author == client.user or message.content.startswith(client.command_prefix) or message.content.startswith(comment_prefix) or message.webhook_id:
        return

    connections = client.cogs["messaging"].connections
    # sends outgoing messages
    if message.channel in connections.keys():
        if not connections[message.channel]:
            return
        try:
            await connections[message.channel].send(message.content)
        except discord.Forbidden:
            title = "Missing Permissions"
            msg = f"{client.user.name} lacks the required permissions"
            embed = discord.Embed(title = title, color = color, description = msg)
            embed.set_author(name = message.author, icon_url = message.author.avatar_url)
            await message.channel.send(embed = embed)

    # sends incoming messages
    if message.channel in connections.values():
        for pair in connections:
            if connections[pair] == message.channel:
                await pair.send(f"`{message.author.name}` {message.content}")

client.run(token)