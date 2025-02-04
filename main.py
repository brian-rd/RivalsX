import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import httpx
import orjson
import os
from dotenv import load_dotenv
import pandas as pd
from collections import Counter
from datetime import datetime



intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='r.', intents=intents)

heroes_icons = {
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

def parse_stats(data):
    username = data.get("player_name")
    rank = data["stats"]["rank"]["rank"]
    ranked_stats = data["stats"]["ranked"]
    total_ranked_matches = ranked_stats["total_matches"]
    total_ranked_wins = ranked_stats["total_wins"]
    overall_winrate = round((total_ranked_wins / total_ranked_matches) * 100, 2) if total_ranked_matches > 0 else 0
    
    hero_stats = data["hero_stats"]
    hero_data = [
        {
            "Hero": stats["hero_name"],
            "Matches": ranked.get("matches", 0),
            "Wins": ranked.get("wins", 0),
            "Losses": ranked.get("matches", 0) - ranked.get("wins", 0),
            "Win Rate (%)": round((ranked.get("wins", 0) / ranked.get("matches", 1)) * 100, 2) if ranked.get("matches", 0) > 0 else 0,
            "K/D Ratio": float(ranked.get("kdr", 0.0)),
            "MVPs": ranked.get("mvp", 0),
        }
        for stats in hero_stats.values()
        if (ranked := stats.get("ranked"))
    ]

    hero_df = pd.DataFrame(hero_data).sort_values(by="Matches", ascending=False)
    top_3_heroes = hero_df.head(3)
    
    match_history = data.get("match_history", [])
    recent_heroes = [
        hero_stats[str(match["stats"]["hero"]["id"])]["hero_name"]
        for match in match_history
        if str(match["stats"]["hero"]["id"]) in hero_stats
    ]
    recent_hero_counts = Counter(recent_heroes)

    recent_hero_data_all = [
        {"Hero": hero, "Matches in Recent History": matches}
        for hero, matches in recent_hero_counts.items()
    ]
    recent_hero_df_all = pd.DataFrame(recent_hero_data_all)

    results = {
        "Username": username,
        "Rank": rank,
        "Overall Ranked Stats": {
            "Total Ranked Matches": total_ranked_matches,
            "Total Wins": total_ranked_wins,
            "Overall Win Rate (%)": overall_winrate,
        },
        "Top 3 Most Played Heroes in Ranked": top_3_heroes.to_dict(orient="records"),
        "Recently Played Heroes": recent_hero_df_all.to_dict(orient="records"),
    }

    
    return results

def build_embed(results):
    username = results["Username"]
    rank = results.get("Rank", "Unranked")
    
    embed = discord.Embed(
        title=f"📊 {username}'s Stats",
        url=f"https://tracker.gg/marvel-rivals/profile/ign/{username}/overview",
        colour=0x00b0f4,
        timestamp=datetime.now()
    )

    overall_stats = results["Overall Ranked Stats"]
    embed.add_field(
        name="🏆 Overall Stats",
        value=(
            f"• **Rank:** {rank}\n"
            f"• **Win Rate:** {overall_stats['Overall Win Rate (%)']}%\n"
            f"• **Matches:** {overall_stats['Total Ranked Matches']}\n"
            f"• **Wins:** {overall_stats['Total Wins']}"
        ),
        inline=False
    )
    
    embed.add_field(name="Most Played Heroes", value="", inline=False)

    top_heroes = results["Top 3 Most Played Heroes in Ranked"]

    for i, hero in enumerate(top_heroes):
        embed.add_field(
            name=f"{hero['Hero']}",
            value=(
                f"• **WR:** {hero['Win Rate (%)']}%\n"
                f"• **Matches:** {hero['Matches']}\n"
                f"• **Wins:** {hero['Wins']}\n"
                f"• **K/D:** {hero['K/D Ratio']}\n"
                f"• **MVPs:** {hero['MVPs']}"
            ),
            inline=True
        )

    recent_heroes = results["Recently Played Heroes"]
    if recent_heroes:
        recent_heroes_text = "\n".join(
            [f"• **{hero['Hero']}**: {hero['Matches in Recent History']} matches" for hero in recent_heroes]
        )
    else:
        recent_heroes_text = "No recent matches found."

    embed.add_field(name="⏳ Recently Played Heroes", value=recent_heroes_text, inline=False)

    top_hero = top_heroes[0]['Hero'] if top_heroes else None
    if top_hero and top_hero in heroes_icons:
        embed.set_thumbnail(url=heroes_icons[top_hero])

    embed.set_footer(
        text="Powered by RivalsX",
        icon_url="https://cdn2.steamgriddb.com/icon/916030603cc86a9b3d29f4d64f1bc415/32/256x256.png"
    )
    
    return embed


@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print(f"Synced slash commands for {bot.user}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    print(f'Logged in as {bot.user}')

@bot.command()
async def stats(ctx, *args):
    name = ' '.join(args)
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://mrapi.org/api/player-id/{name}")
        if response.status_code == 200:
            data = orjson.loads(response.content)
            userID = data['id']
            response2 = await client.get(f"https://mrapi.org/api/player/{userID}")
            if response2.status_code == 200:
                data2 = orjson.loads(response2.content)
                results = parse_stats(data2)
                embed = build_embed(results)
                await ctx.send(embed=embed)
            else:
                print(f"Request failed with status {response.status_code}")
                await ctx.send("Player not found")
        else:
            print(f"Request failed with status {response.status_code}")
            await ctx.send("Player not found")

    
      
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)