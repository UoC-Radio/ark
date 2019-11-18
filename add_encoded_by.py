#!/usr/bin/env python3
import os
import sys
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TENC
from mutagen.flac import FLAC
import argparse
from utils import *

__author__ = "Thanasis Serntedakis"


def count_files(target_path):
    sum = 0
    print(target_path)
    for path, dirs, files in os.walk(target_path):
        sum += len(files)
    return sum


def parent_path(path, target_path):
    newpath = path[len(target_path) + 1:]
    basename = str(os.path.basename(newpath))
    pathlist = newpath.split("/")
    parentname = str(pathlist[0])
    if parentname == basename:
        owner = parentname
    else:
        owner = parentname + " " + basename
    return owner


def mutagen_fun(track_path, track, enc):
    if track.endswith(".mp3"):
        audio = MP3(track_path)
        audio["TENC"] = TENC(encoding=3, text=enc)
        audio.save()
    elif track.endswith(".flac"):
        audio = FLAC(track_path)
        audio["Encoded by"] = enc
        audio.save()
    else:
        bcolors.print('Operation not_supported!', bcolors.WARNING)


def print_progress(file_path, cnt, n_total_files):
    sys.stdout.write(file_path)
    sys.stdout.write("\r %d out of %d \n" % (cnt, n_total_files))
    sys.stdout.flush()


def main(args):
    accepted_files_list = ['mp3', 'wav', 'flac', 'ogg', 'mp4', 'aac']

    cnt = 1
    n_total_files = count_files(args.target_path)
    bcolors.print(n_total_files, bcolors.OKGREEN)
    for path, dirs, files in os.walk(args.target_path):
        enc = args.encoded_by if len(args.encoded_by) > 0 else parent_path(path, args.target_path)
        for f in files:
            file_path = path + "/" + f

            if not f.endswith(tuple(accepted_files_list)):
                print_progress(file_path, cnt, n_total_files)

            mutagen_fun(file_path, f, enc)
            cnt += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Add tag "encoded by" to files in the specified target folder')
    parser.add_argument('--target_path', nargs='?', type=str, default=".",
                        help='The directory to search and put the tag.')
    parser.add_argument('--encoded_by', nargs='?', type=str, default="",
                        help='The name to put to the tag.')
    args = parser.parse_args()
    main(args)
