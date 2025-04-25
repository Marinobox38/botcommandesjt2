import os
from dotenv import load_dotenv
import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
from discord.ext import commands, tasks
from discord import app_commands
from keep_alive import keep_alive

load_dotenv()
DISCORD_TOKEN= os.getenv('DISCORD_TOKEN')

# ========== CONFIGURATION ==========
CHANNEL_ID = 1364912996379529256  # ID de ton salon #test-marin
ROLE_ID = 1357005838144897155      # Remplace par l'ID du rôle @notif-blog

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ========== TÂCHE DE FOND ==========
@tasks.loop(hours=2)
async def check_update():
    feed = feedparser.parse(FEED_URL)
    latest_article = feed.entries[0]
    title = latest_article.title
    link = latest_article.link
    description = latest_article.summary

    # Couper la description si elle est trop longue
    short_description = (description[:200] + '...') if len(description) > 200 else description

    channel = await bot.fetch_channel(CHANNEL_ID)
    embed = discord.Embed(
        title=title,
        url=link,
        description=short_description,
        color=discord.Color.blue()
    )
    await channel.send(content="@notif-blog", embed=embed)


# ========== COMMANDES SLASH ==========
@bot.command()
async def verif(ctx):
    """Force une vérification immédiate"""
    await ctx.send("Vérification manuelle lancée...")
    await check_updates()

@bot.tree.command(name="infos", description="Affiche des infos sur le Journal Théâtral")
async def infos_command(interaction: discord.Interaction):
    text = (
        "Le Journal Théâtral a été fondé en 2023, alors que nous étions en 4ème, par Théo. "
        "Il a fait confiance à quelques membres et ils ont sorti plusieurs numéros cette année-là. "
        "Aujourd'hui, nous sommes 8 membres et le journal connaît une belle croissance. "
        "Le site Internet du Journal Théâtral a été créé par Marin, épaulé de Elya. Il nous permet de partager "
        "les actualités de notre classe et nos journaux à nos professeurs, les autres classes mais aussi nos familles. "
        "Vous êtes ainsi au cœur de la vie de la 3ème4. Nous sommes la classe théâtre de l'Externat Notre Dame, "
        "la 3ème4 (anciennement 4ème5).\n\n"
        "Depuis un an maintenant, Mme Bertocchi, aidée de Mme Caillet notre prof de français, nous apprend le théâtre "
        "dans l'objectif de monter une pièce que nous jouerons en juin 2025. Au programme, au-delà des répliques, "
        "nous aurons chant, danse, tableaux...\n\n"
        "Nous sommes une classe enthousiaste, soudée et des projets plein la tête : ce journal, la pièce de fin d'année, "
        "des journées à thèmes, sorties, goûters..."
    )
    await interaction.response.send_message(text, ephemeral=True)

@bot.tree.command(name="site", description="Affiche le lien du site du Journal Théâtral")
async def site_command(interaction: discord.Interaction):
    await interaction.response.send_message("🔗 https://journaltheatral.com", ephemeral=False)

@bot.tree.command(name="message", description="Envoie un message personnalisé dans le salon")
@app_commands.describe(texte="Le message à envoyer")
async def message_command(interaction: discord.Interaction, texte: str):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("⛔ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=False)
        return
    await interaction.channel.send(texte)
    await interaction.response.send_message("✅ Message envoyé avec succès.", ephemeral=True)

@bot.tree.command(name="ban", description="Bannit un utilisateur du serveur")
@app_commands.describe(user="L'utilisateur à bannir", reason="Raison du bannissement (optionnel)")
async def ban_command(interaction: discord.Interaction, user: discord.Member, reason: str = "Aucune raison spécifiée"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("⛔ Tu n'as pas la permission de bannir des membres.", ephemeral=True)
        return
    try:
        await user.ban(reason=reason)
        await interaction.response.send_message(f"🚫 {user.mention} a été banni.\n📝 Raison : {reason}")
    except Exception as e:
        await interaction.response.send_message(f"❌ Impossible de bannir ce membre : {e}")
    
# ========== KICK ==========
@bot.tree.command(name="kick", description="Expulse un utilisateur du serveur")
@app_commands.describe(user="L'utilisateur à expulser", reason="Raison de l'expulsion (optionnel)")
async def kick_command(interaction: discord.Interaction, user: discord.Member, reason: str = "Aucune raison spécifiée"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("⛔ Tu n'as pas la permission d'expulser des membres.", ephemeral=True)
        return
    try:
        await user.kick(reason=reason)
        await interaction.response.send_message(f"👢 {user.mention} a été expulsé.\n📝 Raison : {reason}")
    except Exception as e:
        await interaction.response.send_message(f"❌ Impossible d’expulser ce membre : {e}")

# ========== MUTE ==========
@bot.tree.command(name="mute", description="Donne le rôle 'Mute' à un utilisateur")
@app_commands.describe(user="Utilisateur à réduire au silence")
async def mute_command(interaction: discord.Interaction, user: discord.Member):
    mute_role = discord.utils.get(interaction.guild.roles, name="Mute")
    if not mute_role:
        await interaction.response.send_message("❌ Le rôle 'Mute' n'existe pas. Crée-le manuellement d'abord.", ephemeral=True)
        return
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("⛔ Tu n'as pas la permission de gérer les rôles.", ephemeral=True)
        return
    await user.add_roles(mute_role)
    await interaction.response.send_message(f"🔇 {user.mention} a été réduit au silence.")

# ========== UNMUTE ==========
@bot.tree.command(name="unmute", description="Retire le rôle 'Mute' à un utilisateur")
@app_commands.describe(user="Utilisateur à rétablir")
async def unmute_command(interaction: discord.Interaction, user: discord.Member):
    mute_role = discord.utils.get(interaction.guild.roles, name="Mute")
    if not mute_role:
        await interaction.response.send_message("❌ Le rôle 'Mute' n'existe pas.", ephemeral=True)
        return
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("⛔ Tu n'as pas la permission de gérer les rôles.", ephemeral=True)
        return
    await user.remove_roles(mute_role)
    await interaction.response.send_message(f"🔊 {user.mention} peut de nouveau parler.")

# ========== CLEAR ==========
@bot.tree.command(name="clear", description="Supprime un nombre de messages dans le salon")
@app_commands.describe(nombre="Nombre de messages à supprimer (max 100)")
async def clear_command(interaction: discord.Interaction, nombre: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("⛔ Tu n'as pas la permission de gérer les messages.", ephemeral=True)
        return
    if nombre < 1 or nombre > 100:
        await interaction.response.send_message("⚠️ Tu dois entrer un nombre entre 1 et 100.", ephemeral=True)
        return
    deleted = await interaction.channel.purge(limit=nombre)
    await interaction.response.send_message(f"🧹 {len(deleted)} messages supprimés.", ephemeral=False)



# ========== ÉVÉNEMENTS ==========
@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Commandes synchronisées : {len(synced)}")
    except Exception as e:
        print(f"Erreur lors de la sync des commandes : {e}")
    check_updates.start()

# ========== LANCEMENT ==========
keep_alive()
bot.run(DISCORD_TOKEN)
