# world_locations = [{}, {}, {}] -> {{}, {}, {}}
# ls_locations =  [{}, {}] -> {{}, {}}
from copy import deepcopy
from typing import List

from library.tools_match import what_to_do


def pairs(ls: set, w: set) -> list:
    result = []
    if (not ls) or (not w):
        return []
    el1 = ls.pop()
    ls.add(el1)
    for el2 in w:
        tail = pairs(ls - {el1}, w - {el2})
        if tail:
            for res in tail:
                result.append([(el1, el2)] + res )
        else:
            result.append([(el1, el2)])
    return result





def fit_loc_children(loc: dict, ls: dict):
    fit = True
    combinations = pairs(ls["Characters"],ls["Characters"])
    for combination, nr in zip(combinations, range(len(combinations))):
        for pair in combination:
            if "Name" in pair[0] and pair[0]["Name"] != pair[1]["Name"]:
                pass


    return fit



#
# print(kmp("ara", "Kara Barabasza"))
# print(kmp(["a","r","a"], ["K","a","r","a"," ","B","a","r","a","b","a","s","z","a"]))


import tempfile

from config.config import path_root
from library.tools import nodes_list_from_tree, destinations_change_to_nodes, breadcrumb_pointer, get_quest_nr
from library.tools_process import apply_instructions_to_world

from library.tools_validation import get_jsons_storygraph_validated, get_generic_productions_from_file, \
    print_errors_warnings
from library.tools_visualisation import draw_graph, merge_images

# json_schema_path = f'../json_validation/schema_updated_20220213.json'
# dict_schema_path = f'../json_validation/schema_sheaf_updated_20220213.json'
json_path = f'{path_root}/productions'


# gdyby w sprawdzanych katalogach nie było pliku z produkcjami generycznymi, trzeba byłoby dodać ich listę jako argument
# production_titles_dict, użylibyśmy do tego g z poniższego wywołania:
# g, e = get_generic_productions_from_file(f'{path_root}/productions/generics/produkcje_generyczne.json')


# walidowanie plików json i wypisywanie błędów
jsons_sg_validated, jsons_schema_validated, errors, warnings = get_jsons_storygraph_validated(json_path)
print_errors_warnings(jsons_schema_validated, errors, warnings)

# generowanie obrazków z prawymi i lewymi stronami produkcji

for production in jsons_schema_validated[get_quest_nr('produkcje_generyczne',jsons_schema_validated)]["json"]:
    prod_to_match = None
    # for production in mission:
    if production["Title"] == "Picking item up / Podniesienie przedmiotu":
        prod_to_match = deepcopy(production)
        destinations_change_to_nodes(prod_to_match["LSide"]["Locations"])
        break
    # if prod_to_match:
    #     break

for mission in [jsons_schema_validated[get_quest_nr('produkcje_generyczne',jsons_schema_validated)], jsons_schema_validated[get_quest_nr('quest00_Dragon_story',jsons_schema_validated)]]:
    for production in mission["json"]:

        # przygotowuję produkcję do wykonania
        destinations_change_to_nodes(production["LSide"]["Locations"])
        nodes_list = nodes_list_from_tree(production["LSide"]["Locations"], "Locations")

        world = deepcopy(production["LSide"]["Locations"])


        character_name = 'Main_hero'
        character_paths = breadcrumb_pointer(world, is_object=True)
        if character_paths:
            character = character_paths[0][-1]
            main_location = character_paths[0][-2]
            for path in character_paths:
                character = path[-1]
                main_location = path[-2]
                productions_matched, todos = what_to_do(world, main_location, [prod_to_match], character=character, prod_vis_mode=True)
                print(f"{production['Title']}")
                print("Co może zrobić Main hero:")
                if not productions_matched:
                    print(f"Nie udało się dopasować produkcji do postaci {character} w świecie.")
                else:
                    print(
                        f"Z {len([prod_to_match])} produkcji dla {len(character_paths)} postaci udało się dopasować {len(todos)}. ")
                    for element in todos:
                        for e in element["Matches"]:
                            for f in e:
                                print(f'{f[0].get("Id", f[0].get("Name"))}, {f[1].get("Id", f[1].get("Name"))}')
                                # print(f'aaaa   {str(f)[0:100]}')
                    print()
        else:
            main_location = world[0]
            productions_matched, todos = what_to_do(world, main_location, [prod_to_match],
                                                    prod_vis_mode=True)

            print(f"{production['Title']}")
            print("Co może zrobić Main hero:")
            if not productions_matched:
                print(f"Nie udało się dopasować produkcji do postaci {character} w świecie.")
            else:
                print(
                    f"Z {len([prod_to_match])} produkcji dla wszystkich postaci udało się dopasować {len(todos)}.")
                for element in todos:
                    for e in element:
                        print(f'{e[0].get("Id")}, {e[1].get("Id")}')
                print()



