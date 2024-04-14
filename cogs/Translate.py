import json
import os

import deepl
import discord
from discord import Embed
from discord.ext import commands


def is_allowed_guild():
    allowed_guild_ids = {1045479020940234783, 383365467894710272}  # Add your guild IDs here
    async def predicate(ctx):
        return ctx.guild and ctx.guild.id in allowed_guild_ids
    return commands.check(predicate)


class Translate(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client
        deepl_key = os.getenv("DEEPLKEY")
        if deepl_key is None:
            raise ValueError("DEEPLKEY environment variable is not set")
        self.translator = deepl.Translator(deepl_key)
        self.language_dict = self.load_language_dict()

    def load_language_dict(self):
        try:
            with open('cogs/cogfiles/FlagDict.json', 'r') as lang_file:
                return json.load(lang_file)
        except Exception as e:
            print(f"Failed to load language dictionary: {e}")
            return {}

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        print(f"Reaction received: {payload.emoji}")  # Log received reactions
        channel = self.client.get_channel(payload.channel_id)

        messages = []  # Initialize messages as an empty list

        # Adapted to fetch the last 10 messages for translating in DMs
        if isinstance(channel, discord.DMChannel):
            messages = [message async for message in channel.history(limit=10)]
        else:
            message = None
            if isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.GroupChannel)):
                try:
                    message = await channel.fetch_message(payload.message_id)
                except discord.NotFound:
                    return
                except discord.Forbidden:
                    return
                except discord.HTTPException:
                    return
                messages = [message]

        if not messages:
            return

        if str(payload.emoji) in self.language_dict:
            lang_code = self.language_dict[str(payload.emoji)]
            for message in messages:
                try:
                    result = self.translator.translate_text(message.content,
                                                            target_lang=lang_code)
                    translated_message = result.text
                    detected_lang = result.detected_source_lang

                    embed = Embed(title="Translation", color=0x00ff00)
                    embed.add_field(name="Original", value=message.content, inline=False)
                    embed.add_field(name=f"Translated from {detected_lang} to {lang_code}",
                                    value=translated_message,
                                    inline=False)
                    if isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.GroupChannel)):
                        await channel.send(embed=embed)
                except Exception as e:
                    if isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.GroupChannel)):
                        await channel.send(f"Error during translation: {e}")
                    break  # If an error occurs, break the loop to prevent spamming the channel


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Translate(client))