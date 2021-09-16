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

bot = commands.Bot(command_prefix = ["grog ", "_"])

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
    'source_address': '0.0.0.0',
}

# ffmpeg_options = {
#     'options': '-vn',
#     'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
# }

queues = dict()
list_titles = dict() 
url_list = dict()
volume_list = dict()
nowPlaying = dict()

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

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
            info = ydl.extract_info(f"ytsearch:{term}", download = True)['entries'][0]
            #printd(info)
        except:
            print(f"{Fore.RED}[*]{Fore.WHITE} Failed fetching info for {term} from YouTube.")
            return
    
    music_file = get_filename(info['id'], ctx.guild.id)
    
    #printd(info)
    printd(info['title'])
    thumbnail = info['thumbnail']
    printd(thumbnail)
    if vc.is_playing() or vc.is_paused():
        queues[ctx.guild.id].append(info)
        url_list[ctx.guild.id].append("https://www.youtube.com/watch?v=" + info['id'])
        list_titles[ctx.guild.id].append(info['title'])
        embed = discord.Embed(title = "Added to Queue", description = f"`{info['title']}`")
        await ctx.send(embed = embed)
        return
    try:
        # printd("Playing " + info['thumbnail'])
        embed = discord.Embed(title = "Now Playing", description = f"[__{info['title']}__]({'https://www.youtube.com/watch?v=' + info['id']})", color = 0xfffb49)
        embed.set_image(url=info['thumbnail'])
        await ctx.send(embed = embed)
        #vc.play(discord.FFmpegPCMAudio(info['formats'][0]['url'], **ffmpeg_options), after=lambda e: queue(ctx))
        vc.play(discord.FFmpegPCMAudio(music_file), after = lambda e: queue(ctx))
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
        if len(queues[ctx.guild.id]) == 0:
                await ctx.send(embed=discord.Embed(title="Error",
                                                   description="Nothing is playing",
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

@bot.command()
async def pause(ctx):
    vc = get(bot.voice_clients, guild = ctx.guild)
    if vc.is_connected() and vc.is_playing() : 
        vc.pause()
        await ctx.send(embed = discord.Embed(title = "Pause", description = "Song successfully **paused**", color = 0xfffb49))
    else:
        await ctx.send(embed = discord.Embed(title = "Pause", description = "**Failed** to Pause Bot because there is either no voice client in current server or nothing is playing. ", color = 0x3dffb1))

@bot.command()
async def resume(ctx):
    vc = get(bot.voice_clients, guild = ctx.guild)
    if vc.is_paused():
        vc.resume()
        await ctx.send(embed = discord.Embed(title = "Resume", description = "Song successfully **resumed**", color = 0xfffb49))


def queue(ctx):
    guild = ctx.guild.id
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if len(queues[guild]) != 0:
        filename = get_filename(queues[guild][0]['id'], guild, queue=True)
        vc.play(discord.FFmpegPCMAudio(filename),
                   after=lambda e: queue(ctx))
        vc.source = discord.PCMVolumeTransformer(vc.source, volume=volume_list[guild][0])
        nowPlaying[guild][0] = url_list[guild][0]
        nowPlaying[guild][1] = list_titles[guild][0]
        printd(nowPlaying)
        printd("Playing " + nowPlaying[guild][1])
        embed = discord.Embed(title = "Now Playing", description = nowPlaying[guild][1], color = 0xfffb49)
        embed.set_image(url = queues[guild][0]['thumbnail'])
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

def get_filename(search_term, guild_id, queue = False):
    search_dir = "./"
    if queue: search_dir = "./downloaded_songs/" 
    for root, dirs, files in os.walk(search_dir):
        for file in files:
            if file.rsplit('.', 1)[0].endswith(search_term):
                if not queue :
                    os.system(f"mv {file} ./downloaded_songs/{file}")
                    printd(f"mv {file} ./downloaded_songs/{file}")
                return f"./downloaded_songs/{file}"
    return False

def print_banner():
    os.system('cat banner.txt | lolcat')
    print("\n\n")


if __name__ == "__main__":
    print_banner()
    bot.run("ODg1NTM5NzQ1NzEzNzUwMDI2.YTohJw.b0KVdUwfMm-5zSRL1OXMQivRHp0")