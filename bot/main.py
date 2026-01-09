import discord
from discord.ext import commands
import yaml
import os
from dotenv import load_dotenv

# Carregar configurações
load_dotenv()

with open('config/config.yaml', 'r') as f:
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
        # Carregar comandos
        await self.load_extension('bot.commands')
        print("✅ Comandos carregados")
    
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