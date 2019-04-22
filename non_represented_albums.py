#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
(1) Loads a directory which contains playlist files in its subfolders.
(2) Loads a directory which contains the music library from which those playlists are created. It is assumed that each
leaf directory represents an album.
(3) Albums that are not represented in any playlist are reported.

Currently supported playlist extensions: .pls
"""

import os
import argparse


def get_pls_almbums(pls_path):
    albums_set = set()
    with open(pls_path, encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith('File'):
                line = line.strip('\n')
                tokens = line.split('=')
                albums_set.add(os.path.join(os.path.dirname(tokens[1])))

    return albums_set


def parse_playlists(playlists_path, accepted_extensions):
    list_albums_set = set()
    total_playlists = 0
    # Parse playlists
    for root, dirs, files in os.walk(playlists_path):
        if len(files) == 0:
            continue
        else:
            for f in files:
                file_path = os.path.join(root, f)
                filename, ext = os.path.splitext(file_path)

                if ext in accepted_extensions:
                    # set union
                    total_playlists += 1
                    list_albums_set |= get_pls_almbums(file_path)

    print('Parsed {0} playlists in total.'.format(total_playlists))
    return list_albums_set


def parse_library(library_path):
    library_albums_set = set()

    # Parse library
    for root, dirs, files in os.walk(library_path):
        if len(files) == 0:
            continue
        else:
            # Get the leaf directory
            if not dirs:
                # Add the album path without the trailing slash
                library_albums_set.add(os.path.join(root, os.path.dirname(files[0]))[:-1])

    return library_albums_set


def main(playlists_path, library_path):
    accepted_extensions = ['.pls']

    list_albums_set = parse_playlists(playlists_path, accepted_extensions)
    print('{0} albums are included in at least one playlist.'.format(len(list_albums_set)))

    library_albums_set = parse_library(library_path)
    print('{0} albums are included in the library.'.format(len(library_albums_set)))

    unrepresented_albums_set = library_albums_set - list_albums_set
    print('{0} albums are not included in any playlist.'.format(len(unrepresented_albums_set)))

    for album_path in sorted(unrepresented_albums_set):
        # print the album path relative to the music library directory
        print('{0}.'.format(album_path[len(library_path)+1:]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Report albums that are not represented in any playlist.')
    parser.add_argument('--playlists_path', nargs='?', required=True, help='Source library path')
    parser.add_argument('--library_path', nargs='?', required=True, help='Target library path')
    args = parser.parse_args()

    main(args.source, args.target)
