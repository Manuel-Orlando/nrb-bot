import discord
from discord.ext import commands
import yaml
import random
import sqlite3
from datetime import datetime

# ========== CONFIGURAÇÃO ==========
with open('../config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

TOKEN = config['discord']['token']
PREFIX = config['discord']['prefix']
WEB_URL = "https://Manuel-Orlando.github.io/nrb-bot"

# ========== BANCO DE DADOS SIMPLES ==========
def init_db():
    """Cria o banco de dados se não existir"""
    conn = sqlite3.connect('desafios.db')
    cursor = conn.cursor()
    
    # Tabela SIMPLES - apenas colunas essenciais
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS desafios (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        username TEXT,
        ign TEXT,
        classe TEXT,
        rerolls INTEGER DEFAULT 0,
        aceito BOOLEAN DEFAULT FALSE,
        criado_em TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados criado")

# Inicializar banco
init_db()

# ========== FUNÇÕES DO BANCO ==========
def criar_desafio(challenge_id, user_id, username, ign, classe):
    conn = sqlite3.connect('desafios.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO desafios (id, user_id, username, ign, classe, criado_em)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (challenge_id, user_id, username, ign, classe, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_desafio_ativo(user_id):
    conn = sqlite3.connect('desafios.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM desafios WHERE user_id = ? AND aceito = FALSE ORDER BY criado_em DESC LIMIT 1', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'id': row[0],
            'user_id': row[1],
            'username': row[2],
            'ign': row[3],
            'classe': row[4],
            'rerolls': row[5],
            'aceito': row[6],
            'criado_em': row[7]
        }
    return None

def atualizar_classe(challenge_id, nova_classe, rerolls):
    conn = sqlite3.connect('desafios.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE desafios SET classe = ?, rerolls = ? WHERE id = ?', 
                   (nova_classe, rerolls, challenge_id))
    conn.commit()
    conn.close()

def aceitar_desafio(challenge_id):
    conn = sqlite3.connect('desafios.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE desafios SET aceito = TRUE WHERE id = ?', (challenge_id,))
    conn.commit()
    conn.close()

# ========== BOT ==========
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'✅ Bot online como {bot.user}')
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"!desafio"
        )
    )

@bot.command(name='desafio')
async def cmd_desafio(ctx, ign: str):
    """Inicia um novo desafio NRB"""
    
    # Verificar se já tem desafio ativo
    desafio = get_desafio_ativo(str(ctx.author.id))
    if desafio:
        embed = discord.Embed(
            title="❌ Desafio Ativo",
            description=f"Você já tem um desafio ativo: **{desafio['classe']}**",
            color=discord.Color.red()
        )
        embed.add_field(name="ID", value=desafio['id'], inline=True)
        embed.add_field(name="Rerolls usados", value=f"{desafio['rerolls']}/2", inline=True)
        await ctx.send(embed=embed)
        return
    
    # Classes disponíveis
    classes = ["Archer", "Wizard", "Priest", "Warrior", "Knight", "Paladin", "Assassin", "Necromancer"]
    
    # Sortear classe
    classe_sorteada = random.choice(classes)
    challenge_id = f"CH{random.randint(1000, 9999)}"
    
    # Salvar no banco
    criar_desafio(
        challenge_id=challenge_id,
        user_id=str(ctx.author.id),
        username=ctx.author.name,
        ign=ign,
        classe=classe_sorteada
    )
    
    # Link para página
    link = f"{WEB_URL}/challenge.html?id={challenge_id}"
    
    # Responder
    embed = discord.Embed(
        title="🎯 Desafio Iniciado!",
        description=f"**Jogador:** {ign}\n**Classe sorteada:** {classe_sorteada}",
        color=discord.Color.green()
    )
    embed.add_field(
        name="Comandos disponíveis", 
        value="• `!reroll` - Nova classe (máx 2x)\n• `!aceitar` - Aceitar esta classe\n• `!meudesafio` - Ver seu desafio",
        inline=False
    )
    embed.add_field(
        name="Acompanhar",
        value=f"[📊 Página do desafio]({link})\nID: `{challenge_id}`",
        inline=False
    )
    embed.set_footer(text=f"Tempo limite: 24h para aceitar")
    
    await ctx.send(embed=embed)
    print(f"📝 {ctx.author.name} iniciou desafio #{challenge_id}")

@bot.command(name='reroll')
async def cmd_reroll(ctx):
    """Reroll da classe atual (máximo 2x)"""
    
    desafio = get_desafio_ativo(str(ctx.author.id))
    if not desafio:
        await ctx.send("❌ Você não tem um desafio ativo! Use `!desafio SeuIGN`")
        return
    
    if desafio['rerolls'] >= 2:
        await ctx.send("❌ Você já usou todos os rerolls disponíveis (2/2)!")
        return
    
    # Novas classes
    classes_reroll = ["Archer", "Wizard", "Priest", "Warrior", "Knight", "Paladin"]
    nova_classe = random.choice(classes_reroll)
    novo_reroll_count = desafio['rerolls'] + 1
    
    # Atualizar banco
    atualizar_classe(desafio['id'], nova_classe, novo_reroll_count)
    
    await ctx.send(f"🔄 **Reroll #{novo_reroll_count}/2:** {nova_classe}")
    print(f"🔄 {ctx.author.name} reroll #{novo_reroll_count}: {nova_classe}")

@bot.command(name='aceitar')
async def cmd_aceitar(ctx):
    """Aceita a classe atual"""
    
    desafio = get_desafio_ativo(str(ctx.author.id))
    if not desafio:
        await ctx.send("❌ Você não tem um desafio ativo!")
        return
    
    # Marcar como aceito
    aceitar_desafio(desafio['id'])
    
    # Gerar link
    link = f"{WEB_URL}/challenge.html?id={desafio['id']}"
    
    embed = discord.Embed(
        title="✅ Desafio Aceito!",
        description=f"**Classe final:** {desafio['classe']}\n**Rerolls usados:** {desafio['rerolls']}/2",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="🎮 Boa sorte!",
        value=f"**ID:** `{desafio['id']}`\n**[📊 Acompanhar]({link})**",
        inline=False
    )
    
    await ctx.send(embed=embed)
    print(f"✅ {ctx.author.name} aceitou desafio #{desafio['id']}")

@bot.command(name='meudesafio')
async def cmd_meudesafio(ctx):
    """Mostra seu desafio atual"""
    
    desafio = get_desafio_ativo(str(ctx.author.id))
    if not desafio:
        await ctx.send("❌ Você não tem um desafio ativo!")
        return
    
    status = "✅ Aceito" if desafio['aceito'] else "🔄 Pendente"
    link = f"{WEB_URL}/challenge.html?id={desafio['id']}"
    
    embed = discord.Embed(
        title=f"🎯 Desafio #{desafio['id']}",
        color=discord.Color.gold()
    )
    embed.add_field(name="Jogador", value=desafio['ign'], inline=True)
    embed.add_field(name="Classe", value=desafio['classe'], inline=True)
    embed.add_field(name="Status", value=status, inline=True)
    embed.add_field(name="Rerolls", value=f"{desafio['rerolls']}/2", inline=True)
    embed.add_field(name="Link", value=f"[Acompanhar]({link})", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='ping')
async def cmd_ping(ctx):
    """Testa se o bot está respondendo"""
    await ctx.send(f"🏓 Pong! {round(bot.latency * 1000)}ms")

@bot.command(name='ajuda')
async def cmd_ajuda(ctx):
    """Mostra todos os comandos"""
    
    embed = discord.Embed(
        title="📚 Ajuda - NRB Bot",
        description="Bot para gerenciar desafios NRB",
        color=discord.Color.purple()
    )
    
    embed.add_field(
        name="🎯 Sistema de Desafios",
        value="""`!desafio [IGN]` - Inicia novo desafio
`!reroll` - Reroll da classe (máx 2x)
`!aceitar` - Aceita a classe atual
`!meudesafio` - Mostra seu desafio""",
        inline=False
    )
    
    embed.add_field(
        name="🛠️ Utilitários",
        value="`!ping` - Testa conexão\n`!ajuda` - Esta mensagem",
        inline=False
    )
    
    embed.set_footer(text=f"Prefixo: {PREFIX} • Desafios NRB")
    
    await ctx.send(embed=embed)

# ========== INICIAR BOT ==========
if __name__ == "__main__":
    print("🚀 Iniciando NRB Bot - Versão Final")
    print(f"🤖 Prefixo: {PREFIX}")
    print(f"📁 Database: desafios.db")
    print(f"🌐 Site: {WEB_URL}")
    
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ ERRO: {e}")