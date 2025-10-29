import os
import asyncio
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")  # opcional, acelera o sync na sua guild

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # <--- importante pra detectar novos membros
bot = commands.Bot(command_prefix="!", intents=intents)



# ---------- EVENTOS ----------
@bot.event
async def on_ready():
    print(f"✅ Logado como {bot.user} (id: {bot.user.id})")
    try:
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            # IMPORTANTE: copia os comandos globais para a guild
            bot.tree.copy_global_to(guild=guild)
            # agora sincroniza na guild (aparece instantâneo)
            synced = await bot.tree.sync(guild=guild)
            print(f"🔁 Comandos sincronizados APENAS na guild {GUILD_ID}: {len(synced)}")
        else:
            # sincroniza global (pode demorar a aparecer)
            synced = await bot.tree.sync()
            print(f"🌍 Comandos globais sincronizados: {len(synced)}")
    except Exception as e:
        print("Erro ao sincronizar comandos:", e)




@bot.event
async def on_message(msg: discord.Message):
    if msg.author.bot:
        return
    if msg.content.lower() == "!oi":
        await msg.reply("👋 Olá! Use **/ping** ou **/anunciar** para testar.")
    await bot.process_commands(msg)


# ---------- SLASH COMMANDS (sem Cog) ----------
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
    quando: str | None = None,
    canal: discord.TextChannel | None = None
):
    try:
        # responde já para não estourar timeout
        await interaction.response.defer(ephemeral=True, thinking=True)

        # checa permissão de quem executa (opcional, remova se não quiser)
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.followup.send(
                "❌ Você precisa da permissão **Gerenciar Mensagens** para usar este comando.",
                ephemeral=True
            )
            return

        destino = canal or interaction.channel
        texto = f"**<a:coroaWhite:1432554574891188294>  〔 CHX 〕APRESENTA:** {titulo}\n{mensagem}\n"

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

# ---------- EVENTO DE ENTRADA AUTO-CARGO EM NOVOS MEMBROS ----------
@bot.event
async def on_member_join(member: discord.Member):
    try:
        # ID do cargo que o bot deve dar
        cargo_id = 134816779215612674  # <-- coloque o ID real do cargo
        cargo = member.guild.get_role(cargo_id)

        # ID do canal onde a mensagem será enviada
        canal_id = 1432561541483335873  # <-- ID do canal de boas-vindas
        canal = member.guild.get_channel(canal_id)

        # Dá o cargo automaticamente
        if cargo:
            await member.add_roles(cargo, reason="Cargo automático de boas-vindas")
            print(f"✅ Dei o cargo '{cargo.name}' para {member.name}")
        else:
            print("⚠️ Cargo não encontrado! Verifique o ID.")

        # Cria o embed de boas-vindas (sem link)
        embed = discord.Embed(
            title=f"<:DcChX3:1427835778700017725> Seja Bem-Vindo(a)! <:DcChX3:1427835778700017725>",
            description="🫶 **Servidor do seu amigo ChX!**",
            color=discord.Color.from_rgb(255, 215, 0)  # cor dourada
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(
            text=f"Bem-vindo(a) à comunidade, {member.name}!",
            icon_url=member.display_avatar.url
        )

        # Envia o embed no canal
        if canal:
            await canal.send(content=f"👋 Seja bem-vindo(a) {member.mention}!", embed=embed)
            print(f"📨 Embed de boas-vindas enviado em #{canal.name}")
        else:
            print("⚠️ Canal de boas-vindas não encontrado!")

    except Exception as e:
        print("❌ Erro ao dar cargo automático:", e)




# ---------- EXECUÇÃO ----------
async def main():
    if not TOKEN:
        raise RuntimeError("❌ Coloque DISCORD_TOKEN no .env")
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())


