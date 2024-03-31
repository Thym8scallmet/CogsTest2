import asyncio

import discord
from discord import app_commands
from discord.ext import commands


class PurgeBot(commands.Cog):

  def __init__(self, client: commands.Bot):
    self.client = client

  @app_commands.command(
      name="purge",
      description="Purge recent messages or messages older than 14 days")
  #@app_commands.guilds(
      #discord.Object(id=1045479020940234783),
      #discord.Object(id=383365467894710272))  #Enter Allowed Guild IDs
  async def purge(self, interaction: discord.Interaction, amount: int):
    if not interaction.guild:
      await interaction.response.send_message(
          "This command can only be used within a server.", ephemeral=True)
      return
    member = interaction.guild.get_member(interaction.user.id)
    if member is None:
      await interaction.response.send_message(
          "Could not retrieve member information.", ephemeral=True)
      return
    roles = [role.name for role in member.roles]
    if "Admin" not in roles and not member.guild_permissions.manage_messages:
      await interaction.response.send_message(
          "You do not have the required permissions to use this command.",
          ephemeral=True)
      return
    channel = interaction.channel
    if not isinstance(channel, discord.TextChannel):
      await interaction.response.send_message(
          content="This command can only be used in text channels.")
      return
    permissions = channel.permissions_for(channel.guild.me)
    if not permissions.manage_messages or not permissions.read_message_history:
      await interaction.response.send_message(
          content=
          "Purgebot does not have permissions to manage messages in this channel."
      )
      return

    await interaction.response.send_message(content="Checking messages...")

    older_messages_exist = False
    async for message in channel.history(limit=min(100, amount)):
      if (discord.utils.utcnow() - message.created_at).days > 14:
        older_messages_exist = True
        break

    if older_messages_exist:
      await interaction.followup.send(
          content=
          "Some messages are older than 14 days. Purging will start now. Please be patient as this may take some time.",
          ephemeral=True)

    purged = 0
    while amount > 0:
      messages = [
          message async for message in channel.history(limit=min(100, amount))
      ]
      older_messages = [
          m for m in messages
          if (discord.utils.utcnow() - m.created_at).days > 14
      ]
      recent_messages = [m for m in messages if m not in older_messages]

      if recent_messages:
        try:
          await channel.delete_messages(recent_messages)
          purged += len(recent_messages)
          amount -= len(recent_messages)
        except discord.HTTPException:
          for msg in recent_messages:
            try:
              await msg.delete()
              purged += 1
              amount -= 1
            except discord.HTTPException:
              continue

        await asyncio.sleep(1.5)

      for msg in older_messages:
        try:
          await msg.delete()
          purged += 1
          amount -= 1
        except discord.HTTPException:
          continue

        await asyncio.sleep(1.5)

      if not messages or amount <= 0:
        break

    msg = await interaction.followup.send(content=f'Purged {purged} messages.')
    await asyncio.sleep(7)
    await msg.delete()

  @purge.error
  async def purge_error(self, interaction: discord.Interaction,
                        error: Exception):
    await interaction.response.send_message(
        content=f"An error occurred: {str(error)}", ephemeral=True)


async def setup(client: commands.Bot) -> None:
  await client.add_cog(PurgeBot(client))
