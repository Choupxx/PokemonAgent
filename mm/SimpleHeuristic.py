from mm.BattleStatus import BattleStatus
from mm.Heuristic import Heuristic
from core.stats import estimate_stat

"""
Evaluate state in the minimax algorithm using only the knowledge of the two active Pokémon in the battle
Parameters: battle_node: minimax node containing the state information
Parameters: depth: depth of the node in the minimax tree
Returns: evaluation score of the minimax node
"""
class SimpleHeuristic(Heuristic):

    def compute(self, battle_node: BattleStatus, depth: int) -> float:
        bot_hp = battle_node.act_poke.current_hp
        opp_hp = battle_node.opp_poke.current_hp
        opp_max_hp = estimate_stat(battle_node.opp_poke.pokemon, "hp")
        score = (bot_hp / battle_node.act_poke.pokemon.max_hp) - (
                opp_hp / opp_max_hp)

        return score
