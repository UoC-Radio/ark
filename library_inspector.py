#!/usr/bin/env python3
"""
An inspector of a music library
Currently supported functionality:
a) Statistics: how many files of a type (flac, mp3, etc), genres and bitrates
b) Musicbrainz tagged and untagged files
c) Consistency of an album, i.e. if the number of album tracks corresponds to the files in the directory
    - May have the same album multiple times, and with different bitrates/file formats
    - May miss a track
    - May have wrongly tagged the album
    - An album may have a ghost track
"""

import sys
import os
import configparser
import os
import re
from collections import Counter
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis
from mutagen.id3 import ID3, TENC
from mutagen.flac import FLAC
from mutagen import MutagenError
from bisect import bisect_left
import numpy as np
from abc import ABC
import argparse

from utils import *

# Options
MP3_MAX_BITATE = 512
MP3_N_BINS = 64


def get_closest_idx(l: list, n: int):
    ''' Assumes that input list is sorted '''
    pos = bisect_left(l, n)

    if pos == 0:
        return 0
    if pos == len(l):
        return len(l) - 1

    prev = l[pos - 1]
    next = l[pos]

    return pos if next - n < n - prev else pos - 1


def find_closest(l: list, n: int):
    min(l, key=lambda x: abs(x - n))


class GenericFileTypeStat(ABC):
    def __init__(self):
        self._total_files = 0
        self._name = 'gen'
        self._untagged_list = []
        self._genres = dict()

    def add_file(self, track_path: str):
        self._total_files += 1

    def size(self):
        return self._total_files

    def name(self):
        return self._name

    def contains_tag(self, tags_dict: dict, tag: str):
        pass

    def _inspect(self, metadata: dict, track_path: str):
        pass

    def directory_is_consistent(self, album_path: str):
        pass

    def get_genres(self):
        return self._genres

    def get_untagged(self):
        return self._untagged_list

    def get_stats(self):
        pass


class FlacFileTypeHolder(GenericFileTypeStat):
    def __init__(self):
        GenericFileTypeStat.__init__(self)
        self._name = 'flac'

    def add_file(self, track_path: str):
        GenericFileTypeStat.add_file(self, track_path)

        audio = FLAC(track_path)
        kbps = audio.info.sample_rate * audio.info.bits_per_sample * audio.info.channels / 1000

        self._inspect(audio, track_path)

    def contains_tag(self, tags_dict: dict, tag: str):
        return True if tag in tags_dict and len(tags_dict[tag]) > 0 else False

    def _inspect(self, metadata: dict, track_path: str):
        if not self.contains_tag(metadata, 'musicbrainz_albumid') or \
                not self.contains_tag(metadata, 'musicbrainz_trackid'):
            self._untagged_list.append(track_path)
        if self.contains_tag(metadata, 'genre'):
            for g in metadata['genre']:
                trimmed_genres = re.split('; |;', g)  # handle additional splits
                for gg in trimmed_genres:
                    if gg not in self._genres:
                        self._genres[gg] = 0
                    self._genres[gg] += 1

    def directory_is_consistent(self, album_path: str):
        files = os.listdir(album_path)

        flac = FLAC(os.path.join(album_path, files[0]))

        total_tracks = 0
        if self.contains_tag(flac, 'TOTALTRACKS'):
            try:
                total_tracks = int(flac['TOTALTRACKS'][0])
            except IndexError:
                return False, len(files), None

        return total_tracks == len(files), len(files), total_tracks


class Mp3FileTypeHolder(GenericFileTypeStat):
    def __init__(self):
        GenericFileTypeStat.__init__(self)
        self._name = 'mp3'
        self.__mp3_bitrates = np.zeros(int(MP3_MAX_BITATE / MP3_N_BINS + 1))  # fill zeros
        self.__mp3_bins = []
        self.__fill_bins()

    def __fill_bins(self):
        for i in range(0, MP3_MAX_BITATE + 1, MP3_N_BINS):
            self.__mp3_bins.append(i)

    def add_file(self, track_path: str):
        GenericFileTypeStat.add_file(self, track_path)

        audio = MP3(track_path)
        kbps = int(audio.info.bitrate / 1000)

        idx = get_closest_idx(self.__mp3_bins, kbps)
        self.__mp3_bitrates[idx] += 1

        self._inspect(ID3(track_path), track_path)

    def contains_tag(self, tags_dict: dict, tag: str):
        return True if tag in tags_dict and len(tags_dict[tag].text) > 0 else False

    def _inspect(self, metadata: dict, track_path: str):
        if not self.contains_tag(metadata, 'TXXX:MusicBrainz Album Id'):
                # Commented out because some don't have at the time they were tagged
                #or not self.contains_tag(metadata, 'TXXX:MusicBrainz Release Track Id'):
            self._untagged_list.append(track_path)
        if self.contains_tag(metadata, 'TCON'):
            for g in metadata['TCON'].text:
                trimmed_genres = re.split('; |;', g)  # handle additional splits
                for gg in trimmed_genres:
                    if gg not in self._genres:
                        self._genres[gg] = 0
                    self._genres[gg] += 1

    def get_stats(self):
        if self._total_files > 0:
            return dict(zip(self.__mp3_bins, self.__mp3_bitrates / self._total_files))

    def directory_is_consistent(self, album_path: str):
        files = os.listdir(album_path)

        id3 = ID3(os.path.join(album_path, files[0]))

        if self.contains_tag(id3, 'TRCK'):
            try:
                total_tracks = int(id3['TRCK'].text[0].split('/')[1])
            except IndexError:
                return False, len(files), None

        return total_tracks == len(files), len(files), total_tracks


FlacFileTypeHolder = SingletonDecorator(FlacFileTypeHolder)
Mp3FileTypeHolder = SingletonDecorator(Mp3FileTypeHolder)


class LibraryInspector:
    def __init__(self):
        # Initializations
        self.__holders = \
            {
                '.flac': FlacFileTypeHolder(),
                '.mp3': Mp3FileTypeHolder()
            }

        self.__inconsistent_directories = []
        self.__unknown_errors = []

        # Options
        self.__accepted_extensions = None
        self.__detail_level = None
        self.__output_file = None

    """

    """
    def run(self, library_path, accepted_extensions, detail_level, output_file):
        self.__accepted_extensions = ['.' + s for s in accepted_extensions]
        self.__detail_level = detail_level
        self.__output_file = output_file

        # A quick look ahead in order to report processing status
        n_children_dirs = \
            len([ None for path, dirs, files in os.walk(library_path)])

        print('Root directory contains: {0} folders'.format(n_children_dirs))

        total_processed_dirs = 0
        for path, dirs, files in os.walk(library_path):
            total_processed_dirs += 1

            print("Processing path {1}/{2}\n{0} ".format(path, total_processed_dirs, n_children_dirs))

            if len(files) == 0:
                continue
            else:

                # Directory specific inspection, by examining the first file
                track_path = os.path.join(path, files[0])
                filename, ext = os.path.splitext(track_path)

                if ext not in self.__accepted_extensions:
                    # Here we continue, because we want to report only the invalid directory
                    self.__inconsistent_directories.append((path, 'Unsupported filetype'))
                    continue

                is_consistent = False

                if ext in self.__holders.keys():
                    try:
                        is_consistent, existing, expected = self.__holders[ext].directory_is_consistent(path)
                    except:
                        is_consistent, existing, expected = False, 0, 0
                        self.__unknown_errors.append('Error occured for track {0}'.format(track_path))
                else:
                    continue

                if not is_consistent:
                    self.__inconsistent_directories.append(
                        (path, 'Total tracks not consistent: {0}/{1} '.format(existing, expected)))

            for f in files:
                track_path = os.path.join(path, f)
                filename, ext = os.path.splitext(track_path)

                if ext in self.__holders.keys():
                    try:
                        self.__holders[ext].add_file(track_path)
                    except:
                        self.__unknown_errors.append('Error occured for track {0}'.format(track_path))
                # elif f.endswith('.ogg'):
                #    audio = OggVorbis(track_path)

        with open(self.__output_file, 'w') as f:
            f.write("------------ Stats ------------\n")
            for k, h in self.__holders.items():
                f.write('\nNumber of {0} files: {1}\n'.format(h.name(), h.size()))
                f.write('Bitrate stats:\n' + str(h.get_stats()))
                untagged = h.get_untagged()
                f.write("\nFiles without musicbrainz tag:\n{0}".format('\n'.join('{}: {}'.format(*k) for k in enumerate(untagged))))

            genres_counter = Counter()
            for k, h in self.__holders.items():
                genres_counter += Counter(h.get_genres())

            f.write("\n*****************************************\n")
            f.write("Genres:\n")
            genexp = ((k, genres_counter[ k ]) for k in sorted(genres_counter, key=genres_counter.get, reverse=True))
            for k, v in genexp:
                if not k.isspace() and k is not None:
                    f.write('{0} {1}\n'.format(k, v))

            f.write("\n*****************************************\n")
            f.write("Inconsistent directories:\n{0}".format(
                '\n'.join('{}: {}'.format(*k) for k in enumerate(self.__inconsistent_directories))))

            f.write("\n*****************************************\n")
            f.write("Unknown errors:\n{0}".format(
                '\n'.join('{}: {}'.format(*k) for k in enumerate(self.__unknown_errors))))


LibraryInspector = SingletonDecorator(LibraryInspector)


def main(library_path, output_path):
    config_file = './LibraryInspector.conf'

    inspector = LibraryInspector()
    inspector.run( library_path, ['flac', 'mp3', 'ogg'], 1, output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='An inspector of a music library')
    parser.add_argument('--library_path', nargs='?', required=True, help='The directory which contains the music library.')
    parser.add_argument('--output_path', nargs='?', required=True, help='The filepath to store inspection output')
    args = parser.parse_args()

    main(args.library_path, args.output_path)
