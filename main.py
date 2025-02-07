import os
import re
import io
import cv2
import httpx
import orjson
import asyncio
import discord
import urllib.parse
import numpy as np
import pandas as pd
from PIL import Image
from dotenv import load_dotenv
from datetime import datetime
from collections import Counter
from discord.ext import commands, tasks
from discord import app_commands
import easyocr
reader = easyocr.Reader(["en", "de", "es", "sv", "fr"], gpu=False)

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

heroes_colors = {
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


def parse_stats(data):
    try:
        if not data:
            return {"Private": "true"}
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

        hero_df = pd.DataFrame(hero_data).fillna({'Matches': 0}).sort_values(by="Matches", ascending=False)
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
        recent_hero_df_all = pd.DataFrame(recent_hero_data_all).sort_values(by="Matches in Recent History", ascending=False).head(5)

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
            "Recently Played Heroes": recent_hero_df_all.to_dict(orient="records"),
        }

        return results
    except Exception as e:
        print(f"Error parsing stats: {e}")
        return 0

def build_embed(results):        
    username = results["Username"]
    rank = results.get("Rank", "Unranked")
    
    top_heroes = results["Top 3 Most Played Heroes in Ranked"]
    top_hero = top_heroes[0]['Hero'] if top_heroes else None

    embed = discord.Embed(
        title=f"📊 {username}'s Stats",
        url=f"https://tracker.gg/marvel-rivals/profile/ign/{username}/overview",
        colour=discord.Colour(int(heroes_colors.get(top_hero, "#000000").lstrip('#'), 16)),
        timestamp=datetime.now()
    )
    
    if top_hero and top_hero in heroes_icons:
        embed.set_thumbnail(url=heroes_icons[top_hero])

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
    print(*args)
    print(name)
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://mrapi.org/api/player-id/{name}")
        if response.status_code == 200:
            data = orjson.loads(response.content)
            if data['id'] is None or data['name'].lower() !=  name.lower():
                await ctx.send(f"{name} couldn't be found, try here: https://tracker.gg/marvel-rivals/profile/ign/{urllib.parse.quote(name)}/overview")
                return
            userID = data['id']
            response2 = await client.get(f"https://mrapi.org/api/player/{userID}")
            if response2.status_code == 200:
                data2 = orjson.loads(response2.content)
                results = parse_stats(data2)
                if results == 0:
                    await ctx.send(f"Error fetching stats for {name}")
                    return
                embed = build_embed(results)
                await ctx.send(embed=embed)
            else:
                print("Private Profile 1")
                embed = discord.Embed(
                    title=f"🔒 {name}'s stats",
                    description="This profile is set to private.",
                    colour=0xff0000,
                    timestamp=datetime.now()
                )
                await ctx.send(embed=embed)
        else:
            print(f"Request failed with status {response.status_code}")
            print("Flag2")
            await ctx.send(f"{name} couldn't be found")

def clean_name(text):
    """ Removes numbers at the start and extra spaces from names """
    return re.sub(r"^\d+", "", text).strip()

def extract_names_from_image(image_data):
    """ Extract player names from a leaderboard image using strict OCR filtering. """
    image = np.array(Image.open(io.BytesIO(image_data)).convert("RGB"))
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    extracted_text = reader.readtext(image, detail=0)
    player_names = [clean_name(line) for line in extracted_text if len(line) > 2]
    return list(set(player_names))

@bot.command()
async def leaderboard(ctx):
    if not ctx.message.attachments:
        return await ctx.send("Please upload an image of the leaderboard.")

    attachment = ctx.message.attachments[0]
    
    if not attachment.content_type.startswith("image/"):
        return await ctx.send("Please upload a valid image file.")

    image_data = await attachment.read()

    player_names = extract_names_from_image(image_data)

    if not player_names:
        return await ctx.send("No valid player names detected in the image.")

    await ctx.send(f"Detected Players: {', '.join(player_names)}\nFetching stats...")

    not_found = []
    private_profiles = []
    successful_embeds = []

    async with httpx.AsyncClient() as client:
        for name in player_names:
            response = await client.get(f"https://mrapi.org/api/player-id/{name}")
            if response.status_code == 200:
                data = orjson.loads(response.content)
                if data['id'] is None or data['name'].lower() != name.lower():
                    not_found.append(name)
                    continue
                userID = data['id']
                response2 = await client.get(f"https://mrapi.org/api/player/{userID}")
                if response2.status_code == 200:
                    data2 = orjson.loads(response2.content)
                    results = parse_stats(data2)
                    if results == 0:
                        not_found.append(name)
                        continue
                    embed = build_embed(results)
                    successful_embeds.append(embed)
                else:
                    private_profiles.append(name)
            else:
                not_found.append(name)

    if not_found:
        for name in not_found:
            await ctx.send(f"Couldn't find user: {name}. Please try here: https://tracker.gg/marvel-rivals/profile/ign/{urllib.parse.quote(name)}/overview")

    if private_profiles:
        await ctx.send(f"These profiles are set to private: {', '.join(private_profiles)}")

    for embed in successful_embeds:
        await ctx.send(embed=embed)

      
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)