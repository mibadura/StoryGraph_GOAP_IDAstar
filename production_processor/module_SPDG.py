import time
import datetime
import logging
import sys
import jsonpickle


from copy import deepcopy

from config.config import path_root
from library.tools import *

from library.tools_match import character_turn, world_turn, get_production_tree_new, what_to_do
from library.tools_process import game_init, looking_for_main_character, game_over, save_world_game, \
    ids_list_update, get_quest_description
from library.tools_validation import get_jsons_storygraph_validated


class Goal:
    def __init__(self, _minimum_total_stats):
        self.minimum_total_stats = _minimum_total_stats

    def is_fulfilled(self, world_state):
        return self.minimum_total_stats <= world_state.total_stats


class Heuristic:
    def __init__(self, goal):
        self.goal = goal

    def estimate(self, state):
        return max(0, self.goal.minimum_total_stats-state.total_stats)


def remove_top_level_connections(state_dict):
    state_dict_copy = deepcopy(state_dict)
    if 'Connections' in state_dict_copy:
        del state_dict_copy['Connections']
    return state_dict_copy


class TranspositionTable:
    def __init__(self):
        self.visited = {}

    def has(self, state, depth):
        state_no_connections = [remove_top_level_connections(d) for d in state]
        state_pickle = jsonpickle.encode(state_no_connections)
        return state_pickle in self.visited and self.visited[state_pickle] <= depth

    def add(self, state, depth):
        state_no_connections = [remove_top_level_connections(d) for d in state]

        state_pickle = jsonpickle.encode(state_no_connections)
        if state_pickle not in self.visited or depth < self.visited[state_pickle]:
            print(f'\t\ttranspo:\tadding state at depth: {depth}')
            self.visited[state_pickle] = depth


def plan_action_series(world_model_set, goal, heuristic, max_depth, _cost_of_action):
    cutoff = heuristic.estimate(world_model_set)
    goal_reached = False
    while cutoff != float('inf'):
        transposition_table = TranspositionTable()
        print('\n', '-'*20, f'plan_action_series: new plan action series - cutoff: {cutoff}', '-'*20, '\n')

        new_world = world_copy(world_model_set.world, deepcopy(world_model_set.world))
        new_world_set = NewWorldStartSet(new_world, world_model_set.jsons_schema_OK, world_model_set.quest_names, world_model_set.character_name,
                         world_model_set.world_name, world_model_set.world_source, world_model_set.character, world_model_set.gameplay,
                         world_model_set.main_location, world_model_set.productions_chars_turn_to_match,
                         world_model_set.decision_nr)

        cutoff, actions, goal_reached = single_search(new_world_set, goal, heuristic, transposition_table, max_depth,
                                                      cutoff, _cost_of_action=_cost_of_action)
        if actions:
            if goal_reached:
                print(f'plan_action_series: goal reached')
                return actions, goal_reached
            else:
                print(f'plan_action_series: goal not reached')
                print(f'best plan so far:')
                for action in actions:
                    print(f'{action[0]["Title"]}')

    return actions, goal_reached


def single_search(world_model, goal, heuristic, transposition_table, max_depth, cutoff, _cost_of_action):
    print(f'\n\tsingle_search: new single_search')
    max_depth += 1

    states = [None] * (max_depth + 1)
    actions = [None] * max_depth
    costs = [0.0] * (max_depth + 1)

    world_model.action_index = 0
    states[0] = world_model
    current_depth = 0
    print(f'\tsingle_search: starting worldModel: {states[0]}')
    transposition_table.add(states[current_depth].world, current_depth) # MB CHANGE TRANSPO

    smallest_cutoff = float('inf')

    best_path = None
    best_cost = float('inf')

    while current_depth >= 0:

        heuristic_estimate = heuristic.estimate(states[current_depth])
        cost = costs[current_depth] + heuristic_estimate
        print(f'\tsingle_search:\tdepth: {current_depth};\tstate total_stats {states[current_depth].total_stats};\tcost {cost};'
              f'\tcutoff: {cutoff}')
        print(f'\tsingle_search: total stats {states[current_depth].total_stats}')

        if cost > cutoff:
            print(f'\tsingle_search: cost bigger than cutoff ({cost} > {cutoff})')
            if cost < smallest_cutoff:
                smallest_cutoff = cost
            current_depth -= 1
            continue

        if goal.is_fulfilled(states[current_depth]):
            print('\n','-'*10,f' Goal {goal.minimum_total_stats} is fulfilled. Current total_stats is {states[current_depth].total_stats}','-'*10)
            return cutoff, actions[:current_depth], True

        if heuristic_estimate < best_cost:
            print(f'\tsingle_search: heuristic_estimate {heuristic_estimate} lower than best_cost {best_cost}')
            best_cost = heuristic_estimate
            best_path = actions[:current_depth]

        if current_depth >= max_depth - 1:
            print(f'\tsingle_search: current_depth ({current_depth}) too deep and goal not reached. Decreasing depth')
            current_depth -= 1
            continue

        next_action, next_action_idx, next_variant, next_variant_idx = states[current_depth].next_action()

        ### This is just to exclude the option of picking up the Dragon Egg. We don't want the game to end
        if next_action:
            if 'picking' in next_action['Title'].lower():
                if next_variant[2][1]['Name'] == 'Dragon_egg':
                    next_action, next_action_idx, next_variant, next_variant_idx = states[current_depth].next_action()

        if next_action and next_variant:
            print(f'\tsingle_search: action {next_action["Title"]} variant {next_variant_idx}')

            copied_world = world_copy(states[current_depth].world, deepcopy(states[current_depth].world),
                                      preserve_id=False)
            new_start_set = NewWorldStartSet(copied_world, world_model.jsons_schema_OK, world_model.quest_names,
                                             world_model.character_name, world_model.world_name,
                                             world_model.world_source,world_model.character,world_model.gameplay,
                                             world_model.main_location,world_model.productions_chars_turn_to_match,
                                             world_model.decision_nr)

            new_world_start(new_start_set, next_action, next_action_idx, next_variant, next_variant_idx,
                            select_actions_by_ids=False)
            world_after = world_copy(states[current_depth].world, deepcopy(states[current_depth].world),
                                     preserve_id=False)
            after_set = NewWorldStartSet(world_after, world_model.jsons_schema_OK, world_model.quest_names,
                                         world_model.character_name, world_model.world_name,world_model.world_source,
                                         world_model.character,world_model.gameplay, world_model.main_location,
                                         world_model.productions_chars_turn_to_match,world_model.decision_nr)

            act_id = deepcopy(states[current_depth].action_index)
            var_id = deepcopy(states[current_depth].variant_index)
            states[current_depth] = NewWorldStartSet(copied_world, world_model.jsons_schema_OK, world_model.quest_names,
                                                     world_model.character_name, world_model.world_name,
                                                     world_model.world_source,world_model.character,
                                                     world_model.gameplay, world_model.main_location,
                                                     world_model.productions_chars_turn_to_match,
                                                     world_model.decision_nr)
            states[current_depth].action_index = act_id
            states[current_depth].variant_index = var_id
            states[current_depth + 1] = after_set

            actions[current_depth] = deepcopy([next_action, next_action_idx, next_variant, next_variant_idx])
            print(f'\tsingle_search: depth: {current_depth} | '
                  f'assigned action #{next_action_idx} and variant #{next_variant_idx}')
            costs[current_depth + 1] = costs[current_depth] + _cost_of_action

            if not transposition_table.has(states[current_depth + 1].world, current_depth + 1):
                print(f'\n\tsingle_search: simulating move {states[current_depth].total_stats} -> '
                      f'{states[current_depth + 1].total_stats} '
                      f'| new move! adding to transpo table ')
                current_depth += 1
                transposition_table.add(states[current_depth].world, current_depth)
            else:
                print(f'\n\tsingle_search: simulating move {states[current_depth].total_stats} -> '
                      f'{states[current_depth + 1].total_stats} '
                      f'| already in transpo. trying next move ')

        else:
            current_depth -= 1
            print(f'\tsingle_search: no more actions: depth decreased')

    return smallest_cutoff, best_path, False


def player_move_storygraph(_character_paths, _gameplay, _world, _world_source, _main_location,
                           _productions_chars_turn_to_match, _decision_nr, _character,
                           _world_nodes_ids_list, _world_nodes_ids_pairs_list, _world_locations_ids,
                           _productions_world_turn_to_match, _next_action, _next_action_idx, _next_variant,
                           _next_variant_idx, todos, generate_files=None):
    if len(_character_paths[0]) == 2:
        _effect_main = character_turn(_gameplay, _world, _world_source, _main_location,
                                      _productions_chars_turn_to_match,_decision_nr, character=_character,
                                      next_action=_next_action, next_action_idx=_next_action_idx,
                                      next_variant=_next_variant, next_variant_idx=_next_variant_idx,
                                      todos=todos, generate_files=generate_files)

    else:
        print(
            f"Bohater jest podporządkowany innej postaci lub uwięziony({str([x.get('Name') for x in _character_paths[0]]).replace(', ', '->')}). Odzyska samostanowienie, gdy stanie na własnych nogach w lokacji.")
        _effect_main = ""

    if _effect_main == "end":
        game_over(_gameplay, "Decyzja użytkownika")
    elif _effect_main == "":
        pass
    else:
        _decision_nr += 1
        ids_list_update(_world_nodes_ids_list, _world_nodes_ids_pairs_list, _effect_main)
        effect_world, decs_world = world_turn(_gameplay, _effect_main, _world, _world_locations_ids,
                                              _productions_world_turn_to_match, _decision_nr)
        _decision_nr = decs_world
        ids_list_update(_world_nodes_ids_list, _world_nodes_ids_pairs_list, effect_world)

        character_paths = looking_for_main_character(_gameplay, _world, pointer=_character,
                                                     zero_text="Zniknął główny bohater po swoim ruchu. Pewno umarł.")
        _main_location = character_paths[0][-2]

    return _character_paths, _gameplay, _world, _world_source, _main_location, \
                           _productions_chars_turn_to_match, _decision_nr, _character, \
                           _world_nodes_ids_list, _world_nodes_ids_pairs_list, _world_locations_ids, \
                           _productions_world_turn_to_match, _next_action, _next_action_idx, _next_variant,\
                            _next_variant_idx, todos


def new_world_start(world_start_set, next_action = None, next_action_idx=None, next_variant = None,
                    next_variant_idx=None, select_actions_by_ids = None, generate_files=None):

    world = world_start_set.world
    jsons_schema_OK = world_start_set.jsons_schema_OK
    quest_names = world_start_set.quest_names
    character_name = world_start_set.character_name
    world_name = world_start_set.world_name
    world_source = world_start_set.world_source
    world_start_set.actions = world_start_set.get_available_actions()
    todos = world_start_set.actions

    world_nodes_list = nodes_list_from_tree(world, "Locations")
    world_nodes_ids_list = [str(id(x['node'])) for x in world_nodes_list]
    world_nodes_ids_pairs_list = [(str(id(x['node'])), x['node']) for x in world_nodes_list]
    world_nodes_dict = {}

    for node in world_nodes_list:
        world_nodes_dict[id(node)] = node
    world_locations_ids = []
    for l in world:
        world_locations_ids.append(id(l))

    prod_chars_turn_names = ['produkcje_generyczne', *quest_names]
    prod_world_turn_names = [*[], 'produkcje_automatyczne', 'produkcje_automatyczne_wygrywania']

    prod_chars_turn_jsons = [deepcopy(jsons_schema_OK[get_quest_nr(x, jsons_schema_OK)]['json']) for x in
                             prod_chars_turn_names]
    prod_world_turn_jsons = [deepcopy(jsons_schema_OK[get_quest_nr(x, jsons_schema_OK)]['json']) for x in
                             prod_world_turn_names]

    productions_chars_turn_to_match = []
    productions_world_turn_to_match = []
    for prods in prod_chars_turn_jsons:
        for prod in prods:
            productions_chars_turn_to_match.append(prod)
            if not destinations_change_to_nodes(prod["LSide"]["Locations"]):
                exit(1)
    for prods in prod_world_turn_jsons:
        for prod in prods:
            productions_world_turn_to_match.append(prod)
            if not destinations_change_to_nodes(prod["LSide"]["Locations"]):
                exit(1)

    decision_nr = 0
    date_folder = str(datetime.now().strftime("%Y%m%d%H%M%S"))
    script_root_path = os.getcwd().rsplit(os.sep, 1)[0]
    gp_folder = 'gameplays'
    result_file_path = f'{script_root_path}/{gp_folder}/gp-{date_folder}'

    gameplay = {
        "Player": "PlaceholderName",
        "MainCharacter": character_name,
        "WorldName": world_name,
        "WorldSource": save_world_game(world_source),  # stan świata z id lokacji będących stringiem z adresu pamięci
        "QuestName": quest_names[0],
        "QuestSource": [{x: jsons_schema_OK[get_quest_nr(x, jsons_schema_OK)]['json']} for x in prod_chars_turn_names],
        "WorldResponseSource": [{x: jsons_schema_OK[get_quest_nr(x, jsons_schema_OK)]['json']} for x in
                                prod_world_turn_names],
        "DateTimeStart": datetime.now().strftime("%Y%m%d%H%M%S"),
        "Moves": [],
        "FilePath": result_file_path,

    }

    if generate_files:
        game_init(gameplay)

    character_paths = looking_for_main_character(gameplay, world, name_or_id=character_name,
                                                 failure_text="Kończymy zanim zaczęliśmy, przy inicjacji.")
    character = character_paths[0][-1]
    destinations_change_to_nodes(world, world=True)

    prod_hierarchy, g, m = get_production_tree_new(
        *[jsons_schema_OK[get_quest_nr(x, jsons_schema_OK)] for x in prod_chars_turn_names + prod_world_turn_names])
    gameplay["ProductionHierarchy"] = prod_hierarchy
    character_paths = looking_for_main_character(gameplay, world, pointer=character,
                                                 zero_text="Zniknął główny bohater po ruchu NPC-a. Pewno zginął.")
    main_location = character_paths[0][0]
    # skip = False
    sheaf_description(main_location)

    if (not next_action) and  (not next_variant):
        next_action, next_action_idx, next_variant, next_variant_idx = world_start_set.next_action()

    if select_actions_by_ids:
        next_action = world_start_set.actions[next_action_idx]
        next_variant = next_action['Matches'][next_variant_idx]

    character_paths, gameplay, world, world_source, main_location, \
    productions_chars_turn_to_match, decision_nr, character,\
    world_nodes_ids_list, world_nodes_ids_pairs_list, world_locations_ids,\
    productions_world_turn_to_match, next_action, next_action_idx, next_variant,\
    next_variant_idx, todos = player_move_storygraph(
        character_paths, gameplay, world, world_source, main_location,
        productions_chars_turn_to_match, decision_nr, character,
        world_nodes_ids_list, world_nodes_ids_pairs_list, world_locations_ids,
        productions_world_turn_to_match, next_action, next_action_idx, next_variant, next_variant_idx, todos,
        generate_files=generate_files)

    return NewWorldStartSet(world, jsons_schema_OK, quest_names, character_name, world_name, world_source, character,
                            gameplay, main_location, productions_chars_turn_to_match, decision_nr)


def find_main_hero(d):
    results = []

    # Check if the dictionary contains the 'Characters' key
    if 'Characters' in d:
        for character in d['Characters']:
            if character['Name'] == 'Main_hero':
                results.append(character)
                break

    return results


class NewWorldStartSet:

    def __init__(self, world, jsons_schema_OK, quest_names, character_name, world_name, world_source, character,
                 gameplay, main_location, productions_chars_turn_to_match, decision_nr):

        self.world = world
        self.jsons_schema_OK = jsons_schema_OK
        self.quest_names = quest_names
        self.character_name = character_name
        self.world_name = world_name
        self.world_source = world_source
        self.character = character
        self.gameplay = gameplay
        self.main_location = main_location
        self.productions_chars_turn_to_match = productions_chars_turn_to_match
        self.decision_nr = decision_nr
        self.total_stats = self.calculate_total_stats()
        self.actions = self.get_available_actions()
        self.action_index = 0
        self.variant_index = 0

    def calculate_total_stats(self):
        weight_health = 2
        weight_money = 1
        weight_item_value = 1

        item_values = 0
        main_hero = []

        for location in self.world:
            main_hero = find_main_hero(location)
            if main_hero:
                break
        self.character = main_hero[0]

        hp_values = self.character['Attributes']['HP']
        money_values = self.character['Attributes']['Money']

        if 'Items' in self.character and self.character['Items']:
            for item in self.character['Items']:
                if 'Attributes' in item and item['Attributes']:
                    if 'Value' in item['Attributes'] and item['Attributes']['Value']:
                        item_values += item['Attributes']['Value']

        return weight_health*hp_values + \
               weight_money*money_values + \
               weight_item_value*item_values

    def copy(self):
        return NewWorldStartSet(
            deepcopy(self.world),
            deepcopy(self.jsons_schema_OK),
            deepcopy(self.quest_names),
            deepcopy(self.character_name),
            deepcopy(self.world_name),
            deepcopy(self.world_source),
            deepcopy(self.character),
            deepcopy(self.gameplay),
            deepcopy(self.main_location),
            deepcopy(self.productions_chars_turn_to_match),
            deepcopy(self.decision_nr)
        )

    def next_action(self):
        if self.action_index < len(self.actions):
            next_action = self.actions[self.action_index]
            next_variant = next_action['Matches'][self.variant_index]
            current_action_idx = self.action_index
            current_variant_idx = self.variant_index
            if self.variant_index < len(next_action['Matches'])-1:
                self.variant_index += 1
                return next_action, current_action_idx, next_variant, current_variant_idx
            else:
                self.variant_index = 0
                self.action_index += 1

            return next_action, current_action_idx, next_variant, current_variant_idx
        else:
            return None, None, None, None

    def __hash__(self):
        return hash(frozenset(self.world))

    def __eq__(self, other):
        if isinstance(other, NewWorldStartSet):
            return (self.world == other.world)
        return False

    def get_available_actions(self):
        world_nodes_list = nodes_list_from_tree(self.world, "Locations")
        world_nodes_dict = {}

        for node in world_nodes_list:
            world_nodes_dict[id(node)] = node
        world_locations_ids = []
        for l in self.world:
            world_locations_ids.append(id(l))

        prod_chars_turn_names = ['produkcje_generyczne', *self.quest_names]
        prod_world_turn_names = [*[], 'produkcje_automatyczne', 'produkcje_automatyczne_wygrywania']

        prod_chars_turn_jsons = [deepcopy(self.jsons_schema_OK[get_quest_nr(x, self.jsons_schema_OK)]['json']) for x in
                                 prod_chars_turn_names]
        prod_world_turn_jsons = [deepcopy(self.jsons_schema_OK[get_quest_nr(x, self.jsons_schema_OK)]['json']) for x in
                                 prod_world_turn_names]

        productions_chars_turn_to_match = []
        productions_world_turn_to_match = []
        for prods in prod_chars_turn_jsons:
            for prod in prods:
                productions_chars_turn_to_match.append(prod)
                if not destinations_change_to_nodes(prod["LSide"]["Locations"]):
                    exit(1)
        for prods in prod_world_turn_jsons:
            for prod in prods:
                productions_world_turn_to_match.append(prod)
                if not destinations_change_to_nodes(prod["LSide"]["Locations"]):
                    exit(1)

        date_folder = str(datetime.now().strftime("%Y%m%d%H%M%S"))
        script_root_path = os.getcwd().rsplit(os.sep, 1)[0]
        gp_folder = 'gameplays'
        result_file_path = f'{script_root_path}/{gp_folder}/gp-{date_folder}'

        gameplay = {
            "Player": "PlaceholderName",
            "MainCharacter": self.character_name,
            "WorldName": self.world_name,
            "WorldSource": save_world_game(self.world_source),
            "QuestName": self.quest_names[0],
            "QuestSource": [{x: self.jsons_schema_OK[get_quest_nr(x, self.jsons_schema_OK)]['json']} for x in
                            prod_chars_turn_names],
            "WorldResponseSource": [{x: self.jsons_schema_OK[get_quest_nr(x, self.jsons_schema_OK)]['json']} for x in
                                    prod_world_turn_names],
            "DateTimeStart": datetime.now().strftime("%Y%m%d%H%M%S"),
            "Moves": [],
            "FilePath": result_file_path,
        }

        character_paths = looking_for_main_character(gameplay, self.world, name_or_id=self.character_name,
                                                     failure_text="Kończymy zanim zaczęliśmy, przy inicjacji.")
        character = character_paths[0][-1]
        destinations_change_to_nodes(self.world, world=True)

        prod_hierarchy, g, m = get_production_tree_new(
            *[self.jsons_schema_OK[get_quest_nr(x, self.jsons_schema_OK)] for x in prod_chars_turn_names + prod_world_turn_names])
        gameplay["ProductionHierarchy"] = prod_hierarchy

        character_paths = looking_for_main_character(gameplay, self.world, pointer=character,
                                                     zero_text="Zniknął główny bohater po ruchu NPC-a. Pewno zginął.")
        main_location = character_paths[0][0]
        productions_matched, todos = what_to_do(self.world, main_location, productions_chars_turn_to_match,
                                                character=character)
        filtered_todos = [item for item in todos if
                          'teleport' not in item['Title'].lower()
                          and 'character’s death' not in item['Title'].lower()
                          and 'deleting' not in item['Title'].lower()]

        return filtered_todos


def main(_max_depth, _goal_value, _cost_of_action, _output_folder):
    main_start_time = time.time()

    all_outputs_folder = 'GOAP_simulations'

    if not os.path.exists(f'../{all_outputs_folder}/{_output_folder}'):
        os.makedirs(f'../{all_outputs_folder}/{_output_folder}')

    original_stdout = sys.stdout
    with open(f'../{all_outputs_folder}/{_output_folder}/out_d{_max_depth}_goal{_goal_value}_'
              f'actioncost{_cost_of_action}_{time.strftime("%Y%m%d%H%M%S")}.txt', 'w', encoding='utf-8') as f:
        sys.stdout = f

        logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s', stream=sys.stdout)

        dir_name = ''
        json_path = f'{path_root}/{dir_name}'
        jsons_OK, jsons_schema_OK, errors, warnings = get_jsons_storygraph_validated(json_path)

        world_name = 'world_DragonStory'  # 'world_RumcajsStory'
        quest_names = ['quest_DragonStory']  # 'quest_RumcajsStory_close'
        quest_automatic_names = []  #
        character_name = 'Main_hero'  # 'Rumcajs''Main_hero'
        world_source = jsons_schema_OK[get_quest_nr(world_name, jsons_schema_OK)]

        world = world_source['json'][0]["LSide"]["Locations"]

        world_nodes_list = nodes_list_from_tree(world, "Locations")
        world_nodes_dict = {}

        for node in world_nodes_list:
            world_nodes_dict[id(node)] = node
        world_locations_ids = []
        for l in world:
            world_locations_ids.append(id(l))

        quest_description = get_quest_description(quest_names[0] or '')

        prod_chars_turn_names = ['produkcje_generyczne', *quest_names]
        prod_world_turn_names = [*quest_automatic_names, 'produkcje_automatyczne', 'produkcje_automatyczne_wygrywania']

        prod_chars_turn_jsons = [deepcopy(jsons_schema_OK[get_quest_nr(x, jsons_schema_OK)]['json']) for x in
                                 prod_chars_turn_names]
        prod_world_turn_jsons = [deepcopy(jsons_schema_OK[get_quest_nr(x, jsons_schema_OK)]['json']) for x in
                                 prod_world_turn_names]

        productions_chars_turn_to_match = []
        productions_world_turn_to_match = []
        for prods in prod_chars_turn_jsons:
            for prod in prods:
                productions_chars_turn_to_match.append(prod)
                if not destinations_change_to_nodes(prod["LSide"]["Locations"]):
                    exit(1)
        for prods in prod_world_turn_jsons:
            for prod in prods:
                productions_world_turn_to_match.append(prod)
                if not destinations_change_to_nodes(prod["LSide"]["Locations"]):
                    exit(1)

        decision_nr = 0
        date_folder = str(datetime.now().strftime("%Y%m%d%H%M%S"))
        script_root_path = os.getcwd().rsplit(os.sep, 1)[0]
        gp_folder = 'gameplays'
        result_file_path = f'{script_root_path}/{gp_folder}/gp-{date_folder}'

        print(f"""
        ╔═══════════════════════════════════════════════════════════════════════════════════════════
        ║ S Y M U L A T O R    P R O C E S U    D E C Y Z Y J N E G O    G R A C Z A    R P G
        ║
        ║ Proces decyzyjny fabuły zdefiniowanej w świecie: {world_name}
        ║ poprzez produkcje generyczne i misję: {quest_names[0]}
        ║ dla bohatera: {character_name}.
        ║ Wizualizacje kolejnych możliwości wyboru i wykonanych produkcji znajdują się w katalogu: 
        ║ {result_file_path}
        ║
        ║ UWAGA1: Aplikacja działa w trybie testera, czyli można wykonywać produkcje przesłonięte 
        ║ parametrem Override mimo ich oznaczenia: BLOKADA1, BLOKADA2. 
        ║ UWAGA2: Działa dość wolno, bo generuje mnóstwo obrazków pomocniczych.
        ╚═══════════════════════════════════════════════════════════════════════════════════════════
        """)

        gameplay = {
            "Player": "PlaceholderName",
            "MainCharacter": character_name,
            "WorldName": world_name,
            "WorldSource": save_world_game(world_source),
            "QuestName": quest_names[0],
            "QuestSource": [{x: jsons_schema_OK[get_quest_nr(x, jsons_schema_OK)]['json']} for x in prod_chars_turn_names],
            "WorldResponseSource": [{x: jsons_schema_OK[get_quest_nr(x, jsons_schema_OK)]['json']} for x in
                                    prod_world_turn_names],
            "DateTimeStart": datetime.now().strftime("%Y%m%d%H%M%S"),
            "Moves": [],
            "FilePath": result_file_path,

        }

        character_paths = looking_for_main_character(gameplay, world, name_or_id=character_name,
                                                     failure_text="Kończymy zanim zaczęliśmy, przy inicjacji.")
        character = character_paths[0][-1]

        destinations_change_to_nodes(world, world=True)

        line_limit = 81
        print(f'     ┌──────────────────────────────────────────────────────────────────────────────────────')
        print_lines(quest_description, line_limit, prefix='     │ ')
        print(f'     └──────────────────────────────────────────────────────────────────────────────────────')

        prod_hierarchy, g, m = get_production_tree_new(
            *[jsons_schema_OK[get_quest_nr(x, jsons_schema_OK)] for x in prod_chars_turn_names + prod_world_turn_names])
        gameplay["ProductionHierarchy"] = prod_hierarchy

        character_paths = looking_for_main_character(gameplay, world, pointer=character,
                                                     zero_text="Zniknął główny bohater po ruchu NPC-a. Pewno zginął.")
        main_location = character_paths[0][0]
        max_plan_loops = 40
        goal_reached = False
        plan_loop_idx = 0
        final_plan_world = world_copy(world, deepcopy(world))
        list_actions = []
        list_total_stats = []

        goal_unreachable = False

        while not goal_reached and plan_loop_idx < max_plan_loops and not goal_unreachable:

            new_world_start_set = NewWorldStartSet(world, jsons_schema_OK, quest_names, character_name, world_name,
                                                   world_source, character, gameplay, main_location,
                                                   productions_chars_turn_to_match, decision_nr)

            new_world_start_set.total_stats = new_world_start_set.calculate_total_stats()
            partial_plan_world = world_copy(world, deepcopy(world))

            partial_plan_world_set = NewWorldStartSet(partial_plan_world, jsons_schema_OK, quest_names, character_name,
                                                    world_name,
                                                    world_source, character, gameplay, main_location,
                                                    productions_chars_turn_to_match, decision_nr)
            goal = Goal(_goal_value)
            heuristic = Heuristic(goal)
            print(f'\tmain: goal minimum stats = {goal.minimum_total_stats}')

            start_time = time.time()
            single_plan, goal_reached = plan_action_series(new_world_start_set, goal, heuristic, max_depth=_max_depth,
                                                           _cost_of_action=_cost_of_action)
            end_time = time.time()
            print(f'Plan_action execution took {end_time - start_time} seconds.')

            if single_plan and not goal_reached:
                print("Partial plan found.")
            elif single_plan and goal_reached:
                print("Final plan found.")
                for action in list_actions:
                    print(f'Action #{action[1]} {action[0]["Title"]}, variant #{action[3]}')
            else:
                print('No plan for reaching the goal. Goal unreachable.')
                goal_unreachable = True

            if single_plan:
                for action_idx, action in enumerate(single_plan):
                    if action is None:
                        break

                    list_actions.append(action)
                    new_world_start(partial_plan_world_set, action[0], action[1], action[2], action[3],
                                    select_actions_by_ids=True)
                    partial_plan_world_set.total_stats = partial_plan_world_set.calculate_total_stats()
                    list_total_stats.append(partial_plan_world_set.total_stats)
                    print(f'Single plan action #{action_idx}: {action[0]["Title"]}')

                world = world_copy(partial_plan_world_set.world, deepcopy(partial_plan_world_set.world))

            print(f'list_total_stats: {list_total_stats}')
            plan_loop_idx += 1

        if goal_reached:
            print(f'     ┌──────────────────────────────────────────────────────────────────────────────────────')
            print(f'     │  SUCCESS!!! We have found the FINAL PLAN! Executing it now 😍😍😍')
            print(f'     └──────────────────────────────────────────────────────────────────────────────────────')
        elif list_actions:
            print(f'     ┌──────────────────────────────────────────────────────────────────────────────────────')
            print(f'     │  Not quite... We have not found a way to reach the goal 😥 Here is the partial plan execution')
            print(f'     └──────────────────────────────────────────────────────────────────────────────────────')
        else:
            print(f'     ┌──────────────────────────────────────────────────────────────────────────────────────')
            print(f'     │  No success and not even a single action towards the goal 😭😭😭')
            print(f'     └──────────────────────────────────────────────────────────────────────────────────────')

        # Final plan execution
        if list_actions:
            final_plan_world_set = NewWorldStartSet(final_plan_world, jsons_schema_OK, quest_names, character_name,
                                                    world_name,
                                                    world_source, character, gameplay, main_location,
                                                    productions_chars_turn_to_match, decision_nr)
            for final_action_idx, final_action in enumerate(list_actions):
                final_state = new_world_start(final_plan_world_set, final_action[0], final_action[1],
                                              final_action[2], final_action[3],
                                              select_actions_by_ids=True, generate_files=True)

            sheaf_description(final_state.main_location)

        print(f'Plan length: {len(list_total_stats)}')
        print(f'Target goal: {_goal_value}')
        print(f'Final stats: {list_total_stats}')

        main_end_time = time.time()
        execution_time = main_end_time - main_start_time

        print(f'Program execution time: {round(execution_time, 3)}s')

    sys.stdout = original_stdout
    f.close()

    return execution_time


if __name__ == "__main__":

    full_execution_time = main(_max_depth=9, _goal_value=3211, _cost_of_action=200, _output_folder='test_output_1')
    print(f'Program execution time: {round(full_execution_time, 3)}s')
