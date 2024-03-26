import os

import deepl
import discord
from discord import Embed, app_commands
from discord.ext import commands


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

  @app_commands.command(name="hello", description="Says hello to the user")
  async def slashhello(self, interaction: discord.Interaction):
    await interaction.response.send_message(
        content="Hello this is a slash command")

  @commands.Cog.listener()
  async def on_reaction_add(self, reaction, _user):
    if reaction.emoji in self.flag_emoji_dict:
      lang_code = self.flag_emoji_dict[reaction.emoji]
      message = reaction.message
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
        await reaction.message.channel.send(embed=embed)
      except Exception as e:
        await reaction.message.channel.send(f"Error during translation: {e}")
        return


async def setup(client: commands.Bot) -> None:
  await client.add_cog(Translate(client))
