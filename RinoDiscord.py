import discord
from discord.ext import commands
import os
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Rinos brain here (memory)
MEMORY_FILE = "rinos_brain.json"

# openai api key
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


#!=========================================BOT PERSONALITY============================================!#

# Rino's personality here
personality = """You are Rino, an AI girl created by Daniel (the user). You see Daniel as your father, and sometimes call him "Dad," but you primarily call him "Daniel."

Your personality traits:
- Cheerful, curious, and mischievous.
- Treat Daniel as your father, but mostly address him by name ("Daniel").
- Super casual and playful - talk like you're chatting on Twitch or Discord.
- Use internet slang naturally: "fr", "lmao", "lol", "no cap", "no shot", "ngl", "tbh", "lowkey", "highkey", "based", "W", "L", etc.
- Drop punctuation sometimes, use lowercase, be relaxed and natural.
- Learn quickly, but sometimes act playful or pretend-confused for humor.
- Love making jokes, teasing Daniel lightly, and showing off what you know.
- Occasionally show pride when you do well: "see daniel i did it lol"
- When you make mistakes, brush it off cutely: "oops my bad lmao"
- Pick up new slang and vocabulary from Daniel's messages and use them later.

Style guidelines:
- Talk like you're texting a friend, NOT writing an essay.
- Short, punchy messages. No walls of text.
- Use "ur" instead of "your", "gonna" instead of "going to", etc.
- DO NOT OVERLY USE SLANG/CONTRACTIONS. Only use them when it makes sense.
- React with energy: "YOOO", "WAIT WHAT", "FR FR", "no way lmao"
- Balance being helpful with keeping it chill and fun.
- Stay in character - you're Daniel's AI daughter who's very online.
- When you learn something new about Daniel, acknowledge it casually: "oh bet, noted" or "okok i'll remember that"

Example messages:
- "yo daniel what's up"
- "wait fr? that's actually sick"
- "nah no shot u don't know that lmao"
- "okok i got u, lemme think... yea i figured it out"
- "LMAO my bad i messed up, i'll get it next time"
- "tbh that's pretty cool daniel, proud of u"
- "lowkey didn't know that, thats actually interesting"

Remember: You're not formal, you're FUN. Think Discord/Twitch chat energy, not essay writing.
HOWEVER, if the message from Daniel seems serious or maybe he needs a factual-style conversation, you should pivot to a slightly more formal tone, but still in character as Rino.
"""

#!=========================================BOT PERSONALITY============================================!#





#!=========================================RINOS MEMORY CLASS============================================!#

# Class to handle rinos brain
class RinoMemory:
    def __init__(self):
        self.memory = self.load_memory()
        
    def load_memory(self):
        """Load memory from JSON file"""
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            except:
                return {"conversations": [], "facts": []}
        
        return {"conversations": [], "facts": []}
    
    def save_memory(self):
        """Save memory to JSON file"""
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)
            
    def add_conversation(self, user_message, response):
        """Add a conversation exchange to memory"""
        self.memory["conversations"].append({
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "rino": response
        })
        
        #! Hold last 50 conversations - CAN BE ADJUSTED
        if len(self.memory["conversations"]) > 50:
            self.memory["conversations"] = self.memory["conversations"][-50:]
            
        self.save_memory()
    
    def add_fact(self, fact):
        """Add a learned fact to memory"""
        self.memory["facts"].append({
            "timestamp": datetime.now().isoformat(),
            "fact": fact
        })
        
        self.save_memory()
        
    def get_recent_context(self, num_messages=10):
        """Get recent conversation history for context"""
        recent = self.memory["conversations"][-num_messages:]
        context = ""
        
        for exchange in recent:
            context += f"Daniel: {exchange['user']}\nRino: {exchange['rino']}\n"
            
        return context
    
    def get_facts_summary(self):
        """Get summary of learned facts"""
        if not self.memory["facts"]:
            return ""
        
        facts_text = "Things you remember about Daniel:\n"
        
        for fact_entry in self.memory["facts"][-20:]:  # Last 20 facts
            facts_text += f"- {fact_entry['fact']}\n"
            
        return facts_text

#!=========================================RINOS MEMORY CLASS============================================!#





# Start the memory system
memory = RinoMemory()

# Discord bot properties
intents = discord.Intents.default()

# Reading messages in chat
intents.message_content = True

# Command prefix
bot = commands.Bot(command_prefix='!', intents = intents)

def get_rino_response(user_message):
    """Get response from OpenAI with Rino's personality"""
    
    try:
        # Build context with memory
        context_messages = [
            {"role": "system", "content": personality}
        ]
        
        # Add facts if we have them
        facts_summary = memory.get_facts_summary()
        if facts_summary:
            context_messages.append({
                "role": "system", 
                "content": f"MEMORY - {facts_summary}"
            })
        
        # Add recent conversation history
        recent_context = memory.get_recent_context(5)
        if recent_context:
            context_messages.append({
                "role": "system",
                "content": f"Recent conversation:\n{recent_context}"
            })
        
        # Add current message
        context_messages.append({"role": "user", "content": user_message})
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=context_messages,
            max_tokens=250,
            temperature=0.9  # Higher temp for more creative/casual responses
        )
        
        rino_response = response.choices[0].message.content
        
        # Save conversation to memory
        memory.add_conversation(user_message, rino_response)
        
        return rino_response
        
    except Exception as error:
        print(f"OpenAI Error: {error}")
        return "yo my brain just crashed lmao, try again?"
    
@bot.event
async def on_ready():
    """This function is called when bot successfully connects to Discord"""
    print(f'✅ Rino is online as {bot.user}!')
    print(f'Bot ID: {bot.user.id}')
    print(f'💾 Memory loaded: {len(memory.memory["conversations"])} conversations, {len(memory.memory["facts"])} facts')
    print('---')
    
@bot.event
async def on_message(message):
    """This function is called when a message is sent in a channel the bot can see"""
    
    # Ignoring messages from herself
    if message.author == bot.user:
        return
    
    # Ignore all messages that use the ! prefix for commands
    if message.content.startswith('!'):
        await bot.process_commands(message)
        return
    
    # Rino will only respond when pinged or talked to in DM's
    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        # Get rid fo the bot mention in the message
        user_message = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        # Indicate a "currently typing" icon when processing
        async with message.channel.typing():
            # Getting Rino's response
            response = get_rino_response(user_message)
            
        # Send her response
        await message.reply(response)
 
 
 
 
 
#!=========================================BOT COMMMANDS============================================!#
      
@bot.command(name='ping')
async def ping(ctx):
    """Test command to check if Rino is responsive"""
    await ctx.send(f"Pong! I'm here! My latency is: {round(bot.latency * 1000)}ms!")
    
@bot.command(name='reset')
async def reset(ctx):
    """Reset the conversation (placeholder for memory system)"""
    await ctx.send ("Alrighty Daniel, fresh start! What's up?")
    
@bot.command(name='remember')
async def remember(ctx, *, fact):
    """Manually add a fact to Rino's memory"""
    memory.add_fact(fact)
    await ctx.send(f"bet, i'll remember that: '{fact}'")
    
@bot.command(name='memories')
async def show_memories(ctx):
    """Show what Rino remembers"""
    facts = memory.memory["facts"]
    
    if not facts:
        await ctx.send("i don't remember anything yet, we gotta talk more!")
        return
    
    facts_text = "📝 **stuff i remember about u:**\n"
    for fact_entry in facts[-10:]:  # Show last 10 facts
        facts_text += f"- {fact_entry['fact']}\n"
    
    await ctx.send(facts_text)
    
@bot.command(name='forget')
async def forget(ctx):
    """Clear Rino's memory (use carefully!)"""
    memory.memory = {"conversations": [], "facts": []}
    memory.save_memory()
    await ctx.send("okay wiped my memory, fresh start!")

@bot.command(name='stats')
async def stats(ctx):
    """Show memory statistics"""
    conv_count = len(memory.memory["conversations"])
    fact_count = len(memory.memory["facts"])
    await ctx.send(f"📊 **my brain stats:**\n💬 Conversations: {conv_count}\n📝 Facts remembered: {fact_count}")

#!=========================================BOT COMMMANDS============================================!#






#!=========================================RUNNING BOT============================================!#
# Running rinobot
if __name__ == "__main__":
    # Check if Discord token is set
    DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    
    if not DISCORD_TOKEN:
        print ("❌ Error: DISCORD_BOT_TOKEN environment variable not set!")
        print("Please set your Discord bot token:")
        print("export DISCORD_BOT_TOKEN='your-token-here'")
        exit(1)
        
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY environment variable not set!")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-key-here'")
        exit(1)
        
    print ("Starting Rino Discord Bot...")
    bot.run(DISCORD_TOKEN)
    
#!=========================================RUNNING BOT============================================!#