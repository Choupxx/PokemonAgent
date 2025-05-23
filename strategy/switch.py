from poke_env.environment import Pokemon, Weather, Field, Status
from core.utils import outspeed_prob
from typing import Union
import numpy as np

"""
Defines a switch strategy for the bot taking into account the matchup of its active Pokémon and all the other not
fainted Pokémon in the team, the outspeed probability and the number of toxic turns that have passed
Parameters: bot_pokemon: the bot's Pokémon
Parameters: matchup: the bot's Pokémon matchup
Parameters: outspeed_p: the outspeed probability of the bot's Pokémon against the opponent's.
Parameters: max_team_matchup: the highest matchup value in the bot's team
Parameters: toxic_turn: the number of turns that the current Pokémon has passed with the toxic status
Returns: Boolean that the bot if it should switch out or not
"""
def should_switch(bot_pokemon: Pokemon,
                  matchup: float,
                  outspeed_p: float,
                  max_team_matchup: int,
                  toxic_turn: int = 0) -> bool:

    # Do not switch out the Pokèmon if it is dynamaxed unless there is a very bad matchup
    if bot_pokemon.is_dynamaxed:
        if matchup <= -4:
            return True

        return False

    # We can switch out if there are matchups better than the current one
    if max_team_matchup > matchup:
        # The "toxic" status is one of the worst status, we need to attenuate its effects by switching
        if bot_pokemon.status is Status.TOX and matchup - toxic_turn <= -2:
            return True

        # If one of the defense stat was decreased too much, switch out to not take heavy hits
        if bot_pokemon.boosts["def"] <= -2 or bot_pokemon.boosts["spd"] <= -2:
            return True

        # If the attack stat was decreased too much and the Pokèmon is a physical attacker, switch out
        if bot_pokemon.base_stats["atk"] > bot_pokemon.boosts["spa"]:
            if matchup <= -1.5 or bot_pokemon.boosts["atk"] <= -2:
                return True

        # If the special attack stat was decreased too much and the Pokèmon is a special attacker, switch out
        if bot_pokemon.base_stats["spa"] > bot_pokemon.boosts["atk"]:
            if matchup <= -1.5 or bot_pokemon.boosts["spa"] <= -2:
                return True

        # Switch out if the matchup is on the opponent's favor
        if matchup <= -1.5:
            return True
        elif matchup <= -1 and outspeed_p <= 0.5:
            return True

    return False

"""
Computes the best not fainted Pokémon to switch in
Parameters: team_matchups: all the matchup values for the not fainted Pokémon in the bot's team
Parameters: opp_pokemon: the opponent's Pokémon
Parameters: weather: the current weather
Parameters: terrains: the current active fields
Parameters: max_team_matchup: the highest matchup value in the bot's team
Returns: The best Pokémon to switch in
"""
def compute_best_switch(team_matchups: dict[Pokemon, float],
                        opp_pokemon: Pokemon,
                        weather: Weather,
                        terrains: list[Field],
                        max_team_matchup: int) -> Union[Pokemon | None]:

    if team_matchups:
        # Retrieve all the Pokémon in the team with the best matchup
        best_switches = {pokemon: pokemon.stats for pokemon, matchup in team_matchups.items()
                         if matchup == max_team_matchup}

        # Keep those Pokémon that can outspeed the opponent's Pokémon
        outspeed_opp = [pokemon for pokemon, _ in best_switches.items()
                        if outspeed_prob(pokemon, opp_pokemon, weather, terrains)["outspeed_p"] > 0.6]
        if outspeed_opp:
            # If there are no Pokémon that can outspeed the opponent, then choose one randomly
            switch_choice = np.random.randint(0, len(outspeed_opp))
            return outspeed_opp[switch_choice]
        else:
            # Choose a Pokémon randomly from the team
            best_switches = list(best_switches.keys())
            switch_choice = np.random.randint(0, len(best_switches))
            return best_switches[switch_choice]
    else:
        return None
