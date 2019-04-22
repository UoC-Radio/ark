#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Given two directories containing music libraries, source and target, compare and report albums in source
that there are not in target. It is assumed that each leaf directory represents an album and the track is tagged with
MusicBrainz group release id and/or MusicBrainz release id
"""

import os
from mutagen.oggvorbis import OggVorbis
from mutagen.id3 import ID3
from mutagen.flac import FLAC
import argparse


def safe_get(dictionary, key):
    # return the string representation, because sometimes the value is an object, rather than the required string
    if key in dictionary:
        val = dictionary[key]
        return str(val) if not isinstance(val, list) else val
    else:
        return ''


def squeeze(l):
    if isinstance(l, list):
        return ", ".join(str(x) for x in l)
    elif isinstance(l, str):
        return l
    else:
        return ''


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


def find_release_mbids(albums):
    albums_aid_map = {}
    albums_gid_map = {}
    without_info = []
    for a in albums:
        filepath = os.path.join(a, os.listdir(a)[0])
        file_extension = filepath.split('.')[-1]
        if file_extension == 'mp3':
            id3_metadata = ID3(filepath)
            album_id = safe_get(id3_metadata, 'TXXX:MusicBrainz Album Id')
            album_gid = safe_get(id3_metadata, 'TXXX:MusicBrainz Release Group Id')
        elif file_extension == 'flac' or file_extension == 'ogg':
            vorbis_metadata = FLAC(filepath) if file_extension == 'flac' else OggVorbis(filepath)
            album_id = squeeze(safe_get(vorbis_metadata, 'musicbrainz_albumid'))
            album_gid = squeeze(safe_get(vorbis_metadata, 'musicbrainz_releasegroupid'))
        else:
            print('Unsupported file extension [{}] in album {}'.format(file_extension, a))
            continue

        if len(album_id) == 0 and len(album_gid) == 0:
            without_info.append(a)
        else:
            if len(album_id) != 0:
                albums_aid_map[album_id] = a
            if len(album_gid) != 0:
                albums_gid_map[album_gid] = a

    return albums_aid_map, albums_gid_map, without_info


def main(source_library_path, target_library_path):
    source_albums_id_map, source_albums_gid_map, source_without_info = \
        find_release_mbids(parse_library(source_library_path))
    target_albums_id_map, target_albums_gid_map, target_without_info = \
        find_release_mbids(parse_library(target_library_path))

    non_existing_albums = []
    for k in source_albums_gid_map.keys():
        if k not in target_albums_gid_map:
            non_existing_albums.append(source_albums_gid_map[k])

    possibly_non_existing_albums = []
    for k in source_albums_id_map.keys():
        if k not in target_albums_id_map:
            p = source_albums_id_map[k]
            if p not in non_existing_albums:
                possibly_non_existing_albums.append(source_albums_id_map[k])

    print('\n\nAlbums of source library, definitely not in target library:\n')
    print(*non_existing_albums, sep='\n')

    print('\n\nAlbums of source library, possibly not in target library:\n')
    print(*possibly_non_existing_albums, sep='\n')

    print('\n\nAlbums of source library, without info:\n')
    print(*source_without_info, sep='\n')

    print('\n\nAlbums of target library, without info:\n')
    print(*target_without_info, sep='\n')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Compare two music libraries and report albums of source not in target library.')
    parser.add_argument('--source', nargs='?', required=True, help='Source library path')
    parser.add_argument('--target', nargs='?', required=True, help='Target library path')
    args = parser.parse_args()

    main(args.source, args.target)
