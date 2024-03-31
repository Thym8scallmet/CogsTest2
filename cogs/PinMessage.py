import json
import time

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Select, View


class PinJobSelect(Select):
    def __init__(self, jobs, **kwargs):
        super().__init__(**kwargs)
        self.jobs = jobs
        for job in jobs:
            self.add_option(label=f"Message ID: {job['message_id']}", description=f"Channel ID: {job['channel_id']}", value=str(job['message_id']))

    async def callback(self, interaction: discord.Interaction):
        selected_message_id = int(self.values[0])
        self.view.stop()  # Stops the view and prevents any further interaction
        for job in self.jobs:
            if job['message_id'] == selected_message_id:
                self.jobs.remove(job)
                await interaction.client.get_cog("PinMessages").save_job()
                break
        await interaction.response.send_message(f"Stopped pinning message {selected_message_id} and removed from jobs.", ephemeral=True)


class PinMessages(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client
        self.jobs = []  # Now stores multiple pin jobs
        self.jobs_file_path = 'cogs/cogfiles/pinjobs.json'
        self.keep_message_at_bottom.start()

    @commands.Cog.listener()
    async def on_ready(self):
        print("PinMessages cog is ready.")
        await self.load_jobs()

    async def load_jobs(self):
        try:
            with open(self.jobs_file_path, 'r') as f:
                loaded_jobs = json.load(f)
                if isinstance(loaded_jobs, list) and all(isinstance(item, dict) for item in loaded_jobs):
                    self.jobs = loaded_jobs
                else:
                    raise ValueError("Loaded jobs are not in the expected format (list of dictionaries).")
        except FileNotFoundError:
            print("No jobs file found, starting fresh.")
        except (Exception, ValueError) as e:
            print(f"Failed to load jobs due to {e}")

    async def save_job(self):
        with open(self.jobs_file_path, 'w') as f:
            json.dump(self.jobs, f)

    @app_commands.command(name="pin_message", description="Pins a message to the bottom of the chat and allows specifying update frequency")
    async def pinbottom(self, interaction: discord.Interaction, message_id: str, frequency_in_minutes: int = 10):
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
                content=f"Message with ID {message_id_int} will now be kept at the bottom of this channel and updated every {new_job['update_frequency']} minute(s).",
                ephemeral=True)
            await self.save_job()
        except ValueError:
            await interaction.response.send_message(
                content=f"Invalid message ID: {message_id}. Please ensure it's a valid integer.",
                ephemeral=True)

    @tasks.loop(seconds=60)
    async def keep_message_at_bottom(self):
        for job in self.jobs:
            if time.time() - job['last_update_timestamp'] >= job['update_frequency'] * 60:
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
                                await self.save_job()
                    except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
                        print(f"Error keeping message at bottom for channel {job['channel_id']}: {e}")

    @keep_message_at_bottom.before_loop
    async def before_keep_message_at_bottom(self):
        await self.client.wait_until_ready()

    @app_commands.command(name="stop_pinning", description="Stops pinning the message to the bottom of the chat")
    async def stoppinning(self, interaction: discord.Interaction):
        # Create View
        view = View()
        # Create Select Menu and add it to the view
        select = PinJobSelect(custom_id="select", placeholder="Choose a message to stop pinning", min_values=1, max_values=1, jobs=self.jobs)
        view.add_item(select)
        await interaction.response.send_message(view=view, content="Select a message to unpin:", ephemeral=True)

async def setup(client: commands.Bot) -> None:
    await client.add_cog(PinMessages(client))