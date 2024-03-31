from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands


class Feedback(commands.Cog):

  def __init__(self, client: commands.Bot):
    self.client = client
    self.owner_id = int(
        '383364055433478154'
    )  # Convert string to integer

  @app_commands.command(
      name="feedback",
      description="Provide feedback or report an issue about the bot.")
  @app_commands.describe(feedback_details="Your feedback or issue report.")
  async def feedback_command(self, interaction: discord.Interaction,
                             feedback_details: str):
    # Include user and time in the feedback message
    user = interaction.user
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    feedback_message = (f"Feedback received from {user} ({user.id}) at {timestamp}:\n"
                        f"{feedback_details}")

    # Attempt to send feedback to the bot owner
    owner = await self.client.fetch_user(self.owner_id)
    if owner:
      try:
        await owner.send(feedback_message)
        await interaction.response.send_message(
            "Your feedback has been forwarded to the bot owner. Thank you!",
            ephemeral=True)
      except discord.HTTPException as e:
        print(f"Error sending feedback to bot owner: {e}")
        await interaction.response.send_message(
            "An error occurred while forwarding your feedback.",
            ephemeral=True)
    else:
      await interaction.response.send_message(
          "Bot owner could not be found. Feedback not sent.", ephemeral=True)


async def setup(client: commands.Bot) -> None:
  await client.add_cog(Feedback(client))