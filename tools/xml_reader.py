import xml.etree.ElementTree as ET

import re
from copy import deepcopy

from config.config import path_root
from library.tools_validation import production_names_list_builder, get_jsons_schema_validated

# wgrywanie jsonów
mask = '*.json'
dir_name = ''  #    przykłady do testowania dopasowań
json_path = f'{path_root}/{dir_name}'
jsons_sg_validated = []
warnings = {}
jsons_schema_validated, errors = get_jsons_schema_validated(json_path, mask)

# usuwanie plików duplikujących produkcje wspólne
limit = len(jsons_schema_validated)
for nr in range(limit):
    inv_nr = limit-nr-1
    # print(inv_nr, jsons_schema_validated[inv_nr]['file_path'])
    if 'included' in jsons_schema_validated[inv_nr]['file_path'] or 'from other groups' in jsons_schema_validated[inv_nr]['file_path']:
        del(jsons_schema_validated[inv_nr])
        # print ('     deleted')

# budowanie listy nazw produkcji
production_titles_dict, errors, warnings = production_names_list_builder(jsons_schema_validated, errors=errors, warnings=warnings)

json_prod_by_quest = {'-01': [], '-02': [], '-03': [], '-04': [], '-05': [], '-06': [], '-07': [], '-08': [], '-09': [],
                      '-10': [], '-11': [], '-12': [], '-13': [], '-14': [], '-15': []}

for k, v in production_titles_dict.items():
    nr = re.search(r'-\d+', v['file_path'], flags=0)

    if nr:
        json_prod_by_quest[nr.group()].append(k)

json_prod_by_quest2 = deepcopy(json_prod_by_quest)
nodes_by_quest = {}
nodes_wrong_by_quest = {}
nodes_lack_by_quest = {}

xml_names =['quest2021-01_Releasing_the_brother.xml', 'quest2021-02_Need_of_ship.xml', 'quest2021-03_Being_ill.xml', 'quest2021-04_Tax_to_pay.xml', 'quest2021-05_Prison_break.xml', 'quest2021-06_Misterious_potion.xml', 'quest2021-07_Monkey_attack.xml', 'quest2021-08_Lumberjack_in_trouble.xml', 'quest2021-09_Encounter_in_the_tavern.xml', 'quest2021-10_Ship_password.xml', 'quest2021-11_Keys_for_a_horse.xml', 'quest2021-12_Black_wizard_and_ship.xml', 'quest2021-13_Fiddler_story.xml', 'quest2021-14_Troll_story.xml', 'quest2021-15_Theft_in_wizards_hut.xml']
nodes_names = {}
print('############### Produkcje z diagramów nieistniejące w jsonach (i inne węzły z ukośnikami, niesttey)')
for name in xml_names:

    root = ET.parse(f'tmp/{name}')
    nodes_by_quest[name] = []


    for elem in root.findall('.//*[@value]'):
        # print(elem.attrib.get('id'), elem.attrib.get('value'))
        node_name = re.sub(r'(&lt;|<)[^>]+(>|&gt;)', '', elem.attrib.get('value'))
        # print(elem.attrib.get('id'), node_name)
        if node_name in production_titles_dict:
            if node_name not in nodes_by_quest[name]:
                nodes_by_quest[name].append(node_name)
                # json_prod_by_quest[name[9:11]].remove(node_name)
                # print(json_prod_by_quest[name[9:11]])
                if node_name in json_prod_by_quest[name[9:12]]:
                    json_prod_by_quest[name[9:12]].remove(node_name)

        elif "/" in node_name:
            if not nodes_wrong_by_quest.get(name):
                nodes_wrong_by_quest[name] = []
                print(f"      Błedy w {name}:")
            if node_name not in nodes_wrong_by_quest[name]:
                nodes_wrong_by_quest[name].append(node_name)
                print(node_name)
            # else:
            #     if not nodes_names.get(name):
            #         nodes_names[name] = []
            #     nodes_names[name].append(node_name)


print('############### Produkcjie z jsonów nieużywanie (i automatyczne, niestety)')
for k, v in json_prod_by_quest.items():
    print(k)
    for e in v:
        gen = False
        for e2 in json_prod_by_quest2[k]:
            if production_titles_dict[e2]["production"]["TitleGeneric"] == e:
                gen = True
        if not gen:
            print(e)



