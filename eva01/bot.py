import os
import logging

import sake
import hikari
import aiosqlite
import lightbulb
from pytz import utc
from lightbulb import commands
from aiohttp import ClientSession
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

log = logging.getLogger(__name__)

bot = lightbulb.BotApp(
    token=os.environ['TOKEN'],
    prefix="$",
    default_enabled_guilds=int(os.environ['DEFAULT_GUILD_ID']),
    help_slash_command=True,
    case_insensitive_prefix_commands=True,
    intents=hikari.Intents.ALL
)

bot.d.scheduler = AsyncIOScheduler()
bot.d.scheduler.configure(timezone=utc)

# bot.load_extensions_from('.eva01/extensions')

@bot.listen(hikari.StartingEvent)
async def on_starting(event: hikari.StartingEvent) -> None:
    # Create database
    bot.d.db = await aiosqlite.connect("./data/database.sqlite3")
    await bot.d.db.execute("pragma journal_mode=wal")
    with open("./data/build.sql") as f:
        await bot.d.db.executescript(f.read())
    bot.d.scheduler.add_job(bot.d.db.commit, CronTrigger(second=0))
    log.info("Database connection opened.")

    # Create cache
    cache = sake.redis.RedisCache("redis://127.0.0.1:6379", bot, bot)
    await cache.open()
    log.info("Connected to Redis.")

    # Create utils
    bot.d.scheduler.start()
    bot.d.session = ClientSession(trust_env=True)
    log.info("AIOHttp session started.")

@bot.listen(hikari.StartedEvent)
async def on_started(event: hikari.StartedEvent) -> None:
    await bot.d.scheduler.add_job(
        lambda: log.info(f"Ping: {bot.heartbeat_latency:.0f} ms")
    )

    await bot.rest.create_message(
        int(os.environ['STDOUT_CHANNEL_ID']), 
        f"Systems loaded successfully! {os.environ['BOT_NAME']} STARTED."
    )

@bot.listen(hikari.StoppingEvent)
async def on_stopping(event: hikari.StoppingEvent) -> None:
    bot.d.scheduler.shutdown()
    await bot.d.session.close()
    log.info("AIOHttp session closed.")

    await bot.d.db.close()
    log.info("Database connection closed.")

    await bot.rest.create_message(
        int(os.environ["STDOUT_CHANNEL_ID"]),
        "Shutting down systems, closing IA neuronal interface..."
    )

@bot.listen(hikari.ExceptionEvent)
async def on_error(event: hikari.ExceptionEvent) -> None:
    raise event.exception


@bot.listen(lightbulb.CommandErrorEvent)
async def on_command_error(event: lightbulb.CommandErrorEvent) -> None:
    if isinstance(event, lightbulb.CommandErrorEvent):
        return
    
    if isinstance(event, lightbulb.NotEnoughArguments):
        await event.context.respond(
            "There are some missing arguments: " + ", ".join(event.exception.missing_args)
        )
        return

    if isinstance(event.exception, lightbulb.ConverterFailure):
        await event.context.respond(
            f"The '{event.exception.option}' option is invalid."
        )
        return
    
    if isinstance(event, lightbulb.CommandIsOnCooldown):
        await event.context.respond(
            f"Command is in cooldown. Try again in {event.exception.retry_after:.0f} seconds"
        )
        return
    
    await event.context.respond("Critic levels of power... ||MASSIVE ERROR|| ! ! !")
    
    if isinstance(event.exception, lightbulb.CommandInvocationError):
        raise event.exception.original
    
    raise event.exception

@bot.command()
@lightbulb.command("ping", "Says pong.")
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def ping(ctx: lightbulb.context.Context) -> None:
    await ctx.respond("Pong.")

@bot.command()
@lightbulb.command("deploy", "Use to deploy a serverless stack.")
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def deploy(ctx: lightbulb.context.Context) -> None:
    print("Starting deploy: core")
    os.system("cd core-repositories/ && cd redcore-core/ && git checkout master && git pull && serverless deploy")
    await ctx.respond("Test deploy - core.")

def run() -> None:
    if os.name != "nt":
        import uvloop
        uvloop.install()
    
    bot.run()