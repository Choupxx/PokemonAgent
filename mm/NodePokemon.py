from typing import List, Dict
from poke_env.environment import Pokemon, Move, MoveCategory, Weather, Field, Status
from core.useful_data import DEFAULT_MOVES_IDS
from core.stats import estimate_stat, compute_stat_modifiers, compute_stat_boost
import copy

"""
Instantiate a Pokémon node with the parameters that could change during the simulation of the progress of a
battle, that happens during the computation of the minimax tree
Parameters: pokemon: a Pokémon
Parameters: is_act_poke: true if it is the bot's Pokémon, false otherwise
Parameters: current_hp: current simulated heath points of the Pokémon
Parameters: boosts: current simulated statistics boost of the Pokémon
Parameters: status: current simulated status of the Pokémon
Parameters: moves: known moves of the Pokémon
Parameters: effects: status effects of the Pokémon
"""
class NodePokemon:

    def __init__(self,
                 pokemon: Pokemon,
                 is_act_poke: bool,
                 current_hp: int = None,
                 boosts: Dict[str, int] = None,
                 status: Status = None,
                 moves: List[Move] = None,
                 effects: Dict = None):

        self.pokemon: Pokemon = pokemon
        self.poke = copy.deepcopy(pokemon)
        self.is_act_poke: bool = is_act_poke

        if current_hp is None and is_act_poke:
            current_hp = pokemon.current_hp
        elif current_hp is None and not is_act_poke:
            current_hp = estimate_stat(pokemon, 'hp') * pokemon.current_hp_fraction
        elif current_hp < 0:
            current_hp = 0
        self.current_hp: int = current_hp
        assert self.current_hp >= 0

        if boosts is None:
            boosts = pokemon.boosts
        self.boosts: Dict[str, int] = boosts

        if status is None:
            status = pokemon.status
        self.status: Status = status

        if is_act_poke or len(moves) == 4:
            self.moves: List[Move] = list(moves)
        elif not is_act_poke:
            self.moves: List[Move] = self.enrich_moves(list(moves))
        assert self.moves is not None

        if effects is None:
            effects = pokemon.effects
        self.effects: Dict = effects

    """
    Computes if the pokémon is fainted
    Returns: true if the pokémon is fainted, false otherwise
    """
    def is_fainted(self) -> bool:
        return self.current_hp <= 0

    """
    Clones all the fields of the current object
    Returns: a copy of this object
    """
    def clone_all(self):
        return NodePokemon(self.pokemon, self.is_act_poke, self.current_hp, self.boosts.copy(), self.status,
                           self.moves.copy(), self.effects.copy())

    """
    Clones the current object with the possibility of specifying some custom fields
    Returns: a copy of this object
    """
    def clone(self,
              is_act_poke: bool = None,
              current_hp: int = None,
              boosts: Dict[str, int] = None,
              status: Status = None,
              moves: list[Move] = None,
              effects: Dict = None):
        if is_act_poke is None:
            is_act_poke = self.is_act_poke
        if current_hp is None:
            current_hp = self.current_hp
        if boosts is None:
            boosts = self.boosts.copy()
        if status is None:
            status = self.status
        if moves is None:
            moves = self.moves.copy()
        if effects is None:
            effects = self.effects.copy()
        return NodePokemon(self.pokemon, is_act_poke, current_hp, boosts, status, moves, effects)

    """
    Assigns default moves to a Pokémon with the same type of the Pokémon's ones if there are no known moves with
    those type. If the known_moves have a different type with respect to this Pokémon, they are joined to the
    default ones
    Parameters: known_moves: some known moves of this Pokémon
    Returns: a list of all the known moves plus the default ones
    """
    def enrich_moves(self, known_moves: List[Move]) -> List[Move]:
        moves_added: List[Move] = []
        for poke_type in iter(self.pokemon.types):
            if poke_type is not None:
                move_same_poke_type = False
                for move in known_moves:
                    if move.type == poke_type:
                        move_same_poke_type = True
                        break
                if not move_same_poke_type:
                    # def_move: Gen8Move = self.default_moves[poke_type]
                    if self.pokemon.base_stats["atk"] >= self.pokemon.base_stats["spa"]:
                        moves_added.append(DEFAULT_MOVES_IDS[poke_type][MoveCategory.PHYSICAL])
                    else:
                        moves_added.append(DEFAULT_MOVES_IDS[poke_type][MoveCategory.SPECIAL])
                    # moves_added.append(def_move)
        return moves_added + known_moves
