#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import inotify.adapters


class RecordingsPublisher:
    def __init__(self):
        credentials_path = 'local_credentials.txt'
        self.__drive = GoogleDrive(self.__authenticate(credentials_path))

    def __authenticate(self, creds):
        # Snippet from https://stackoverflow.com/questions/24419188/automating-pydrive-verification-process
        gauth = GoogleAuth()
        gauth.LoadCredentialsFile(creds)
        if gauth.credentials is None:
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            gauth.Refresh()
        else:
            gauth.Authorize()
        gauth.SaveCredentialsFile(creds)
        return gauth

    def upload_file(self, filepath):
        def _get_folder_id(file_list, folder_name):
            for f in file_list:
                if f['title'] == folder_name:
                    return f['id']
            return None

        def _get_folder_contents(file_list):
            contents = []
            for f in file_list:
                contents.append(f['title'])
            return contents

        # Find the id of the recordings folder
        root_contents = self.__drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
        recordings_folder_id = _get_folder_id(root_contents, 'recordings')

        # Get a list of the recordings folder contents
        recordings_contents = \
            self.__drive.ListFile({'q': "'{}' in parents and trashed=false".format(recordings_folder_id)}).GetList()
        recordings_contents = _get_folder_contents(recordings_contents)

        # Extract filename from path
        filename = os.path.basename(filepath)

        if filename in recordings_contents:
            print('File already exists in recordings. Aborting upload.')
            return

        # Check if file exists just before upload
        if not os.path.exists(filepath):
            print('File does not exist. Aborting upload.')

        # Create file metadata and upload
        file_meta = {'title': filename, 'parents': [{'kind': 'drive#fileLink', 'id': recordings_folder_id}]}
        f = self.__drive.CreateFile(file_meta)
        f.SetContentFile(filepath)
        f.Upload()

        print('Succesfully uploaded file:{}'.format(filename))


def inotify_loop(recordings_path):
    watch_folder = recordings_path.encode()
    audio_logger_prefix = 'Live-['
    file_ext = '.ogg'

    rec_pub = RecordingsPublisher()

    notifier = inotify.adapters.Inotify()
    notifier.add_watch(watch_folder)

    try:
        for event in notifier.event_gen():
            if event is not None:
                (header, type_names, watch_path, filename) = event
                # Catch creation or rename
                # TODO: Probably there is a better way to omit multiple notifications
                if 'IN_CREATE' in type_names or 'IN_CLOSE_NOWRITE' in type_names \
                        and 'IN_ISDIR' not in type_names:

                    watch_path = watch_path.decode('ascii')
                    filename = filename.decode('ascii')

                    if filename.endswith(file_ext) and not filename.startswith(audio_logger_prefix):
                        path = os.path.join(watch_path, filename)
                        rec_pub.upload_file(path)
                    else:
                        print('Omiting upload for file:{}'.format(filename))
                    print(event)
    finally:
        notifier.remove_watch(watch_folder)


def run_once(filepath):
    rec_pub = RecordingsPublisher()
    rec_pub.upload_file(filepath)


def main():
    # initiate the parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", "-m", help="Set mode. Options: watch, once")
    parser.add_argument("--path", "-p", help="Path for file to be uploaded.")
    parser.add_argument("--recordings-path", "-r", help="Recordings path.")

    # read arguments from the command line
    args = parser.parse_args()

    # check for --width
    if args.mode:
        print("Set mode to %s" % args.mode)

    if args.mode == "watch":
        inotify_loop(args.recordings_path)
    elif args.mode == "once":
        run_once(args.path)
    else:
        raise ValueError("Invalid mode.")


if __name__ == "__main__":
    main()
