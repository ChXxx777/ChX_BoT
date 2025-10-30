import os
os.environ["DISCORD_NO_AUDIO"] = "1"

import asyncio
from typing import Optional

from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands

# --------- CARREGA VARIÁVEIS (.env local) ---------
load_dotenv()  # no Render não é obrigatório; lá use Environment Variables

TOKEN = os.getenv("DISCORD_TOKEN")              # obrigatório
GUILD_ID = os.getenv("GUILD_ID")                # opcional (sync instantâneo na guild)
PREFIX = os.getenv("PREFIX", "!")               # opcional (para !oi e futuros comandos de texto)
OWNER_ID = os.getenv("OWNER_ID")                # opcional

# Auto-cargo / Boas-vindas (se não usar, deixe em branco)
AUTO_ROLE_ID = os.getenv("CARGO_ID")            # ID do cargo para novos membros
WELCOME_CHANNEL_ID = os.getenv("CANAL_ID")      # ID do canal de boas-vindas
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")    # ID do canal de logs ao iniciar (opcional)

# --------- INTENTS E BOT ---------
intents = discord.Intents.default()
intents.message_content = True    # para ler mensagens de texto (ex: !oi)
intents.members = True            # para on_member_join

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    allowed_mentions=discord.AllowedMentions(everyone=False, roles=False)  # evita @everyone acidental
)

# --------- EVENTOS ---------
@bot.event
async def on_ready():
    print(f"✅ Logado como {bot.user} (id: {bot.user.id})")
    try:
        # Sincroniza slash commands
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            bot.tree.copy_global_to(guild=guild)       # copia comandos globais para a guild (aparição instantânea)
            synced = await bot.tree.sync(guild=guild)
            print(f"🔁 Comandos sincronizados APENAS na guild {GUILD_ID}: {len(synced)}")
        else:
            synced = await bot.tree.sync()             # globais (podem demorar até ~1h a aparecer)
            print(f"🌍 Comandos globais sincronizados: {len(synced)}")
    except Exception as e:
        print("Erro ao sincronizar comandos:", e)

    # Loga no canal de logs (se configurado)
    try:
        if LOG_CHANNEL_ID:
            ch = bot.get_channel(int(LOG_CHANNEL_ID))
            if ch:
                await ch.send(f"🚀 **{bot.user}** está online e pronto para uso!")
    except Exception as e:
        print("Aviso: falha ao enviar mensagem no canal de logs:", e)


@bot.event
async def on_message(msg: discord.Message):
    # ignora outros bots
    if msg.author.bot:
        return

    # exemplo simples de comando de texto
    if msg.content.lower() == f"{PREFIX}oi":
        await msg.reply("👋 Olá! Use **/ping** ou **/anunciar** para testar.")

    # mantém processamento de comandos/extensões
    await bot.process_commands(msg)


@bot.event
async def on_member_join(member: discord.Member):
    """Dá cargo automático e envia boas-vindas com embed (se IDs estiverem configurados)."""
    try:
        # Auto-cargo
        if AUTO_ROLE_ID:
            role = member.guild.get_role(int(AUTO_ROLE_ID))
            if role:
                await member.add_roles(role, reason="Cargo automático de boas-vindas")
                print(f"✅ Dei o cargo '{role.name}' para {member} ({member.id})")
            else:
                print("⚠️ AUTO_ROLE_ID configurado, mas cargo não encontrado.")

        # Boas-vindas (embed)
        if WELCOME_CHANNEL_ID:
            canal = member.guild.get_channel(int(WELCOME_CHANNEL_ID))
            if canal:
                embed = discord.Embed(
                    title="<:DcChX3:1427835778700017725> Seja Bem-Vindo(a)! <:DcChX3:1427835778700017725>",
                    description="🫶 **Servidor do seu amigo ChX!**",
                    color=discord.Color.from_rgb(255, 215, 0)  # dourado
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(
                    text=f"Bem-vindo(a) à comunidade, {member.name}!",
                    icon_url=member.display_avatar.url
                )
                await canal.send(content=f"👋 Seja bem-vindo(a) {member.mention}!", embed=embed)
                print(f"📨 Embed de boas-vindas enviado em #{canal.name}")
            else:
                print("⚠️ WELCOME_CHANNEL_ID configurado, mas canal não encontrado.")
    except discord.Forbidden:
        print("⚠️ Sem permissão para dar cargo/mandar mensagem de boas-vindas (verifique permissões e hierarquia).")
    except Exception as e:
        print("❌ Erro no on_member_join:", e)

# --------- SLASH COMMANDS ---------
@bot.tree.command(name="ping", description="Mostra a latência do bot.")
async def ping(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True, ephemeral=True)
    api_ms = round(bot.latency * 1000)
    await interaction.followup.send(f"🏓 Pong! Latência de API: **{api_ms}ms**", ephemeral=True)


@bot.tree.command(name="anunciar", description="Envia um anúncio formatado.")
@app_commands.describe(
    titulo="Título do anúncio",
    mensagem="Mensagem principal",
    quando="Data/horário (opcional)",
    canal="Canal de destino (opcional)"
)
async def anunciar(
    interaction: discord.Interaction,
    titulo: str,
    mensagem: str,
    quando: Optional[str] = None,
    canal: Optional[discord.TextChannel] = None
):
    try:
        # responde já para não estourar timeout
        await interaction.response.defer(ephemeral=True, thinking=True)

        # permissão mínima de quem usa o comando (ajuste/remova se não quiser)
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.followup.send(
                "❌ Você precisa da permissão **Gerenciar Mensagens** para usar este comando.",
                ephemeral=True
            )
            return

        destino = canal or interaction.channel
        texto = (
            f"**<a:coroaWhite:1432554574891188294>  〔 CHX 〕APRESENTA:** {titulo}\n"
            f"{mensagem}\n"
        )
        if quando:
            texto += f"🕒 **Quando:** {quando}"

        await destino.send(texto)
        await interaction.followup.send(f"✅ Anúncio enviado em {destino.mention}.", ephemeral=True)

    except discord.Forbidden:
        await interaction.followup.send(
            "⚠️ Não tenho permissão para enviar mensagens nesse canal. "
            "Conceda **Enviar Mensagens** para o bot e tente novamente.",
            ephemeral=True
        )
    except Exception as e:
        print("Erro em /anunciar:", repr(e))
        await interaction.followup.send("⚠️ Ocorreu um erro ao tentar enviar o anúncio.", ephemeral=True)

# --------- EXECUÇÃO ---------
async def main():
    if not TOKEN:
        raise RuntimeError("❌ Falta DISCORD_TOKEN (defina no .env local ou em Environment Variables do Render).")
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
