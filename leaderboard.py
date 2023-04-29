#!/usr/bin/python3

#     Leaderboard for H1emu servers
#     Copyright (C) 2023  Doogs
#
#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; version 2 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License along
#     with this program; if not, write to the Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import asyncio
import discord
from discord import Intents
from pymongo import MongoClient
from dataclasses import dataclass
from beautifultable import BeautifulTable
import configparser

config = configparser.ConfigParser()  # Set the config variable
config.read('config.ini')  # Read the config file
DatabaseIP: str = config['MongoDB']['DatabaseIP']  # Set the DatabaseIP from config file
DatabasePort: str = config['MongoDB']['DatabasePort']  # Set the DatabasePort from config file
RemoveKillsByBannedPlayers: bool = bool(config['Banned Players'][
                                            'RemoveKillsByBannedPlayers'])  # Set the RemoveKillsByBannedPlayers variable from config file
RemoveKillsByBannedPlayersReason: list = config['Banned Players']['RemoveKillsByBannedPlayersReason'].split(
    ',')  # Import list of ban reasons to remove banned player kills from the database separated by a comma
Token: str = config['Discord']['Token']  # Set the Token variable from the config file
channel_id: int = int(config['Discord']['ChannelId'])  # set the channel_id variable from config file
leaderboard_size: int = int(
    config['Leaderboard']['LeaderboardSize'])  # set the leaderboard_size variable from config file
seconds_between_updates: int = int(
    config['Leaderboard']['SecondsBetweenUpdates'])  # set the seconds_between_updates variable from config file
sort_by: str = config['Leaderboard']['SortBy']  # set the sort_by variable from config file

client = discord.Client(intents=Intents.default())  # create the discord client/bot and declare the intents
KillLeaderboard = []  # Create KillLeaderboard list


@client.event
async def on_ready():  # runs when discord bot has connected
    print('Logged in as {0.user}'.format(client))  # inform the user that the bot has connected with a username
    channel = client.get_channel(channel_id)  # get the channel to post leaderboard to
    async for prev_message in channel.history():  # iterate though messages in the channel
        if prev_message.author == client.user:  # check if bot is the author of the message
            await prev_message.delete()  # delete the bot's previous message
            break  # stop iterating though messages
    txt = process_string_for_discord(get_kill_leaderboard(0, leaderboard_size))  # generate the message
    message = await client.get_channel(channel_id).send(txt)  # post the leaderboard into discord
    asyncio.create_task(update_message(message))  # start the loop for updating the leaderboard


async def update_message(message):  # updates the leaderboard on a timed loop
    while True:
        await asyncio.sleep(seconds_between_updates)  # Wait for given time in seconds
        txt = process_string_for_discord(get_kill_leaderboard(0, leaderboard_size))  # generate the message
        await message.edit(content=txt)  # edit the bot's previous post to display the new information


@dataclass
class Player(object):  # define Player class
    Name: str = ""  # create Name variable
    Kills: int = 0  # create Kills variable
    Deaths: int = 0  # create Deaths variable
    KD: float = 0  # create KD variable
    ID: str = ""  # create ID variable used to link a player's loginSessionId


def get_database():  # Create a connection to the database
    connection_string: str = "mongodb://" + DatabaseIP + ':' + DatabasePort  # Set MongoDB address
    print("[MongoDB]: Connecting to " + connection_string)  # display the database we are connecting to
    try:
        mongodb_client = MongoClient(connection_string)  # Connect to MongoDB
        print("[MongoDB]: Connected.")  # inform us that we have connected to the database
        return mongodb_client['h1server']  # Connect to database collection named h1server
    except Exception as ee:
        print('[MongoDB]: Connection Failed: ' + str(ee))  # inform the user of a connection failure


def calculate_kills():  # Calculate number of kills by each player and add them to the Leaderboard
    kill_list = kills_db.find()  # Collect all documents in the kills collection into a list
    for item in kill_list:  # Iterate though all documents containing a kill record
        if item['type'] == 'player':  # Confirms that the kill was a player and not a zombie
            player_exists_in_leaderboard: bool = False  # Variable for tracking if the player exist in the leaderboard
            for player in KillLeaderboard:  # Iterate though all players in the leaderboard
                if item['loginSessionId'] == player.ID and item[
                        'characterName'] == player.Name:  # Find player in leaderboard
                    player.Kills += 1  # Increase the player's kill count by one
                    player_exists_in_leaderboard = True  # Confirm that the player has been found in the leaderboard
            if not player_exists_in_leaderboard:  # Player was not found in the leaderboard
                player = Player(Name=item['characterName'], Kills=1, Deaths=0,
                                ID=item['loginSessionId'])  # Initialize the player to add to the leaderboard
                KillLeaderboard.append(player)  # Add the player to the leaderboard
    return


def calculate_deaths():  # Calculate number of deaths by each player and add them to the Leaderboard
    item_details = kills_db.find()  # Collect all documents in the kills collection into a list
    for item in item_details:  # Iterate though all documents containing a kill record
        if item['type'] == 'player':  # Confirms that the kill was a player and not a zombie
            # player_exists_in_leaderboard: bool = False  # Variable for tracking if the player exist in the leaderboard
            for listPlayer in KillLeaderboard:  # Iterate though all players in the leaderboard
                if item['playerKilled'] == listPlayer.Name:  # Find player in leaderboard
                    listPlayer.Deaths += 1  # Increase the player's death count by one
    return


def calculate_kd():  # Calculate the kill/death ratio of players
    for player in KillLeaderboard:  # Iterate though all players in the leaderboard
        if player.Kills > 0 and player.Deaths > 0:  # Check if the player has at-least one kill and one death
            player.KD = player.Kills / player.Deaths  # Set the player's K/D by diving kills by deaths
    return


def get_kill_leaderboard(start=0, end=20):  # Return a leaderboard sorted by number of kills
    table = BeautifulTable()  # Create a variable to store the table
    KillLeaderboard.clear()  # Clear the list
    count = 0  # Variable for tracking the number of current entry in the leaderboard
    calculate_kills()  # Calculate number of kills by each player and add them to the Leaderboard
    calculate_deaths()  # Calculate number of deaths by each player and add them to the Leaderboard
    calculate_kd()  # Calculate the kill/death ratio of players
    if sort_by == 'kills':
        KillLeaderboard.sort(key=lambda x: x.Kills, reverse=True)  # Sort the leaderboard by number of kills
    elif sort_by == 'deaths':
        KillLeaderboard.sort(key=lambda x: x.Deaths, reverse=True)  # Sort the leaderboard by number of deaths
    elif sort_by == 'kd':
        KillLeaderboard.sort(key=lambda x: x.KD, reverse=True)  # Sort the leaderboard by number of K/D
    for player in KillLeaderboard:  # Iterate though all players in the leaderboard
        if count < end or end == 0:  # Check if the leaderboard has reached the desired size (0 = unlimited)
            if count >= start:  # Check if we have reached the desired starting position of the leaderboard
                if player.Kills > 0:  # Check that the player has more at-least one kill
                    table.rows.append(
                        [str(count + 1), player.Name, str(player.Kills), round(player.KD, 2), player.Deaths])
            count += 1  # Increase the position counter by one
    table.columns.header = (["#", "Player", "Kills", "K/D", "Deaths"])
    table.columns.alignment = BeautifulTable.ALIGN_RIGHT
    table.columns.alignment['Player'] = BeautifulTable.ALIGN_LEFT
    table.set_style(BeautifulTable.STYLE_COMPACT)
    leaderboard = str(table)
    return leaderboard


def remove_banned_player_kills():  # Remove kills by players that have been banned for a reason stated in config.ini
    if RemoveKillsByBannedPlayers:  # Check if banned players' kills should be removed from database
        print("Removing kills by players that have been banned for the following reasons: " + str(
            RemoveKillsByBannedPlayersReason))
        banned_db = dbname["banned"]  # Select database collection that contains banned players
        banned_list = banned_db.find()  # Import entries into a list
        for ban in banned_list:  # Iterate through list of banned players
            if ban['expirationDate'] == 0 and ban['active']:  # Check if the ban is permanent
                if RemoveKillsByBannedPlayersReason != "any":  # Check if filtering by ban reason
                    for reason in RemoveKillsByBannedPlayersReason:  # Iterate though all reasons given
                        if ban['banReason'] == reason:  # Check if player's ban matches a reason
                            target = {"loginSessionId": ban['loginSessionId']}  # Target banned player's loginSessionId
                            kills_db.delete_many(target)  # Delete all kills by player's loginSessionId

                else:  # Remove kill entries by banned players regardless of ban reason
                    target = {"loginSessionId": ban['loginSessionId']}  # Target banned player's loginSessionId
                    kills_db.delete_many(target)  # Delete all documents containing player's loginSessionId in kills
    return


def process_string_for_discord(txt):  # Makes sure the text will fit into a discord message and display monospaced
    txt = ':\n`' + txt  # add a character, start a new line and start monospaced formatting of the text
    if len(txt) > 1999:  # check if the text is too long to display in a discord message
        txt = txt[:1999]  # trim the text to 1999 characters
        lines = txt.splitlines()  # split the text by each new line
        txt = "\n".join(lines[:-1])  # remove the last line because it would have been cutoff
    txt = txt + '`'  # enclose the text with monospaced formatting
    return txt  # return the processed text as output from the function


if sort_by != 'kills' and sort_by != 'deaths' and sort_by != 'kd':  # Check if SortBy config is valid
    print(
        "SortBy is set to " + "'%s'" % sort_by + ". Possible settings are 'kills', 'deaths' or 'kd'.  Defaulting to SortBy = kills")
    sort_by = 'kills'  # Default to sorting by number of kills

try:
    dbname = get_database()  # Connect to database collection named h1server
    kills_db = dbname["kills"]  # Connect to database collection that contains records of player kills
    remove_banned_player_kills()  # Remove kills by players that have been banned for a reason stated in config.ini

except Exception as e:
    print('Failed to import data from database: ' + str(e))  # inform the user that the database is inaccessible


client.run(Token)  # START THE BOT =D
