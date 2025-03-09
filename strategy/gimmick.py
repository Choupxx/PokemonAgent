from typing import List
from poke_env.environment import Pokemon

"""
Define a simple dynamax strategy considering both active Pokémon and the current matchup
Parameters: bot_pokemon: the bot's Pokémon
Parameters: bot_team: the bot's not fainted Pokémon excluding the active one
Parameters: matchup: the current Pokémon's matchup value
Parameters: max_team_matchup: the highest matchup value in the bot's team
Parameters: best_stats_pokemon: the sum of the best Pokémon's stats
Returns: If the bot should use the dynamax gimmick or not
"""
def should_dynamax(bot_pokemon: Pokemon,
                   bot_team: List[Pokemon],
                   matchup: float,
                   max_team_matchup: float = None,
                   best_stats_pokemon: int = None) -> bool:

    # use dynamax if the agent's Pokémon is the last one alive
    if len(bot_team) == 0:
        return True

    # use dynamax if the current Pokèmon is the best one regarding base stats and the matchup is favorable
    if sum(bot_pokemon.base_stats.values()) == best_stats_pokemon \
            and matchup >= 1 and bot_pokemon.current_hp_fraction >= 0.8:
        return True

    if bot_pokemon.current_hp_fraction == 1:
        # use dynamax if the current Pokèmon is the last one at full hp
        if len([pokemon for pokemon in bot_team if pokemon.current_hp_fraction == 1]) == 0:
            return True
        else:
            # use dynamax if the current matchup is the best one and favorable
            if matchup >= max_team_matchup and matchup > 2:
                return True

    if matchup >= max_team_matchup and matchup > 2 and bot_pokemon.current_hp_fraction == 1:
        return True

    return False
