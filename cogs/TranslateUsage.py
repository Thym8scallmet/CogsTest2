import datetime
import os

import deepl
import discord
from discord import app_commands
from discord.ext import commands, tasks


class TranslatorUsage(commands.Cog):

  def __init__(self, client: commands.Bot):
    self.client = client
    deepl_key = os.getenv('DEEPLKEY')
    if deepl_key is None:
      raise ValueError("DEEPLKEY environment variable is not set")
    self.translator = deepl.Translator(deepl_key)

    async def cog_load(self):
      # Make sure the weekly report task starts when the cog is loaded
      # (requires discord.py 2.0+)
      self.weekly_report.start()

    def get_delay_until_next_run(self, weekday=6, hour=0, minute=0):
      """Calculate the delay until the next run time. 
      Default next run time: Sunday at 00:00 UTC."""
      now = datetime.datetime.now(datetime.timezone.utc)
      target = now + datetime.timedelta(days=(weekday - now.weekday()) % 7)
      target = target.replace(hour=hour,
                              minute=minute,
                              second=0,
                              microsecond=0)

      if target < now:
        # If the target time is in the past, move to next week
        target += datetime.timedelta(days=7)

      delay = (target - now).total_seconds()
      return delay

    @tasks.loop(hours=168)  # Weekly frequency
    async def weekly_report(self):
      channel_id = 1215338735949062206  # Replace with your actual channel ID
      channel = self.client.get_channel(channel_id)
      if channel:
        usage = self.translator.get_usage(
        )  # Sample usage report retrieval logic
        # Assuming your report generation code stays the same
        embed = discord.Embed(title="Weekly Translator Usage Report",
                              color=0x00ff00)
        if usage.any_limit_reached:
          embed.add_field(name="Limit Reached",
                          value="Translation limit reached.",
                          inline=False)
        if usage.character.valid:
          embed.add_field(
              name="Character Usage",
              value=f"{usage.character.count} of {usage.character.limit}",
              inline=False)
        if usage.document.valid:
          embed.add_field(
              name="Document Usage",
              value=f"{usage.document.count} of {usage.document.limit}",
              inline=False)
        try:
          await channel.send(embed=embed)
        except Exception as e:
          print(f"Failed to send weekly report: {str(e)}")

    @weekly_report.before_loop
    async def before_weekly_report(self):
      """Wait until the loop should run next."""
      await self.client.wait_until_ready()
      delay = self.get_delay_until_next_run()
      await discord.utils.sleep_until(datetime.datetime.now(datetime.timezone.utc) +
                                      datetime.timedelta(seconds=delay))

  @app_commands.command(
      name="check_translator_usage",
      description="Checks the current usage of the translator for this month")
  async def check_translator_usage(self, interaction: discord.Interaction):
    try:
      usage = self.translator.get_usage()
      embed = discord.Embed(title="Translator Usage", color=0x00ff00)
      if usage.any_limit_reached:
        embed.add_field(name="Limit Reached",
                        value="Translation limit reached.",
                        inline=False)
      if usage.character.valid:
        embed.add_field(
            name="Character Usage",
            value=f"{usage.character.count} of {usage.character.limit}",
            inline=False)
      if usage.document.valid:
        embed.add_field(
            name="Document Usage",
            value=f"{usage.document.count} of {usage.document.limit}",
            inline=False)

      await interaction.response.send_message(embed=embed)
    except Exception as e:
      await interaction.response.send_message(
          content=f"Failed to retrieve usage information: {str(e)}")


async def setup(client: commands.Bot) -> None:
  await client.add_cog(TranslatorUsage(client))
