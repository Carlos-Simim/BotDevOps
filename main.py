import json
import disnake

from disnake.ext import commands, tasks
from azure.devops.connection import Connection
from azure.devops.v7_1.work_item_tracking import Wiql
from msrest.authentication import BasicAuthentication

# Create an instance of the Disnake bot
with open("info.json", "r") as file:
    config = json.load(file)

bot_token = config.get("bot_token")
user_id = config.get("user_id")
projeto = config.get("projeto")
personal_access_token = config.get("personal_access_token")
organization_url = config.get("organization_url")

intents = disnake.Intents.default()
intents.message_content = True
bot = commands.Bot(help_command=None, case_insensitive=True, intents=intents, command_prefix="/")
past_tasks = []


@tasks.loop(seconds=30)
async def recurrent_devops_check():
    fecthed_work_item = check_devops()
    if fecthed_work_item is not None and fecthed_work_item.fields['System.Id'] not in past_tasks:
        past_tasks.append(fecthed_work_item.fields['System.Id'])
        dono = await bot.fetch_user(user_id)
        embed = disnake.Embed(title=f"Você tem uma task : {fecthed_work_item.fields['System.Title']}",
                              color=disnake.colour.Color.green())
        await dono.send(embed=embed)
        print("Notificação enviada.")


# Event handler for when the bot is ready
@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user.name}")
    recurrent_devops_check.start()


def check_devops():
    # Fill in with your personal access token and org URL

    # Create a connection to Azure DevOps
    credentials = BasicAuthentication('', personal_access_token)
    connection = Connection(base_url=organization_url, creds=credentials)

    # Get the Work Item Tracking client
    wit_client = connection.clients.get_work_item_tracking_client()

    # Define a WIQL query to find work items assigned to you in the specified project
    wiql_query = Wiql(
        query=f"SELECT [System.Id] FROM WorkItems WHERE [System.AssignedTo] = @Me AND [System.TeamProject] = '{projeto}' AND [System.State] = 'Committed'")

    # Execute the query
    query_result = wit_client.query_by_wiql(wiql_query, top=1000)

    if query_result.work_items:
        work_item_ids = [work_item.id for work_item in query_result.work_items]

        if work_item_ids[-1] not in past_tasks:
            last_id = work_item_ids[-1]
            work_item = wit_client.get_work_item(last_id, expand='all')
            print(work_item.fields['System.Title'])
            return work_item
        else:
            return None
    else:
        print("No work items found in the project.")
        return None


bot.run(bot_token)
