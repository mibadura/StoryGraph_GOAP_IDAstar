import os

from config.config import path_root
from library.tools import destinations_change_to_nodes, nodes_list_from_tree, get_quest_nr, breadcrumb_pointer

from library.tools_validation import get_jsons_storygraph_validated, get_generic_productions_from_file, \
    print_errors_warnings

# data = [('john','marry'),('mike','john'),('mike','hellen'),('john','elisa')]
#
# print(os.getcwd().rsplit("/", 1))
from library.tools_visualisation import draw_graph

# json_schema_path = f'../json_validation/schema_updated_20220213.json'
# dict_schema_path = f'../json_validation/schema_sheaf_updated_20220213.json'
json_path = f'{path_root}/productions'  #
# productions
#productions/questsPWK2020/0'
# D:\Uniwersytet Jagielloński\StoryGraph - General\materiały fabularne\

g, e = get_generic_productions_from_file(f'{path_root}/productions/generics/produkcje_generyczne.json')



# get_jsons_storygraph_validated(json_path, json_schema_path, dict_schema_path, production_titles_dict=g)

# test_list = ["A", "B", "C", "D", "E", "F", "G", "H"]

# for nr, letter in enumerate(test_list[::2]):
#     print(f'{nr}. {letter}, {test_list[nr]}, {test_list[nr + 1]}')

# for nr in range(len(test_list))[::2]:
#     print(f'{nr}. {test_list[nr]}, {test_list[nr + 1]}')


# dict_one = {'name': 'John', 'last_name': 'Doe', 'job': 'Python Consultant', 'holiday': 'Inn'}
# dict_two = {'name': 'Jane', 'job': 'Community Manager', 'last_name': 'Doe'}
#
# print(dict_one.keys())
# print(dict_two.keys())
#
# print(list(set(dict_one.keys() + dict_two.keys())))
#
# for (k1, v1), (k2, v2) in zip(dict_one.items(), dict_two.items()):
#     print(k1, '->', v1)
#     print(k2, '->', v2)

# todos = [1,2,3,4,5,6,7,8,9,10]
# print(todos)
# for nr, elem in reversed(list(enumerate(todos))):
#
#     if elem % 3 == 0:
#         print(elem, "---")
#         todos.pop(nr)
#     else:
#         print(elem)
# print(todos)


# walidowanie plików json i wypisywanie błędów
jsons_sg_validated, jsons_schema_validated, errors, warnings = get_jsons_storygraph_validated(json_path)
print_errors_warnings(jsons_schema_validated, errors, warnings)


mission = jsons_schema_validated[get_quest_nr("rumcajs-world_Nantes_add_necklace2", jsons_schema_validated)]
production = mission["json"][0]
# przygotowuję produkcję do wykonania
world  = production["LSide"]["Locations"]
destinations_change_to_nodes(world)
nodes_list = nodes_list_from_tree(world, "Locations")
variant = []
red_nodes = []
red_edges = []

ch = breadcrumb_pointer(world, name_or_id="Merchant")
red_nodes.append(id(ch[0][-1]))
red_nodes.append(id(ch[0][-2]))
red_nodes.append(id(ch[0][-2]["Connections"][0]["Destination"]))
red_edges.append((id(ch[0][-2]), id(ch[0][-2]["Connections"][0]["Destination"])))
# for node in nodes_list:
#     if node["node"]["Connections"] == ch[0][-2]:
#         red_nodes.append(id(node["node"]))

ch = breadcrumb_pointer(world, name_or_id="Rumcajs")
red_nodes.append(id(ch[0][-1]))
red_nodes.append(id(ch[0][-2]))
for node in ch[0][-2]["Connections"]:
    if node["Destination"].get("Items",[{}])[0].get("Name") == "Brushwood":
        red_nodes.append(id(node["Destination"]))
        red_edges.append((id(ch[0][-2]), id(node["Destination"])))

# rysowanie wizualizacji

# generuję obrazek lewej strony
d_title = f'{production["Title"].split(" / ")[0]}'
d_desc = f'{production["Description"]}'
d_w = True
draw_id = False
d_dir = f'{path_root}/{mission["file_path"].rsplit("/", 1)[0]}/production_vis/'
d_file = f'{production["Title"].split(" / ")[0]}_red_nodes'
draw_graph(production["LSide"], d_title, d_desc, d_file, d_dir, r_n=red_nodes, r_e=red_edges, w=d_w, draw_id=draw_id)
