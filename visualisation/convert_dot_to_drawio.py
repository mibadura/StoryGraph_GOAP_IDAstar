from graphviz2drawio import graphviz2drawio

######################################################
dot_file = f'out/drawio/prod_generyczne_nowe.dot'
drawio_file = f'out/drawio/prod_generyczne_nowe.drawio'
######################################################

files = [
    # '/Users/gradzinski/dev_home/StoryGraphPython/json_validation/productions/production_vis/Drunkard gets thrown out of Inn_left',
    # '/Users/gradzinski/dev_home/StoryGraphPython/json_validation/productions/production_vis/Drunkard gets thrown out of Inn_right',
    '/Users/gradzinski/dev_home/StoryGraphPython/json_validation/productions/production_vis/Obtaining poison_left',
    # '/Users/gradzinski/dev_home/StoryGraphPython/json_validation/productions/production_vis/Obtaining poison_right',
    # '/Users/gradzinski/dev_home/StoryGraphPython/json_validation/productions/production_vis/Wizard receives a distress call from Main hero_left',
    # '/Users/gradzinski/dev_home/StoryGraphPython/json_validation/productions/production_vis/Wizard receives a distress call from Main hero_right',
    # '/Users/gradzinski/dev_home/StoryGraphPython/json_validation/productions/production_vis/World_q0',
]

for filename in files:
    with open(f'{filename}.drawio', 'w+') as f_drawio:
        f_drawio.write(graphviz2drawio.convert(filename))
