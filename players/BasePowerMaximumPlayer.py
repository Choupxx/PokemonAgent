from poke_env.environment import Move, Pokemon
from poke_env.player import Player
from poke_env.teambuilder import Teambuilder
from poke_env import PlayerConfiguration, ServerConfiguration
from core.utils import bot_status_to_string, get_battle_info
from typing import Optional, Union


class BasePowerMaximumPlayer(Player):

    def __init__(self,
                 player_configuration: Optional[PlayerConfiguration] = None,
                 *,
                 avatar: Optional[int] = None,
                 battle_format: str = "gen8randombattle",
                 log_level: Optional[int] = None,
                 max_concurrent_battles: int = 1,
                 save_replays: Union[bool, str] = False,
                 server_configuration: Optional[ServerConfiguration] = None,
                 start_timer_on_battle_start: bool = False,
                 start_listening: bool = True,
                 ping_interval: Optional[float] = 20.0,
                 ping_timeout: Optional[float] = 20.0,
                 team: Optional[Union[str, Teambuilder]] = None,
                 verbose: bool = False
                 ):
        super(BasePowerMaximumPlayer, self).__init__(
            player_configuration = player_configuration,
            avatar = avatar,
            battle_format = battle_format,
            log_level = log_level,
            max_concurrent_battles = max_concurrent_battles,
            save_replays = save_replays,
            server_configuration = server_configuration,
            start_timer_on_battle_start = start_timer_on_battle_start,
            start_listening = start_listening,
            ping_interval = ping_interval,
            ping_timeout = ping_timeout,
            team = team
        )
        self.verbose = verbose

    def choose_move(self, battle):
        if battle.available_moves:
            weather, fields, agent_conditions, opp_agent_conditions = get_battle_info(battle).values()
            if self.verbose:
                print("Turn " + str(battle.turn))
                print(bot_status_to_string(battle.active_pokemon, battle.opponent_active_pokemon, weather, fields))

            best_move: Move = max(battle.available_moves, key=lambda move: move.base_power)
            trick = False
            if battle.can_dynamax:
                trick = True

            if self.verbose:
                print("Best move: {0}, type: {1}\n{2}".format(best_move.id, best_move.type, "*" * 110))

            return self.create_order(best_move, dynamax=trick)
        else:
            return self.choose_random_move(battle)
