import json, discord, sys, asyncio, requests, pytz
from pickle import NONE
from datetime import datetime, timezone, timedelta
from discord.ui import Modal, TextInput, View, Button
from discord.ext import commands
from discord import app_commands
from turtle import title

intents = discord.Intents.all()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix=".", intents=intents)

config = None
join_times = {}
last_seen_in_vc = {}
activity_file = 'activity.json'

def load_activity_data():
    """Load activity data from a JSON file."""
    try:
        with open(activity_file, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_activity_data(data):
    """Save activity data to a JSON file."""
    with open(activity_file, 'w') as file:
        json.dump(data, file, indent=4)

activity_data = load_activity_data()

class ConfirmActionModal(Modal):
    def __init__(self, action_type, member, user, view):
        super().__init__(title=f"Confirm {action_type}")

        # Store the action type, member, user, and view
        self.action_type = action_type
        self.member = member
        self.user = user
        self.view = view

        # Add a text input to the modal to confirm the action
        self.confirmation = TextInput(
            label=f"Type '{action_type}' to confirm",
            style=discord.TextStyle.short,  # single line text input
            required=True,
            placeholder=f"Type '{action_type}' here...",
        )
        self.add_item(self.confirmation)

        # Add a text input to the modal for entering a reason
        self.reason = TextInput(
            label="Enter Reason",
            style=discord.TextStyle.paragraph,  # multi-line text input
            required=True,
            placeholder="Enter the reason for this action...",
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        payload = {
            "Discord ID": interaction.user.id,  # Banning user
            "targetDiscordID": self.member.id,      # Target user to be banned
            "role": "ban_usr",
            "Api-Key": "THIS IS THE API KEY"
        }

        RBAC_URL = f"http://{config.API['IP_ADDR']}:{config.API['Port']}/api/RBAC"
        response = requests.get(url=RBAC_URL, json=payload)  # Send the request to the API
        response_data = response.json()

        print(response_data)

        if response_data['status'] == 404:
            await interaction.response.send_message(embed=discord.Embed(description="You don't have perms to run this command!", color=discord.Color.yellow()))
            return
        
        if response_data['status'] == 403:
            await interaction.response.send_message(embed=discord.Embed(description="You cannot ban a user with the same or higher rank than yourself!", color=discord.Color.red()))
            return
        
        if response_data['status'] == 500:
            await interaction.response.send_message(embed=discord.Embed(description="Internal Server Error", color=discord.Color.red()))
            return


        # Check if the user typed the correct confirmation
        if self.confirmation.value == self.action_type:
            # Retrieve the original embed and update it
            embed = interaction.message.embeds[0]
            embed.add_field(name="Action Taken", value=self.user.display_name, inline=True)
            embed.add_field(name="Reason", value=self.reason.value, inline=True)
            embed.add_field(name="Type of Action", value=self.action_type, inline=True)  # Update the embed with the action type
            await interaction.message.edit(embed=embed)
            self.view.disable_all_buttons()  # Disable the buttons after confirmation
            await interaction.message.edit(view=self.view)  # Update the message with disabled buttons

            # Ban logic
            already_banned = False
            failed_guilds = []

            for guild_id in config.GUILD_IDS:
                guild = bot.get_guild(int(guild_id))
                if guild:
                    try:
                        if not already_banned:
                            await guild.fetch_ban(discord.Object(id=self.member.id))
                            already_banned = True
                    except discord.NotFound:
                        try:
                            await guild.ban(discord.Object(id=self.member.id), reason=self.reason.value)
                        except discord.Forbidden:
                            failed_guilds.append(guild.name)
                else:
                    failed_guilds.append(f"Guild with ID {guild_id}")


            # Continue with the API call
            payload = {
                "Discord ID": self.member.id,
                "resignation": self.action_type.split()[0],
                "Reason": self.reason.value,
                "banned_by": str(interaction.user.id),
                "case_number": None, # add to the confirmation
                "ban_type": "Permanent",
                "Api-Key": "THIS IS THE API KEY"
            }

            print(payload)

            endpoint = f"http://{config.API['IP_ADDR']}:{config.API['Port']}/api/discord/ban"
            response = requests.post(url=endpoint, json=payload)
            response_data = response.json()

            print(response_data["status"])

            if response_data['status'] == 200:
                await interaction.response.send_message(content=f"{self.action_type} confirmed.", ephemeral=True)
                return

            if response_data['status'] == 404:
                await interaction.response.send_message(embed=discord.Embed(description="You don't have perms to run this command!", color=discord.Color.yellow()))
                return
            
            if response_data['status'] == 403:
                await interaction.response.send_message(embed=discord.Embed(description="You cannot ban a user with the same or higher rank than yourself!", color=discord.Color.red()))
                return
            
            if response_data['status'] == 500:
                #await interaction.response.defer(ephemeral=True)
                print(f"Internal Server Error - {response_data['error']}")
                return

class LeaveMemberView(View):
    def __init__(self, member):
        super().__init__(timeout=86400)
        self.member = member

    @discord.ui.button(label="Proper Res", style=discord.ButtonStyle.green)
    async def proper_res(self, interaction: discord.Interaction, button: Button):
        await self.show_confirmation(interaction, "Proper Resignation")

    @discord.ui.button(label="Improper Res", style=discord.ButtonStyle.red)
    async def improper_res(self, interaction: discord.Interaction, button: Button):
        await self.show_confirmation(interaction, "Improper Resignation")

    @discord.ui.button(label="Ban Member", style=discord.ButtonStyle.danger)
    async def ban_member(self, interaction: discord.Interaction, button: Button):
        await self.show_confirmation(interaction, "Banned")

    async def show_confirmation(self, interaction: discord.Interaction, action_type):
        # Open the modal for confirmation
        modal = ConfirmActionModal(action_type, self.member, interaction.user, self)
        await interaction.response.send_modal(modal)

    def disable_all_buttons(self):
        for item in self.children:
            item.disabled = True

class BanInfoView(View):
    def __init__(self, website_ids, resignation_types, resignation_dates, resignation_counts, 
                 processed_by, users_primary_departments, membership_durations, notes, 
                 membership_history_ids, ia_case_files, community_discipline_records, interaction):
        super().__init__()
        self.website_ids = website_ids or []
        self.resignation_types = resignation_types or []
        self.resignation_dates = resignation_dates or []
        self.resignation_counts = resignation_counts or []
        self.processed_by = processed_by or []
        self.users_primary_departments = users_primary_departments or []
        self.membership_durations = membership_durations or []
        self.notes = notes or []
        self.membership_history_ids = membership_history_ids or []
        self.ia_case_files = ia_case_files or []
        self.community_discipline_records = community_discipline_records or []
        self.interaction = interaction  # Store interaction for context
        self.index = 0

        # Add navigation buttons with unique custom IDs
        self.previous_button = Button(label="Previous", style=discord.ButtonStyle.primary, custom_id="previous_button")
        self.next_button = Button(label="Next", style=discord.ButtonStyle.primary, custom_id="next_button")

        self.previous_button.callback = self.previous
        self.next_button.callback = self.next

        self.add_item(self.previous_button)
        self.add_item(self.next_button)


    def generate_embed(self):
        website_id = self.website_ids[self.index] if self.website_ids else "N/A"
        resignation_type = self.resignation_types[self.index] if self.resignation_types else "N/A"
        resignation_date = self.resignation_dates[self.index] if self.resignation_dates else "N/A"
        resignation_count = self.resignation_counts[self.index] if self.resignation_counts else "N/A"
        processed_by = self.processed_by[self.index] if self.processed_by else "Unknown"
        users_primary_department = self.users_primary_departments[self.index] if self.users_primary_departments else "N/A"
        membership_duration = self.membership_durations[self.index] if self.membership_durations else "N/A"
        note = self.notes[self.index] if self.notes else "No notes provided"
        membership_history_id = self.membership_history_ids[self.index] if self.membership_history_ids else "N/A"
        ia_case_file = self.ia_case_files[self.index] if self.ia_case_files else "N/A"
        community_discipline_record = self.community_discipline_records[self.index] if self.community_discipline_records else "N/A"


        # Check if resignation_date is not "N/A" and then format it
        if resignation_date != "N/A":
            # Convert from ISO format to datetime object
            resignation_date = datetime.fromisoformat(resignation_date[:-1])
            # Format the date as MM-DD-YYYY
            resignation_date = resignation_date.strftime("%m-%d-%Y")

        name = "Insert Name"

        banned_user_payload = {
            "Api-Key": "THIS IS THE API KEY",
            "websiteID": website_id
        }

        
        processed_by_payload = {
            "Api-Key": "THIS IS THE API KEY",
            "websiteID": processed_by
        }



        banned_user_id = requests.get(url=f"http://{config.API['IP_ADDR']}:{config.API['Port']}/api/discord/websiteID/to/discordID", json=banned_user_payload)
        banned_user_id_response = banned_user_id.json()
        if banned_user_id_response['status'] != 200:
            return 


        processed_by_id = requests.get(url=f"http://{config.API['IP_ADDR']}:{config.API['Port']}/api/discord/websiteID/to/discordID", json=processed_by_payload)
        processed_by_id_response = processed_by_id.json()
        if processed_by_id_response['status'] != 200:
            return 


        embed = discord.Embed(color=discord.Color.blue(), 
            title=f"Cases For: {name}", 
            description=f"""
                ### __User Information__
                > **Website ID: [{website_id}](https://sokrpcommunity.com/profile/{website_id}) | <@!{banned_user_id_response['discordID']}> **
                ### __Resignation Information__
                > **Resignation Type: {resignation_type}
                > Processed By: [{processed_by}](https://sokrpcommunity.com/profile/{processed_by}) | <@!{processed_by_id_response['discordID']}>
                > Resignation Date: {resignation_date}**
                ### __Membership Information__
                > **Primary Department: {users_primary_department}
                > Notes: {note}
                > Membership Duration: {str(membership_duration) + " Days"}**
                ### __Community Discipline Record:__
                > **{community_discipline_record}**
                ### IA Case File:
                > **{ia_case_file}**
            """
        )

        embed.set_footer(icon_url="https://media.discordapp.net/attachments/1260497668669706292/1260497883501826068/SOKRP_Dev_Seal-01.png?ex=66d611e2&is=66d4c062&hm=943d7d76ae6b99f64a7e57660c1c4edbb1f2f9e428c75ba8cf16629e37c0caab&=&format=webp&quality=lossless&width=676&height=676")
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1260497668669706292/1262683848831926293/PD_Psd_1.png?ex=66d573f9&is=66d42279&hm=86dc6ac5d2ddbc0a5a62adaec30e65422c16a4b14f104d7200f6ff2207493ed3&=&format=webp&quality=lossless&width=676&height=676")
        embed.set_footer(text=f"Record {self.index + 1} of {len(self.website_ids)}")

        return embed


    async def previous(self, interaction: discord.Interaction):
        if self.website_ids:
            if self.index > 0:
                self.index -= 1
            else:
                self.index = len(self.website_ids) - 1
            try:
                await interaction.response.edit_message(embed=self.generate_embed(), view=self)
            except discord.errors.InteractionResponded:
                pass

    async def next(self, interaction: discord.Interaction):
        if self.website_ids:
            if self.index < len(self.website_ids) - 1:
                self.index += 1
            else:
                self.index = 0
            try:
                await interaction.response.edit_message(embed=self.generate_embed(), view=self)
            except discord.errors.InteractionResponded:
                pass


    def get_member_mention(self, member_id):
        guild = self.interaction.guild  # Use self.interaction to access the guild context
        member = guild.get_member(member_id)
        if member:
            return member.mention
        return f"<@{member_id}>"


def format_duration(duration_seconds):
    duration = timedelta(seconds=duration_seconds)
    days = duration.days
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days > 0:
        return f"{days} days, {hours} hours, {minutes} minutes"
    elif hours > 0:
        return f"{hours} hours, {minutes} minutes"
    elif minutes > 0:
        return f"{minutes} minutes"
    else:
        return f"{seconds} seconds"

async def IA_SPY():
    ia_guild = bot.get_guild(config.IA_GUILD)

    for guild_id in config.GUILD_IDS:
        guild = bot.get_guild(guild_id)
        if guild:
            for category_name, channel_ids in config.COC_Channels.items():
                # Check if category exists in IA_GUILD
                target_category = discord.utils.get(ia_guild.categories, name=category_name)
                if not target_category:
                    target_category = await ia_guild.create_category(category_name)

                for channel_id in channel_ids:
                    channel = discord.utils.get(guild.channels, id=channel_id)
                    if channel and isinstance(channel, discord.TextChannel):
                        # Check if the channel name already exists in the target category
                        target_channel = discord.utils.get(target_category.text_channels, name=channel.name)
                        if target_channel:
                            print(f"Channel already exists in category: {target_channel.name}")
                        else:
                            print(f"Creating channel: {channel.name}")
                            await target_category.create_text_channel(channel.name)    

@bot.event
async def on_ready():
    print(f"Bot in runnig in {len(config.GUILD_IDS)} guilds.")
    
    try:
        synced = await bot.tree.sync()
        print(f"synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
        
    await IA_SPY()

    while True:
        try:
            interaction = await bot.wait_for("button_click")
            await bot.process_commands(interaction)
        except asyncio.TimeoutError:
            pass

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Load activity data
    activity_data = load_activity_data()
    activity_data.setdefault('last_message_time', {})[str(message.author.id)] = datetime.now(timezone.utc).isoformat()
    save_activity_data(activity_data)

    ia_guild = bot.get_guild(config.IA_GUILD)

    # Find the corresponding target channel in the IA guild
    for category_name, channel_ids in config.COC_Channels.items():
        if message.channel.id in channel_ids:
            target_category = discord.utils.get(ia_guild.categories, name=category_name)
            if target_category:
                target_channel = discord.utils.get(target_category.text_channels, name=message.channel.name)
                if target_channel:
                    await target_channel.send(f"{message.author.name}: {message.content}")
                    break

    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel != after.channel:
        if before.channel is None:
            # Member joined a voice channel
            channel = bot.get_channel(config.LOG_JOIN_VC)  # Replace with your log channel ID
            if channel:
                embed = discord.Embed(title="Member Joined VC", description=f"{member.mention} joined {after.channel.name}", color=discord.Color.green())
                await channel.send(embed=embed)
            
            # Record join time
            join_times[member.id] = datetime.now(timezone.utc)
        
        elif after.channel is None:
            # Member left a voice channel
            channel = bot.get_channel(config.LOG_LEAVE_VC)  # Replace with your log channel ID
            if channel:
                if member.id in join_times:
                    join_time = join_times.pop(member.id)
                    duration = datetime.now(timezone.utc) - join_time
                    duration_str = format_duration(duration.total_seconds())
                    embed = discord.Embed(title="Member Left VC", description=f"{member.mention} left {before.channel.name}, Duration: {duration_str}", color=discord.Color.red())
                    await channel.send(embed=embed)
                else:
                    print(f"Unexpected state: {member.display_name} left {before.channel.name} without a recorded join time")
        
        else:
            # Member switched voice channels
            channel = bot.get_channel(config.LOG_LEAVE_VC)  # Replace with your log channel ID
            if channel:
                if member.id in join_times:
                    join_time = join_times[member.id]
                    duration = datetime.now(timezone.utc) - join_time
                    duration_str = format_duration(duration.total_seconds())
                    embed = discord.Embed(title="Member Switched VC's", description=f"{member.mention} left {before.channel.name}, Duration: {duration_str}", color=discord.Color.orange())
                    await channel.send(embed=embed)
                else:
                    print(f"Unexpected state: {member.display_name} left {before.channel.name} without a recorded join time")
                
                # Log joining the new voice channel
                channel = bot.get_channel(config.LOG_JOIN_VC)  # Replace with your log channel ID
                if channel:
                    embed = discord.Embed(title="Member Joined VC", description=f"{member.mention} joined {after.channel.name}", color=discord.Color.green())
                    await channel.send(embed=embed)
                
                # Update join time for the new channel
                join_times[member.id] = datetime.now(timezone.utc)
                print(f"{member.display_name} joined {after.channel.name} at {join_times[member.id]}")

@bot.event
async def on_message_edit(before, after):
    # Check if the message content was edited
    if before.content != after.content:
        channel = bot.get_channel(config.LOG_EDIT_CHANNEL_ID)  # Replace with your log channel ID
        if channel:
            embed = discord.Embed(title="Message Edited", color=discord.Color.gold())
            embed.add_field(name="Before", value=before.content, inline=False)
            embed.add_field(name="After", value=after.content, inline=False)
            embed.add_field(name="Editor", value=after.author.mention, inline=False)  # Assuming you want to mention the editor

            await channel.send(embed=embed)
        
        ia_guild = bot.get_guild(config.IA_GUILD)

        # Find the corresponding target channel in the IA guild
        for category_name, channel_ids in config.COC_Channels.items():
            if before.channel.id in channel_ids:
                target_category = discord.utils.get(ia_guild.categories, name=category_name)
                if target_category:
                    target_channel = discord.utils.get(target_category.text_channels, name=before.channel.name)
                    if target_channel:
                        embed = discord.Embed(title="Edited Message", color=discord.Color.gold())
                        embed.add_field(name="Before", value=before.content, inline=False)
                        embed.add_field(name="After", value=after.content, inline=False)
                        embed.add_field(name="Editor", value=after.author.mention, inline=False)
                        
                        await target_channel.send(embed=embed)
                        break

@bot.event
async def on_message_delete(message):
    # Logging deleted messages
    channel = bot.get_channel(config.LOG_DELETE_CHANNEL_ID)  # Replace with your log channel ID
    if channel:
        embed = discord.Embed(title="Message Deleted", color=discord.Color.red())
        embed.add_field(name="Content", value=message.content, inline=False)
        embed.add_field(name="Deletor", value=message.author.mention, inline=False)  # Use message.author to get the user who deleted the message

        await channel.send(embed=embed)
    
    ia_guild = bot.get_guild(config.IA_GUILD)

    # Find the corresponding target channel in the IA guild
    for category_name, channel_ids in config.COC_Channels.items():
        if message.channel.id in channel_ids:
            target_category = discord.utils.get(ia_guild.categories, name=category_name)
            if target_category:
                target_channel = discord.utils.get(target_category.text_channels, name=message.channel.name)
                if target_channel:
                    embed = discord.Embed(title="Deleted Message", color=discord.Color.red())
                    embed.add_field(name="Content", value=message.content, inline=False)
                    embed.add_field(name="Deletor", value=message.author.mention, inline=False)
                    
                    await target_channel.send(embed=embed)
                    break
   
@bot.event
async def on_member_join(member):
    needs_verification_role = discord.utils.get(member.guild.roles, name="Needs Verification")
    
    if needs_verification_role:
        await member.add_roles(needs_verification_role)
    else:
        print("Role 'needs verification' does not exist.")

    payload = {
        "Discord ID": str(member.id),
        "Api-Key": "THIS IS THE API KEY"
    }

    try:
        response = requests.post(url=f"http://{config.API['IP_ADDR']}:{config.API['Port']}/api/discord/get/nick", json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        response_data = response.json()

        main_guild = bot.get_guild(config.DEV_GUILD)  # Retrieve the guild object
        category_name = "All Logs"
        text_name = "bot-logs"

        if response_data.get('nick'):
            # Update the member's nickname in Discord
            await member.edit(nick=response_data['nick'])
        else:
            # Handle missing nickname (send message to bot-commands channel)
            target_category = discord.utils.get(main_guild.categories, name=category_name)
            if target_category:
                target_channel = discord.utils.get(target_category.text_channels, name=text_name)
                if target_channel:
                    await target_channel.send(
                        embed=discord.Embed(
                            description=f"Error - User {member.mention} is missing either name or Call-Sign",
                            color=discord.Color.red()
                        )
                    )
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        # Optionally, log the error in the bot-commands channel
        target_category = discord.utils.get(main_guild.categories, name=category_name)
        if target_category:
            target_channel = discord.utils.get(target_category.text_channels)
            if target_channel:
                await target_channel.send(
                    embed=discord.Embed(
                        description=f"API request failed for {member.mention}: {str(e)}",
                        color=discord.Color.red()
                    )
                )

@bot.event
async def on_member_remove(member):
    guild = member.guild

    if guild.id != config.MAIN_GUILD:
        return

    channel = bot.get_channel(config.LOG_LEAVE_SERVER)

    payload = {
        "Discord ID": str(member.id),
        "Api-Key": "THIS IS THE API KEY"
    }

    RBAC_URL = f"http://{config.API['IP_ADDR']}:{config.API['Port']}/api/discord/member/leave"
    response = requests.get(url=RBAC_URL, json=payload)  # Send the request to the API
    response_data = response.json()

    # Check if the member was banned
    was_banned = False
    async for ban_entry in guild.bans():
        if ban_entry.user.id == member.id:
            was_banned = True
            break

    if channel:
        embed = discord.Embed(
            title="A Member of our Community Left!",
            color=discord.Color.red()
        )
        
        # Add fields for NickName and Discord ID
        embed.add_field(name="Name", value=member.display_name, inline=True)
        embed.add_field(name="Website ID", value=response_data['WebsiteID']['WebsiteID'], inline=True)
        embed.add_field(name="Discord ID", value=member.id, inline=True)

        # Calculate membership duration
        join_date = member.joined_at
        leave_date = datetime.utcnow().replace(tzinfo=timezone.utc)  # Make utcnow offset-aware
        membership_duration = leave_date - join_date
        
        # Convert membership duration to a human-readable format
        days = membership_duration.days
        hours, remainder = divmod(membership_duration.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        duration_str = f"{days} days, {hours} hours, {minutes} minutes"

        embed.add_field(name="Membership Duration", value=duration_str, inline=False)
        
        # Prepare roles for mention and listing in the embed
        roles_to_mention = [role.mention for role in member.roles if role.name != "@everyone"]
        
        if roles_to_mention:
            roles_str = ", ".join(roles_to_mention)
        else:
            roles_str = "No Roles"

        # Add fields for All Roles and Pinged Roles
        embed.add_field(name='Users Roles', value=roles_str if roles_str else "No Roles", inline=False)
        
        # Check for config roles to mention in content
        roles_to_ping_in_content = [
            role.mention for role in member.roles if role.id in [
                config.All_Departments, 
                config.Development, 
                config.Media_Team, 
                config.State_Police, 
                config.Sheriffs_Office, 
                config.Police_Department, 
                config.Central_Dispatch, 
                config.Fire_Department, 
                config.Civilian
            ]
        ]

        content_ping = " ".join(roles_to_ping_in_content) if roles_to_ping_in_content else None

        # Add footer with timestamp
        embed.set_footer(
            text="SOKRP Warden", 
            icon_url="https://sokrpcommunity.com/ECRP-Website/asset/main-logo.png"
        )
        embed.timestamp = discord.utils.utcnow()

        if was_banned:
            embed.add_field(name="Note", value="This user was banned from the server.", inline=False)
            await channel.send(embed=embed)
        else:
            view = LeaveMemberView(member)  # Create the view with buttons
            # Send the message with content ping if available
            if content_ping:
                await channel.send(content=content_ping, embed=embed, view=view)
            else:
                await channel.send(embed=embed, view=view)

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel != after.channel:
        activity_data = load_activity_data()

        if before.channel is None:
            # Member joined a voice channel
            channel = bot.get_channel(config.LOG_JOIN_VC)  # Replace with your log channel ID
            if channel:
                embed = discord.Embed(title="Member Joined VC", description=f"{member.mention} joined {after.channel.name}", color=discord.Color.green())
                await channel.send(embed=embed)
            
            # Record join time
            join_times[member.id] = datetime.now(timezone.utc)
            activity_data.setdefault('last_seen_in_vc', {})[str(member.id)] = datetime.now(timezone.utc).isoformat()

        elif after.channel is None:
            # Member left a voice channel
            channel = bot.get_channel(config.LOG_LEAVE_VC)  # Replace with your log channel ID
            if channel:
                if member.id in join_times:
                    join_time = join_times.pop(member.id)
                    duration = datetime.now(timezone.utc) - join_time
                    duration_str = format_duration(duration.total_seconds())
                    embed = discord.Embed(title="Member Left VC", description=f"{member.mention} left {before.channel.name}, Duration: {duration_str}", color=discord.Color.red())
                    await channel.send(embed=embed)
                else:
                    print(f"Unexpected state: {member.display_name} left {before.channel.name} without a recorded join time")
            activity_data.setdefault('last_seen_in_vc', {})[str(member.id)] = datetime.now(timezone.utc).isoformat()

        else:
            # Member switched voice channels
            channel = bot.get_channel(config.LOG_LEAVE_VC)  # Replace with your log channel ID
            if channel:
                if member.id in join_times:
                    join_time = join_times[member.id]
                    duration = datetime.now(timezone.utc) - join_time
                    duration_str = format_duration(duration.total_seconds())
                    embed = discord.Embed(title="Member Switched VC's", description=f"{member.mention} left {before.channel.name}, Duration: {duration_str}", color=discord.Color.orange())
                    await channel.send(embed=embed)
                else:
                    print(f"Unexpected state: {member.display_name} left {before.channel.name} without a recorded join time")
                
                # Log joining the new voice channel
                channel = bot.get_channel(config.LOG_JOIN_VC)  # Replace with your log channel ID
                if channel:
                    embed = discord.Embed(title="Member Joined VC", description=f"{member.mention} joined {after.channel.name}", color=discord.Color.green())
                    await channel.send(embed=embed)
                
                # Update join time for the new channel
                join_times[member.id] = datetime.now(timezone.utc)
                activity_data.setdefault('last_seen_in_vc', {})[str(member.id)] = datetime.now(timezone.utc).isoformat()
                print(f"{member.display_name} joined {after.channel.name} at {join_times[member.id]}")

        save_activity_data(activity_data)

@bot.tree.command(name="ban", description="Ban a member from all servers.")
@app_commands.describe(
    id="Discord ID of the member to ban", 
    resignation="Resignation status", 
    reason="Reason for the ban", 
    case_number="Optional case number for tracking purposes", 
    ban_type="Type of ban (Temporary or Permanent)"
)
@app_commands.choices(resignation=[
    app_commands.Choice(name="Proper", value="Proper"),
    app_commands.Choice(name="Improper", value="Improper"),
    app_commands.Choice(name="Banned", value="Banned")
])
@app_commands.choices(ban_type=[
    app_commands.Choice(name="Temporary", value="Temporary"),
    app_commands.Choice(name="Permanent", value="Permanent")
])
async def ban(
    interaction: discord.Interaction, 
    id: str, 
    resignation: app_commands.Choice[str], 
    reason: str, 
    case_number: str,  
    ban_type: app_commands.Choice[str]
):
    # Your ban command logic here
    try:
        discord_id = int(id)
        payload = {
            "Discord ID": str(interaction.user.id),  # Banning user
            "role": "ban_usr",
            "Api-Key": "THIS IS THE API KEY"
        }

        RBAC_URL = f"http://{config.API['IP_ADDR']}:{config.API['Port']}/api/RBAC"
        response = requests.get(url=RBAC_URL, json=payload)  # Send the request to the API
        response_data = response.json()

        if response_data['status'] == 404:
            await interaction.response.send_message(embed=discord.Embed(description="You don't have perms to run this command!", color=discord.Color.yellow()))
            return
        
        if response_data['status'] == 403:
            await interaction.response.send_message(embed=discord.Embed(description="You cannot ban a user with the same or higher rank than yourself!", color=discord.Color.red()))
            return
        
        if response_data['status'] == 500:
            await interaction.response.send_message(embed=discord.Embed(description=f"Internal Server Error - {response_data['error']}", color=discord.Color.red()))
            return

        # Continue with the ban logic if permission is granted
        payload = {
            "Discord ID": str(interaction.user.id),
            "resignation": resignation.value,
            "Reason": reason,
            "banned_by": str(interaction.user.id),
            "case_number": case_number,
            "ban_type": ban_type.value,
            "targetDiscordID": discord_id,      # Target user to be banned
            "Api-Key": "THIS IS THE API KEY"
        }

        await interaction.response.defer()

        endpoint = f"http://{config.API['IP_ADDR']}:{config.API['Port']}/api/discord/ban"
        response = requests.post(url=endpoint, json=payload)
        response_data = response.json()

        if response_data['status'] == 200:
            banned = False
            already_banned = False

            for guild_id in config.GUILD_IDS:
                guild = bot.get_guild(int(guild_id))
                if guild:
                    try:
                        if not already_banned:
                            await guild.fetch_ban(discord.Object(id=discord_id))
                            already_banned = True
                    except discord.NotFound:
                        await guild.ban(discord.Object(id=discord_id), reason=reason)
                        banned = True
                    except discord.Forbidden:
                        await interaction.followup.send(embed=discord.Embed(description="I don't have permission to ban", color=discord.Color.red()))
                else:
                    await interaction.followup.send(embed=discord.Embed(description=f"Could not find guild with ID {guild_id}", color=discord.Color.red()))

            if banned:
                await interaction.followup.send(embed=discord.Embed(description=f"Banned member with ID {discord_id} in all discords.\nReason: {reason}\nBan Type: {ban_type.value}", color=discord.Color.red()))
            elif not already_banned:
                await interaction.followup.send(embed=discord.Embed(description=f"Could not ban member with ID {discord_id} in any guild.", color=discord.Color.red()))

            if already_banned:
                await interaction.followup.send(embed=discord.Embed(description=f"Member with ID {discord_id} is already banned.", color=discord.Color.red()))

        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Error - {response_data['error']}.", color=discord.Color.red()))

    except ValueError:
        await interaction.followup.send(embed=discord.Embed(description=f"Invalid Discord ID: {id}", color=discord.Color.red()))
    except discord.HTTPException as e:
        await interaction.followup.send(embed=discord.Embed(description=f"An error occurred: {str(e)}", color=discord.Color.red()))
    except requests.exceptions.RequestException as e:
        await interaction.followup.send(embed=discord.Embed(description=f"API request failed: {str(e)}", color=discord.Color.red()))

@bot.tree.command(name='member_count', description='Return Member Count.')
async def memberCount(interaction: discord.Integration):
    payload = {
        "Api-Key": "THIS IS THE API KEY"
    }
    response = requests.get(url=f"http://{config.API['IP_ADDR']}:{config.API['Port']}/api/discord/get/member/count", json=payload)
    data = response.json()
    MemberCount = data['MemberCount']['MemberCount']
        
    await interaction.response.send_message(embed=discord.Embed(description=f"Member Count: {MemberCount}", color=discord.Color.green()))

@bot.tree.command(name='live', description='You are live streaming')
async def live(interaction: discord.Interaction):
    guild = interaction.guild  # Correctly get the guild object

    role = discord.utils.get(guild.roles, name='Live')
    if role:
        await interaction.user.add_roles(role)
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Successfully added the Live Role! Go get em {interaction.user.display_name} 😎", 
                color=discord.Color.green()
            )
        )
    else:
        await interaction.response.send_message(
            embed=discord.Embed(
                description="Role not found", 
                color=discord.Color.red()
            )
        )

@bot.tree.command(name='stop_live', description='You stopped live streaming')
async def stop_live(interaction: discord.Interaction):
    guild = interaction.guild  # Correctly get the guild object

    role = discord.utils.get(guild.roles, name='Live')
    if role:
        await interaction.user.remove_roles(role)
        await interaction.response.send_message(embed=discord.Embed(description=f"Successfully Removed Live Role :smiling_face_with_tear: you should get back on server... ", color=discord.Color.red()))
        
@bot.tree.command(name='clear', description='Delete Messages')
@app_commands.describe(amount='Enter Number of messages:')
async def clear(interaction: discord.Interaction, amount: int):
    payload = {
        "Discord ID": interaction.user.id,  # Banning user
        "role": "execute_clear_command",
        "Api-Key": "THIS IS THE API KEY"
    }

    RBAC_URL = f"http://{config.API['IP_ADDR']}:{config.API['Port']}/api/RBAC"
    response = requests.get(url=RBAC_URL, json=payload)  # Send the request to the API
    response_data = response.json()

    if response_data['status'] == 404:
        await interaction.response.send_message(embed=discord.Embed(description="You don't have perms to run this command!", color=discord.Color.yellow()))
        return
    
    if response_data['status'] == 403:
        await interaction.response.send_message(embed=discord.Embed(description="You cannot ban a user with the same or higher rank than yourself!", color=discord.Color.red()))
        return
    
    if response_data['status'] == 500:
        await interaction.response.send_message(embed=discord.Embed(description=f"Internal Server Error - {response_data['error']}", color=discord.Color.red()))
        return

    channel = interaction.channel

    if amount <= 0:
        await interaction.response.send_message("Please enter a positive number of messages to delete.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    try:
        deleted = await channel.purge(limit=amount)

        if len(deleted) == 0:
            await interaction.followup.send("No messages to delete.")
        else:
            await interaction.followup.send(f"Deleted {len(deleted)} messages.")

    except discord.Forbidden:
        await interaction.followup.send("I don't have permission to delete messages in this channel.")
    except discord.HTTPException as e:
        await interaction.followup.send(f"Failed to delete messages due to an error: {e}")

@bot.tree.command(name='dep_info', description='Important links')
@app_commands.choices(dep_info=[
    app_commands.Choice(name="MCSO", value='MCSO'),
    app_commands.Choice(name="MPD", value='MPD'),
    app_commands.Choice(name="CIV", value='CIV'),
    app_commands.Choice(name="KSP ", value='KSP')
])
async def dep_info(interaction: discord.Interaction, dep_info: app_commands.Choice[str]):
    dep_description = config.dep_info[dep_info.value][0]
    img = config.dep_info[dep_info.value][1]
    thumbnail = config.dep_info[dep_info.value][2]
    footer = config.dep_info[dep_info.value][3]
    dep_color = int(config.dep_info[dep_info.value][4], 16) if len(config.dep_info[dep_info.value]) > 1 else 0xFFFFFF  # default to white if no color is provided

    embed = discord.Embed(
        title=dep_info.value, 
        description=dep_description, 
        color=discord.Color(dep_color)
    )

    if img:
        embed.set_image(url=img)
    
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)

    if footer:
        embed.set_footer(text=footer, icon_url="https://i.gyazo.com/f5f8e859ffa4564284e6ca24efeae43c.png")

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="nick", description="Change a member's nickname")
@app_commands.describe(id="Discord ID of the user", name="New nickname")
async def nick(interaction: discord.Interaction, id: str, name: str):
    payload = {
        "Discord ID": interaction.user.id,  # Banning user
        "role": "ban_usr",
        "Api-Key": "THIS IS THE API KEY"
    }

    RBAC_URL = f"http://{config.API['IP_ADDR']}:{config.API['Port']}/api/RBAC"
    response = requests.get(url=RBAC_URL, json=payload)  # Send the request to the API
    response_data = response.json()

    if response_data['status'] == 404:
        await interaction.response.send_message(embed=discord.Embed(description="You don't have perms to run this command!", color=discord.Color.yellow()))
        return
    
    if response_data['status'] == 403:
        await interaction.response.send_message(embed=discord.Embed(description="You cannot ban a user with the same or higher rank than yourself!", color=discord.Color.red()))
        return
    
    if response_data['status'] == 500:
        await interaction.response.send_message(embed=discord.Embed(description=f"Internal Server Error - {response_data['error']}", color=discord.Color.red()))
        return


    discord_id = int(id)  # Convert to integer
    found_member = False  # Track if the member is found in any guild
    message_sent = False

    for guild_id in config.GUILD_IDS:
        guild = bot.get_guild(guild_id)
        if guild:
            member = guild.get_member(discord_id)
            if member:
                found_member = True

                # Check if the bot has permission to manage nicknames in the guild
                bot_member = guild.get_member(bot.user.id)
                if bot_member.guild_permissions.manage_nicknames:
                    # Check role hierarchy: the bot's highest role must be higher than the target member's highest role
                    if bot_member.top_role > member.top_role:
                        try:
                            await member.edit(nick=name)
                            if not message_sent:
                                await interaction.response.send_message(
                                    embed=discord.Embed(
                                        description=f"Nickname for {member.mention} has been changed to: {name}",
                                        color=discord.Color.green()
                                    )
                                )
                                message_sent = True
                        except discord.Forbidden:
                            if not message_sent:
                                await interaction.response.send_message(
                                    embed=discord.Embed(
                                        description=f"I don't have permission to change nicknames in {guild.name}.",
                                        color=discord.Color.red()
                                    )
                                )
                                message_sent = True
                        except discord.HTTPException as e:
                            if not message_sent:
                                await interaction.response.send_message(
                                    embed=discord.Embed(
                                        description=f"Failed to change nickname in {guild.name} due to an error: {str(e)}",
                                        color=discord.Color.red()
                                    )
                                )
                                message_sent = True
                    else:
                        if not message_sent:
                            await interaction.response.send_message(
                                embed=discord.Embed(
                                    description=f"My role is not high enough to change nicknames for members with roles higher or equal to mine in {guild.name}.",
                                    color=discord.Color.red()
                                )
                            )
                            message_sent = True
                else:
                    if not message_sent:
                        await interaction.response.send_message(
                            embed=discord.Embed(
                                description=f"I don't have permission to manage nicknames in {guild.name}.",
                                color=discord.Color.red()
                            )
                        )
                        message_sent = True

    if not found_member:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Could not find member with ID {discord_id} in any of the guilds.",
                color=discord.Color.red()
            )
        )

@bot.tree.command(name='unban', description='Unban member from all servers.')
@app_commands.describe(id="Discord ID of the member to unban")
async def unban(interaction: discord.Interaction, id: str):
    payload = {
        "Discord ID": interaction.user.id,  # Banning user
        "role": "ban_usr",
        "Api-Key": "THIS IS THE API KEY"
    }

    RBAC_URL = f"http://{config.API['IP_ADDR']}:{config.API['Port']}/api/RBAC"
    response = requests.get(url=RBAC_URL, json=payload)  # Send the request to the API
    response_data = response.json()

    if response_data['status'] == 404:
        await interaction.response.send_message(embed=discord.Embed(description="You don't have perms to run this command!", color=discord.Color.yellow()))
        return
    
    if response_data['status'] == 403:
        await interaction.response.send_message(embed=discord.Embed(description="You cannot ban a user with the same or higher rank than yourself!", color=discord.Color.red()))
        return
    
    if response_data['status'] == 500:
        await interaction.response.send_message(embed=discord.Embed(description=f"Internal Server Error - {response_data['error']}", color=discord.Color.red()))
        return 
    
    message = True
    
    for guild_id in config.GUILD_IDS:
        guild = bot.get_guild(guild_id)
        if guild:
            user_id = int(id)  # Convert the ID to an integer
            try:
                # Check if the user is banned
                ban_entry = await guild.fetch_ban(discord.Object(id=user_id))
                # If the user is banned, proceed to unban them
                await guild.unban(discord.Object(id=user_id))
                
                if message:
                    await interaction.response.send_message(embed=discord.Embed(description=f"Member has been unbanned from all discords.", color=discord.Color.green()))
                    message = False
                else:
                    continue
            except discord.NotFound:
                # If the user is not banned, send a message indicating this
                if message:
                    await interaction.response.send_message(embed=discord.Embed(description=f"Member with ID {user_id} is not banned.", color=discord.Color.green()))
                    message = False
        else:
            continue

@bot.tree.command(name='seen', description='Shows the last time a user was in a VC or sent a message')
@app_commands.describe(id="Discord ID of the member")
async def seen(interaction: discord.Interaction, id: str):
    payload = {
        "Discord ID": interaction.user.id,  # Banning user
        "role": "execute_seen_command",
        "Api-Key": "THIS IS THE API KEY"
    }

    RBAC_URL = f"http://{config.API['IP_ADDR']}:{config.API['Port']}/api/RBAC"
    response = requests.get(url=RBAC_URL, json=payload)  # Send the request to the API
    response_data = response.json()

    if response_data['status'] == 404:
        await interaction.response.send_message(embed=discord.Embed(description="You don't have perms to run this command!", color=discord.Color.yellow()))
        return
    
    if response_data['status'] == 403:
        await interaction.response.send_message(embed=discord.Embed(description="You cannot ban a user with the same or higher rank than yourself!", color=discord.Color.red()))
        return
    
    if response_data['status'] == 500:
        await interaction.response.send_message(embed=discord.Embed(description=f"Internal Server Error - {response_data['error']}", color=discord.Color.red()))
        return 

    try:
        member_id = str(int(id))  # Convert to string for JSON key compatibility
    except ValueError:
        await interaction.response.send_message("Invalid ID provided. Please provide a numeric Discord ID.")
        return

    # Load the most recent activity data
    activity_data = load_activity_data()

    # Check both last voice and message activity
    last_seen_voice = activity_data.get('last_seen_in_vc', {}).get(member_id)
    last_seen_message = activity_data.get('last_message_time', {}).get(member_id)

    # Determine the most recent activity
    if last_seen_voice and last_seen_message:
        last_seen_time = max(last_seen_voice, last_seen_message, key=lambda x: datetime.fromisoformat(x))
    elif last_seen_voice:
        last_seen_time = last_seen_voice
    elif last_seen_message:
        last_seen_time = last_seen_message
    else:
        last_seen_time = None

    if last_seen_time:
        last_seen_time = datetime.fromisoformat(last_seen_time)
        # Convert UTC to EST
        est_timezone = pytz.timezone('US/Eastern')
        est_time = last_seen_time.astimezone(est_timezone)
        formatted_time = est_time.strftime('%m/%d/%Y %I:%M:%S %p EST')

        await interaction.response.send_message(embed=discord.Embed(description=f"The user <@{member_id}> was last active at {formatted_time}.", color=discord.Color.green()))
    else:
        await interaction.response.send_message(embed=discord.Embed(description=f"No activity recorded for user <@{member_id}>.", color=discord.Color.red()))

@bot.tree.command(name="new_project", description="Creates a new Project.")
@app_commands.describe(name="Name of Project", link="Link to Plane Card.", ids="Ping Members To Assign")
async def new_project(interaction: discord.Interaction, name: str, link: str, ids: str):
    payload = {
        "Discord ID": interaction.user.id,  # Banning user
        "role": "create_dev_project",
        "Api-Key": "THIS IS THE API KEY"
    }

    guild = interaction.guild.id

    await interaction.response.defer()

    if guild != config.DEV_GUILD:
        await interaction.followup.send(embed=discord.Embed(description="Only run this command in the Dev Discord", color=discord.Color.red()))
        return  # Ensure the command stops execution

    RBAC_URL = f"http://{config.API['IP_ADDR']}:{config.API['Port']}/api/RBAC"
    
    # Error handling for the API request
    try:
        response = requests.get(url=RBAC_URL, json=payload)
        response.raise_for_status()  # Check for HTTP errors
        response_data = response.json()
    except requests.RequestException as e:
        await interaction.followup.send(embed=discord.Embed(description=f"Failed to communicate with the API: {e}", color=discord.Color.red()))
        return

    # Permission checks
    if response_data.get('status') == 404:
        await interaction.followup.send(embed=discord.Embed(description="You don't have permissions to run this command!", color=discord.Color.yellow()))
        return
    
    if response_data.get('status') == 403:
        await interaction.followup.send(embed=discord.Embed(description="You cannot ban a user with the same or higher rank than yourself!", color=discord.Color.red()))
        return
    
    if response_data.get('status') == 500:
        await interaction.followup.send(embed=discord.Embed(description=f"Internal Server Error - {response_data['error']}", color=discord.Color.red()))
        return 

    members = interaction.guild.members

    # When a selection is made, remove <@> and validate the IDs
    id_list = ids.split(">")
    id_list = [id.replace("<@", "").replace(">", "").strip() for id in id_list]
    id_list.pop(len(id_list)-1)

    # Validate if the IDs correspond to real members
    valid_members = []
    for user_id in id_list:
        member = discord.utils.get(members, id=int(user_id))
        if member:
            valid_members.append(member.mention)
        else:
            await interaction.followup.send(embed=discord.Embed(description=f"Invalid member ID: {user_id}", color=discord.Color.red()))
            return
    
    # Get the current date and format it to EST time
    current_date = datetime.now(timezone.utc)
    est_timezone = pytz.timezone('US/Eastern')
    est_time = current_date.astimezone(est_timezone)
    formatted_time = est_time.strftime('%m/%d/%Y')

    # Create the embed message
    embed = discord.Embed(
        title=f"Project: {name}",
        description=f"""
        >>> Assigned Developers: {', '.join(valid_members)}
        Plane Card Link: [Link]({link})
        Assigned on: {formatted_time}
        """,
        color=discord.Color.blue()
    )
    embed.set_footer(icon_url="https://sokrpcommunity.com/ECRP-Website/asset/server_logo.png", text="Development Command")

    # Find the "Projects" category
    category = discord.utils.get(interaction.guild.categories, name="Projects")
    if category is None:
        await interaction.followup.send(embed=discord.Embed(description="The 'Projects' category does not exist. Please create it first.", color=discord.Color.red()))
        return

    # Create the new text channel under the "Projects" category
    new_channel = await interaction.guild.create_text_channel(name=name, category=category)
    
    # Send the embed message to the new channel
    await new_channel.send(embed=embed)

    # Send a link to the new channel in the channel where the command was executed
    await interaction.followup.send(f"""
                                    ### Project: {name} Created! 
                                    > Assigned Members: {', '.join(valid_members)}
                                    > Project Channel: {new_channel.mention}""")

@bot.tree.command(name='cases_for', description='Get info on banned members.')
@app_commands.describe(id="Discord ID of the member to get info on")
async def info(interaction: discord.Interaction, id: str):
    payload = {
        "Discord ID": interaction.user.id,  # Banning user
        "role": "create_dev_project",
        "Api-Key": "THIS IS THE API KEY"
    }

    RBAC_URL = f"http://{config.API['IP_ADDR']}:{config.API['Port']}/api/RBAC"
    response = requests.get(url=RBAC_URL, json=payload)  # Send the request to the API
    response_data = response.json()



    if response_data['status'] == 404:
        await interaction.followup.send(embed=discord.Embed(description="You don't have perms to run this command!", color=discord.Color.yellow()))
        return
    
    if response_data['status'] == 403:
        await interaction.followup.send(embed=discord.Embed(description="You cannot ban a user with the same or higher rank than yourself!", color=discord.Color.red()))
        return
    
    if response_data['status'] == 500:
        await interaction.followup.send(embed=discord.Embed(description=f"Internal Server Error - {response_data['error']}", color=discord.Color.red()))
        return 
    
    
    user_id = int(id)
    
    payload = {
        "discord_id": user_id,
        "Api-Key": "THIS IS THE API KEY"
    }

    # Ensure the URL has the proper schema
    endpoint = f"http://{config.API['IP_ADDR']}:{config.API['Port']}/api/discord/cases_for"
    headers = {'Content-Type': 'application/json'}  # Adjust headers as necessary


    response = requests.get(url=endpoint, json=payload, headers=headers)
    data = response.json()

    if data['status'] != 200:
        await interaction.response.send_message(embed=discord.Embed(description=f"Error - {data['error']}", color=discord.Color.red()))
        return


    website_ids = data.get('WebsiteIds', [])
    resignation_types = data.get('ResignationTypes', [])
    resignation_dates = data.get('ResignationDates', [])
    resignation_counts = data.get('ResignationCounts', [])
    processed_by = data.get('ProcessedBy', [])
    users_primary_departments = data.get('UsersPrimaryDepartments', [])
    membership_durations = data.get('MembershipDurations', [])
    notes = data.get('Notes', [])
    membership_history_ids = data.get('MembershipHistoryIds', [])
    ia_case_files = data.get('IACaseFiles', [])
    community_discipline_records = data.get('CommunityDisciplineRecords', [])

    view = BanInfoView(website_ids, resignation_types, resignation_dates, resignation_counts, processed_by, users_primary_departments, membership_durations, notes, membership_history_ids, ia_case_files, community_discipline_records, interaction)

    await interaction.response.send_message(embed=view.generate_embed(), view=view)

@bot.tree.command(name='sync', description='Upadte Discord Roles.')
async def sync(interaction: discord.Integration):
    payload = {
        "Discord ID": interaction.user.id
    }

    response = requests.get(url=f"http://{config.API['IP_ADDR']}:{config.API['Port']}/api/discord/verify", json=payload)
    data = response.json()

    roleList = data.get("RoleList", [])
    guild = interaction.guild  # Correctly get the guild object
    notFound = []
    noName = False
    
    for role_name in roleList:
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            await interaction.user.add_roles(role)
        else:
          Noname = True
          notFound.append(role_name)  
          
    result = ", ".join(notFound)

    
    if noName:
        await interaction.response.send_message(embed=discord.Embed(description="Roles updated successfully", color=discord.Color.green()))
    else:
        await interaction.response.send_message(embed=discord.Embed(description=f"Role(s) don't exist: {result}", color=discord.Color.red()))

@bot.tree.command(name='update_ha', description='Upadte HA Google Sheets')
async def update_ha(interaction: discord.Integration):
    payload = {
        "Discord ID": interaction.user.id,  # Banning user
        "role": "sudo_web_admin",
        "Api-Key": "THIS IS THE API KEY"
    }

    RBAC_URL = f"http://{config.API['IP_ADDR']}:{config.API['Port']}/api/RBAC"
    response = requests.get(url=RBAC_URL, json=payload)  # Send the request to the API
    response_data = response.json()

    if response_data['status'] == 404:
        await interaction.response.send_message(embed=discord.Embed(description="You don't have perms to run this command!", color=discord.Color.yellow()))
        return
    
    if response_data['status'] == 403:
        await interaction.response.send_message(embed=discord.Embed(description="You cannot ban a user with the same or higher rank than yourself!", color=discord.Color.red()))
        return
    
    if response_data['status'] == 500:
        await interaction.response.send_message(embed=discord.Embed(description=f"Internal Server Error - {response_data['error']}", color=discord.Color.red()))
        return 
    
    
    payload = {
        "Api-Key": "THIS IS THE API KEY"
    }

    url = f"http://{config.API['IP_ADDR']}:{config.API['Port']}/api/discord/update/HA/roster"

    response = requests.post(url=url, json=payload)
    response_json = response.json()


    if response_json['status'] != 200:
        await interaction.response.send_message(embed=discord.Embed(description=f"Error: {response_json['error']}", color=discord.Color.red()))

    await interaction.response.send_message(embed=discord.Embed(description="HA Google Sheets updated Successfully!", color=discord.Color.green()))



if __name__ == '__main__':
    import config
    bot.run(config.DISCORD_TOKEN)
