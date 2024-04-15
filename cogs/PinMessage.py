import json
import os  # Import os module for path operations
import sys
import time

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Select, View


class PinJobSelect(Select):

  def __init__(self, jobs, client, **kwargs):
    super().__init__(**kwargs)
    self.jobs = jobs
    for job in jobs:
      # Attempt to get the channel name using the channel ID. If the channel is not found, use "Unknown Channel".
      channel = client.get_channel(int(job['channel_id']))
      channel_name = channel.name if channel else "Unknown Channel"
      self.add_option(label=f"ID: {job['message_id']} in {channel_name}",
                      description=f"Channel ID: {job['channel_id']}",
                      value=str(job['message_id']))

  async def callback(self, interaction: discord.Interaction):
    selected_message_id = int(self.values[0])
    if self.view is not None:
      self.view.stop()  # Stops the view and prevents any further interaction
    for job in self.jobs:
      if job['message_id'] == selected_message_id:
        self.jobs.remove(job)
        await interaction.client.get_cog("PinMessages").save_job(
            interaction.guild.id)
        break
    await interaction.response.send_message(
        f"Stopped pinning message {selected_message_id} and removed from jobs.",
        ephemeral=True)


class PinMessages(commands.Cog):

  def __init__(self, client: commands.Bot):
    self.client = client
    self.jobs = []  # Now stores multiple pin jobs
    self.jobs_file_base_path = 'cogs/cogfiles/pinjobs'  # Base path without guild ID
    self.keep_message_at_bottom.start()

  @commands.Cog.listener()
  async def on_ready(self):
    print("PinMessages cog is ready.")
    # No need to load jobs here, since they will be loaded per guild

  def get_jobs_file_path(self, guild_id):
    # Generates a file path unique to each guild
    return f"{self.jobs_file_base_path}_{guild_id}.json"

  async def load_jobs(self, guild_id):
    jobs_file_path = self.get_jobs_file_path(guild_id)
    try:
      if not os.path.exists(jobs_file_path):
        self.jobs = []  # Reset to empty if file doesn't exist
        return

      with open(jobs_file_path, 'r') as f:
        self.jobs = json.load(f)
    except Exception as e:
      print(f"Failed to load jobs for guild {guild_id} due to: {e}",
            file=sys.stderr)
      self.jobs = []

  async def save_job(self, guild_id):
    jobs_file_path = self.get_jobs_file_path(guild_id)
    with open(jobs_file_path, 'w') as f:
      json.dump(self.jobs, f)

  @app_commands.command(
      name="pin_message",
      description=
      "Pins a message to the bottom of the chat and allows specifying update frequency"
  )
  async def pinbottom(self,
                      interaction: discord.Interaction,
                      message_id: str,
                      frequency_in_minutes: int = 10):
    await self.load_jobs(
        interaction.guild_id
    )  # Ensure we're working with the current guild's jobs
    try:
      message_id_int = int(message_id)
      new_job = {
          'channel_id': interaction.channel_id,
          'message_id': message_id_int,
          'update_frequency': max(1, frequency_in_minutes),
          'last_update_timestamp': time.time()
      }
      self.jobs.append(new_job)
      await interaction.response.send_message(
          content=
          f"Message with ID {message_id_int} will now be kept at the bottom of this channel and updated every {new_job['update_frequency']} minute(s).",
          ephemeral=True)
      await self.save_job(interaction.guild_id)
    except ValueError:
      await interaction.response.send_message(
          content=
          f"Invalid message ID: {message_id}. Please ensure it's a valid integer.",
          ephemeral=True)

  @tasks.loop(seconds=60)
  async def keep_message_at_bottom(self):
    for guild in self.client.guilds:
      await self.load_jobs(guild.id)
      for job in self.jobs:
        if time.time(
        ) - job['last_update_timestamp'] >= job['update_frequency'] * 60:
          channel = self.client.get_channel(job['channel_id'])
          if channel:
            try:
              messages = [msg async for msg in channel.history(limit=1)]
              if messages:
                last_message = messages[0]
                if last_message.id != job['message_id']:
                  message = await channel.fetch_message(job['message_id'])
                  await message.delete()
                  embeds = message.embeds
                  new_message = await channel.send(
                      content=message.content,
                      embeds=embeds,
                      allowed_mentions=discord.AllowedMentions.none())
                  job['message_id'] = new_message.id
                  job['last_update_timestamp'] = time.time()
              await self.save_job(guild.id)  # Save changes per guild basis
            except (discord.NotFound, discord.Forbidden,
                    discord.HTTPException) as e:
              print(
                  f"Error keeping message at bottom for channel {job['channel_id']}: {e}"
              )

  @keep_message_at_bottom.before_loop
  async def before_keep_message_at_bottom(self):
    await self.client.wait_until_ready()

  @app_commands.command(
      name="stop_pinning",
      description="Stops pinning the message to the bottom of the chat")
  async def stoppinning(self, interaction: discord.Interaction):
    await self.load_jobs(
        interaction.guild_id
    )  # Load the current guild's jobs before displaying them
    # Create View
    view = View()
    # Create Select Menu and add it to the view
    select = PinJobSelect(custom_id="select",
                          placeholder="Choose a message to stop pinning",
                          min_values=1,
                          max_values=1,
                          jobs=self.jobs,
                          client=self.client)
    view.add_item(select)
    await interaction.response.send_message(
        view=view, content="Select a message to unpin:", ephemeral=True)


async def setup(client: commands.Bot) -> None:
  await client.add_cog(PinMessages(client))
