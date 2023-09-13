import datetime
import logging
import sys
from copy import deepcopy

from config.config import path_root
# from library.tools import *


# wgrywanie jsonów do testów

#################################################################
from library.tools import breadcrumb_pointer, destinations_change_to_nodes, find_reference_leaves, \
    get_quest_nr
from library.tools_match import what_to_do
from library.tools_process import retrace_gameplay
from library.tools_validation import get_jsons_storygraph_validated
from library.tools_visualisation import GraphVisualizer

json_path = f'{path_root}/productions'
# json_schema_path = f'{path_root}/schema/schema_updated_20220120.json'
mask = '*.json'
# mask = 'World_pptx_base.json'
logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s', stream=sys.stdout)
#################################################################

# jsons_OK, jsons_schema_OK, errors = get_files_validated(json_path, json_schema_path, mask)
# json_schema_path = f'{path_root}/schema/schema_updated_20220213.json'
# dict_schema_path = f'{path_root}/schema/schema_sheaf_updated_20220213.json'
dir_name = 'productions'
json_path = f'{path_root}/{dir_name}'
jsons_OK, jsons_schema_OK, errors, warnings = get_jsons_storygraph_validated(json_path)

# show_errors = True
# if show_errors:
#     for json_spoiled in errors:
#         print('#' * len(json_spoiled['file_path']))
#         print(json_spoiled['file_path'])
#         print('#' * len(json_spoiled['file_path']), '\n')
#         for e in json_spoiled["errors"]:
#             print(e)
#         print()
#
# show_missions_list = True
# if show_missions_list:
#     if jsons_OK:
#         print(f'Poprawne jsony w katalogu "{json_path}" wśród plików "{mask}":')
#         for json_ok, nr in zip(jsons_OK, range(len(jsons_OK))):
#             print(f"     {nr}. {json_ok['file_path']}")
#     if jsons_schema_OK:
#         print(f'Zgodne ze schematem jsony w katalogu "{json_path}" wśród plików "{mask}":')
#         for schema_ok, nr in zip(jsons_schema_OK, range(len(jsons_schema_OK))):
#             print(f"     {nr}. {schema_ok['file_path']}")
#     else:
#         print(f"W katalogu {json_path} wśród plików {mask} nie ma poprawnych plików!")


########################################################################################################################
# testy robione są na liście wyrażeń ze zwalidowaną schemą albo konkretnych pozycjach z tej listy
########################################################################################################################


########################################################################################################################
# Testy walidacji wyrażeń ##############################################################################################
expression_tests = False
# if expression_tests:
    # expr = set()
    # for json_ok in jsons:
    #     for production in json_ok['json']:
    #         x = expr_from_list(list_from_tree(production))
    #         y = param_cond_from_list(list_from_tree(production))
    #         # expr.update(x)
    #         for e in x:
    #             validate_expressions_old(e,production['LSide']["Locations"])
    #         # print(y)
    #         for e in y:
    #             validate_expressions_old(e,production['LSide']["Locations"])
    #         # print(x)

    # validate_expressions_old("Inn/Characters/Drunkard.isTroublemaker + 5", jsons_schema_OK[27]['json'][0]['LSide']["Locations"])
    # validate_expressions_old("(Inn/Characters/Drunkard.isTroublemaker+ 5) * 10", jsons_schema_OK[27]['json'][0]['LSide']["Locations"])
    # validate_expressions_old("(Inn/Characters/Drunkard.isTroublemaker+ dupa 5) * 10", jsons_schema_OK[27]['json'][0]['LSide']["Locations"])
    # validate_expressions_old("Drunkard.isTroublemaker <= 0 or Drunkard.isTroublemaker == None", jsons_schema_OK[27]['json'][0]['LSide']["Locations"])
    # for e in expr:
    #     print(e)



########################################################################################################################
# Testy ścieżki do węzła o zadanych parametrach ########################################################################
breadcrumb_pointer_tests = False
if breadcrumb_pointer_tests:
    results = breadcrumb_pointer(jsons_schema_OK[24]['json'][0]["LSide"]["Locations"], [], attr = {"Value":1000})
    print(results)
    for result in results:
        for node in result:
            print(node['Name'], end='->')
        print()

    results = breadcrumb_pointer(jsons_schema_OK[1]['json'][0]["LSide"]["Locations"], [], attr = {"isTroublemaker":None})
    print(results)
    for result in results:
        for node in result:
            print(node['Name'], end='->')
        print()

    # results = breadcrumb_pointer(jsons_schema_OK[1]['json'][0]["LSide"]["Locations"], [], pointer = result[-1])
    # print(results)
    # for result in results:
    #     for node in result:
    #         print(node['Name'], end='->')
    #     print()

    results = breadcrumb_pointer(jsons_schema_OK[21]['json'][0]["LSide"]["Locations"], [], name_or_id="Lokacja_A")
    print(results)
    for result in results:
        for node in result:
            print(node['Name'], end='->') if 'Name' in node else print(node['Id'], end='->')
        print()




########################################################################################################################
# Testy rozwijania referencji ##########################################################################################
reference_leaves_tests = False
if reference_leaves_tests:
    productions_to_match = jsons_schema_OK[21]['json'] + jsons_schema_OK[1]['json'] #
    for production in productions_to_match:
        destinations_change_to_nodes(production["LSide"]["Locations"])
    world = jsons_schema_OK[27]['json'][0]["LSide"]["Locations"]
    destinations_change_to_nodes(world)
    productions_matched, todos = what_to_do(world, "Main_hero", productions_to_match)
    variant = todos[11]['Matches'][0]

    world = jsons_schema_OK[27]['json'][0]["LSide"]["Locations"]
    print(find_reference_leaves(todos[11]['LSide']['Locations'], variant, "Poison"))
    print(
        find_reference_leaves(todos[11]['LSide']['Locations'], variant, "Innkeeper/**/Items/Egg"))
    print(
        find_reference_leaves(todos[11]['LSide']['Locations'], variant, "Innkeeper/Items/Poison"))
    print(
        find_reference_leaves(todos[11]['LSide']['Locations'], variant, "Somewhere/**/Items/Poison"))
    print(
        find_reference_leaves(todos[11]['LSide']['Locations'], variant, "Somewhere/**/Items/Egg/**/Items/Poison"))
    print(
        find_reference_leaves(todos[11]['LSide']['Locations'], variant, "Somewhere/Characters/Innkeeper/**/Items/Egg/Items/Poison"))
    print(
        find_reference_leaves(todos[11]['LSide']['Locations'], variant, "Buyer/Items/Poison"))
    print(
        find_reference_leaves(todos[11]['LSide']['Locations'], variant, "Buyer/**/Items/Poison"))
    # find_reference_leaves(world, variant, "Inn/Characters/Innkeeper/Items/Poison/Items")
    # find_reference_leaves(world, variant, "Inn/Characters/Innkeeper/Items")
    # find_reference_leaves(world, variant, "Innkeeper/Items/*")
    # find_reference_leaves(world, variant, "Inn/**/Items/Poison")
    # find_reference_leaves(world, variant, "Inn/**/Items/Egg/**/Items/Poison")
    # find_reference_leaves(world, variant, "Inn/Characters/*/**/Items/Egg/Items/Poison")
    # find_reference_leaves(world, variant, "Inn/Characters/*/Items/*/Items")
    # find_reference_leaves(world, variant, "*/Characters/Innkeeper/Items")

    # print(kmp("ara", "Kara barabasza"))
    # print(naive_search("ara", "Kara barabasza"))


########################################################################################################################
# Testy ewaluacji wyrażeń ##############################################################################################
eval_tests = False
if eval_tests:
    world = jsons_schema_OK[27]['json'][0]["LSide"]["Locations"]
    hero = breadcrumb_pointer(world, name_or_id="Main_hero")[0][-1]


    from types import SimpleNamespace
    dane_1 = {'Money': 10, 'HP': 20}
    dane_2 = {'Money': 1000, 'HasDagger': True}

    print(eval("Main_hero.Money + 5 + Main_hero.HP", {"Main_hero": SimpleNamespace(**dane_1), "Merchant": SimpleNamespace(**dane_2)}))


########################################################################################################################
# Testy breadcrumba jednoelementowego ##################################################################################
bc_tests = False
if bc_tests:
    world = jsons_schema_OK[27]['json'][0]["LSide"]["Locations"]
    loc_inn = breadcrumb_pointer(world, name_or_id="Inn")[0][-1]
    print(breadcrumb_pointer({"Locations": [loc_inn]}, name_or_id="Inn"))
          # breadcrumb_pointer({"Locations": [json_dict_or_list]}, parent_key, pointer, name_or_id, attr, layer, remove)
    print(breadcrumb_pointer(loc_inn, name_or_id="Inn"))


########################################################################################################################
# Testy porównywania światów ###########################################################################################
wc_tests = False
if wc_tests:
    world_name ='World_PWK2021_base' #   World_q0_pure   rumcajs-world
    world_source = jsons_schema_OK[get_quest_nr(world_name, jsons_schema_OK)]
    world = world_source['json'][0]["LSide"]["Locations"]

    world2 = deepcopy(world)
    print (world2[-1]["Characters"][0]["Attributes"]["HP"])
    del(world2[-1]["Characters"][0])
    if world == world2:
        print("== Są identyczne")
    else:
        print("== Różnią się")
    if world is world2:
        print("is Są identyczne")
    else:
        print("is Różnią się")
    world2[-1]["Characters"].append(world[-1]["Characters"][0])
    if world == world2:
        print("== Są identyczne")
    else:
        print("== Różnią się")
    if world is world2:
        print("is Są identyczne")
    else:
        print("is Różnią się")


########################################################################################################################
# Testy porównywania światów ###########################################################################################
gp_tests = True
if gp_tests:
    gp_file = 'gameplay_quest00_Dragon_story_World_q00_20220511230633_IGG.json'
    gp_path = '../gameplays/gp-20220511230629'

    retrace_gameplay(gp_path, gp_file)


########################################################################################################################
# Testy nie wiadomo czego ##############################################################################################
# results = list_of_paths_from_tree(jsons_schema_OK[24]['json'][0]["LSide"]["Locations"])
# for result in results:
#     print(result)

# print(breadcrumb2(jsons[0], "Main_hero"))
# print(breadcrumb_old(jsons[0]['json'][0]['LSide']['Locations'], "Inn"))
# print(breadcrumb_old(jsons[0]['json'][0]['LSide']['Locations'], "Main_hero"))

# x = find_reference_leaf_old("Inn/Characters/*", jsons[1]['json'][1]['LSide']["Locations"])
# print(x)
# x = breadcrumb_old(jsons[1]['json'][1]['LSide']["Locations"],"Broom", remove = True)
# print(x)

# x = breadcrumb_all_old(jsons[2]['json'][1]['LSide']["Locations"],"Broom")
# print(x)


