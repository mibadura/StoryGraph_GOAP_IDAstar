from __future__ import annotations

import ctypes
import datetime
import logging
import sys
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache # od Pythona 3.9 można: from functools import cache
from tempfile import TemporaryDirectory
from typing import Optional, Union

import uvicorn

from library.tools_visualisation import draw_graph
from subprocess import Popen

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from config.config import path_root
from library.tools import *
from library.tools_match import what_to_do, world_turn
from library.tools_process import (
    CannotFindCharacter,
    apply_instructions_to_world,
    dict_from_variant,
    game_init,
    looking_for_main_character,
    save_world_game,
    world_copy, looking_for_main_character_for_api, dict_from_variant_preserve_id, add_uuid,
)
from library.tools_validation import get_jsons_storygraph_validated

logging.basicConfig(
    level=logging.ERROR, format="%(levelname)s: %(message)s", stream=sys.stdout
)

##########################################################################################################


jsons_OK, jsons_schema_OK, errors, warnings = get_jsons_storygraph_validated(path_root)


# ######################################################
# definicje
# definiowanie świata
world_name = 'world_DragonStory' #'World_PWK2021_misje_P' #'world_RumcajsStory'  #'World_PWK2021_Main_13_do_testow'"World_q00"
# definiowanie misji
quest_names = [
    'quest_DragonStory' #"quest2021-04_Tax_to_pay"
]  #'quest2021-13_Fiddler_story', 'Exchanging_item_for_ingredient_item_and_money_(generic_q-13)'
quest_automatic_names = (
    []
)  #'Turning_a_dead_rat_into_a_rat_tail_with_discount_(automatic_q-13)'
# definiowanie głównego bohatera
main_character_name = "Main_hero"  # 'Rumcajs' 'Main_hero'
# ######################################################


# świat z naszego katalogu
world_source = jsons_schema_OK[get_quest_nr(world_name, jsons_schema_OK)]


world = world_source["json"][0]["LSide"]["Locations"]
world_nodes_list = nodes_list_from_tree(world, "Locations")
world_nodes_ids_list = [str(id(x["node"])) for x in world_nodes_list]
world_nodes_ids_pairs_list = [(str(id(x["node"])), x["node"]) for x in world_nodes_list]
world_nodes_dict = {}

for node in world_nodes_list:
    world_nodes_dict[id(node)] = node
world_locations_ids = []
for l in world:
    world_locations_ids.append(id(l))
destinations_change_to_nodes(world, world=True, remove_ids=False)


# pobieranie produkcji zserializowanych
prod_chars_turn_names = ["produkcje_generyczne", *quest_names]
prod_world_turn_names = [
    *quest_automatic_names,
    "produkcje_automatyczne",
    "produkcje_automatyczne_wygrywania",
]


@lru_cache(maxsize=None)  # od Pythona 3.9 można: @cache
def get_productions_chars_turn_to_match():
    prod_chars_turn_jsons = [
        deepcopy(jsons_schema_OK[get_quest_nr(x, jsons_schema_OK)]["json"])
        for x in prod_chars_turn_names
    ]
    prod_world_turn_jsons = [
        deepcopy(jsons_schema_OK[get_quest_nr(x, jsons_schema_OK)]["json"])
        for x in prod_world_turn_names
    ]

    # scalanie i rozwijanie destynacji w produkcjach
    productions_chars_turn_to_match = []
    productions_world_turn_to_match = []
    for prods in prod_chars_turn_jsons:
        for prod in prods:
            productions_chars_turn_to_match.append(prod)
            if not destinations_change_to_nodes(prod["LSide"]["Locations"]):
                raise Exception()
    for prods in prod_world_turn_jsons:
        for prod in prods:
            productions_world_turn_to_match.append(prod)
            if not destinations_change_to_nodes(prod["LSide"]["Locations"]):
                raise Exception()

    return productions_chars_turn_to_match

def get_productions_chars_and_world_turn_to_match():
    prod_chars_turn_jsons = [
        deepcopy(jsons_schema_OK[get_quest_nr(x, jsons_schema_OK)]["json"])
        for x in prod_chars_turn_names
    ]
    prod_world_turn_jsons = [
        deepcopy(jsons_schema_OK[get_quest_nr(x, jsons_schema_OK)]["json"])
        for x in prod_world_turn_names
    ]

    # scalanie i rozwijanie destynacji w produkcjach
    productions_chars_turn_to_match = []
    productions_world_turn_to_match = []
    for prods in prod_chars_turn_jsons:
        for prod in prods:
            productions_chars_turn_to_match.append(prod)
            if not destinations_change_to_nodes(prod["LSide"]["Locations"]):
                raise Exception()
    for prods in prod_world_turn_jsons:
        for prod in prods:
            productions_world_turn_to_match.append(prod)
            if not destinations_change_to_nodes(prod["LSide"]["Locations"]):
                raise Exception()

    return productions_chars_turn_to_match, productions_world_turn_to_match

gameplay = {
    "Player": "Web player",  # Można dodać obsługę
    "MainCharacter": main_character_name,
    "WorldName": world_name,
    "WorldSource": save_world_game(
        world_source
    ),  # stan świata z id lokacji będących stringiem z adresu pamięci
    "QuestName": quest_names[0],
    "QuestSource": [
        {x: jsons_schema_OK[get_quest_nr(x, jsons_schema_OK)]["json"]}
        for x in prod_chars_turn_names
    ],
    "WorldResponseSource": [
        {x: jsons_schema_OK[get_quest_nr(x, jsons_schema_OK)]["json"]}
        for x in prod_world_turn_names
    ],
    "DateTimeStart": datetime.now().strftime("%Y%m%d%H%M%S"),
    "Moves": [],
    "FilePath": str(Path(TemporaryDirectory().name).resolve()),  # We don't need that.
}

game_init(gameplay)


app = FastAPI()


def word_to_serializable(word: dict) -> dict:
    world_target = deepcopy(word)
    world_copy(
        word,
        world_target,
        preserve_id = True
    )
    return world_target


class GameStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    WIN = "win"
    LOST = "lost"


class AnswerSchema(BaseModel):
    available_productions: list = Field(
        description="List of available production to apply."
    )
    world: list = Field(description="Current world state.", example="{word}")
    changed_nodes: Optional[dict] = Field(description="Identifiers of changed nodes in old and new world.")
    message: Optional[str] = Field(description="Optional message from game.")
    game_status: GameStatus = Field(description="Current game state.")
    location_info: dict = Field(description="Information about current location.")
    main_character: str = Field(description="Id of current main character.")


class AnswerOnErrorSchema(BaseModel):
    message: str = Field(description="Information about error.")


class GameRequest(BaseModel):
    world: list = Field(description="Base world for production.")
    production: dict = Field(description="Production to apply on world.")
    variant: list = Field(description="Variant of production to apply on world")

class GameRequest2(BaseModel):
    world: list = Field(description="Base world for production")
    production: dict = Field(description="Production to apply on world")
    variant: list = Field(description="Variant of production to apply on world")
    object: str = Field(description="Name of the acting character")

class MapRequest(BaseModel):
    whole: list = Field(description="World with productions and everything else.")

@dataclass()
class AvailableProductions:
    prod: list
    variants: list[str]


def get_all_available_actions(
    world, main_location, productions_chars_turn_to_match, character
) -> list[AvailableProductions]:
    result: list[AvailableProductions] = []
    _, todos = what_to_do(
        world, main_location, productions_chars_turn_to_match, character=character
    )

    for prod in todos:
        prod_copy = deepcopy(prod)
        del prod_copy["Matches"]
        current_production = AvailableProductions(
            prod=prod_copy,
            variants=[],
        )
        for variant in prod["Matches"]:
            current_production.variants.append(dict_from_variant_preserve_id(variant))
        result.append(current_production)
    return result


@app.get("/getWorld", response_model=Union[AnswerSchema, AnswerOnErrorSchema])
async def root():
    current_world = deepcopy(world)
    productions_chars_turn_to_match = get_productions_chars_turn_to_match()

    # sprawdzamy, gdzie jest główny bohater
    try:
        character_paths = looking_for_main_character_for_api(
            gameplay,
            current_world,
            name_or_id=main_character_name,
            zero_text="Zniknął główny bohater. Pewno zginął.",
        )

    except CannotFindCharacter as e:
        return AnswerOnErrorSchema(message=e.message)

    main_location = character_paths[0][0]

    location_info = sheaf_description_dict(main_location)
    location_info["main_location_id"] = main_location.get("Id")

    sheaf_description(main_location)

    character = character_paths[0][-1]

    available_actions = get_all_available_actions(
        current_world,
        main_location,
        productions_chars_turn_to_match,
        character=character,
    )

    return AnswerSchema(
        available_productions=available_actions,
        world=word_to_serializable(current_world),
        message=None,
        game_status=GameStatus.IN_PROGRESS.value,
        location_info=location_info,
        main_character = character.get("Id")
    )


@app.post("/postNewWorld", response_model=Union[AnswerSchema, AnswerOnErrorSchema])
async def action(request: GameRequest2):
    current_world = deepcopy(request.world)
    red_nodes_new = []
    productions_chars_turn_to_match, productions_world_turn_to_match = get_productions_chars_and_world_turn_to_match()

    # sprawdzamy, gdzie jest aktualny bohater
    try:
        character_paths = looking_for_main_character_for_api(
            gameplay,
            current_world,
            name_or_id=request.object,
            zero_text=f"Zniknął aktualny główny bohater ({request.object}). Pewno zginął.",
        )
    except CannotFindCharacter as e:
        return AnswerOnErrorSchema(message=e.message)

    main_location = character_paths[0][0]

    location_info = sheaf_description_dict(main_location)
    location_info["main_location_id"] = main_location.get("Id")

    character = character_paths[0][-1]

    production: list[tuple()] = []

    def search_in_world(world: dict, id: int) -> Optional[dict]:
        result = list(filter(lambda x: int(x["Id"]) == id, world))
        if result:
            return result[0]

        for x in world:
            for key in [None, "Attributes", "Characters", "Items", "Connections"]:
                if key not in x:
                    continue
                result = list(
                    filter(
                        lambda x: "id" in x and int(x.get("Id")) == id, x[key] if key else x
                    )
                )
                if result:
                    return result[0]
        return None

    def search_in_production(production: dict, id: int) -> Optional[dict]:
        l_side = production["LSide"]
        for z in l_side.values():
            result = list(filter(lambda x: x.get("Id") == id, z))
            if result:
                return result[0]
        return None

    for v in request.variant:
        # w_node = search_in_world(current_world, v["WorldNodeId"])
        # if not w_node:
        w_node = breadcrumb_pointer(
            current_world, name_or_id=str(v["WorldNodeId"])
        )[0][-1]
        if not w_node:
            raise Exception()
        ls_node = search_in_production(request.production, v["LSNodeRef"])
        if not ls_node:
            ls_node = breadcrumb_pointer(request.production, name_or_id=v["LSNodeRef"])[
                0
            ][-1]
            if not ls_node:
                raise Exception()

        production.append((ls_node, w_node))


    destinations_change_to_nodes(current_world, world=True, remove_ids=False)

    available_actions = []
    if request.production and request.variant:
        red_nodes_new = apply_instructions_to_world(
            request.production, production, current_world
        )
        if red_nodes_new:
            action_description(request.production, production)
            world_production_ids = [id(x[1]) for x in production] + red_nodes_new
            current_world_locations_ids = [id(x[1]) for x in production if x[1] in current_world] + [x for x in red_nodes_new if ctypes.cast(x, ctypes.py_object).value in current_world]

            effect_world, decs_world = world_turn(gameplay, world_production_ids, current_world, current_world_locations_ids,
                                                  productions_world_turn_to_match, 0)
            red_nodes_new += effect_world

        else:
            return AnswerOnErrorSchema(
                message=f'Nie dało się zastosować produkcji „{request.production["Title"].split(" / ")[0]}” do świata. '
                f"Żaden węzeł nie został zmodyfikowany."
            )



    # sprawdzamy, gdzie jest _aktualny_ bohater
    try:
        character_paths = looking_for_main_character_for_api(
            gameplay,
            current_world,
            name_or_id=character.get("Id"), # bieżący bohater
            # TODO UWAGA: jeśli podany po Id, to dupa! E, chyba już OK
            zero_text="Zniknął aktualny bohater. Pewno zginął.",
        )
        main_location = character_paths[0][0]
        character = character_paths[0][-1]
        available_actions = get_all_available_actions(
            current_world,
            main_location,
            productions_chars_turn_to_match,
            character=character,
        )

    except CannotFindCharacter as e:
        available_actions = []
        # return AnswerOnErrorSchema(message=e.message)


    # sprawdzamy, gdzie jest _główny_ bohater
    try:
        character_paths = looking_for_main_character_for_api(
            gameplay,
            current_world,
            name_or_id=main_character_name,  # główny bohater, nie bieżący, bo bieżący może być NPC-em
            # TODO UWAGA: jeśli podany po Id, to dupa! E, chyba już OK
            zero_text="Zniknął główny bohater. Pewno zginął.",
        )

    except CannotFindCharacter as e:
        return AnswerOnErrorSchema(message=e.message)

    main_character_location = character_paths[0][0]
    main_character = character_paths[0][-1]

    location_info = sheaf_description_dict(main_location)
    location_info["main_location_id"] = main_location.get("Id")


    sheaf_description(main_location)




    changed_nodes = {}
    # robimy listę stare/nowe id tylko dla zmienionych węzłów, ale można przelecieć się po wszystkich
    if red_nodes_new:
        for i in red_nodes_new:

            changed_nodes[add_uuid(ctypes.cast(i, ctypes.py_object).value)] = ''


    return AnswerSchema(
        available_productions=available_actions,
        world=word_to_serializable(current_world),
        message=None,
        changed_nodes=changed_nodes,
        game_status=GameStatus.IN_PROGRESS.value,
        location_info=location_info,
        main_character = main_character.get("Id")
    )


@app.post("/generateMap", response_model=Union[AnswerSchema, AnswerOnErrorSchema])
async def action(request: MapRequest):
    current_world = deepcopy(request.whole)
    map_dir_path = f'{tempfile.gettempdir()}'
    os.makedirs(f'{map_dir_path}{os.sep}SGtmp', exist_ok=True)
    os.makedirs(f'{map_dir_path}{os.sep}SGmap', exist_ok=True)
    std_out_file = f"{map_dir_path}{os.sep}SGtmp{os.sep}stdout.log"
    std_err_file = f"{map_dir_path}{os.sep}SGtmp{os.sep}stderr.log"
    draw_graph(current_world, '', f'', f'map_graph', f'{map_dir_path}{os.sep}SGtmp', clean=False, draw_id=False, map_style=True)

    # my_env = os.environ.copy()
    # my_env["PATH"] = r"D:\anaconda3\Scripts;D:\anaconda3\envs\myenv\Scripts;" + my_env["PATH"]
    # my_env['VIRTUAL_ENV'] = r'D:\anaconda3\envs\myenv\Scripts'

    with open(std_out_file, "wb") as out, open(std_err_file, "wb") as err:
        p = Popen(
            f'sfdp -Goverlap=prism {map_dir_path}{os.sep}SGtmp{os.sep}map_graph | gvmap  -e | neato -Ecolor="#55555522" -n2 -Tpng > {map_dir_path}{os.sep}SGmap{os.sep}map_post.png',
            stdout=out, stderr=err, shell=True)  # , env=my_env
        p.communicate()
    return FileResponse(f'{map_dir_path}{os.sep}SGmap{os.sep}map_post.png')




if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
