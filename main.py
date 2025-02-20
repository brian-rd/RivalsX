import os
import httpx
import orjson
import asyncio
import discord
import urllib.parse
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, UTC
from collections import Counter
from discord.ext import commands


API_BASE_URL = "https://mrapi.org/api"

async def fetch_hero_data():
    async with httpx.AsyncClient() as client:
        heroes = []
        ids_heroes = {}
        heroes_icons = {}
        url = f"{API_BASE_URL}/heroes"
        response = await client.get(url)
        if response.status_code == 200:
            data = orjson.loads(response.content)
            for hero in data:
                heroes.append(hero["name"])
                ids_heroes[hero["id"]] = hero["name"]
                heroes_icons[hero["name"]] = hero["transformations"][0]["icon"]
        else:
            print(f"Failed to fetch hero data with status {response.status_code}")
        
        return(heroes, ids_heroes, heroes_icons)

HEROES, IDS_HEROES, HEROES_ICONS = asyncio.run(fetch_hero_data())

HEROES_COLORS = {
    "Bruce Banner": "#4A7A3D",
    "The Punisher": "#2B2B2B",
    "Storm": "#D4D4D4",
    "Loki": "#4B6F44",
    "Doctor Strange": "#8B0000",
    "Mantis": "#3FA34D",
    "Hawkeye": "#6B3FA0",
    "Captain America": "#0033A0",
    "Rocket Raccoon": "#704214",
    "Hela": "#0B3D2E",
    "Cloak & Dagger": "#000000",
    "Black Panther": "#101820",
    "Groot": "#8B5A2B",
    "Magik": "#FFD700",
    "Moon Knight": "#C0C0C0",
    "Luna Snow": "#B0E0E6",
    "Squirrel Girl": "#A0522D",
    "Black Widow": "#990000",
    "Iron Man": "#B22222",
    "Venom": "#1A1A1A",
    "Spider-man": "#E60000",
    "Magneto": "#800020",
    "Scarlet Witch": "#FF2400",
    "Thor": "#A9A9A9",
    "Mister Fantastic": "#4169E1",
    "Winter Soldier": "#555555",
    "Peni Parker": "#FF4F00",
    "Star-lord": "#993333",
    "Namor": "#0047AB",
    "Adam Warlock": "#DAA520",
    "Jeff The Land Shark": "#87CEEB",
    "Psylocke": "#4B0082",
    "Wolverine": "#FFD700",
    "Invisible Woman": "#ADD8E6",
    "Iron Fist": "#32CD32"
}

for hero in HEROES:
    if hero not in HEROES_COLORS:
        HEROES_COLORS[hero] = "#000000"
        
RANK_ICONS = {
    "Bronze": "<:1BronzeRank:1337210495085842504>",
    "Silver": "<:2SilverRank:1337210492812267612>",
    "Gold": "<:3GoldRank:1337210490853789786>",
    "Platinum": "<:4PlatinumRank:1337210489079332935>",
    "Diamond": "<:5DiamondRank:1337210680612229172>",
    "Grandmaster": "<:6GrandmasterRank:1337210682286018600>",
    "Celestial": "<:7CelestialRank:1337210684987146272>",
    "Eternity": "<:8EternityRank:1337210686786240512>",
    "One Above All": "<:9OneAboveAllRank:1337210689051299871>"
}


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='r.', intents=intents)
bot.remove_command('help')

@bot.event
async def on_ready():
    servers = bot.guilds
    server_count = str(len(bot.guilds))
    await bot.change_presence(activity=discord.CustomActivity(name=f'r.stats • In {server_count} servers' ,emoji='🖥️'))
    try:
        await bot.tree.sync()
        print(f"Synced slash commands for {bot.user}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    print(f'Logged in as {bot.user}')
    
    activeservers = bot.guilds
    print(f"Bot is online in {server_count} servers: {activeservers}")


class PlayerNotFoundException(Exception):
    """Raised when a player cannot be found via the API."""
    pass

class PrivateProfileException(Exception):
    """Raised when a player's profile is set to private."""
    pass

class APIUpdateFailedException(Exception):
    """Raised when updating player data fails."""
    pass


class MRApiClient:
    """
    Client to interact with MR API.
    """
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def get_player_id(self, name: str) -> dict:
        url = f"{API_BASE_URL}/player-id/{urllib.parse.quote(name)}"
        response = await self.client.get(url)
        if response.status_code != 200:
            print(f"get_player_id failed with status {response.status_code}")
            raise PlayerNotFoundException(f"Player {name} not found.")
        data = orjson.loads(response.content)
        if data.get("id") is None or data.get("name", "").lower() != name.lower():
            raise PlayerNotFoundException(f"Player {name} not found.")
        return data

    async def update_player(self, user_id: str) -> dict:
        url = f"{API_BASE_URL}/player-update/{user_id}"
        response = await self.client.get(url)
        if response.status_code != 200:
            print(f"update_player failed with status {response.status_code}")
            raise APIUpdateFailedException("Failed to update player data.")
        data = orjson.loads(response.content)
        if not data.get("success", False):
            raise APIUpdateFailedException("API update not successful.")
        return data

    async def get_player_stats(self, user_id: str) -> dict:
        url = f"{API_BASE_URL}/player/{user_id}"
        response = await self.client.get(url)
        if response.status_code != 200:
            print(f"get_player_stats failed with status {response.status_code}")
            raise APIUpdateFailedException("Failed to fetch player stats.")
        return orjson.loads(response.content)

    
def parse_stats(data: dict) -> dict:
    """
    Parse player stats JSON from the API into a structured dict.
    """
    if not data or data.get("is_profile_private") is True or not data.get("match_history"):
        player_rank = data.get("stats", {}).get("rank", {}).get("rank")
        if player_rank:
            raise PrivateProfileException(player_rank)
        else:
            return {"Private": "true"}
    
    username = data.get("player_name")
    rank = data["stats"]["rank"]["rank"]
    ranked_stats = data["stats"]["ranked"]
    total_ranked_matches = ranked_stats["total_matches"]
    total_ranked_wins = ranked_stats["total_wins"]
    overall_winrate = round(
        (total_ranked_wins / total_ranked_matches) * 100, 2
    ) if total_ranked_matches > 0 else 0

    hero_stats = data["hero_stats"]
    hero_data = []
    for stats in hero_stats.values():
        ranked = stats.get("ranked")
        if ranked:
            hero_data.append({
                "Hero": stats["hero_name"],
                "Matches": ranked.get("matches", 0),
                "Wins": ranked.get("wins", 0),
                "Losses": ranked.get("matches", 0) - ranked.get("wins", 0),
                "Win Rate (%)": round(
                    (ranked.get("wins", 0) / ranked.get("matches", 1)) * 100, 2
                ) if ranked.get("matches", 0) > 0 else 0,
                "K/D Ratio": float(ranked.get("kdr", 0.0)),
                "MVPs": ranked.get("mvp", 0),
            })

    hero_df = pd.DataFrame(hero_data).fillna({'Matches': 0}).sort_values(
        by="Matches", ascending=False
    )
    top_3_heroes = hero_df.head(3)
    
    # Count recently played heroes and calculate recent win rate
    match_history = data.get("match_history", [])
    recent_heroes = []
    recent_wins = Counter()
    recent_games = Counter()
    for match in match_history:
        hero_id = str(match["stats"]["hero"]["id"])
        if hero_id in hero_stats:
            hero_name = hero_stats[hero_id]["hero_name"]
            recent_heroes.append(hero_name)
            recent_games[hero_name] += 1
            if match["stats"]["is_win"]:
                recent_wins[hero_name] += 1
    
    recent_hero_data = [
        {
            "Hero": hero,
            "Matches in Recent History": count,
            "Win Rate (%)": round((recent_wins[hero] / count) * 100, 2) if count > 0 else 0
        }
        for hero, count in recent_games.items()
    ]
    
    recent_hero_df = pd.DataFrame(recent_hero_data).sort_values(
        by="Matches in Recent History", ascending=False
    ).head(5)

    recent_matches = len(match_history)
    recent_winrate = round((sum(recent_wins.values()) / recent_matches) * 100, 2) if recent_matches > 0 else 0

    results = {
        "Username": username,
        "Private": "false",
        "Rank": rank,
        "Overall Ranked Stats": {
            "Total Ranked Matches": total_ranked_matches,
            "Total Wins": total_ranked_wins,
            "Overall Win Rate (%)": overall_winrate,
        },
        "Top 3 Most Played Heroes in Ranked": top_3_heroes.to_dict(orient="records"),
        "Recently Played Heroes": recent_hero_df.to_dict(orient="records"),
        "Recent Matches Win Rate (%)": recent_winrate,
    }
    return results

def parse_history(data: dict) -> list:
    """
    Parse match history JSON from the API into a structured list.
    """
    if not data or not data.get("match_history"):
        return []

    name = data.get("player_name")
    match_history = data.get("match_history", [])
    parsed_history = []
    for match in match_history:
        kills = match["stats"]["kills"]
        deaths = match["stats"]["deaths"]
        assists = match["stats"]["assists"]

        # Compute KDA ratio (avoiding division by zero)
        kda_ratio = (kills + assists) / deaths if deaths != 0 else (kills + assists)

        parsed_history.append({
            "Name": name,
            "Match Timestamp": datetime.fromtimestamp(match['match_timestamp'], UTC).strftime('%Y-%m-%d %H:%M:%S'),
            "Match Duration": f"{match['match_duration']['minutes']}m {match['match_duration']['seconds']}s",
            "Season": match["season"],
            "Match UID": match["match_uid"],
            "Map": match["match_map"]["name"],
            "Gamemode": match["gamemode"]["name"].title(),
            "Gamemode2": match["match_map"]["gamemode"].title(),
            "Score": f"Ally: {match['score']['ally']} - Enemy: {match['score']['enemy']}",
            "Winner Side": match["winner_side"],
            "Player Side": match["player_side"],
            "MVP UID": match["mvp_uid"],
            "SVP UID": match["svp_uid"],
            "Kills": kills,
            "Deaths": deaths,
            "Assists": assists,
            "Is Win": match["stats"]["is_win"],
            "Hero ID": match["stats"]["hero"]["id"],
            "KDA": f"{kda_ratio:.2f}",
        })
    return parsed_history

async def fetch_history_data(name: str) -> dict:
    """
    Fetch match history data using the MRApiClient.
    """
    async with httpx.AsyncClient() as http_client:
        api_client = MRApiClient(http_client)
        # Get the player ID
        player_data = await api_client.get_player_id(name)
        user_id = player_data["id"]

        # Update player data
        await api_client.update_player(user_id)

        # Fetch detailed player stats
        stats_data = await api_client.get_player_stats(user_id)
        return parse_history(stats_data)
    
def build_history_embeds(history: list) -> discord.Embed:
    """
    Build Discord embeds for the parsed history.
    """
    embeds = []
    if not history:
        return [discord.Embed(title="No match history found.", colour=0xff0000)]
    for match in history:
        if len(embeds) >= 10:
            break
        embed = discord.Embed(
            title='Victory' if match['Is Win'] else 'Defeat' + f" ({match['Name']})",
            url=f"https://tracker.gg/marvel-rivals/matches/{match['Match UID']}",
            colour=discord.Colour(0x5EE790) if match['Is Win'] else discord.Colour(0xE4485D),
            timestamp=datetime.now()
        )

        embed.add_field(
            name="Details",
            value=f"- {match['Gamemode']}\n- **Time**: {match["Match Timestamp"]}\n- **Duration**: {match["Match Duration"]}\n- **Gamemode**: {match["Gamemode2"]}\n- **Map**: {match["Map"]}\n- **Score**: {match["Score"]}",
            inline=True
        )
        embed.add_field(name="Performance",
                        value=f"- **KDA**: {match['KDA']}\n- **Kills**: {match['Kills']}\n- **Deaths**: {match['Deaths']}\n- **Assists**: {match['Assists']}",
                        inline=True)
        hero_id = match["Hero ID"]
        hero_name = IDS_HEROES.get(str(hero_id), "Unknown Hero")
        embed.add_field(name="Heroes Played",
                value=f"- {hero_name}",
                inline=True)
        
        embed.set_thumbnail(url=HEROES_ICONS.get(hero_name, "https://cdn2.steamgriddb.com/icon/916030603cc86a9b3d29f4d64f1bc415/32/256x256.png"))
        embed.set_footer(
            text="Powered by RivalsX",
            icon_url="https://cdn2.steamgriddb.com/icon/916030603cc86a9b3d29f4d64f1bc415/32/256x256.png"
        )
        embeds.append(embed)
    return embeds
        
def build_embed(results: dict) -> discord.Embed:
    """
    Build a Discord embed from the parsed stats.
    """
    username = results["Username"]
    rank = results.get("Rank", "Unranked")
    rank_tier = ''.join(filter(str.isalpha, rank))
    rank_icon = RANK_ICONS.get(rank_tier, "")
    
    top_heroes = results.get("Top 3 Most Played Heroes in Ranked", [])
    top_hero = top_heroes[0]['Hero'] if top_heroes else None

    # Determine color (default to black if hero not found)
    color_hex = HEROES_COLORS.get(top_hero, "#000000")
    embed = discord.Embed(
        title=f"📊 {username}'s Stats",
        url=f"https://tracker.gg/marvel-rivals/profile/ign/{urllib.parse.quote(username)}/overview",
        colour=discord.Colour(int(color_hex.lstrip('#'), 16)),
        timestamp=datetime.now()
    )

    if top_hero and top_hero in HEROES_ICONS:
        embed.set_thumbnail(url=HEROES_ICONS[top_hero])

    overall = results["Overall Ranked Stats"]
    embed.add_field(
        name="🏆 Overall Stats",
        value=(
            f"• **Rank:** {rank} {rank_icon}\n"
            f"• **Win Rate:** {overall['Overall Win Rate (%)']}%\n"
            f"• **Matches:** {overall['Total Ranked Matches']}\n"
            f"• **Wins:** {overall['Total Wins']}"
        ),
        inline=False
    )
    
    embed.add_field(name="Most Played Heroes", value="", inline=False)
    for hero in top_heroes:
        fire = "🔥" if hero['Win Rate (%)'] > 70 else ""
        embed.add_field(
            name=hero['Hero'],
            value=(
                f"• **WR:** {hero['Win Rate (%)']}% {fire}\n"
                f"• **Matches:** {hero['Matches']}\n"
                f"• **Wins:** {hero['Wins']}\n"
                f"• **K/D:** {hero['K/D Ratio']}\n"
                f"• **MVPs:** {hero['MVPs']}"
            ),
            inline=True
        )
        
    recent = results.get("Recently Played Heroes", [])
    recent_winrate = results.get("Recent Matches Win Rate (%)", 0)
    if recent:
        recent_text = "\n".join(
            f"• **{item['Hero']}**: {item['Matches in Recent History']} matches ({item['Win Rate (%)']}%)"
            for item in recent
        )
    else:
        recent_text = "No recent matches found."

    embed.add_field(name="⏳ Recently Played Heroes", value=f"{recent_text}\n**Recent Win Rate:** {recent_winrate}%", inline=False)
    embed.set_footer(
        text="Powered by RivalsX",
        icon_url="https://cdn2.steamgriddb.com/icon/916030603cc86a9b3d29f4d64f1bc415/32/256x256.png"
    )
    return embed

async def fetch_player_stats(name: str) -> dict:
    """
    Fetch player stats using the MRApiClient.
    """
    async with httpx.AsyncClient() as http_client:
        api_client = MRApiClient(http_client)
        # Get the player ID
        player_data = await api_client.get_player_id(name)
        user_id = player_data["id"]

        # Update player data
        await api_client.update_player(user_id)

        # Fetch detailed player stats
        stats_data = await api_client.get_player_stats(user_id)
        return parse_stats(stats_data)

class StatsView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(emoji="🔄", label="Refresh", style=discord.ButtonStyle.secondary)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        message = interaction.message
        if not message.embeds:
            await interaction.response.send_message("No embed found to refresh.", ephemeral=True)
            return
        
        name = message.embeds[0].title.split("'s")[0].replace("📊 ", "")
        await message.edit(content=f"Updating stats for {name}...", embed=None)
        await interaction.response.defer()
        try:
            results = await fetch_player_stats(name)
            embed = build_embed(results)
            await message.edit(content=None, embed=embed)
        except Exception as e:
            await message.edit(content=f"Failed to refresh stats: {e}")

@bot.hybrid_command(name="stats", description="Get stats for a given player name.")
async def stats(ctx: commands.Context, *, name: str):
    """
    Get stats for a given player name.
    Usage: r.stats <username>
    """
    print(f"Fetching stats for {name} at {datetime.now()} by {ctx.author.name}")
    message = await ctx.send(f"Fetching stats for {name}...", view=StatsView())
    try:
        results = await fetch_player_stats(name)
        embed = build_embed(results)
        await message.edit(content=None, embed=embed, view=StatsView())
    except PlayerNotFoundException:
        url = f"https://tracker.gg/marvel-rivals/profile/ign/{urllib.parse.quote(name.replace(' ', '%20'))}/overview"
        await ctx.send(f"{name} couldn't be found. Try checking here: {url}")
    except PrivateProfileException as e:
        if e:
            rank_tier = ''.join(filter(str.isalpha, str(e)))
            rank_icon = RANK_ICONS.get(rank_tier, "")
            desc = f"🔒 This profile is set to private.\n**Rank:** {e} {rank_icon}"
            
        else:
            desc = "🔒 This profile is set to private."

        embed = discord.Embed(
            title=f"🔒 {name}'s stats",
            description=desc,
            colour=0xff0000,
            timestamp=datetime.now()
        )
        await ctx.send(embed=embed)
    except APIUpdateFailedException:
        await ctx.send(f"Error updating data for {name}")
    except Exception as e:
        print(e)
        await ctx.send("An unexpected error occurred while fetching stats.")

@bot.hybrid_command(name="leaderboard", description="Get stats for all names in an image.")
async def leaderboard(ctx: commands.Context):
    await ctx.send("I'm in non-image mode. Use `r.stats <username>` to get stats for a player.")

@bot.hybrid_command(name="help", description="Show help information for commands.")
async def help(ctx: commands.Context):
    embed = discord.Embed(
        title="Help | RivalsX",
        description="Here are the available commands:",
        colour=0xF8BC6C,
        timestamp=datetime.now()
    )
    embed.add_field(
        name="r.stats <username>",
        value="Get stats for a given player name.",
        inline=False
    )
    embed.add_field(
        name="r.leaderboard",
        value="Get stats for all names in an image (currently in non-image mode).",
        inline=False
    )
    
    embed.add_field(
        name="r.history <username>",
        value="Get recent matches for a player.",
        inline=False
    )
    
    embed.set_footer(
        text="Powered by RivalsX",
        icon_url="https://cdn2.steamgriddb.com/icon/916030603cc86a9b3d29f4d64f1bc415/32/256x256.png"
    )
    await ctx.send(embed=embed)


class HistoryView(discord.ui.View):
    def __init__(self, embeds):
        super().__init__()
        self.embeds = embeds
        self.current_page = 0

    @discord.ui.button(emoji="⬅️", label="Previous", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @discord.ui.button(emoji="➡️", label="Next", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @discord.ui.button(emoji="🔄", label="Refresh", style=discord.ButtonStyle.secondary)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        message = interaction.message
        if not message.embeds:
            await interaction.response.send_message("Nothing found to refresh.", ephemeral=True)
            return
        
        name = message.embeds[0].title.split('(')[1].split(')')[0]
        await message.edit(content=f"Updating history for {name}...", embed=None)
        await interaction.response.defer()
        try:
            history_data = await fetch_history_data(name)
            self.embeds = build_history_embeds(history_data)
            self.current_page = 0
            await message.edit(content=None, embed=self.embeds[self.current_page], view=self)
        except Exception as e:
            await message.edit(content=f"Failed to refresh stats: {e}")

@bot.hybrid_command(name="history", description="Get recent matches for a player.")
async def history(ctx: commands.Context, *, name: str):
    print(f"Fetching match history for {name} at {datetime.now()} by {ctx.author.name}")
    message = await ctx.send(f"Fetching match history for {name}...")
    try:
        history_data = await fetch_history_data(name)
        embeds = build_history_embeds(history_data)
        if embeds:
            await message.edit(content=None, embed=embeds[0], view=HistoryView(embeds))
        else:
            await message.edit(content="No match history found.")
    except PlayerNotFoundException:
        url = f"https://tracker.gg/marvel-rivals/profile/ign/{urllib.parse.quote(name.replace(' ', '%20'))}/overview"
        await ctx.send(f"{name} couldn't be found. Try checking here: {url}")
    except APIUpdateFailedException:
        await ctx.send(f"Error updating data for {name}")
    except Exception as e:
        print("Error", e)
        await ctx.send("An unexpected error occurred while fetching match history.")



@bot.event
async def on_message(message: discord.Message):
    if bot.user.mentioned_in(message):
        await message.channel.send("I'm online! Run `r.help` to see available commands.")
    await bot.process_commands(message)

      
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)