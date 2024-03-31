import asyncio
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Button, Modal, Select, TextInput, View


class VotePoll(commands.Cog):

  def __init__(self, client: commands.Bot):
    self.client = client
    self.active_polls = []

  async def finalize_poll(self, poll):
    await asyncio.sleep((poll.end_time - datetime.now()).total_seconds())
    final_embed = create_poll_embed(poll)
    channel_id, message_id = poll.message_details
    channel = self.client.get_channel(channel_id)
    message = await channel.fetch_message(message_id)
    await message.edit(content="Poll Ended!", embed=final_embed, view=None)
    self.active_polls.remove(poll)


class Poll:

  def __init__(self, title, options, roles, visibility, duration,
               message_details):
    self.title = title
    self.options = options
    self.roles = roles
    self.visibility = visibility
    self.end_time = datetime.now() + timedelta(minutes=duration)
    self.votes = {}
    self.message_details = message_details  # Tuple (channel_id, message_id)


class VotingModal(Modal):
    def __init__(self, cog):  # Pass the cog instance during initialization
        self.cog = cog  # Store the cog instance
        super().__init__(title="Create a Vote Poll")
        self.add_item(TextInput(label="Enter the Title of the Poll", placeholder="Enter the title", required=True))
        for i in range(4):
            self.add_item(TextInput(label=f"Option {i + 1}", placeholder="Enter an option", required=True))

    async def on_submit(self, interaction: discord.Interaction):
        title = self.children[0].value
        options = {}
        for i in range(1, 5):
            if i < len(self.children) and self.children[i].value:
                options[str(i)] = [self.children[i].value, 0]

        if options:
            poll = Poll(title=title, options=options, roles=[], visibility=True, duration=60, message_details=(interaction.channel_id, None))
            view = PollView(poll)
            message = await interaction.response.send_message("Poll created!", embed=create_poll_embed(poll), view=view, ephemeral=False)
            if message:
                poll.message_details = (interaction.channel_id, message.id)
                self.cog.active_polls.append(poll)
            else:
                print("Failed to get a message.")
        else:
            await interaction.response.send_message("Please provide options for the poll.", ephemeral=True)

    #asyncio.create_task(self.cog.finalize_poll(poll))


class PollView(View):

    def __init__(self, poll):
        super().__init__()
        for option_id, option in poll.options.items():
            self.add_item(VoteButton(option=option, option_id=option_id, poll=poll))


class VoteButton(Button):

    def __init__(self, option, option_id, poll):
        super().__init__(label=option[0], style=discord.ButtonStyle.primary)
        self.option_id = option_id
        self.poll = poll

    async def callback(self, interaction: discord.Interaction):
        if self.poll.roles and not any(role.id in self.poll.roles
                                       for role in interaction.user.roles):
            return await interaction.response.send_message(
                "You are not allowed to vote in this poll.", ephemeral=True)
        self.poll.votes[interaction.user.id] = self.option_id
        self.poll.options[self.option_id][1] += 1
        if self.poll.visibility:
            await interaction.message.edit(embed=create_poll_embed(self.poll))
        await interaction.response.send_message(
            f"Your vote for '{self.poll.options[self.option_id][0]}' has been counted.",
            ephemeral=True)


def create_poll_embed(poll):
    embed = discord.Embed(title=poll.title,
                          description="Vote now!",
                          color=discord.Color.blue())
    for option_id, option in poll.options.items():
        embed.add_field(name=f"Option {option_id}: {option[0]}", value=f'Votes: {option[1]}', inline=False)
    return embed

 
@app_commands.command(name="create_poll", description="Creates a new interactive poll.")
async def create_poll(interaction: discord.Interaction):
    # Retrieve the cog instance from the client instead of using 'vote_poll'
    cog = interaction.client.get_cog('VotePoll')
    if cog:
        modal = VotingModal(cog=cog)  # Pass the cog instance to VotingModal
        await interaction.response.send_modal(modal)
    else:
        print("VotePoll cog not found.")  # Handle the case when VotePoll cog is not found


async def setup(client: commands.Bot):
    vote_poll = VotePoll(client)
    voting_modal = VotingModal(vote_poll)  # Pass vote_poll instance to VotingModal
    await client.add_cog(vote_poll)
    client.tree.add_command(create_poll)
