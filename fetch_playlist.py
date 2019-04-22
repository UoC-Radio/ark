#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import shutil
import argparse


def main(playlist_path: str, output_path):
    if not playlist_path.endswith('.pls'):
        raise RuntimeError('Only pls filetype is currently supported!')

    if not os.path.exists(output_path):
        os.mkdir(output_path)

    with open(playlist_path) as f:
        lines = f.readlines()

    for l in lines:
        if l.startswith('File'):
            filepath = l[:-1].split('=')[1]
            if os.path.exists(filepath):
                shutil.copy2(filepath, output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Copies files contained in a playlist  to a specified folder.')
    parser.add_argument('--playlist_path', nargs='?', required=True, help='PLS playlist path')
    parser.add_argument('--output_path', nargs='?', required=True, help='Target directory')
    args = parser.parse_args()

    main(args.playlist_path, args.output_path)
