import os
from dotenv import load_dotenv

import interactions
from interactions import (
    slash_command,
    slash_option,
    SlashContext,
    listen,
    Intents,
    Embed,
    OptionType,
    Channel,
    Permissions,
)

# ----- CARREGA VARIÁVEIS .env (apenas local) -----
# No Render ele ignora o .env e usa Environment Variables
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")        # obrigatório
GUILD_ID = os.getenv("GUILD_ID")          # opcional (sync só nessa guild)
PREFIX = os.getenv("PREFIX", "!")         # pra comando !oi
OWNER_ID = os.getenv("OWNER_ID")          # opcional

AUTO_ROLE_ID = os.getenv("CARGO_ID")                # cargo automático novos membros
WELCOME_CHANNEL_ID = os.getenv("CANAL_ID")          # canal de boas-vindas
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")        # canal de log inicial


# ----- CONFIGURA O BOT -----
# Precisamos de intents pra ver membros e mensagens
intents = (
    Intents.DEFAULT
    | Intents.GUILD_MEMBERS
    | Intents.GUILD_MESSAGES
    | Intents.MESSAGE_CONTENT
)

bot = interactions.Client(
    token=TOKEN,
    intents=intents,
)


# ----- helper pra logar no canal de log -----
async def send_log_message(text: str):
    if not LOG_CHANNEL_ID:
        return
    try:
        ch = await bot.fetch_channel(int(LOG_CHANNEL_ID))
        if ch:
            await ch.send(text)
    except Exception as e:
        print("Falha ao enviar log:", e)


# ----- EVENTO: BOT PRONTO -----
@listen()
async def on_ready():
    # bot.me costuma ser um User
    nome_bot = getattr(bot.me, "name", str(bot.me))
    print(f"✅ Bot {nome_bot} está online!")

    await send_log_message(
        f"🚀 **{nome_bot}** está online e pronto para uso!"
    )


# ----- EVENTO: NOVO MEMBRO ENTRA -----
# o nome do evento nessa lib é "on_guild_member_add"
@listen()
async def on_guild_member_add(member: interactions.Member):
    try:
        # dar cargo automático
        if AUTO_ROLE_ID:
            try:
                role_id_int = int(AUTO_ROLE_ID)

                # pega o Role dentro da guild
                role_obj = member.guild.get_role(role_id_int)
                if role_obj:
                    await member.add_role(
                        role_obj,
                        reason="Cargo automático de boas-vindas"
                    )
                    print(
                        f"✅ Dei o cargo {role_obj.name} "
                        f"para {member.user.username}"
                    )
                else:
                    print("⚠️ Cargo não encontrado na guild. Verifique o ID.")

            except Exception as e:
                print("⚠️ Erro ao dar cargo automático:", e)

        # mensagem de boas-vindas em canal
        if WELCOME_CHANNEL_ID:
            try:
                ch = await bot.fetch_channel(int(WELCOME_CHANNEL_ID))
                if ch:
                    embed = Embed(
                        title="👋 Seja bem-vindo(a)!",
                        description="🫶 Servidor do seu amigo ChX!",
                        color=0xFFD700  # dourado
                    )

                    avatar_url = getattr(member.user, "avatar_url", None)
                    username = getattr(member.user, "username", "novo membro")

                    if avatar_url:
                        embed.set_thumbnail(url=avatar_url)
                        embed.set_footer(
                            text=f"Bem-vindo(a) à comunidade, {username}!",
                            icon_url=avatar_url
                        )
                    else:
                        embed.set_footer(
                            text=f"Bem-vindo(a) à comunidade, {username}!"
                        )

                    await ch.send(
                        content=f"👋 Seja bem-vindo(a) <@{member.user.id}>!",
                        embeds=[embed],  # precisa ser lista
                    )
                    print(
                        f"📨 Boas-vindas enviadas para {username}"
                    )
            except Exception as e:
                print("⚠️ Erro ao enviar boas-vindas:", e)

    except Exception as e:
        print("❌ Erro geral em on_guild_member_add:", e)


# ----- EVENTO: MENSAGEM NORMAL (!oi) -----
@listen()
async def on_message_create(event: interactions.api.events.MessageCreate):
    msg = event.message

    # ignora bot
    if msg.author.bot:
        return

    # comando !oi
    if msg.content and msg.content.strip().lower() == f"{PREFIX}oi":
        try:
            await msg.reply(
                "👋 Olá! Use **/ping** ou **/anunciar** pra testar."
            )
        except Exception as e:
            print("Erro respondendo !oi:", e)


# ----- SLASH: /ping -----
@slash_command(
    name="ping",
    description="Mostra que o bot está vivo.",
    scopes=[int(GUILD_ID)] if GUILD_ID else None,
)
async def ping(ctx: SlashContext):
    # discord-py-interactions não expõe bot.latency do jeito antigo
    await ctx.send(
        f"🏓 Pong! Estou vivo e respondendo, {ctx.author.mention}!",
        ephemeral=True,
    )


# ----- SLASH: /anunciar -----
@slash_command(
    name="anunciar",
    description="Envia um anúncio formatado.",
    scopes=[int(GUILD_ID)] if GUILD_ID else None,
    default_member_permissions=Permissions.MANAGE_MESSAGES,
)
@slash_option(
    name="titulo",
    description="Título do anúncio",
    required=True,
    opt_type=OptionType.STRING,
)
@slash_option(
    name="mensagem",
    description="Mensagem principal",
    required=True,
    opt_type=OptionType.STRING,
)
@slash_option(
    name="quando",
    description="Data/horário (opcional)",
    required=False,
    opt_type=OptionType.STRING,
)
@slash_option(
    name="canal",
    description="Canal de destino (opcional)",
    required=False,
    opt_type=OptionType.CHANNEL,
)
async def anunciar(
    ctx: SlashContext,
    titulo: str,
    mensagem: str,
    quando: str = None,
    canal: Channel = None,
):
    try:
        destino = canal or ctx.channel

        texto = (
            f"**<a:coroaWhite:1432554574891188294>  〔 CHX 〕APRESENTA:** {titulo}\n"
            f"{mensagem}\n"
        )
        if quando:
            texto += f"🕒 **Quando:** {quando}"

        # manda mensagem no canal alvo
        await destino.send(texto)

        # responde pro staff que usou o comando
        mention_destino = getattr(destino, "mention", f"#{getattr(destino, 'name', 'canal')}")
        await ctx.send(
            f"✅ Anúncio enviado em {mention_destino}.",
            ephemeral=True,
        )

    except Exception as e:
        print("Erro em /anunciar:", repr(e))
        await ctx.send(
            "⚠️ Ocorreu um erro ao tentar enviar o anúncio.",
            ephemeral=True,
        )


# ----- INICIAR O BOT -----
if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError(
            "❌ Coloque DISCORD_TOKEN no .env (local) "
            "ou nas Environment Variables do Render"
        )

    # isso bloqueia e mantém o processo vivo (o Render precisa disso)
    bot.start()
