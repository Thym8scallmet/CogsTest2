import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View

class HelpSelect(Select):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        # Embed dictionary for each help command
        help_embeds = {
            'mill_depletion_help': discord.Embed(
                title="Alliance Mill Depletion Instructions",
                description=("-Users can use the included command `/screenshot_timer` for a one minute timer-\n\n"
                             "The `/rss_depletion` command will ask for 2 values. To obtain these values:\n\n"
                             "- Take a screenshot of your alliance's Resource mill's View Details page.\n"
                             "- After one minute, take another screenshot of the same page.\n\n"
                             "Once you have your screenshots, use the `/rss_depletion` command.\n\n"
                             "The command will bring up a form asking you to provide 2 values.\n"
                             "Enter the information requested by the form, and the bot will\n"
                             "calculate and display the time until resource depletion.\n")),
            'purge_command_help': discord.Embed(
                title="Purge Command Instructions",
                description=("The `/purge` command can be used to delete messages from a channel.\n\n"
                             "To use the purge command, you need to have the admin role or manage messages permission.\n\n"
                             "For the purge command to work, it must have the following Permissions:\n"
                             "1. Manage Messages\n2. View channel\n3. Read Message History\n4. Send Messages\n\n"
                             "Use:\n"
                             "- The /purge command to delete messages in a channel including messages older than 14 days.\n"
                             "- If there are several messages older than 14 days, please be patient as the\n"
                             "process may take some time to complete.\n\n"
                             "If you plan to purge a large number of messages, it is recommended to do it in\n"
                             "several separate batches to avoid rate limiting.\n")),
            'flag_capture_help': discord.Embed(
                title="Flag Capture Lineup Instructions",
                description=("-Flag Capture Lineup is a command that can take alliance players along with their flag capture march might and return 3 lanes. 2 lanes will be made up of your strongest players balanced between 2 lanes and the 3rd lane will contain the rest of the players.-\n\n"
                             "Flag Capture Lineup must be set up properly to work. To set it up, use the `/player_upkeep` command:\n\n"
                             "- Click on add player and then click `name`. Type the player name in the name box.\n"
                             "- Click outside the box in the discord chat input area and then click on `might`.\n"
                             "- Type in the players Flag Capture Might found in the Flag Capture `View Deployment` screen in PNS.\n"
                             "Once you have all your players added and their Flag Capture might added \n"
                             "use the `/flag_capture_lineup` command to get your lane assignments\n\n"
                             "     Use the `/display_players` command to see a list of the players\n"
                             "     you have currently added\n\n"
                             "     Use the `/remove_player` command to remove players by typing in the\n"
                             "     first letter of the player name in the `name` box and then choosing\n"
                             "     the player from the drop down screen.\n\n"
                             "     Use the `/adjust_player_might` command in much the same way:\n"
                             "     Click `name`, and type in the first letter of that players name\n"
                             "     Choose the player from the drop down screen.\n"
                             "     Then click `might` and type in the new player might\n\n"
                             " If you have a list of players with their Flag Capture Might\n"
                             " use the `/feedback` command to request the list be added for your bot.\n\n"
                             "**Known issue**\n"
                             "If for some reason lane 1 shows 19 players and lane 2 shows 21 players\n"
                             "remove a player from your list of players and run the `/flag_capture_line up`\n"
                             "command and then re-add the player. Doing this should update the Player list\n"
                             "and correctly display the lane assignments.")),
            'sstimer_help': discord.Embed(
                title="Screenshot Timer Instructions",
                description=("`/ss_timer` is simply a one minute timer to help with timing your screenshot \n"
                             "before using the `/rss_depletion` command.\n\n")),
            'tile_reset_help': discord.Embed(
                title="Tile Reset Instructions",
                description=("The `/tile_reset` command takes the minutes and seconds that are displayed \n"
                             "on the event timer when tile reset occurs. It converts that number into clock time\n"
                             "and then displays what time tile reset will occur, and when the next tile reset will be.\n\n"
                             "the input format is MM:SS, where MM is the number of minutes and SS is the number of seconds.\n\n"
                             "     example: /tile_reset 19:43\n"
                             "     output: Tile reset is: 40 minutes and 17 seconds after the hour.\n")),
            'feedback_help': discord.Embed(
                title="Feedback Instructions",
                description=("The `/feedback` command is for providing feedback\n"
                             "or reporting errors to the bot developer\n\n"
                             "Please provide your feedback or report\n"
                             "a bug in the `feedback_details` box'")),
            'get_send_flag_data_help': discord.Embed(
                title="Get/Send Flag Data Information",
                description=("The `/get_flag_data` and `/send_flag_data` commands are server specific\n"
                             "commands. They can only be run by administrators with the admin role\n\n"
                             "The function of these commands is to retrieve or send data to a linked\n"
                             "Google sheets spreadsheet\n\n"
                             "Adding the function for other servers to have spreadsheets is in development.\n"
                             "If you would like your server to have a linked spreadsheet for Flag Capture data\n"
                             "please use the `/feedback` command and request access to this feature.\n")),
        }
        embed = help_embeds.get(self.values[0])
        await interaction.response.send_message(embed=embed, ephemeral=True)


class BotHelp(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="phx_bot_help", description="Displays help for bot commands.")
    async def help_command(self, interaction: discord.Interaction):
        view = View()
        select = HelpSelect(
            placeholder="Choose a command to get help on...",
            options=[
                discord.SelectOption(label="Mill Depletion Help", value="mill_depletion_help"),
                discord.SelectOption(label="Purge Command Help", value="purge_command_help"),
                discord.SelectOption(label="Flag Capture Help", value="flag_capture_help"),
                discord.SelectOption(label="Screenshot Timer Help", value="sstimer_help"),
                discord.SelectOption(label="Tile Reset Help", value="tile_reset_help"),
                discord.SelectOption(label="Feedback Help", value="feedback_help"),
                discord.SelectOption(label="Get/Send Flag Data Help", value="get_send_flag_data_help"),
            ]
        )
        view.add_item(select)
        await interaction.response.send_message("Select the command you need help with:", view=view, ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(BotHelp(client))