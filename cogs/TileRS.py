import datetime
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands


class TileRS(commands.Cog):
  def __init__(self, client: commands.Bot):
      self.client = client

  @app_commands.command(name="tile_reset", description=
    "Converts Event time Tile Reset to Clock time "
    "and displays the next tile reset time")
  async def tile_reset(self, interaction: discord.Interaction, input_time: str):
      now_utc = datetime.datetime.utcnow()

# Parse the input_time
      try:
      # Step 2: Parsing the input
        minutes, seconds = map(int, input_time.split(":"))
      except ValueError:
        # Step 3: Validation failed - not a valid format or numbers
        await interaction.response.send_message("Invalid format. "
                              "Please use MM:SS format.")
        return

      if minutes < 0 or seconds < 0 or seconds >= 60:
          await interaction.response.send_message("Please enter a valid "
                              "time (MM:SS) with 0 <= seconds < 60.")
          return
      # Parse the event_timer and hour
      event_timer = timedelta(minutes=minutes, seconds=seconds)
      hour = timedelta(hours=1,minutes=0,seconds=0)
      clock_time = hour - event_timer
      # Format clock_time to display 
      #without leading 0 for hours
      minutes, seconds = divmod(clock_time.seconds, 60)
      #formatted_time = f"{minutes}:{seconds:02d}"

      # Calculate the time until the next hour starts
      start_of_next_hour = now_utc.replace(
      minute=0, second=0, microsecond=0) + clock_time

      next_tile_reset_unix_timestamp = int(start_of_next_hour.timestamp())
      message_content = (
      #f"Tile reset is: {formatted_time} after the hour.\n"
      f"Tile reset is: {minutes} minutes and {seconds:02d} seconds after the hour.\n"
      f"The next tile reset starts at <t:{next_tile_reset_unix_timestamp}:T>"
)
      await interaction.response.send_message(message_content)

async def setup(client:commands.Bot) -> None:
  await client.add_cog(TileRS(client))
  
#async def setup(bot):
  #bot.add_cog(TileRS(bot))