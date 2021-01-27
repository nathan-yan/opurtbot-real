import discord
from discord.ext import tasks, commands

import asyncio
import socketio
import threading

import subprocess
import time 
from queue import Queue, Empty

from threading import Thread
from requests import get

import os

import re

import boto3
import utils

ec2 = boto3.client('ec2')

chat_reg = re.compile("\[INFO\] <[^ ]+>")

active_players = set()


class SpinupThread (threading.Thread):
   def __init__(self, ):
      threading.Thread.__init__(self)
      
   def run(self):
      client = Spinup()
      client.run(os.environ['DISCORD_TOKEN'])
    
class ServerThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    
    def run(self):
        run_minecraft([])

class Spinup(discord.Client):
    def __init__(self):
        super().__init__() 

        self.voting = False 
        self.voted = set()
        self.running = False
        self.upsince = 0

        self.voteStarted = 0
        self.voteChannel = None

        self.locked = False

        self.dimensional_rift = None
        self.ip = None

        self.vc = None
        self.sock = None
        self.sock_connected = False 

    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))
        self.dimensional_rift = discord.utils.get(self.get_all_channels(), name = "dimensional-rift")
        self.server_status = discord.utils.get(self.get_all_channels(), name = "server-status")
    
    async def on_message(self, message):
        print(message.author.id, message.channel.name, message.channel.id)

        if message.channel.name == 'dimensional-rift':
            # this is a message sent from minecraft
            if (message.author == client.user) and message.content.startswith("```"):
                return

            await self.sock.emit('discord-chat', {
                "task" : 'message-minecraft',
                "message" : message.content,
                "user" : message.author.nick
            })


        if message.content.startswith('#purge'):
            summary = {}

            num = int(message.content.split(" ")[1])

            if num > 10:
                num = 10
            
            num += 1

            if 'admin' in [r.name for r in message.author.roles]:
                history = await message.channel.history(limit = 100).flatten()
                
                for m in history[:num]:
                    if m.author.display_name not in summary:
                        summary[m.author.display_name] = 1
                    else:
                        summary[m.author.display_name] += 1

                summary_msg = ">>> "
                for n in summary:
                    summary_msg += n + ": " + str(summary[n]) + "\n"

                await message.channel.delete_messages(history[:num])
                await message.channel.send(summary_msg)

        # TODO: Put these in a dictionary or smth
        if message.content == "!clipthat":
            print(message.author.voice.channel)
            try:
                self.vc = await message.author.voice.channel.connect()

                self.vc.play(
                    discord.FFmpegPCMAudio("./audio/wardell_clipthat.mp3")
                )

                while self.vc.is_playing():
                    await asyncio.sleep(.1)
                
                await self.vc.disconnect()
            except discord.errors.ClientException:
                await message.channel.send(
                    "opurtbot is already playing a clip"
                )
        
        if message.content == "!yessir":
            print(message.author.voice.channel)
            try:
                self.vc = await message.author.voice.channel.connect()

                self.vc.play(
                    discord.FFmpegPCMAudio("./audio/wardell_yessir.mp3")
                )

                while self.vc.is_playing():
                    await asyncio.sleep(.1)
                
                await self.vc.disconnect()
            except discord.errors.ClientException:
                await message.channel.send(
                    "opurtbot is already playing a clip"
                )

        if message.content == "!yooo":
            print(message.author.voice.channel)
            try:
                self.vc = await message.author.voice.channel.connect()

                self.vc.play(
                    discord.FFmpegPCMAudio("./audio/csgo_niceknife.mp3")
                )

                while self.vc.is_playing():
                    await asyncio.sleep(.1)
                
                await self.vc.disconnect()
            except discord.errors.ClientException:
                await message.channel.send(
                    "opurtbot is already playing a clip"
                )
        
        if message.content == '!bwaaa':
            try:
                self.vc = await message.author.voice.channel.connect()

                self.vc.play(
                    discord.FFmpegPCMAudio("./audio/victory.mp3")
                )

                while self.vc and self.vc.is_playing():
                    await asyncio.sleep(.1)
                
                await self.vc.disconnect()
            except discord.errors.ClientException:
                await message.channel.send(
                    "opurtbot is already playing a clip"
                )
        
        if message.content == '!bwaa':
            try:
                self.vc = await message.author.voice.channel.connect()

                self.vc.play(
                    discord.FFmpegPCMAudio("./audio/imposter_victory.mp3")
                )

                while self.vc and self.vc.is_playing():
                    await asyncio.sleep(.1)
                
                await self.vc.disconnect()
            except discord.errors.ClientException:
                await message.channel.send(
                    "opurtbot is already playing a clip"
                )
        
            
        if message.content == '!delib':
            try:
                self.vc = await message.author.voice.channel.connect()

                self.vc.play(
                    discord.FFmpegPCMAudio("./audio/naruto_deliberation.mp3")
                )

                while self.vc and self.vc.is_playing():
                    await asyncio.sleep(.1)
                
                await self.vc.disconnect()
            except discord.errors.ClientException:
                await message.channel.send(
                    "opurtbot is already playing a clip"
                )
        
        elif message.content == '!!delib':
            if self.vc:
                await self.vc.disconnect()
                self.vc = None

        if message.content.startswith("!spinup"):
            return  # disable spinup so people can't spend my money -Kavel

            if self.voting:
                await message.channel.send("you mf clown there's already an active vote")
            elif self.running:
                await message.channel.send("the server is already up u fool")
            elif self.locked:
                await message.channel.send("the server is locked! nathan's probably playing valorant...")
            else:
                if (message.author.id == 279456734773510145) and not message.content.endswith("nosudo"):
                    await self.spinup(message)
                else:
                    await message.channel.send("starting vote, need 5 people to confirm. you have 3 MINUTES to vote [type `!yes` to vote, `!no` to cancel your existing vote]")

                    self.voteChannel = message.channel
                    self.voteStarted = time.time()
                    self.voting = True
                    self.voted = set()


        elif message.content.startswith("!whois"):
            if len(active_players):
                res = "players currently on: \n```" 
                for p in active_players:
                    res += "  - " + p + "\n"
                await message.channel.send(res + "```")
            else:
                await message.channel.send("no one is on, hop in!")

        elif message.content.startswith("!lock"):
            if (message.author.id == 279456734773510145):
                await message.channel.send("the server is locked and cannot be spun up")

                self.locked = True

                if self.voting:
                    await message.channel.send("the active vote has been cancelled")
                    self.voting = False
                    self.voted = set()
        
        elif message.content.startswith("!unlock"):
            if (message.author.id == 279456734773510145):
                await message.channel.send("the server is unlocked can can be spun up")

                self.locked = False

        elif message.content.startswith("!help"):
            await message.channel.send("""
`!spinup`   - starts a vote to spin up the minecraft server, type `!yes` to vote, `!no` to cancel
`!spindown` - spins down the minecraft server, there is NO voting process
`!ip`       - returns the IP address of the server
`!isup`     - checks if the server is currently up/starting up
`!uptime`   - returns the uptime of the server in seconds
            """)


        elif message.content.startswith("!yes"):
            if message.author not in self.voted and self.voting:
                self.voted.add(message.author)
                await message.channel.send("%s out of 5 votes recorded" % len(self.voted))
            
                if len(self.voted) == 5:
                    # spin up the mineraft server
                    await self.spinup(message)        

        elif message.content.startswith("!no"):
            if message.author in self.voted and self.voting:
                self.voted.remove(message.author)
                await message.channel.send("%s out of 5 votes recorded" % len(self.voted))

        elif message.content.startswith("!spindown"):
            await message.channel.send("spinning down the minecraft server")

            try:
                # tell the minecraft server to gracefully shut down
                await self.sock.emit("quit")

                # dc from the websocket connection
                await self.sock.disconnect()
            except:
                pass

            # then spin down the server
            utils.alter_instance(ec2, os.environ['EC2_INSTANCE_ID'], state = 'OFF')
            active_players = set()

            self.running = False

        elif message.content.startswith("!isup"):
            if self.running:
                await message.channel.send("the server IS up") 
            else:
                await message.channel.send("the server is NOT up")
        elif message.content.startswith("!uptime"):
            if self.running:
                await message.channel.send("the server has been up for %s seconds" % ((time.time() - self.upsince)))
            else:
                await message.channel.send("the server is not currently up")
            
        elif message.content.startswith("!ip"):
            self.ip = ec2.describe_instances()['Reservations'][1]['Instances'][0]['NetworkInterfaces'][0]['Association']['PublicIp']

            await message.channel.send("`%s:25565`" % (self.ip))
    
    async def spinup(self, message):
        #self.ip = ec2.describe_instances()['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['Association']['PublicIp']

        await message.channel.send("vote succeeded, spinning up minecraft (IP will be sent soon!)")
        
        self.voting = False
        self.voted = set()

        if (not self.running):
            # spin up the server 
            utils.alter_instance(ec2, os.environ['EC2_INSTANCE_ID'], state = 'ON')
        

            self.running = True
            self.upsince = time.time()
            
client = Spinup()

c = 0
async def check_messages(ctx):
    await ctx.wait_until_ready()

    sock = socketio.AsyncClient(logger = True, reconnection_attempts=1)

    @sock.event
    def connect():
        ctx.sock_connected = True
        print("I'm connected!")

    @sock.event
    async def connect_error():
        print("The connection failed!")

    @sock.event
    def disconnect():
        ctx.sock_connected = False
        print("I'm disconnected!")

    @sock.on("joinleave")
    async def joinleave(data):
        if data['task'] == 'message-discord-joinleave':
                    
            user = data['user']
            message = data['message']

            if data['joining']:
                active_players.add(user)
            else:
                active_players.remove(user)

            await ctx.dimensional_rift.send(message)
    
    @sock.on('minecraft-chat')
    async def chat(data):
        if data['task'] == 'message-discord':
            #channel = discord.utils.get(ctx.get_all_channels(), name = "dimensional-rift")
            #print(channel)
            if not data['message'].endswith("Disconnected"):
                await ctx.dimensional_rift.send("```diff\n+ <%s> %s```" % (data['user'], data['message']))

    last_message = None

    prev_topic = ""
    c = 0
    while True:
        c += 1

        # establish connection to the aws instance
        # we're going to run this every 2 seconds
        if ctx.running and (time.time() - ctx.upsince) > 1 and not ctx.sock_connected and c % 20 == 0:
            try:
                instances = ec2.describe_instances()
                ip_addr = instances['Reservations'][1]['Instances'][0]['NetworkInterfaces'][0]['Association']['PublicIp']

                await sock.connect(url = 'http://{}:5000'.format(os.environ['PRIVATE_IP']))
            except:
                print("attempted to connect and failed.")
            else:
                await ctx.voteChannel.send("minecraft is up @ {}:25565. Hop in!".format(ip_addr))

        ctx.sock = sock

        if ctx.dimensional_rift and ctx.server_status:
            if not last_message:
                last_message = ctx.server_status.last_message_id 

            # set the topic of the chat
            statuses = []

            statuses.append("ON @ %s" % ctx.ip if ctx.running else "OFF")
            statuses.append("LOCKED" if ctx.locked else "UNLOCKED")
            
            if ctx.voting:
                statuses.append("VOTING")

            topic = "SERVER: "
            for status in statuses:
                topic += status + ", "
            topic = topic[:-2]

            if len(active_players) and ctx.running:
                topic += " | "
                for player in active_players:
                    topic += player + ", "
                topic = topic[:-2]

            elif len(active_players) == 0 and ctx.running:
                topic += " | no one is on, hop on!"

            if topic != prev_topic:
                print("EDITING TOPIC: %s, %s" % (prev_topic, topic))

                # delete the last message 
                if last_message: 
                    try:
                        if type(last_message) == int:
                            msg = await ctx.server_status.fetch_message(last_message)
                            await msg.delete()
                        else:
                            await last_message.delete()
                    except Exception as e:
                        print(e)

                last_message = await ctx.server_status.send(topic)

                prev_topic = topic


            if (time.time() - ctx.voteStarted) > 180 and ctx.voting:
                ctx.voting = False
                ctx.voted = set() 

                await ctx.voteChannel.send("sorry! the vote has ended, type `!spinup` to start another vote")
            elif int(time.time() - ctx.voteStarted) == 120 and ctx.voting:
                ctx.voteStarted -= 1    # this is so fucking janky. we only want this message sent once, so we rely on the 0.1 second resolution of the check_messages function. we subtract one from voteStarted to simulate a second of time passing, ensuring this message is only sent once.

                await ctx.voteChannel.send("the vote will end in 1 MINUTE")
            elif int(time.time() - ctx.voteStarted) == 60 and ctx.voting:
                ctx.voteStarted -= 1

                await ctx.voteChannel.send("the vote will end in 2 MINUTES")

            """
            while not outq.empty():
                item = outq.get()

                if item['task'] == 'message-discord':
                    #channel = discord.utils.get(ctx.get_all_channels(), name = "dimensional-rift")
                    #print(channel)
                    if not item['message'].endswith("Disconnected"):
                        await ctx.dimensional_rift.send("```diff\n+ <%s> %s```" % (item['user'], item['message']))

                elif item['task'] == 'message-discord-joinleave':
                    
                    user = item['user']
                    message = item['message']

                    await ctx.dimensional_rift.send(message)
            """

        await asyncio.sleep(0.1)

async def main():
    pass

if __name__ == '__main__':
    client.loop.create_task(check_messages(client))

    client.run(os.environ['DISCORD_TOKEN'])

    #loop = asyncio.get_event_loop()
    #loop.run_until_complete(client.start(os.environ['DISCORD_TOKEN']))
    #loop.close()
    #print("closed")
    #asyncio.run(main())
