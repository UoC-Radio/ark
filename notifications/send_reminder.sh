#!/bin/bash
export PATH="/home/radio/local_bin/pypy3.3-5.5-alpha-20161014-linux_i686-portable/bin:$PATH"
export PYTHONIOENCODING=utf-8

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
python "$DIR/meeting_reminder.py"


