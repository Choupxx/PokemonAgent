from poke_env.player import Player, cross_evaluate
from poke_env.environment import Pokemon, PokemonType
from typing import Union, List, Tuple, Dict
from tabulate import tabulate
import pandas as pd

"""
evaluate BPM-based agent, DM-based agent, MM-based agent offline
Parameters agents: [BPM-based agent, DM-based agent, MM-based agent]
Parameters matches: number of matches
Parameters save_results: Save our offline results
Returns: None
"""
async def evaluate(agents: List[Player], matches: int = 100, save_results: bool = False) -> None:

    # local agents play against each other
    evaluation_results = await cross_evaluate(agents, n_challenges = matches)

    # Show the test results in the console
    evaluation_table = [["agents\\agents"] + [agent.username for agent in agents]]
    for i, results in evaluation_results.items():
        evaluation_table.append([i] + [str(evaluation_results[i][j]) for j in results])
    print(tabulate(evaluation_table))

    # Save the test results in a csv file
    if save_results:
        evaluation_table[0][0] = "agents\\agents"
        df_results = pd.DataFrame(evaluation_table[1:], columns=evaluation_table[0])
        df_results.to_csv("results/offline_evaluation_results_{0}_matches.csv".format(matches))

"""
convert a Pokemon's types to a string
Parameters: Pokemon_types: Pokemon under consideration or a tuple of types
Returns: String of a Pokémon types
"""
def types_to_string(pokemon_types: Union[Pokemon, Tuple[PokemonType, PokemonType | None]]) -> str:

    if issubclass(type(pokemon_types), Pokemon):
        types = pokemon_types.types
    else:
        types = pokemon_types

    types = [pokemon_type.name for pokemon_type in types if pokemon_type is not None]
    types = types[0] if len(types) == 1 else "{0}/{1}".format(types[0], types[1])
    return types

"""
convert a matchup dict to a string
Parameters matchups: A dict that contains matchup values
Returns: String of matchup values.
"""
def matchups_to_string(matchups: Dict[Pokemon, float]) -> str:
    team = ""
    for i, team_matchup in enumerate(matchups.items()):
        team_pokemon, pokemon_matchup = team_matchup
        team += "{0}: {1}".format(team_pokemon.species, pokemon_matchup)
        if i != len(matchups) - 1:
            team += ", "

    return team
