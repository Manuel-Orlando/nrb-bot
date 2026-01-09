import discord
from discord.ext import commands
import yaml
import os
import sys

# Adiciona a pasta atual ao path do Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Carregar configurações
with open('../config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

class NRBBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix=config['discord']['prefix'],
            intents=intents,
            help_command=None
        )
    
    async def setup_hook(self):
        # Carregar comandos diretamente
        try:
            from commands import ChallengeCommands
            await self.add_cog(ChallengeCommands(self))
            print("✅ Comandos carregados com sucesso!")
        except ImportError as e:
            print(f"❌ Erro ao carregar comandos: {e}")
    
    async def on_ready(self):
        print(f"✅ Bot online como {self.user}")
        print(f"📊 Servidores: {len(self.guilds)}")
        
        # Atividade do bot
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.guilds)} servidores"
            )
        )

# Inicializar bot
if __name__ == "__main__":
    bot = NRBBot()
    bot.run(config['discord']['token'])