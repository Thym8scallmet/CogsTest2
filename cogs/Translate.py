import os

import deepl
import discord
from discord import Embed
from discord.ext import commands


def is_allowed_guild():
    allowed_guild_ids = {1045479020940234783, 383365467894710272}  # Add Allowed Server IDs Here
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
    self.flag_emoji_dict = {
        "🇺🇸": "EN-US",
        '🇬🇧': 'EN-GB',
        "🇩🇪": "DE",
        "🇫🇷": "FR",
        "🇪🇸": "ES",
        "🇮🇹": "IT",
        "🇵🇹": "PT-PT",
        "🇷🇺": "RU",
        "🇸🇦": "AR",
        "🇧🇬": "BG",
        "🇨🇳": "ZH",
        "🇨🇿": "CS",
        "🇩🇰": "DA",
        "🇪🇪": "ET",
        "🇫🇮": "FI",
        "🇬🇷": "EL",
        "🇭🇺": "HU",
        "🇮🇩": "ID",
        "🇯🇵": "JA",
        "🇰🇷": "KO",
        "🇱🇻": "LV",
        "🇱🇹": "LT",
        "🇳🇱": "NL",
        "🇳🇴": "NB",
        "🇵🇱": "PL",
        "🇷🇴": "RO",
        "🇸🇰": "SK",
        "🇸🇮": "SL",
        "🇸🇬": "SV",
        "🇹🇷": "TR",
        "🇺🇦": "UK",
        "🇻🇦": "la"
    }

 
  @commands.Cog.listener()
  async def on_raw_reaction_add(self, payload):
      channel = self.client.get_channel(payload.channel_id)
      message = None  # Initialize message to avoid it being possibly unbound

      # Check if the channel is None
      if channel is None:
          return

      # Ensure that the `fetch_message` method exists for the channel type
      if isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.GroupChannel)):
          try:
              message = await channel.fetch_message(payload.message_id)
          except discord.NotFound:
              # Handle the case where the message does not exist
              return
          except discord.Forbidden:
              # Handle the case where the bot does not have permissions to fetch the message
              return
          except discord.HTTPException:
              # Handle other possible HTTP exceptions
              return

      # Ensure message is not None and has content before proceeding
      if message is None or not message.content:
          return

      if str(payload.emoji) in self.flag_emoji_dict:
          lang_code = self.flag_emoji_dict[str(payload.emoji)]
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


async def setup(client: commands.Bot) -> None:
  await client.add_cog(Translate(client))