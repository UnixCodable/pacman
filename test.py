from src.config import ConfigParser
from src.session import GameSession

config = ConfigParser().load_config("config.json")

session = GameSession(config)

print("Current level:", session.level_number)
print("Total levels:", session.total_levels)
print("Score:", session.score)
print("Lives:", session.lives)
print("Time:", session.time_left)
print("Ghost count:", len(session.game.ghosts))
