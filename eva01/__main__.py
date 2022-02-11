import os
import logging

import hikari
import lightbulb
import sake
from pytz import utc
from lightbulb import commands
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
    cache = sake.redis.RedisCache("redis://127.0.0.1:6379", bot, bot)
    await cache.open()
    log.info("Connected to Redis.")

@bot.listen(hikari.StartedEvent)
async def on_started(event: hikari.StartedEvent) -> None:
    await bot.rest.create_message(
        int(os.environ['STDOUT_CHANNEL_ID']), 
        f"Systems loaded successfully! {os.environ['BOT_NAME']} STARTED."
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
@lightbulb.command("shutdown", "Close the connections of the bot.")
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def shutdown(ctx: lightbulb.context.Context) -> None:
    await ctx.respond("Shutting down systems, closing IA neuronal interface...")
    await ctx.bot.close()

@bot.command()
@lightbulb.command("ping", "Says pong.")
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def ping(ctx: lightbulb.context.Context) -> None:
    await ctx.respond("Pong.")

@bot.command()
@lightbulb.command("deploy", "Use to deploy a serverless project.")
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def deploy(ctx: lightbulb.context.Context) -> None:
    print("Test deploy - core")
    os.system("cd core-repositories/ && cd redcore-core/ && git checkout master && git pull && serverless deploy")
    await ctx.respond("Test deploy - core.")

if __name__ == "__main__":
    if os.name != "nt":
        import uvloop
        uvloop.install()
    
    bot.run()