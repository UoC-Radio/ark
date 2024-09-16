import os
from pathlib import Path
import argparse
from collections import namedtuple, defaultdict
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis
from mutagen.id3 import ID3, TENC
from mutagen.flac import FLAC
from mutagen import MutagenError
import pickle
from tqdm import tqdm
import re
import errno
from pathlib import Path
from indexer import TrackIndexer


# https://stackoverflow.com/a/16090640
def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in _nsre.split(s)]


TrackInfo = namedtuple('TrackInfo', ['path', 'track_idx', 'album_id', 'group_id'])


def convert_metadata_entry(t: TrackInfo):
    _, ext = os.path.splitext(t.path)

    try:
        if ext == '.mp3':
            track_idx = int(str(t.track_idx).split('/')[0])
            album_id = str(t.album_id)
            group_id = str(t.group_id)
        else:
            track_idx = int(t.track_idx[0])
            album_id = t.album_id[0]
            if t.group_id != '':
                group_id = t.group_id[0]
            else:
                group_id = ''
    except Exception:
        return None

    return TrackInfo(t.path, track_idx, album_id, group_id)


def get_track_info(track_path):
    def get_info(meta, idx_key, release_key, release_group_key):
        try:
            track_idx = meta[idx_key]
        except KeyError:
            track_idx = ''

        try:
            album_id = meta[release_key]
        except KeyError:
            album_id = ''

        try:
            group_id = meta[release_group_key]
        except KeyError:
            group_id = ''

        return track_idx, album_id, group_id

    filename, ext = os.path.splitext(track_path)
    if ext == '.flac':
        meta = FLAC(track_path)
        track_idx, album_id, group_id = \
            get_info(meta, 'tracknumber', 'musicbrainz_albumid', 'musicbrainz_releasegroupid')
        track_info = TrackInfo(track_path, track_idx, album_id, group_id)
    elif ext == '.mp3':
        meta = ID3(track_path)
        track_idx, album_id, group_id = \
            get_info(meta, 'TRCK', 'TXXX:MusicBrainz Album Id', 'TXXX:MusicBrainz Release Group Id')
        track_info = TrackInfo(track_path, track_idx, album_id, group_id)
    elif ext == '.ogg':
        meta = OggVorbis(track_path)
        track_idx, album_id, group_id = \
            get_info(meta, 'tracknumber', 'musicbrainz_albumid', 'musicbrainz_releasegroupid')
        track_info = TrackInfo(track_path, track_idx, album_id, group_id)
    else:
        assert False

    return track_info


class PlaylistInfo:
    def __init__(self, path):
        self._name = path
        self._found = []
        self._wrong_ext = []
        self._problematic = []
        self._not_found = []
        self._untagged = []

    def add(self, track_path):
        def get_info(meta, idx_key, release_key, release_group_key):
            try:
                track_idx = meta[idx_key]
            except KeyError:
                track_idx = ''

            try:
                album_id = meta[release_key]
            except KeyError:
                album_id = ''

            try:
                group_id = meta[release_group_key]
            except KeyError:
                group_id = ''

            return track_idx, album_id, group_id

        if os.path.exists(track_path):
            filename, ext = os.path.splitext(track_path)
            try:

                if ext == '.flac':
                    meta = FLAC(track_path)
                    track_idx, album_id, group_id = \
                        get_info(meta, 'tracknumber', 'musicbrainz_albumid', 'musicbrainz_releasegroupid')
                elif ext == '.mp3':
                    meta = ID3(track_path)
                    track_idx, album_id, group_id = \
                        get_info(meta, 'TRCK', 'TXXX:MusicBrainz Album Id', 'TXXX:MusicBrainz Release Group Id')
                elif ext == '.ogg':
                    meta = OggVorbis(track_path)
                    track_idx, album_id, group_id = \
                        get_info(meta, 'tracknumber', 'musicbrainz_albumid', 'musicbrainz_releasegroupid')
                else:
                    self._wrong_ext.append(track_path)
                    return

                track_info = TrackInfo(track_path, track_idx, album_id, group_id)
                if track_idx == '' or (album_id == '' and group_id == ''):
                    self._untagged.append(track_info)
                else:
                    self._found.append(track_info)

            except Exception:
                self._problematic.append(track_path)
        else:
            self._not_found.append(track_path)


def get_pls_info(pls_path):
    print('Parsing', pls_path)
    pls_info = PlaylistInfo(pls_path)
    with open(pls_path, encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith('File'):
                line = line.strip('\n')
                tokens = line.split('=')
                pls_info.add(tokens[1])

    return pls_info


def parse_playlists(playlists_path, accepted_extensions):
    playlist_infos = list()
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
                    playlist_infos.append(get_pls_info(file_path))

    #print('Parsed {0} playlists in total.'.format(total_playlists))
    return playlist_infos


def main(playlists_path):
    accepted_extensions = ['.pls']

    playlist_infos = parse_playlists(playlists_path, accepted_extensions)
    pickle.dump(playlist_infos, open('/home/studiouser/track_info/plsinfos-powonly.pkl', 'wb'))
    return
    cases = {'alexis': [], 'makris': [], 'rest': []}
    for song_path in songs_paths_set:
        if not os.path.exists(song_path):
            if '/run/media/alexis' in song_path:
                cases['alexis'].append(song_path)
            elif 'makrisj' in song_path:
                cases['makris'].append(song_path)
            else:
                cases['rest'].append(song_path)

    print(len(cases['alexis']), len(cases['makris']), len(cases['rest']))
    print('\n'.join(cases['rest']))



def track_gen(path):
    for root, dirs, files in os.walk(path):
        for filename in files:
            ext = os.path.splitext(filename)[1]
            if ext in [".mp3", ".ogg", ".flac"]:
                yield os.path.join(root, filename)


def parse_new_library():
    path = '/storage/Library/Sorted'
    all_track_info = []
    for i, track_path in enumerate(tqdm(track_gen(path), total=118643)):
        all_track_info.append(get_track_info(track_path))

        if i > 0 and i % 10000 == 0:
            pickle.dump(all_track_info, open(f'/home/studiouser/track_info/all_track_info_{i}.pkl', 'wb'))
            all_track_info.clear()

    pickle.dump(all_track_info, open(f'/home/studiouser/track_info/all_track_info_last.pkl', 'wb'))


def squeeze(l):
    if isinstance(l, list):
        return ", ".join(str(x) for x in l)
    elif isinstance(l, str):
        return l
    else:
        return ''


def process_new_library():
    data_path = '/home/studiouser/track_info/new_library'

    indexer = TrackIndexer('/home/studiouser/track_info/tracks.db')
    all_track_info = []
    for p in sorted(os.listdir(data_path), key=natural_sort_key):
        infos_path = os.path.join(data_path, p)
        with open(infos_path, 'rb') as f:
            data = pickle.load(f)

        print(f'Processing {p}')
        # fix mp3/vorbis data
        for t in data:
            track_info = convert_metadata_entry(t)
            if track_info:
                all_track_info.append(track_info)
                indexer.add_track(track_info.path, track_info.track_idx, track_info.group_id, track_info.album_id)


# def fix_playlist_infos():
#     plsifno = pickle.load(open('/home/studiouser/track_info/plsinfos.pkl', 'rb'))
#     for playlist in plsifno:
#         playlist._untagged = []
#         found_filtered = []
#         for track in playlist._found:
#             if track.track_idx == '' or (track.album_id == '' and track.group_id == ''):
#                 playlist._untagged.append(track)
#             else:
#                 found_filtered.append(track)
#
#         playlist._found = found_filtered
#
#     pickle.dump(plsifno, open('/home/studiouser/track_info/plsinfos_fixed.pkl', 'wb'))


def associate():
    plsifno = pickle.load(open('/home/studiouser/track_info/plsinfos-powonly.pkl', 'rb'))
    indexer = TrackIndexer('/home/studiouser/track_info/tracks.db')

    not_found = 0
    files_per_playlist = {}
    lost_and_found = []

    for playlist in plsifno:
        playlist_name = os.path.basename(playlist._name)
        playlist_folder = os.path.basename(Path(playlist._name).parent)
        if 'Leaks' in playlist_name or 'Jingles' in playlist_name or 'Spots' in playlist_name:
            continue

        playlist_key = f'{playlist_folder}/{playlist_name}'

        print(f'Processing {playlist_key}')
        files_per_playlist[playlist_key] = []

        for track in tqdm(playlist._found):
            track_info = convert_metadata_entry(track)
            try:
                ret = indexer.get_track(track_info.track_idx, track_info.group_id, track_info.album_id, track_info.path)
                if ret:
                    files_per_playlist[playlist_key].append(ret)
                else:
                    lost_and_found.append((playlist_key, track.path))
            except Exception:
                lost_and_found.append((playlist_key, track.path))


    pickle.dump(files_per_playlist, open('/home/studiouser/track_info/new_playlists-powonly.pkl', 'wb'))
    pickle.dump(lost_and_found, open('/home/studiouser/track_info/lost_and_found-powonly.pkl', 'wb'))


def pls_writer(root_directory, playlist_tag, filepaths):
    lines = [
        '[playlist]\n',
        f'NumberOfEntries={len(filepaths)}\n'
    ]

    for i, p in enumerate(filepaths):
        lines.append(f'File{i+1}={p}\n')

    playlist_filepath = os.path.join(root_directory, playlist_tag)

    if not os.path.exists(os.path.dirname(playlist_filepath)):
        try:
            os.makedirs(os.path.dirname(playlist_filepath))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    with open(playlist_filepath, 'w') as f:
        f.writelines(lines)


def export_playlists():
    files_per_playlist = pickle.load(open('/home/studiouser/track_info/new_playlists-powonly.pkl', 'rb'))

    for tag, filepaths in files_per_playlist.items():
        pls_writer('/storage/Repository/Zones2.0-ws', tag, filepaths)


def pretty_print(name, list):
    if len(list) > 0:
        print(name)
        for e in list:
            if isinstance(e, TrackInfo):
                print(f'\t{e.path}')
            else:
                print(f'\t{e}')


def report_missing(with_leaks=False):
    plsifno = pickle.load(open('/home/studiouser/track_info/plsinfos-powonly.pkl', 'rb'))
    lost_and_found = pickle.load(open('/home/studiouser/track_info/lost_and_found-powonly.pkl', 'rb'))

    print('*** Not Found ***')
    for pls in plsifno:
        if not with_leaks and 'leaks' in pls._name.lower():
            continue
        pretty_print(os.path.basename(pls._name), pls._not_found)
    print('\n\n')

    print('#'*150)

    print('*** Problematic ***')
    for pls in plsifno:
        if not with_leaks and 'leaks' in pls._name.lower():
            continue
        pretty_print(os.path.basename(pls._name), pls._problematic)
    print('\n\n')

    print('#'*150)


    print('*** Wrong extension ***')
    for pls in plsifno:
        if not with_leaks and 'leaks' in pls._name.lower():
            continue
        pretty_print(os.path.basename(pls._name), pls._wrong_ext)
    print('\n\n')

    print('#'*150)

    print('*** Untagged ***')
    for pls in plsifno:
        if not with_leaks and 'leaks' in pls._name.lower():
            continue
        pretty_print(os.path.basename(pls._name), pls._untagged)
    print('\n\n')

    list2paths = defaultdict(list)
    for f in lost_and_found:
        list2paths[f[0]].append(f[1])

    print('#'*150)

    print('*** Not in new Library ***')
    for k, v in list2paths.items():
        print(k)
        for e in sorted(v):
            print(f'\t{e}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Migrate playlists into new library.')
    parser.add_argument('--playlists-path', nargs='?', required=True, help='Zones path')
    args = parser.parse_args()

    # 1.
    #main(args.playlists_path)
    #fix_playlist_infos()
    # 2.
    #parse_new_library()
    #process_new_library()
    #associate()
    #export_playlists()
    report_missing()
