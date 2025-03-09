from poke_env import PlayerConfiguration
from players.BasePowerMaximumPlayer import BasePowerMaximumPlayer
from players.DamageMaximumPlayer import DamageMaximumPlayer
from players.MiniMaxPlayer import MiniMaxPlayer
from utils.utils import evaluate
from mm.TeamHeuristic import TeamHeuristic
import asyncio
import random

async def main():

    # number of matches, the default value is 100
    matches = 100
    # max concurrent battles, the default value is 10
    concurrency = 10
    # whether save the results, the default value is true
    save_results = True
    #In this agent, we define 4 play modes: BasePowerMaximumPlayer,
    #DamageMaximumPlayer, MiniMaxPlayer
    playmodes = ["BPM", "DM", "MM"]

    agents = list()

    for i in range(0, len(playmodes)):
        if playmodes[i] == "BPM":
            username = "BPMPlayer" + str(random.randint(0, 1000))
            agent = BasePowerMaximumPlayer(player_configuration=PlayerConfiguration(username, None),
                                        max_concurrent_battles=concurrency)

        elif playmodes[i] == "DM":
            username = "DMPlayer" + str(random.randint(0, 1000))
            agent = DamageMaximumPlayer(player_configuration=PlayerConfiguration(username, None),
                                      max_concurrent_battles=concurrency)
            agent.can_switch = True

        elif playmodes[i] == "MM":
            username = "MMPlayer" + str(random.randint(0, 1000))
            heuristic = TeamHeuristic()
            agent = MiniMaxPlayer(player_configuration=PlayerConfiguration(username, None),
                                   max_concurrent_battles=concurrency, heuristic=heuristic, max_depth=2)
        else:
            raise ValueError

        agents.append(agent)

    await evaluate(agents, matches, save_results)


if __name__ == '__main__':
    run_bot = asyncio.new_event_loop()
    run_bot.run_until_complete(main())
