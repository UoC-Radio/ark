import sqlite3
from sqlite3 import Error
from threading import Lock
import os
from fuzzywuzzy import fuzz

class TrackIndexer(object):
    def __init__(self, dbfile):
        self.db_handle = None
        self.lock = Lock()

        self.db_handle = sqlite3.connect(dbfile, check_same_thread=False)

        try:
            cur = self.db_handle.cursor()
            cur.execute(
                "CREATE TABLE IF NOT EXISTS tracks (id INTEGER PRIMARY KEY, path TEXT,track_idx INTEGER(32),releasegroup_id TEXT,album_id TEXT)")
            self.db_handle.commit()
        except Error as e:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.db_handle is not None:
            self.db_handle.close()
        del self.db_handle
        return True

    def add_track(self, path, index, releasegroup_id, album_id):
        # Check if album exists
        exists = False

        cur = self.db_handle.cursor()
        query = "SELECT path FROM tracks WHERE path = ?"
        args = (path,)
        cur.execute(query, args)
        results = cur.fetchall()
        for result in results:
            if result[0] == path:
                print('Track already exists on database')
                exists = True

        results.clear()
        del cur, query, args, results

        if exists is True:
            return

        # We need to serialize access to the db to avoid corruption
        self.lock.acquire()

        cur = self.db_handle.cursor()
        query = "INSERT INTO tracks(path, track_idx, releasegroup_id, album_id) VALUES(?, ?, ?, ?)"
        args = (path, index, releasegroup_id, album_id)
        cur.execute(query, args)
        self.db_handle.commit()
        del cur, query, args

        self.lock.release()
        #print("Track added to database")

    def get_track(self, index, releasegroup_id, album_id, filepath):
        cur = self.db_handle.cursor()
        query = "SELECT path FROM tracks WHERE track_idx = ? AND (releasegroup_id = ? OR album_id = ?)"
        args = (index, releasegroup_id, album_id)
        cur.execute(query, args)
        results = cur.fetchall()

        if len(results) == 1:
            return results[0][0]
        elif len(results) == 0:
            return None
        else:
            # Two disks case
            query_filename = os.path.basename(filepath)
            scores = []
            for r in results:
                filename = os.path.basename(r[0])
                scores.append(fuzz.ratio(filename.lower(), query_filename.lower()))

            ret = results[scores.index(max(scores))][0]
            return ret