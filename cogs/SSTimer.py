import asyncio
import discord
from discord import app_commands
from discord.ext import commands

class SSTimer(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="sstimer", description="Gives a one minute timer for taking a screenshot")
    async def sstimer(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)  # Defer the response
        msg = await interaction.followup.send("Starting screenshot timer. Get ready to take your screenshot.", ephemeral=True)

        await asyncio.sleep(2)  # Initial delay before countdown starts

        # First screenshot countdown
        for i in range(3, 0, -1):
            await msg.edit(content=f"Take your screenshot in {i}...")
            await asyncio.sleep(1)

        await msg.edit(content="Take your screenshot now!")

        # Calculate the remaining time until the second screenshot to keep the total time to 60s
        remaining_time_for_second_screenshot = 55  # This can be adjusted if necessary

        # Second screenshot countdown
        for i in range(remaining_time_for_second_screenshot, 0, -5):
            await asyncio.sleep(5)
            if i <= 10:  # Start final countdown when 10 seconds are left, accounting for the final 5s countdown and 2s pause
                break
            await msg.edit(content=f"Get ready to take your second screenshot in {i}...")

        await asyncio.sleep(2)  # Short wait before the final countdown, adjust this as needed

        # Final countdown for the second screenshot
        for i in range(3, 0, -1):
            await msg.edit(content=f"Take your second screenshot in {i}...")
            await asyncio.sleep(1)
          
        await asyncio.sleep(1) #added one second delay here to adjust timing
        await msg.edit(content="Take your second screenshot now!")
        await asyncio.sleep(2)  # Wait before final message, adjust to ensure timings match

        await msg.edit(content="Screenshot Timer has Finished")

async def setup(client: commands.Bot) -> None:
    await client.add_cog(SSTimer(client))