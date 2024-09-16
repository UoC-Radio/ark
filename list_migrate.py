import os
from pathlib import Path

mappings = {
    'iouiou-tsoukoutsoukou.pls': 'iouiou-tsoukoutsoukou/iouiou-tsoukoutsoukou.pls',
    'ExpDm.pls': 'Experimental_Dance_Music/ExpDm.pls',
    'experimental.pls': 'Experimental_Electronica/Experimental_electronica.pls',
    'Drum N\'Bass.pls': 'Zwip/Drum N\'Bass.pls',
    'Futurison.pls': 'Futurison/Futurison.pls',
    'NewReleases.pls': '',
    'Avant_rock.pls': '',
    'Darkiles.pls': 'Darkiles/Darkiles.pls',
    'World_Fusion.pls': 'World_Fusion/World_Fusion.pls',
    'Punky_Reggae_Party.pls': 'Punky_Reggae_Party/Punky_Reggae_Party.pls',
    'Reggae.pls': 'Reggae/Reggae.pls',
    'katsaduboreggae.pls': '',
    'misc.pls': '',
    'Psychedelia.pls': 'Psychedelia/Psychedelia.pls',
    'Post_Rock.pls': 'Post_Rock/Post_Rock.pls',
    'Afro_Power.pls': 'Afro_power/Afro.pls',
    'Hip_Hop.pls': 'Hip-Hop/Hip_Hop.pls',
    'Africain.pls': '',
    'Britpop.pls': 'Britpop/Britpop.pls',
    'Alternative.pls': 'Alternative/Alternative.pls',
    'Anarchokatsadubopunk.pls': 'Anarchokatsadubopunk/Anarchokatsadubopunk.pls',
    'Ellinikohip-hop.pls': 'Hip-Hop/Ellinikohip-hop.pls',
    'MERA_Alternative.pls': '',
    'MERA_futurison.pls': '',
    'ΜΕRA_BritishInvasion.pls': '',
    'ΜΕRA_Latin.pls': '',
    'ΜΕRA_kaitinaimera.pls': '',
}


def read_pls(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    filtered_lines = []
    for l in lines:
        if not l.startswith('File') or 'Sorted' not in l:
            continue
        filtered_lines.append(l.split('=')[1])

    return filtered_lines


wrong_zones_path = Path('/storage/Repository/Zones2.0')

for i in wrong_zones_path.glob('**/*.pls'):
    filtered_lines = read_pls(i)

    if len(filtered_lines) > 0:
        print(i.name)
        #print(filtered_lines)
