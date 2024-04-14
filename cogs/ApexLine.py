import random

import discord
from discord import app_commands
from discord.ext import commands


class ApexLine(commands.Cog):
  def __init__(self, client: commands.Bot):
      self.client = client

  @app_commands.command(name="apex_line", description="Generates a random Apex Lineup")
  async def random_apex_line(self, interaction: discord.Interaction):
      words = ["Riders\n", "Fighters\n", "Shooters\n"]
      random.shuffle(words)  # Shuffles the list in place
      message = " ".join(words)  # Joins the shuffled list into a string
      embed = discord.Embed(title="Here is your Apex Lineup", description=message, color=0x00ff00)
      await interaction.response.send_message(embed=embed, ephemeral=True)  

async def setup(client:commands.Bot) -> None:
  await client.add_cog(ApexLine(client))
#async def setup(bot):
    #bot.add_cog(Hello(bot))
