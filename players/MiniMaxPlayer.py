from poke_env import PlayerConfiguration, ServerConfiguration
from poke_env.environment import Status, Gen8Move
from poke_env.player import Player
from poke_env.teambuilder import Teambuilder
from mm.BattleStatus import BattleStatus
from mm.Heuristic import Heuristic
from mm.NodePokemon import NodePokemon
from core.utils import *
from core.stats import compute_stat
from strategy.gimmick import should_dynamax
from strategy.matchup import matchup_on_types
from strategy.switch import should_switch, compute_best_switch
from mm.SimpleHeuristic import SimpleHeuristic
from utils.utils import matchups_to_string
from core.damage import compute_damage
from typing import Optional, Union, Tuple
import math


class MiniMaxPlayer(Player):

    def __init__(self,
                 heuristic: Optional[Heuristic] = SimpleHeuristic(),
                 max_depth: Optional[int] = 2,
                 verbose: bool = False,
                 player_configuration: Optional[PlayerConfiguration] = None,
                 *,
                 avatar: Optional[int] = None,
                 battle_format: str = "gen8randombattle",
                 log_level: Optional[int] = None,
                 max_concurrent_battles: int = 1,
                 save_replays: Union[bool, str] = False,
                 server_configuration: Optional[ServerConfiguration] = None,
                 # start_timer_on_battle_start: bool = False,
                 start_listening: bool = True,
                 ping_interval: Optional[float] = 20.0,
                 ping_timeout: Optional[float] = 20.0,
                 team: Optional[Union[str, Teambuilder]] = None,
                 ):
        super(MiniMaxPlayer, self).__init__(
            player_configuration = player_configuration,
            avatar = avatar,
            battle_format = battle_format,
            log_level = log_level,
            max_concurrent_battles = max_concurrent_battles,
            save_replays = save_replays,
            server_configuration = server_configuration,
            start_timer_on_battle_start = True,
            start_listening = start_listening,
            ping_interval = ping_interval,
            ping_timeout = ping_timeout,
            team = team
        )
        self.heuristic: Heuristic = heuristic
        self.max_depth: int = max_depth
        self.verbose: bool = verbose
        self.best_stats_pokemon = 0
        self.previous_pokemon = None
        self.max_team_matchup: int = -8
        self.toxic_turn: int = 0

    def choose_move(self, battle):

        # Retrieve both active pokémon
        bot_pokemon: Pokemon = battle.active_pokemon
        opp_pokemon: Pokemon = battle.opponent_active_pokemon

        # Retrieve all the other pokèmon in the team that are still alive
        bot_team = [pokemon for pokemon in battle.team.values()
                    if not pokemon.active and not pokemon.fainted]

        # Retrieve all the pokémon in the opponent's team
        '''opp_team_pokemon = 6 - len([pokemon for pokemon in battle.opponent_team.values()
                                    if not pokemon.active and pokemon.fainted])'''

        # Retrieve weather, terrains and side conditions
        weather, terrains, bot_conditions, opp_conditions = get_battle_info(battle).values()

        # Compute the hp of both pokémon
        # bot_hp = bot_pokemon.current_hp
        opp_max_hp = compute_stat(opp_pokemon, "hp", weather, terrains)
        # opp_hp = int(opp_max_hp * opp_pokemon.current_hp_fraction)

        best_switch, bot_matchup, outspeed_p, team_matchups = self.best_switch_on_matchup(battle, bot_pokemon, bot_team,
                                                                                          opp_pokemon, terrains,
                                                                                          weather)
        if should_switch(bot_pokemon, bot_matchup, outspeed_p, self.max_team_matchup, self.toxic_turn) \
                and battle.available_switches:
            self.previous_pokemon = bot_pokemon
            if self.verbose:
                print("Switching to {0}\n{1}".format(best_switch.species, "-" * 110))

            return self.create_order(best_switch)

        if battle.available_moves:
            opp_team = [poke for poke in battle.opponent_team.values() if not poke.active]
            avail_switches = battle.available_switches

            available_moves = battle.available_moves
            available_moves.sort(reverse=True, key=lambda x: int(x.base_power))
            root_battle_status = BattleStatus(
                NodePokemon(battle.active_pokemon, is_act_poke=True, moves=available_moves),
                NodePokemon(battle.opponent_active_pokemon, is_act_poke=False, current_hp=opp_max_hp,
                            moves=list(battle.opponent_active_pokemon.moves.values())),
                avail_switches, opp_team, battle.weather, terrains,
                opp_conditions, None, Gen8Move('splash'), True)

            can_defeat, best_move = False, Gen8Move('splash')
            if root_battle_status.move_first and len(battle.available_moves) > 0:
                can_defeat, best_move = self.hit_if_act_poke_can_outspeed(battle, terrains, opp_max_hp, opp_conditions)

            if len(battle.available_moves) == 0 or can_defeat is not True:
                best_move = self.get_best_move(battle, root_battle_status)

            dynamax: bool = False
            my_team = [poke for poke in list(battle.team.values()) if poke.status != Status.FNT and not poke.active]
            if battle.can_dynamax and not isinstance(best_move, Pokemon):
                dynamax = should_dynamax(battle.active_pokemon, my_team, bot_matchup,
                                         self.max_team_matchup, self.best_stats_pokemon)

            if self.verbose:
                self.print_chosen_move(battle, best_move, opp_conditions, terrains, weather)

            return self.create_order(best_move, dynamax=dynamax)

        elif battle.available_switches:
            # Update the matchup for each remaining pokèmon in the team
            for pokemon in bot_team:
                team_matchups.update({pokemon: matchup_on_types(pokemon, opp_pokemon)})

            # Choose the new active pokèmon
            self.max_team_matchup = max(team_matchups.values()) if len(team_matchups) > 0 else -8
            best_switch = compute_best_switch(team_matchups, opp_pokemon, weather, terrains, self.max_team_matchup)
            self.previous_pokemon = bot_pokemon
            if self.verbose:
                print("Switching to {0}\n{1}".format(best_switch.species, "-" * 110))

            return self.create_order(best_switch)

        return self.choose_random_move(battle)

    """
    Chooses the best Pokémon that will take the filed, based on the matchup score
    Parameters: battle: current state of the battle
    Parameters: bot_pokemon: our Pokémon
    Parameters: bot_team: our team
    Parameters: opp_pokemon: opponent Pokémon
    Parameters: terrains: list of the active terrains in the battle
    Parameters: weather: the weather condition of a battle
    Returns: a tuple made up of the best Pokémon to switch, the matchup score, the probability to be faster than the
    opponent Pokémon and the matchup of the entire team
    """
    def best_switch_on_matchup(self, battle: AbstractBattle, bot_pokemon: Pokemon, bot_team: List[Pokemon],
                               opp_pokemon: Pokemon, terrains: List[Field], weather: Weather):

        # Compute matchup scores for every remaining pokémon in the team
        bot_matchup = matchup_on_types(bot_pokemon, opp_pokemon)
        team_matchups = dict()
        for pokemon in bot_team:
            team_matchups.update({pokemon: matchup_on_types(pokemon, opp_pokemon)})

        # Set the best pokémon in terms of stats
        if battle.turn == 1:
            self.best_stats_pokemon = max([sum(pokemon.base_stats.values()) for pokemon in battle.team.values()])

        # If we switched pokémon, then update the bot's infos
        if not self.previous_pokemon:
            self.previous_pokemon = bot_pokemon
        elif bot_pokemon.species != self.previous_pokemon.species:
            self.previous_pokemon = bot_pokemon
            self.toxic_turn = 0
        else:
            bot_pokemon._first_turn = False
            if bot_pokemon.status is Status.TOX:
                self.toxic_turn += 1

        # Compute the best pokémon the bot can switch to
        self.max_team_matchup = max(team_matchups.values()) if len(team_matchups) > 0 else -8
        best_switch = compute_best_switch(team_matchups, opp_pokemon, weather, terrains, self.max_team_matchup)

        # Compute the probability of outpseeding the opponent pokémon
        outspeed_p, opp_spe_lb, opp_spe_ub = outspeed_prob(bot_pokemon, opp_pokemon, weather, terrains).values()
        if self.verbose and bot_pokemon.current_hp != 0:
            print("Turn {0}\n".format(battle.turn))
            print(bot_status_to_string(bot_pokemon, opp_pokemon, weather, terrains))
            print("Current matchup: {0}\nTeam matchups: {1}".format(bot_matchup, matchups_to_string(team_matchups)))

        return best_switch, bot_matchup, outspeed_p, team_matchups

    """
    Compute a move that could defeat the opponent Pokémon if ours is faster
    Parameters: battle: current state of the battle
    Parameters: terrains: current active field in the battle
    Parameters: opp_max_hp: max health points of the opponent Pokémon
    Parameters: opp_conditions: the health state of the opponent Pokémon
    Returns: a tuple that indicated whether a move can defeat the opponent Pokémon and the corresponding move
    """
    @staticmethod
    def hit_if_act_poke_can_outspeed(battle: AbstractBattle, terrains: List[Field], opp_max_hp: int,
                                     opp_conditions: List) -> Tuple[bool, Move]:
        opp_hp = math.ceil(opp_max_hp * battle.opponent_active_pokemon.current_hp_fraction)
        for move in battle.available_moves:
            battle_status = BattleStatus(
                NodePokemon(battle.active_pokemon, is_act_poke=True, moves=battle.available_moves),
                NodePokemon(battle.opponent_active_pokemon, is_act_poke=False, current_hp=opp_hp,
                            moves=list(battle.opponent_active_pokemon.moves.values())),
                [], [], battle.weather, terrains,
                opp_conditions, None, move, True)
            opp_is_fainted = battle_status.simulate_action(move, True).opp_poke.is_fainted()
            if opp_is_fainted:
                return True, move
        return False, Gen8Move('splash')

    @staticmethod
    def print_chosen_move(battle, best_move, opp_conditions, terrains, weather):
        if isinstance(best_move, Move):
            for mo in battle.available_moves:
                damage = compute_damage(mo, battle.active_pokemon, battle.opponent_active_pokemon, weather,
                                        terrains, opp_conditions, battle.active_pokemon.boosts,
                                        battle.opponent_active_pokemon.boosts, True)["lb"]
                chs_mv = mo.id + " : " + mo.type.name + " dmg: " + str(damage)
                if mo.id == best_move.id:
                    chs_mv += "♦"
                print(chs_mv)
        elif isinstance(best_move, Pokemon):
            chs_mv = best_move
            print(chs_mv)

        print()

    """
    Computes the best move or the best pokémon to switch
    Parameters: battle: current state of the battle
    Parameters: root_battle_status: root node from which the minimax algorithm starts
    Returns: the best move or the best pokémon to switch
    """
    def get_best_move(self, battle: AbstractBattle, root_battle_status: BattleStatus) -> Pokemon | Move:
        ris = self.alphabeta(root_battle_status, 0, float('-inf'), float('+inf'), True)
        node: BattleStatus = ris[1]
        best_move = self.choose_random_move(battle)  # il bot ha fatto U-turn e node diventava none
        if node is not None and node.move != Gen8Move('splash'):
            best_move = node.move  # self.choose_random_move(battle)
            curr_node = node
            while curr_node.ancestor is not None:
                best_move = curr_node.move
                curr_node = curr_node.ancestor
        return best_move

    """
    Build the minimax tree with alpha-beta pruning
    Parameters: node: to start exploring from
    Parameters: depth: current depth of the minimax tree. A level of depth equals to one turn of the game
    Parameters: alpha: alpha value of the alpha-beta pruning. Initial call: alpha=-inf
    Parameters: beta: beta value of the alpha-beta pruning. Initial call: beta=-inf
    Parameters: is_my_turn: true if the bot attacks, false otherwise
    Returns: a tuple containing the best game state with its value
    (* Initial call *) alphabeta(origin, 0, −inf, +inf, TRUE)
    """
    def alphabeta(self, node: BattleStatus,
                  depth: int,
                  alpha: float,
                  beta: float,
                  is_my_turn: bool) -> Tuple[float, BattleStatus]:
        if depth == self.max_depth or self.is_terminal_node(node):
            score = node.compute_score(self.heuristic, depth)
            node.score = score
            return score, node
        if is_my_turn:
            score = float('-inf')
            ret_node = node
            # print(str(depth) + " bot -> " + str(node))
            for poss_act in node.act_poke_avail_actions():
                new_state = node.simulate_action(poss_act, is_my_turn)
                child_score, child_node = self.alphabeta(new_state, depth, alpha, beta, False)
                if score < child_score:
                    ret_node = child_node
                score = max(score, child_score)
                if score >= beta:
                    break  # beta cutoff
                alpha = max(alpha, score)

            # print(str(depth) + " bot -> " + str(ret_node))
            return score, ret_node
        else:
            score = float('inf')
            ret_node = node
            # print(str(depth) + " bot -> " + str(node))
            for poss_act in node.opp_poke_avail_actions():
                new_state = node.simulate_action(poss_act, is_my_turn)
                child_score, child_node = self.alphabeta(new_state, depth + 1, alpha, beta, True)
                if score > child_score:
                    ret_node = child_node
                score = min(score, child_score)
                if score <= alpha:
                    break  # alpha cutoff
                beta = min(beta, score)

            # print(str(depth) + " opp -> " + str(ret_node))
            return score, ret_node

    """
    Checks whether the opponent player is defeated
    Parameters: node: a node representing a game state
    Returns: a boolean indicating whether the opponent player is defeated
    """
    @staticmethod
    def opponent_loose(node: BattleStatus) -> bool:
        return node.opp_poke.is_fainted() and len(node.opp_poke_avail_actions()) == 0

    """
    Checks whether our player is defeated
    Parameters: node: a node representing a game state
    Returns: a boolean indicating whether our player is defeated
    """
    @staticmethod
    def player_loose(node: BattleStatus) -> bool:
        return node.act_poke.is_fainted() and len(node.act_poke_avail_actions()) == 0

    """
    Check if a node is a terminal node
    Parameters: node: a node representing a game state
    Returns: a boolean indicating whether a node is a terminal one
    """
    def is_terminal_node(self, node: BattleStatus) -> bool:
        return self.player_loose(node) or self.opponent_loose(node)