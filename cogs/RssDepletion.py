# Standard library imports
import datetime

# Third-party imports
import discord
from discord import File, app_commands
from discord.ext import commands


class RssDepletion(commands.Cog):
  def __init__(self, client: commands.Bot):
      self.client = client

  class RssModal(discord.ui.Modal):
    starting_amount = discord.ui.TextInput(label="Starting Amount", style=discord.TextStyle.short,
                                           placeholder="Enter the starting amount here")
    amount_after_one_minute = discord.ui.TextInput(label="Amount After One Minute",
                                                   style=discord.TextStyle.short,
                                                   placeholder="Enter the amount after one minute here")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer() 
        try:
            num1 = float(self.starting_amount.value)
            num2 = float(self.amount_after_one_minute.value)
        except ValueError:
            await interaction.response.send_message("Please enter valid numbers.")
            return

        rate = num1 - num2
        if rate <= 0:
            await interaction.response.send_message("Invalid input. The first number must be greater than the second.")
            return

        minutes = num2 / rate
        hours = minutes / 60
        days = hours / 24
        depletion_time_utc = datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes)


        if rate > 0: 
          file_path = 'files/GasfieldSnip.PNG'
          file = File(file_path, filename="GasfieldSnip.PNG")
          embed = discord.Embed(
            title="Rss Depletion Info",
            description=(
                f"The starting resource amount is {num1:.0f}\n"
                f"The amount after 1 minute is {num2:.0f}\n\n"
                f"Resources are being gathered at **{rate:.0f}** per minute"
            ),
            colour=discord.Colour.blue(),
            timestamp=discord.utils.utcnow()
          )
          embed.set_thumbnail(url="attachment://GasfieldSnip.PNG")
          embed.add_field(name ="At the current gathering rate, the mill will be depleted in:",
            value = f"{minutes:.0f} minutes\n{hours:.1f} hours\n{days:.1f} days", inline=False)
          embed.add_field(name="The mill will be depleted by:",
          value=f"{depletion_time_utc.strftime('%a, %B %#d, %Y, %I:%M %p UTC')}", inline=False)
          embed.add_field(name="Local Time for mill depletion:",
            value=f"<t:{int(depletion_time_utc.timestamp())}:F>", inline=False)
          embed.set_footer(text=f"\nThis command was run by {interaction.user.display_name}")

          await interaction.followup.send(file=file, embed=embed)

  @app_commands.command(name='rss_depletion', description='Calculate resource depletion time and rate')
  async def rss_depletion(self, interaction: discord.Interaction):
    await interaction.response.send_modal(self.RssModal(title="Resource Gathering Information"))

  @app_commands.command(name="rss_depletion_help", description="Displays instructions on using the /rss_depletion command.")
  async def rss_help(self, interaction: discord.Interaction):
      embed = discord.Embed(
          title="Rss Depletion Instructions",
          description=(
              "-Users can use the included command `/screenshot_timer` for a one minute timer-\n\n"
              "The `/rss_depletion` command will ask for 2 values. To obtain these values:\n\n"
              "- Take a screenshot of your alliance's Resource mill's View Details page.\n"
              "- After one minute, take another screenshot of the same page.\n\n"            
              "Once you have your screenshots, use the `/rss_depletion` command.\n\n"              
              "The command will bring up a form asking you to provide 2 values.\n"
              "Enter the information requested by the form, and the bot will\n"
              "calculate and display the time until resource depletion.\n"
          ),
      )
      await interaction.response.send_message(embed=embed)
      #await msg.delete()


async def setup(client:commands.Bot) -> None:
  await client.add_cog(RssDepletion(client))