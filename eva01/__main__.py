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
    case_insensitive_prefix_commands=True
)

bot.d.scheduler = AsyncIOScheduler()
bot.d.scheduler.configure(timezone=utc)

# bot.load_extensions_from('.eva01/extensions')

@bot.listen(hikari.StartingEvent)
async def on_starting(event: hikari.StartingEvent) -> None:
    cache = sake.redis.RedisCache("redis://127.0.0.1", bot, bot)
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
    ...

@bot.listen(lightbulb.CommandErrorEvent)
async def on_command_error(event: lightbulb.CommandErrorEvent) -> None:
    ...


@bot.command()
@lightbulb.command("shutdown", "Close the connections of the bot.")
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def shutdown(ctx: lightbulb.context.Context) -> None:
    await ctx.respond("Shutting down systems, closing IA neuronal interface...")
    await ctx.bot.close()

@bot.command()
@lightbulb.command("ping", "Says pong.")
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def shutdown(ctx: lightbulb.context.Context) -> None:
    await ctx.respond("Pong.")

if __name__ == "__main__":
    if os.name != "nt":
        import uvloop
        uvloop.install()
    
    bot.run()