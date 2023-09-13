import logging
import sys

from config.config import path_root
from library.tools import *


# wgrywanie jsonów do testów

#################################################################
from library.tools_validation import get_jsons_storygraph_validated

json_path = f'{path_root}/productions/worlds'
# json_schema_path = f'../json_validation/schema_updated_20220120.json'
mask = '*.json'
logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s', stream=sys.stdout)
#################################################################

# wczytywanie jsonów
jsons_OK, jsons_schema_OK, errors, warnings = get_jsons_storygraph_validated(json_path, mask)

show_errors = False
if show_errors:
    for json_spoiled in errors:
        print('#' * len(json_spoiled['file_path']))
        print(json_spoiled['file_path'])
        print('#' * len(json_spoiled['file_path']), '\n')
        for e in json_spoiled["errors"]:
            print(e)
        print()

show_missions_list = False
if show_missions_list:
    if jsons_OK:
        print(f'Poprawne jsony w katalogu "{json_path}" wśród plików "{mask}":')
        for json_ok, nr in zip(jsons_OK, range(len(jsons_OK))):
            print(f"     {nr}. {json_ok['file_path']}")
    if jsons_schema_OK:
        print(f'Zgodne ze schematem jsony w katalogu "{json_path}" wśród plików "{mask}":')
        for schema_ok, nr in zip(jsons_schema_OK, range(len(jsons_schema_OK))):
            print(f"     {nr}. {schema_ok['file_path']}")
    else:
        print(f"W katalogu {json_path} wśród plików {mask} nie ma poprawnych plików!")


# Definiowanie świata World_q0_and_introduction World_pptx_base rumcajs-world     20220121223859_World_pptx_base
world_name ='World_q0_pure'
world_source = jsons_schema_OK[get_quest_nr(world_name, jsons_schema_OK)]
world = world_source['json'][0]["LSide"]["Locations"]
destinations_change_to_nodes(world, world=True)



# definiowanie głównego bohatera
character = 'Main_hero' #   Rumcajs

# Definiowanie produkcji
# quest_name = 'quest00_Dragon_story' # rumcajs-rules_validated
# productions_to_match = jsons_schema_OK[get_quest_nr('produkcje_generyczne',jsons_schema_OK)]['json'] + jsons_schema_OK[get_quest_nr(quest_name,jsons_schema_OK)]['json']  # generyczne i produkcja DragonStory
# for production in productions_to_match:
#     destinations_change_to_nodes(production["LSide"]["Locations"])

# for world_source in jsons_schema_OK:
# # world_source = jsons_schema_OK[get_quest_nr(world_name, jsons_schema_OK)]
# world = world_source['json'][0]["LSide"]["Locations"]
# destinations_change_to_nodes(world, world=True)

nodes_list = nodes_list_from_tree(world, "Locations")
attr_table = []
attr_text = ''
attr_dict = {}
for node in nodes_list:
    attrs = node['node'].get('Attributes')
    if not attrs or not len(attrs):
        attr_table.append([node['layer'], node['node'].get('Id') or '', node['node'].get('Name') or ''])
        attr_text += f"{node['layer']}\t{node['node'].get('Id') or ''}\t{node['node'].get('Name') or ''}\n"

    else:
        for attr_k, attr_v in attrs.items():
            if attr_k not in attr_dict:
                attr_dict[attr_k] = {}
            if attr_v not in attr_dict[attr_k]:
                attr_dict[attr_k][attr_v] = []
            attr_dict[attr_k][attr_v].append(node)
            attr_table.append([node['layer'], node['node'].get('Id') or '', node['node'].get('Name') or '', attr_k, attr_v])
            attr_text += f"{node['layer']}\t{node['node'].get('Id') or ''}\t{node['node'].get('Name') or ''}\t{attr_k}\t{attr_v}\n"

# print(attr_text)

attr_match_text = '\t\t'
for attribute in attr_dict:
    attr_match_text += f"{attribute}\t"
attr_match_text+= "\n"

for node in nodes_list:
    attr_match_text += f"{node['node'].get('Id') or ''}\t{node['node'].get('Name') or ''}\t"
    node_attrs = node['node'].get('Attributes')

    for attribute in attr_dict:
        if node_attrs and node_attrs.get(attribute):
            attr_match_text += f"{node_attrs[attribute]}\t"
        else:
            attr_match_text += '\t'
    attr_match_text += '\n'



print(attr_match_text)

# gv = GraphVisualizer()
# gv.visualise({'Locations': world}, title=world_name,
#              description=f'Stan świata w dniu {modification_date.strftime("%d.%m.%Y godz. %H:%M:%S")}',
#              world=True, comments=comments).render(format='png',
#              filename=f'{world_name}_{date_folder}_{decision_nr:03d}_original',
#              directory=f'{json_path}/{world_name}_{date_folder}',cleanup=True)




# file_path = folder.rstrip('/') + '/' + file_name
#     os.makedirs(os.path.dirname(file_path), exist_ok=True)
#     with open(file_path, 'w', encoding="utf8") as outfile:
#         # json.dump(json_string, outfile)
#         json.dump(world_target['json'], outfile, indent=4, ensure_ascii=False)
# world_source = jsons_schema_OK[get_quest_nr(world_name, jsons_schema_OK)]
# file_name = str(datetime.datetime.now().strftime("%Y%m%d%H%M%S")) + '_' + world_target['file_path'].split('/')[-1]
# with open(file_path,'w', encoding="utf8") as write_tsv:
#     write_tsv.write(csv_read.to_csv(sep='\t', index=False))