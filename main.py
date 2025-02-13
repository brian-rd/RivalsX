import os
import httpx
import orjson
import asyncio
import discord
import urllib.parse
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from collections import Counter
from discord.ext import commands, tasks
from discord import app_commands


HEROES_ICONS = {
    "Bruce Banner": "https://mrapi.org/assets/characters/bruce-banner-headbig.png",
    "The Punisher": "https://mrapi.org/assets/characters/the-punisher-headbig.png",
    "Storm": "https://mrapi.org/assets/characters/storm-headbig.png",
    "Loki": "https://mrapi.org/assets/characters/loki-headbig.png",
    "Doctor Strange": "https://mrapi.org/assets/characters/doctor-strange-headbig.png",
    "Mantis": "https://mrapi.org/assets/characters/mantis-headbig.png",
    "Hawkeye": "https://mrapi.org/assets/characters/hawkeye-headbig.png",
    "Captain America": "https://mrapi.org/assets/characters/captain-america-headbig.png",
    "Rocket Raccoon": "https://mrapi.org/assets/characters/rocket-raccoon-headbig.png",
    "Hela": "https://mrapi.org/assets/characters/hela-headbig.png",
    "Cloak & Dagger": "https://mrapi.org/assets/characters/cloak-dagger-headbig.png",
    "Black Panther": "https://mrapi.org/assets/characters/black-panther-headbig.png",
    "Groot": "https://mrapi.org/assets/characters/groot-headbig.png",
    "Magik": "https://mrapi.org/assets/characters/magik-headbig.png",
    "Moon Knight": "https://mrapi.org/assets/characters/moon-knight-headbig.png",
    "Luna Snow": "https://mrapi.org/assets/characters/luna-snow-headbig.png",
    "Squirrel Girl": "https://mrapi.org/assets/characters/squirrel-girl-headbig.png",
    "Black Widow": "https://mrapi.org/assets/characters/black-widow-headbig.png",
    "Iron Man": "https://mrapi.org/assets/characters/iron-man-headbig.png",
    "Venom": "https://mrapi.org/assets/characters/venom-headbig.png",
    "Spider-man": "https://mrapi.org/assets/characters/spider-man-headbig.png",
    "Magneto": "https://mrapi.org/assets/characters/magneto-headbig.png",
    "Scarlet Witch": "https://mrapi.org/assets/characters/scarlet-witch-headbig.png",
    "Thor": "https://mrapi.org/assets/characters/thor-headbig.png",
    "Mister Fantastic": "https://mrapi.org/assets/characters/mister-fantastic-headbig.png",
    "Winter Soldier": "https://mrapi.org/assets/characters/winter-soldier-headbig.png",
    "Peni Parker": "https://mrapi.org/assets/characters/peni-parker-headbig.png",
    "Star-lord": "https://mrapi.org/assets/characters/star-lord-headbig.png",
    "Namor": "https://mrapi.org/assets/characters/namor-headbig.png",
    "Adam Warlock": "https://mrapi.org/assets/characters/adam-warlock-headbig.png",
    "Jeff The Land Shark": "https://mrapi.org/assets/characters/jeff-the-land-shark-headbig.png",
    "Psylocke": "https://mrapi.org/assets/characters/psylocke-headbig.png",
    "Wolverine": "https://mrapi.org/assets/characters/wolverine-headbig.png",
    "Invisible Woman": "https://mrapi.org/assets/characters/invisible-woman-headbig.png",
    "Iron Fist": "https://mrapi.org/assets/characters/iron-fist-headbig.png"
}

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

API_BASE_URL = "https://mrapi.org/api"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='r.', intents=intents)

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print(f"Synced slash commands for {bot.user}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    print(f'Logged in as {bot.user}')
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
        url = f"{API_BASE_URL}/player-id/{name}"
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
    
    # Count recently played heroes
    match_history = data.get("match_history", [])
    recent_heroes = [
        hero_stats[str(match["stats"]["hero"]["id"])]["hero_name"]
        for match in match_history
        if str(match["stats"]["hero"]["id"]) in hero_stats
    ]
    recent_hero_counts = Counter(recent_heroes)
    recent_hero_data = [
        {"Hero": hero, "Matches in Recent History": count}
        for hero, count in recent_hero_counts.items()
    ]
    recent_hero_df = pd.DataFrame(recent_hero_data).sort_values(
        by="Matches in Recent History", ascending=False
    ).head(5)

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
    }
    return results


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
        url=f"https://tracker.gg/marvel-rivals/profile/ign/{username}/overview",
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
    if recent:
        recent_text = "\n".join(
            f"• **{item['Hero']}**: {item['Matches in Recent History']} matches"
            for item in recent
        )
    else:
        recent_text = "No recent matches found."

    embed.add_field(name="⏳ Recently Played Heroes", value=recent_text, inline=False)
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




@bot.command()
async def stats(ctx: commands.Context, *, name: str):
    """
    Get stats for a given player name.
    Usage: r.stats <username>
    """
    print(f"Fetching stats for {name}")
    try:
        results = await fetch_player_stats(name)
        embed = build_embed(results)
        await ctx.send(embed=embed)
    except PlayerNotFoundException:
        url = f"https://tracker.gg/marvel-rivals/profile/ign/{urllib.parse.quote(name)}/overview"
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
        await ctx.send("An unexpected error occurred while fetching stats.")

@bot.command()
async def leaderboard(ctx: commands.Context):
    await ctx.send("I'm in non-image mode. Use `r.stats <username>` to get stats for a player.")

@bot.event
async def on_message(message: discord.Message):
    if bot.user.mentioned_in(message):
        await message.channel.send("I'm online!")
    await bot.process_commands(message)

      
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)