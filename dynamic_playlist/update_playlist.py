from pathlib import Path
import os
import json
import xml
import xml.etree.ElementTree as ET
from enum import Enum
import random
from dataclasses import dataclass
from typing import Optional
import shlex
import subprocess

def find_scheduled_times(schedule_path, playlist_path):
    scheduled_times = []

    tree = ET.parse(schedule_path)
    root = tree.getroot()

    for i, child in enumerate(root):
        for e in child:
            current_main_playlist_path = e.find('./Main/Path').text
            if playlist_path == current_main_playlist_path:
                scheduled_times.append((i, e.attrib['Start']))

    return scheduled_times


class SelectionPolicy(Enum):
    RANDOM = 1
    DATETIME_NEWER = 2
    DATETIME_OLDER = 3


@dataclass
class ShowSource:
    local_source: Optional[str]
    online_source: Optional[str]


class ShowScheduler:
    def __init__(self,
                 show_root_directory,
                 playlist_path,
                 shows_source: ShowSource,
                 selection_policy: SelectionPolicy = SelectionPolicy.RANDOM):
        """

        :param show_root_directory: The directory of the show under (inside DynamicShowsRoot directory)
        :param playlist_path: The path to the playlist which corresponds to the show (which will be updated)
        :param shows_source: The source(s) from which new shows are populated
        :param selection_policy: Policy about which show to select from the upcoming folder. Maybe overridden if
                                    priority file is not empty.
        """
        self._show_root_directory = Path(show_root_directory)
        self._playlist_path = Path(playlist_path)
        self._shows_source = shows_source
        self._selection_policy = selection_policy

        self._upcoming_dir = self._show_root_directory / 'upcoming'
        self._scheduled_dir = self._show_root_directory / 'scheduled'
        self._priority_filepath = self._show_root_directory / 'priority.txt'
        self._check_directory_integrity()

    def _check_directory_integrity(self):
        if not self._show_root_directory.exists():
            raise FileNotFoundError('Show root directory does not exist')

        if not self._playlist_path.exists():
            raise FileNotFoundError('Playlist path does not exist')

        directory_is_ok = (self._upcoming_dir.is_dir() and self._scheduled_dir.is_dir() and
                           self._priority_filepath.is_file())

        if not directory_is_ok:
            raise AssertionError('Directory has no proper structure')

    def _choose_show_from_available(self, upcoming_files) -> Path:
        match self._selection_policy:
            case SelectionPolicy.RANDOM:
                return random.choice(upcoming_files)
            case SelectionPolicy.DATETIME_NEWER:
                return Path(sorted(upcoming_files, key=os.path.getmtime, reverse=True)[0])
            case SelectionPolicy.DATETIME_OLDER:
                return Path(sorted(upcoming_files, key=os.path.getmtime, reverse=False)[0])
            case _:
                raise AssertionError

    def _update_pls(self, show_path):
        with open(self._playlist_path, 'r') as f:
            pls_lines = f.readlines()

        # Change the last entry to the path of the new show
        for i, l in enumerate(pls_lines[::-1]):
            if l.startswith('File'):
                file_label, _ = l.split('=', maxsplit=1)
                pls_lines[-(i + 1)] = f'{file_label}={show_path}'

                with open(self._playlist_path, 'w') as f:
                    f.writelines(pls_lines)

                break
        else:
            raise AssertionError('Invalid pls file')

    def choose_show(self):
        with open(self._priority_filepath, 'r') as f:
            show_files = [show_file[:-1].strip() for show_file in f.readlines()]

        upcoming_files = [f for f in self._upcoming_dir.iterdir()]
        upcoming_files_names = [f.name for f in upcoming_files]

        if len(upcoming_files) == 0:
            print('No available file. Doing nothing.')
            return
        else:
            print('Available files:')
            print('\n'.join(upcoming_files_names))

        # Check for existence is priority files
        if len(show_files) > 0 and show_files[0] in upcoming_files_names:
            show_file = show_files[0]

            # Remove the path from the priority file
            show_files = [show_file + '\n' for show_file in show_files[1:]]
            with open(self._priority_filepath, 'w') as f:
                f.writelines(show_files)
        else:
            show_file = self._choose_show_from_available(upcoming_files).name

        # Move the file to scheduled directory
        original_path = self._upcoming_dir / show_file
        new_path = self._scheduled_dir / show_file
        original_path.rename(new_path)

        # Update the last file of the pls to the newly scheduled show
        if new_path.exists():
            self._update_pls(new_path)

    def _populate_shows(self):
        def populate_from_online_source(local_source, online_source):
            if not local_source.is_dir():
                print('Invalid local path for downloading available shows.')
                return

            # For now I assume that it is a playlist that yt-dlp can handle and latest show is the first playlist item
            cmd = f'yt-dlp {online_source} --playlist-items 1 -o {str(local_source)}/%(title)s.%(ext)s'
            args = shlex.split(cmd)
            # TODO: Check output
            subprocess.run(args)

        def populate_from_local_source(local_source):
            if not local_source.is_dir():
                print('Invalid local path for populating shows.')
                return

            # Populated shows are the concatenation of upcoming + scheduled
            # We assume unique filenames
            populated_shows = set([p.name for p in self._upcoming_dir.iterdir()] +
                                  [p.name for p in self._scheduled_dir.iterdir()])

            all_shows_dict = {p.name: p for p in local_source.rglob('*') if p.is_file()}

            new_shows = all_shows_dict.keys() - populated_shows

            # Create symbolic links from each new show to the upcoming directory
            for show_filename in new_shows:
                (self._upcoming_dir / show_filename).symlink_to(all_shows_dict[show_filename])

        online_source = self._shows_source.online_source
        local_source = Path(self._shows_source.local_source)

        # Populate shows from online source to local source
        if online_source is not None:
            populate_from_online_source()

        # Populate shows from local source to upcoming directory
        if local_source is not None:
            populate_from_local_source()


show_root_directory = '/storage/Repository/Zones2.0/SHOWS/DynamicShowsRoot/Loskop'
show_playlist_path = '/storage/Repository/Zones2.0/CONTEMPORARY/kolaz.pls'
show_source = ShowSource(online_source=None, local_source='/storage/Library/Unsorted/Loskop')
show_scheduler = ShowScheduler(show_root_directory, show_playlist_path, show_source)

# schedule_path = '../.test/schedule.xml'
# show_playlist_path = '/storage/Repository/Zones2.0/CONTEMPORARY/ExpDM.pls'
# scheduled_times = find_scheduled_times(schedule_path, show_playlist_path)
# print(scheduled_times)
