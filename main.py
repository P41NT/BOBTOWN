import discord
from discord.ext import commands
from discord.utils import get
from colorama import Fore, Back, Style
import colorama
import youtube_dl.utils
import youtube_dl
import os
from rainbow_print import printr

colorama.init(autoreset = True)

bot = commands.Bot(command_prefix = ["bob "])

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

queues = dict()
list_titles = dict() 
url_list = dict()
volume_list = dict()
nowPlaying = dict()

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename

@bot.event
async def on_ready():
    print(f"{Fore.MAGENTA}[*] {Fore.WHITE}Bot is Online")
    print(f"{Fore.MAGENTA}[*] {Fore.WHITE}Bot's Username and Tag: {Fore.RED}{bot.user}")

@bot.command()
async def ping(ctx):
    embed = discord.Embed(title = "PING", description = f":ping_pong: You pinged **BOBTOWN**! The latency is **{round(bot.latency * 1000)}** ms", color=0xffd000)
    print(f"{Fore.YELLOW}[*]{Fore.WHITE} The latency was {Fore.GREEN}{bot.latency * 1000}{Fore.WHITE} ms")
    await ctx.send(embed = embed)

@bot.command()
async def connect(ctx, _ = True):
    channel = ctx.message.author.voice.channel
    vc = get(bot.voice_clients, guild = ctx.guild)

    try:
        if vc and vc.is_connected() and vc.channel.name != channel.name:
            await vc.move_to(channel)
            print(f"{Fore.GREEN}[*]{Fore.WHITE} The Bot moved to {Fore.RED}{channel.name}")
            embed = discord.Embed(title= "Connected", description = f"The bot successfully **connected** to **{channel.name}**", color = 0x3dffb1)
        elif not vc:
            vc = await channel.connect()
            print(f"{Fore.GREEN}[*]{Fore.WHITE} The Bot connected to {Fore.RED}{channel.name}")
            embed = discord.Embed(title= "Connected", description = f"The bot successfully **connected** to **{channel.name}**", color = 0x3dffb1)
        else:
            _ = False

    except Exception as e:
        print(f"{Fore.RED}[*]{Fore.WHITE} The Bot faced a problem trying to connect to {Fore.RED}{channel.name} in guild {ctx.guild.name}")
        print(f"{Fore.RED}[*] {e}")
        embed = discord.Embed(title = "Error", description = f"The bot faced some error trying to connect to voice channel", color = 0xff573d)
    if _:
        await ctx.send(embed = embed)
    
    return vc

@bot.command()
async def disconnect(ctx):
    channel = ctx.message.author.voice.channel
    vc = get(bot.voice_clients, guild = ctx.guild)
    embed = discord.Embed()
    try:
        if vc and vc.is_connected():
            await vc.disconnect()
            print(f"{Fore.GREEN}[*]{Fore.WHITE} The Bot disconnected from {Fore.RED}{channel.name}")
            embed = discord.Embed(title= "Disconnected", description = f"The bot successfully **disconnected** from **{channel.name}**")
        else:
            print(f"{Fore.RED}[*]{Fore.WHITE} The Bot tried to disconnect while not connected to any channel")
            embed = discord.Embed(title = "Error", description = f"**BobTown** was not connected to any **voice channel**")
            
    except Exception as e:
        print(f"{Fore.RED}[*]{Fore.WHITE} The Bot faced a problem trying to disconnect to {Fore.RED}{channel.name} {Fore.WHITE}in guild {Fore.RED}{ctx.guild.name}")
        print(f"{Fore.RED}[*]{e}")
    await ctx.send(embed = embed)

@bot.command()
async def play(ctx, *, term):
    vc = await connect(ctx)
    initialize(ctx.guild.id)
    with youtube_dl.YoutubeDL(ytdl_format_options) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{term}", download = False)['entries'][0]
        except:
            print(f"{Fore.RED}[*]{Fore.WHITE} Failed fetching info for {term} from YouTube.")
            return
    if vc.is_playing() or vc.is_paused():
        queues[ctx.guild.id].append(info)
        url_list[ctx.guild.id].append("https://www.youtube.com/watch?v=" + info['id'])
        list_titles[ctx.guild.id].append(info['title'])
        embed = discord.Embed(title = "Added to Queue", description = f"`{info['title']}`")
        await ctx.send(embed = embed)
        return
    try:
        printd("Playing " + info['title'])
        embed = discord.Embed(title = "Now Playing", description = info['title'], color = 0xfffb49)
        await ctx.send(embed = embed)
        vc.play(discord.FFmpegPCMAudio(info['formats'][0]['url'], **ffmpeg_options), after=lambda e: queue(ctx))
        vc.source = discord.PCMVolumeTransformer(vc.source, volume=volume_list[ctx.guild.id][0])
    except discord.errors.ClientException as e:
        print(f"{Fore.RED}[*] {e}")
        return
    
    if len(nowPlaying[ctx.guild.id]) == 0:
        nowPlaying[ctx.guild.id].append("https://www.youtube.com/watch?v=" + info['id'])
        nowPlaying[ctx.guild.id].append(info['title'])

@bot.command(name="queue")
async def queue_(ctx):
    printd(list_titles)
    text = ""
    if(len(list_titles)) == 0 and not nowPlaying[ctx.guild.id][0]:
        text = "```No songs in your queue```"
    text += "```Now Playing : " + nowPlaying[ctx.guild.id][1] + "\n\n"
    for i in range(len(list_titles[ctx.guild.id])):
        text += f"{i+1}) {list_titles[ctx.guild.id][i]} \n"
    text += "```"
    embed = discord.Embed(title = "Queue", description = text, color = 0xfffb49)
    await ctx.send(embed = embed)

@bot.command()
async def skip(ctx):
    vc = get(bot.voice_clients, guild = ctx.guild)
    embed = None
    if vc.is_connected() and vc.is_playing():
        if len(queues[ctx.guild]) == 0:
                await ctx.send(embed=discord.Embed(title="Error",
                                                   description="Nothing is playin",
                                                   color = 0x3dffb1))
        else:
            await ctx.send(embed=discord.Embed(title="Skip",
                                                description="The song has been skipped",
                                                color=0x3dffb1))
        vc.stop()
    else:
        await ctx.send(embed=discord.Embed(title="Error",
                                            description="Bot faced a problem trying to skip the currently playing song",
                                            color=0x3dffb1))

def queue(ctx):
    guild = ctx.guild.id
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if len(queues[guild]) != 0:
        vc.play(discord.FFmpegPCMAudio(queues[guild][0]['formats'][0]['url'], **ffmpeg_options),
                   after=lambda e: queue(ctx))
        vc.source = discord.PCMVolumeTransformer(vc.source, volume=volume_list[guild][0])
        nowPlaying[guild][0] = url_list[guild][0]
        nowPlaying[guild][1] = list_titles[guild][0]
        printd(nowPlaying)
        #channel = bot.get_channel(ctx.channel.id)
        printd("Playing " + nowPlaying[guild][1])
        embed = discord.Embed(title = "Now Playing", description = nowPlaying[guild][1], color = 0xfffb49)
        bot.loop.create_task(ctx.send(embed = embed))
        del queues[guild][0]
        del list_titles[guild][0]
        del url_list[guild][0]
    
def initialize(guild):
    if guild not in queues:
        queues[guild] = list()
        list_titles[guild] = list()
        url_list[guild] = list()
        nowPlaying[guild] = list()
        volume_list[guild] = [0.5]

def printd(message):
    print(f"{Fore.YELLOW}[*] {message}")



def print_banner():
    os.system('cat banner.txt | lolcat')
    print("\n\n")

if __name__ == "__main__":
    print_banner()
    bot.run("ODg1NTM5NzQ1NzEzNzUwMDI2.YTohJw.b0KVdUwfMm-5zSRL1OXMQivRHp0")