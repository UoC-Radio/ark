import sys
import os
from subprocess import call
import argparse


def main(zones_dir, search_term):
    # list all directories inside zones_root_dir
    for (dir_names) in os.walk(zones_dir):

        # keep only 1st leaf dirs
        zone_path = dir_names[0]
        zone_name = os.path.basename(dir_names[0])

        for zone_file in os.listdir(zone_path):
            if (os.path.isdir(zone_path + "/" + zone_file)):
                continue
            with open(zone_path + "/" + zone_file) as plsFile:
                song_entry = plsFile.readline()
                while song_entry:
                    if search_term in song_entry:
                        print(zone_path + "/" + zone_file)
                        break
                    song_entry = plsFile.readline()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Report albums that are not represented in any playlist.')
    parser.add_argument('--zones_dir', nargs='?', required=True, help='A directory containing Zone folders. Each folder may contain multiple PLS playlist files')
    parser.add_argument('--search_term', nargs='?', required=True, help='Search term')
    args = parser.parse_args()

    main(args.zones_dir, args.search_term)
