from typing import List, Dict
from poke_env.environment import Pokemon, Move, Weather, Field, AbstractBattle
from poke_env.environment.move_category import MoveCategory
from core.stats import compute_stat, stats_to_string
from utils.utils import types_to_string

"""
Computes the probability of outspeeding the opponent's Pokémon
Parameters: bot_pokemon: bot's active Pokémon
Parameters: opp_pokemon: opponent's active Pokémon
Parameters: weather: current battle weather
Parameters: terrains: current battle terrains
Parameters: boost: bot's Pokémon "spe" stat boost
Parameters: random_battle: whether the battle is a random battle or not
Parameters: verbose: print the computations
Returns: Outspeed probability, lower and upper bound of the opponent's "spe" stat
"""
def outspeed_prob(bot_pokemon: Pokemon,
                  opp_pokemon: Pokemon,
                  weather: Weather = None,
                  terrains: List[Field] = None,
                  boost: int = None,
                  random_battle: bool = True,
                  verbose: bool = False) -> Dict[str, float]:

    # Compute the stats for both Pokémon
    bot_spe = compute_stat(bot_pokemon, "spe", weather, terrains, True, boost=boost)
    opp_moves = opp_pokemon.moves.keys()
    opp_spe_lb = compute_stat(opp_pokemon, "spe", weather, terrains, ivs=0, evs=0, boost=boost)
    ivs = 0 if "trickroom" in opp_moves or "gyroball" in opp_moves else 31
    if "trickroom" in opp_moves or "gyroball" in opp_moves:
        evs = 0
    elif random_battle:
        evs = 84
    else:
        evs = 252

    opp_spe_ub = compute_stat(opp_pokemon, "spe", weather, terrains, ivs=ivs, evs=evs, boost=boost)
    if verbose:
        print("{0} spe: {1}, {2} spe: {3} {4}".format(bot_pokemon.species, bot_spe, opp_pokemon.species,
                                                      opp_spe_lb, opp_spe_ub))

    # Compute the outspeed probability
    if random_battle:
        opp_spe_lb = opp_spe_ub
        if bot_spe > opp_spe_ub:
            outspeed_p = 1
        elif bot_spe == opp_spe_ub:
            outspeed_p = 0.5  # the so-called speed tie
        else:
            outspeed_p = 0
    elif bot_spe < opp_spe_lb:
        outspeed_p = 0
    elif bot_spe > opp_spe_ub:
        outspeed_p = 1
    elif opp_spe_lb == opp_spe_ub and opp_spe_ub == bot_spe:
        # This will only happen when the bot knows that the opponent's Pokémon has "trick room" or "gyro ball" and their
        # stats are the same
        outspeed_p = 0.5
    else:
        outspeed_p = (bot_spe - opp_spe_lb) / (opp_spe_ub - opp_spe_lb)

    # If "trick room" is active then the priority given by the "spe" stat are inverted
    if Field.TRICK_ROOM in terrains:
        outspeed_p = 1 - outspeed_p

    return {"outspeed_p": round(outspeed_p, 2), "lb": opp_spe_lb, "ub": opp_spe_ub}

"""
Computes the accuracy of a move given various parameters
Parameters: move: move under consideration
Parameters: attacker: attacking Pokémon
Parameters: defender: defending Pokémon
Parameters: weather: current battle weather
Parameters: terrains: current battle terrains
Parameters: attacker_accuracy_boost: attacker's "accuracy" stat boost
Parameters: defender_evasion_boost: defender's "evasion" stat boost
Parameters: verbose: print the computations
Returns: The accuracy of the move
"""
def compute_move_accuracy(move: Move,
                          attacker: Pokemon,
                          defender: Pokemon,
                          weather: Weather = None,
                          terrains: List[Field] = None,
                          attacker_accuracy_boost: int = None,
                          defender_evasion_boost: int = None,
                          verbose: bool = False) -> float:

    # Some moves can't miss by effect of the move itself or the "no guard" ability
    if move.accuracy is True or attacker.is_dynamaxed or attacker.ability == "noguard":
        if verbose:
            print("Move {0} accuracy: {1}".format(move.id, 1))

        return 1

    accuracy = move.accuracy

    # The moves "thunder" and "hurricane" have different accuracies with respect to the active weather
    if move.id in ["thunder", "hurricane"]:
        if weather in [Weather.SUNNYDAY, Weather.DESOLATELAND]:
            accuracy = 0.5
        elif weather in [Weather.RAINDANCE, Weather.PRIMORDIALSEA]:
            return 1

    # The move "blizzard" has an accuracy of 1 if the weather is hail
    if move.id == "blizzard" and weather is Weather.HAIL:
        return 1

    # One-hit KO moves have their accuracy boosted by the difference between the attacker and defender levels
    if move.id in ["fissure", "guillotine", "horndrill", "sheercold"]:
        if defender.level <= attacker.level:
            accuracy += attacker.level - defender.level
        else:
            if verbose:
                print("Move {0} accuracy: {1}".format(move.id, accuracy))

            return move.accuracy

    # Compute accuracy and the evasion
    accuracy *= compute_stat(attacker, "accuracy", weather, terrains, boost=attacker_accuracy_boost)
    if move.ignore_evasion:
        evasion = 1
    else:
        evasion = compute_stat(defender, "evasion", weather, terrains, boost=defender_evasion_boost)

    # Pokémon with the "hustle" ability have their accuracy decreased while using a physical move
    if attacker.ability == "hustle" and move.category is MoveCategory.PHYSICAL:
        accuracy *= 0.8

    # Compute move accuracy
    move_accuracy = accuracy / evasion

    if verbose:
        print("Move {0} accuracy: {1}".format(move.id, move_accuracy))

    return round(move_accuracy, 2)

"""
Get current battle information
Parameters: battle: current battle
Returns: both sides' Weather, fields and conditions
 """
def get_battle_info(battle: AbstractBattle) -> Dict:

    # get weather and fields
    if len(battle.weather.keys()) == 0:
        weather = None
    else:
        weather = next(iter(battle.weather.keys()))
    fields = list(battle.fields.keys())

    # get both sides' conditions
    agent_conditions = list(battle.side_conditions.keys())
    opp_agent_conditions = list(battle.opponent_side_conditions.keys())
    return {"weather": weather, "fields": fields, "agent_conditions": agent_conditions,
            "opp_agent_conditions": opp_agent_conditions}

"""
Battle turn infos to string
Parameters: agent_pokemon: bot's pokémon
Parameters: opp_agent_pokemon: opponent's pokémon
Parameters: weather: current battle weather
Parameters: terrains: current battle terrains
Returns: String with the most useful infos of the current battle turn
"""
def bot_status_to_string(agent_pokemon: Pokemon, opp_agent_pokemon: Pokemon, weather: Weather, fields: List[Field]) -> str:
    agent_max_hp = agent_pokemon.max_hp
    agent_hp = agent_pokemon.current_hp
    opp_agent_max_hp = compute_stat(opp_agent_pokemon, "hp", weather, fields)
    opp_agent_hp = int(opp_agent_max_hp * opp_agent_pokemon.current_hp_fraction)

    bot_infos = "agent Pokemon: {0}, Types: {1}, hp: {2}/{3}\n"\
        .format(agent_pokemon.species, types_to_string(agent_pokemon.types), agent_hp, agent_max_hp)
    bot_infos += "Ability: {0}, Item: {1}\n".format(agent_pokemon.ability, agent_pokemon.item)
    bot_stats = stats_to_string(agent_pokemon, list(agent_pokemon.stats.keys()), weather, fields, True)
    bot_infos += "Stats: {0}\n\n".format(bot_stats)

    bot_infos += "agent Opponent Pokemon: {0}, Types: {1}, hp: {2}/{3}\n"\
        .format(opp_agent_pokemon.species, types_to_string(opp_agent_pokemon.types), opp_agent_hp, opp_agent_max_hp)
    if opp_agent_pokemon.ability:
        opp_abilities = "Ability: {0}".format(opp_agent_pokemon.ability)
    else:
        opp_abilities = "Possible abilities: {0}".format(opp_agent_pokemon.possible_abilities)

    bot_infos += "{0}, Item: {1}\n".format(opp_abilities, opp_agent_pokemon.item)
    opp_stats = stats_to_string(opp_agent_pokemon, list(opp_agent_pokemon.stats.keys()), weather, fields)
    bot_infos += "Stats: {0}\n\n".format(opp_stats)
    bot_infos += "Weather: {0}, Terrains: {1}".format(weather, fields)
    return bot_infos
