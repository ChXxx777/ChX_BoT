import os
from dotenv import load_dotenv
import interactions
from interactions import slash_command, SlashContext, listen, Intents, Embed, OptionType
from interactions import slash_option, Channel, Permissions


# ----- CARREGA VARIÁVEIS .env (local) -----
# No Render, ele ignora o .env e usa Environment Variables
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")        # obrigatório
GUILD_ID = os.getenv("GUILD_ID")          # opcional (pra sync mais rápido)
PREFIX = os.getenv("PREFIX", "!")         # pra comando !oi
OWNER_ID = os.getenv("OWNER_ID")          # opcional

AUTO_ROLE_ID = os.getenv("CARGO_ID")      # cargo automático para novos membros
WELCOME_CHANNEL_ID = os.getenv("CANAL_ID")  # canal de boas-vindas
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")  # canal de log inicial


# ----- CONFIGURA O BOT -----
# Precisamos de intents pra ver membros e mensagens
intents = Intents.DEFAULT | Intents.GUILD_MEMBERS | Intents.MESSAGE_CONTENT
bot = interactions.Client(token=TOKEN, intents=intents)


# ----- HELPER: mandar mensagem de log se canal existir -----
async def send_log_message(text: str):
    if not LOG_CHANNEL_ID:
        return
    try:
        channel = await bot.fetch_channel(int(LOG_CHANNEL_ID))
        if channel:
            await channel.send(text)
    except Exception as e:
        print("Falha ao enviar log:", e)


# ----- EVENTO: BOT PRONTO -----
@listen()
async def on_ready():
    print(f"✅ Bot {bot.me} está online!")
    await send_log_message(f"🚀 **{bot.me}** está online e pronto para uso!")


# ----- EVENTO: NOVO MEMBRO ENTRA -----
@listen()
async def on_member_add(member):
    try:
        # dar cargo automático
        if AUTO_ROLE_ID:
            try:
                role_id_int = int(AUTO_ROLE_ID)
                await member.add_role(role_id_int, reason="Cargo automático de boas-vindas")
                print(f"✅ Dei o cargo {role_id_int} para {member.user.username}")
            except Exception as e:
                print("⚠️ Erro ao dar cargo automático:", e)

        # mensagem de boas-vindas
        if WELCOME_CHANNEL_ID:
            try:
                ch = await bot.fetch_channel(int(WELCOME_CHANNEL_ID))
                if ch:
                    embed = Embed(
                        title="👋 Seja bem-vindo(a)!",
                        description="🫶 Servidor do seu amigo ChX!",
                        color=0xFFD700  # dourado
                    )
                    embed.set_thumbnail(url=member.user.avatar_url)
                    embed.set_footer(
                        text=f"Bem-vindo(a) à comunidade, {member.user.username}!",
                        icon_url=member.user.avatar_url
                    )

                    await ch.send(
                        content=f"👋 Seja bem-vindo(a) <@{member.user.id}>!",
                        embeds=embed
                    )
                    print(f"📨 Boas-vindas enviadas para {member.user.username}")
            except Exception as e:
                print("⚠️ Erro ao enviar boas-vindas:", e)

    except Exception as e:
        print("❌ Erro geral em on_member_add:", e)


# ----- COMANDO DE TEXTO NO CHAT (!oi) -----
@listen()
async def on_message_create(event):
    msg = event.message
    # ignora bot
    if msg.author.bot:
        return

    # comando !oi
    if msg.content.strip().lower() == f"{PREFIX}oi":
        try:
            await msg.reply("👋 Olá! Use /ping ou /anunciar pra testar.")
        except Exception as e:
            print("Erro respondendo !oi:", e)


# ----- SLASH: /ping -----
@slash_command(
    name="ping",
    description="Mostra a latência do bot.",
    scopes=[int(GUILD_ID)] if GUILD_ID else None
)
async def ping(ctx: SlashContext):
    # interactions não tem bot.latency, então vamos só responder fixo
    await ctx.send(
        f"🏓 Pong! Estou vivo e respondendo, {ctx.author.mention}!",
        ephemeral=True
    )


# ----- SLASH: /anunciar -----
@slash_command(
    name="anunciar",
    description="Envia um anúncio formatado.",
    scopes=[int(GUILD_ID)] if GUILD_ID else None,
    default_member_permissions=Permissions.MANAGE_MESSAGES,  # exige Gerenciar Mensagens
)
@slash_option(
    name="titulo",
    description="Título do anúncio",
    required=True,
    opt_type=OptionType.STRING
)
@slash_option(
    name="mensagem",
    description="Mensagem principal",
    required=True,
    opt_type=OptionType.STRING
)
@slash_option(
    name="quando",
    description="Data/horário (opcional)",
    required=False,
    opt_type=OptionType.STRING
)
@slash_option(
    name="canal",
    description="Canal de destino (opcional)",
    required=False,
    opt_type=OptionType.CHANNEL
)
async def anunciar(
    ctx: SlashContext,
    titulo: str,
    mensagem: str,
    quando: str = None,
    canal: Channel = None
):
    try:
        destino = canal or ctx.channel

        texto = (
            f"**<a:coroaWhite:1432554574891188294>  〔 CHX 〕APRESENTA:** {titulo}\n"
            f"{mensagem}\n"
        )
        if quando:
            texto += f"🕒 **Quando:** {quando}"

        await destino.send(texto)
        await ctx.send(
            f"✅ Anúncio enviado em {destino.mention}.",
            ephemeral=True
        )

    except Exception as e:
        print("Erro em /anunciar:", repr(e))
        await ctx.send(
            "⚠️ Ocorreu um erro ao tentar enviar o anúncio.",
            ephemeral=True
        )


# ----- INICIAR O BOT -----
if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("❌ Coloque DISCORD_TOKEN no .env / Render Vars")
    bot.start()  # mantém rodando
