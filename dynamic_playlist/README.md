# Dynamic playlist

The motivation of this tool is to support recorded shows playback in [audio-scheduler](https://github.com/UoC-Radio/audio-scheduler/) which currently does not support it natively. 

The tool takes as argument a playlist filepath and a folder where shows should be placed and pooled along with additional special folders and files. The file structure is expected to be as follows.


```
NameOfTheShow
└── upcoming
    ├── foo.mp3
    ├── bar.flac
    ├── baz.mp3
├── scheduled
    ├── qux.mp3
    ├── quux.flac
    ├── corge.mp3
├── priority.txt
├── ignore (optional)
```

Shows from `upcoming` folder will be pooled at random, except they are found in a priority list. If this is the case they are pooled from there. Show scheduling consists of replacing the filepath in the given playlist file such that audio-scheduler picks this.

The file `priority.txt` should contain the filenames that should be selected out of the random order. For example if the content is the following

```
bar.flac
baz.mp3
```
the tool will select `bar.flac` as the file for the playlist rather than randomly selecting one of the three in `upcoming` folder.

As soon as the tool selects a file it performs the following steps:
1. Moves the file from `upcoming` to `scheduled`
2. Opens the playlist file and replaces the last entry of the file.

Note that is assumed that the real show is found in the last position of the playlist, while previous positions, usually one, contain relevant spots or prologue about the show.

`ignore` is a special file which if encountered the scheduler does not change anything.