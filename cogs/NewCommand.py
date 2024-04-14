import discord
from discord import app_commands
from discord.ext import commands


class NewCommand(commands.Cog):
  def __init__(self, client: commands.Bot):
      self.client = client

  #change the name and command of this and run it when you add a new command to discord
  #doing so will update the command structure once you run it and get the error message
  #This cog can be unloaded once your bot is complete. 

  @app_commands.command(name="new-command", description="Change this when you add a new command to discord")
  async def new_command(self, interaction: discord.Interaction):
      await interaction.response.send_message(content="You have added a new command")

async def setup(client:commands.Bot) -> None:
  await client.add_cog(NewCommand(client))
