from discord.ext import commands
import discord
import random
from datetime import datetime
from .database import Database
from .logger import Logger

db = Database()
logger = Logger()

class ChallengeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="desafio")
    async def start_challenge(self, ctx, ign: str):
        """Inicia um novo desafio NRB"""
        user_id = str(ctx.author.id)
        username = ctx.author.name
        
        # Verificar se já tem desafio ativo
        if db.has_active_challenge(user_id):
            await ctx.send("❌ Você já tem um desafio ativo!")
            return
        
        # Gerar ID único
        challenge_id = f"CH{random.randint(1000, 9999)}"
        
        # Classes disponíveis (excluindo algumas)
        classes = [
            "Archer", "Wizard", "Priest", "Warrior", 
            "Knight", "Paladin", "Assassin", "Necromancer",
            "Huntress", "Mystic", "Trickster", "Sorcerer",
            "Ninja", "Samurai", "Bard", "Summoner"
        ]
        
        # Sortear classe inicial
        initial_class = random.choice(classes)
        
        # Salvar no banco
        db.create_challenge(
            challenge_id=challenge_id,
            user_id=user_id,
            username=username,
            ign=ign,
            initial_class=initial_class,
            current_class=initial_class,
            rerolls_used=0
        )
        
        # Log
        logger.log_admin(f"CHALLENGE_CREATED | ID: {challenge_id} | User: {username}")
        logger.log_user(ctx, f"🎯 **{username}** iniciou desafio #{challenge_id}")
        
        # Responder
        embed = discord.Embed(
            title="🎯 Desafio Iniciado!",
            description=f"**Jogador:** {ign}\n**Classe sorteada:** {initial_class}",
            color=discord.Color.green()
        )
        embed.add_field(name="Comandos disponíveis", value="!reroll - Reroll da classe\n!aceitar - Aceitar classe", inline=False)
        embed.set_footer(text=f"ID: {challenge_id} • Use !reroll (máx 2x)")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="reroll")
    async def reroll_challenge(self, ctx):
        """Faz reroll da classe (máx 2x)"""
        user_id = str(ctx.author.id)
        challenge = db.get_active_challenge(user_id)
        
        if not challenge:
            await ctx.send("❌ Você não tem um desafio ativo!")
            return
        
        if challenge['rerolls_used'] >= 2:
            await ctx.send("❌ Você já usou todos os rerolls disponíveis!")
            return
        
        # Classes disponíveis
        classes = ["Archer", "Wizard", "Priest", "Warrior", "Knight", "Paladin"]
        new_class = random.choice(classes)
        
        # Atualizar banco
        db.update_challenge(
            challenge_id=challenge['id'],
            current_class=new_class,
            rerolls_used=challenge['rerolls_used'] + 1
        )
        
        # Log
        logger.log_admin(f"REROLL | ID: {challenge['id']} | User: {ctx.author.name} | New: {new_class}")
        logger.log_user(ctx, f"🔄 **{ctx.author.name}** reroll #{challenge['rerolls_used']+1}: {new_class}")
        
        await ctx.send(f"🔄 Novo sorteio: **{new_class}** (Reroll {challenge['rerolls_used']+1}/2)")
    
    @commands.command(name="aceitar")
    async def accept_challenge(self, ctx):
        """Aceita a classe atual"""
        user_id = str(ctx.author.id)
        challenge = db.get_active_challenge(user_id)
        
        if not challenge:
            await ctx.send("❌ Você não tem um desafio ativo!")
            return
        
        # Marcar como aceito
        db.accept_challenge(challenge['id'])
        
        # Log
        logger.log_admin(f"CHALLENGE_ACCEPTED | ID: {challenge['id']} | User: {ctx.author.name} | Class: {challenge['current_class']}")
        logger.log_user(ctx, f"✅ **{ctx.author.name}** aceitou: {challenge['current_class']}")
        
        # Gerar link para tracking
        link = f"https://seuusuario.github.io/nrb-bot/?id={challenge['id']}"
        
        embed = discord.Embed(
            title="✅ Desafio Aceito!",
            description=f"**Classe:** {challenge['current_class']}\n**Rerolls usados:** {challenge['rerolls_used']}/2",
            color=discord.Color.blue()
        )
        embed.add_field(name="📊 Acompanhe seu progresso", value=f"[Clique aqui]({link})", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="meudesafio")
    async def my_challenge(self, ctx):
        """Mostra seu desafio atual"""
        user_id = str(ctx.author.id)
        challenge = db.get_active_challenge(user_id)
        
        if not challenge:
            await ctx.send("❌ Você não tem um desafio ativo!")
            return
        
        link = f"https://seuusuario.github.io/nrb-bot/?id={challenge['id']}"
        
        embed = discord.Embed(
            title=f"🎯 Desafio #{challenge['id']}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Jogador", value=challenge['ign'], inline=True)
        embed.add_field(name="Classe", value=challenge['current_class'], inline=True)
        embed.add_field(name="Status", value="✅ Aceito" if challenge['accepted'] else "🔄 Pendente", inline=True)
        embed.add_field(name="Rerolls", value=f"{challenge['rerolls_used']}/2", inline=True)
        embed.add_field(name="Iniciado em", value=challenge['created_at'][:10], inline=True)
        embed.add_field(name="Link", value=f"[Acompanhar]({link})", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ChallengeCommands(bot))