# RivalsX - A Discord Bot for Marvel Rivals Player Stats 📊

A powerful, efficient Discord bot that fetches player statistics from Marvel Rivals, allowing users to quickly view ranked performance, most played heroes, and match history.
Uses [MR(API)](https://mrapi.org/), check out their work!

## 🤖 How to add
[Invite the bot to your server by clicking here!](https://discord.com/oauth2/authorize?client_id=1335330587510046751)
**NOTE**: Currently only hosting the non-image version of the bot because of hosting limitations (Torch has a size of over 1GB, even as CPU only!). As a result, `.leaderboard` will not work.

## ✨ Features
- **Fetch Player Stats**: Retrieve rank, win rate, hero data and match history for any player.
- **Image Support**: Upload an image of player names, and the bot will use OCR to extract player names and retrieve their stats.

## Showcase
![Image 0](https://i.imgur.com/jY3bf7C.png)
![Image 1](https://i.imgur.com/LWERmrD.png)
![Image 2](https://i.imgur.com/3BKTR2Y.png)
![Image 3](https://i.imgur.com/d66b5ly.png)

## Technologies 🌐

- Discord.py
- EasyOCR (CPU-only mode)
- OpenCV
- HTTPX
- Numpy
- Pandas

## Commands 📜
### `r.stats <username>`
Fetches detailed statistics for a specific player, including:
- Rank & Win Rate
- Most Played Heroes with Individual Stats
- Recent Hero Picks
Examples:
- `r.stats pvc`
- `r.stats s1natraa`

### `r.leaderboard` +  attached image
Upload a screenshot of player names, and the bot automatically extracts player names using OCR and retrieves their stats.
Examples:
- Upload an image and run:  
  `/leaderboard`

## Installation ⚙️
1. Clone this repository.
```git clone https://github.com/brian-rd/RivalsX.git```
2. Navigate to the project directory.
```cd RivalsX```
3. Install the dependencies.
```pip install -r requirements.txt -c constraints.txt```
4. Create a .env file in the project directory and add your Bot token.
```DISCORD_TOKEN=your_token_here```
5. Run the bot.
```python main.py```


