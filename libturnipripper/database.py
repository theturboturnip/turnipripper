#a Imports
from pathlib import Path
import hashlib
import base64
import json
import sqlite3
from .data_class import DataClass, str_add_to_set, str_set_as_list
from .disc_info import DiscInfo
from .config import DatabaseConfig
from .db_album import UniqueAlbumId, Album
from .db_disc import UniqueDiscId, Disc, Track
from .musicbrainz import MusicbrainzRecordings

from .db_types import *
import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast


#f Useful functions
def sha1_of(b:bytes) -> str:
    sha1 = hashlib.sha1(b)
    return sha1.hexdigest()

#a Database
#c Exceptions
class DatabaseOpenError(Exception): pass
class DatabaseConfigError(Exception): pass
#c Database
class Database(object):
    config : DatabaseConfig
    albums  : Dict[UniqueAlbumId, Album]
    discs   : Dict[UniqueDiscId, Disc]
    tracks  : Dict[UniqueDiscId, List[Track]]
    #f __init__
    def __init__(self, config:DatabaseConfig) -> None:
        self.config = config
        self.albums = {}
        self.discs = {}
        self.tracks = {}
        pass
    #f from_config
    @classmethod
    def from_config(cls, config:DatabaseConfig) -> "Database":
        db = cls(config)
        if config.primary_is_json():
            files_read = 0
            for json_glob in config.json_paths:
                files_read += db.read_json_files(json_glob)
                pass
            if files_read==0:
                raise DatabaseOpenError("No database json files could be read")
            pass
        else:
            if config.dbfile is None: raise DatabaseConfigError("Database has a primary of sqlite but no dbfile")
            db.read_sqlite3(db_path=db.joinpath(config.dbfile))
            pass
        return db
    #f joinpath
    def joinpath(self, *paths:Any) -> Path:
        return self.config.root.joinpath(*paths)
    #f create_sqlite3
    def create_sqlite3(self, db_path:Path) -> None:
        sql3_conn   = sqlite3.connect(str(db_path))
        sql3_cursor = sql3_conn.cursor()
        Album.sql3_create_table(sql3_cursor)
        Disc.sql3_create_table(sql3_cursor)
        Track.sql3_create_table(sql3_cursor)
        sql3_conn.commit()
        sql3_conn.close()
        self.update_sqlite3(db_path)
        pass
    #f update_sqlite3
    def update_sqlite3(self, db_path:Path) -> None:
        sql3_conn   = sqlite3.connect(str(db_path))
        sql3_cursor = sql3_conn.cursor()
        for album_uid, album in self.iter_albums():
            album.sql3_insert_entry(sql3_cursor)
            pass
        sql3_conn.commit()
        for disc_uid, disc in self.iter_discs():
            disc.sql3_insert_entry(sql3_cursor) # will insert entries to the track database
            pass
        sql3_conn.commit()
        sql3_conn.close()
        pass
    #f read_sqlite3
    def read_sqlite3(self, db_path:Path) -> None:
        print(f"Reading sqlite3 database {db_path}")
        try:
            sql3_conn   = sqlite3.connect(str(db_path))
            pass
        except Exception as e:
            raise DatabaseOpenError(f"Failed to open sql database {db_path} with {e}")
            pass
        sql3_cursor = sql3_conn.cursor()
        for d in Album.sql3_iter_entries(sql3_cursor):
            album_id_str = d["uniq_id"]
            del d["uniq_id"]
            album = self.find_or_create_album(album_id_str, permit_duplicates=False)
            album.from_json(d)
            pass
        sql3_conn.commit()
        for d in Disc.sql3_iter_entries(sql3_cursor):
            disc_id_str = d["uniq_id"]
            del d["uniq_id"]
            disc = self.find_or_create_disc(disc_id_str, permit_duplicates=False)
            disc.from_json(d)
            pass
        for t in Track.sql3_iter_entries(sql3_cursor):
            t_disc_id_str = t["disc_uid"]
            del t["disc_uid"]
            t_disc = self.find_disc_id(t_disc_id_str)
            if t_disc is None: raise Exception("Unknown disc id for track")
            t_disc.tracks[t["number"]-1].from_json(t)
            pass
        sql3_conn.commit()
        sql3_conn.close()
        pass
    #f read_json_files
    def read_json_files(self, pattern:str, subpaths:List[str]=[], verbose:bool=False) -> int:
        files_read = 0
        base_path = self.joinpath(*subpaths)
        for p in base_path.glob(pattern):
            if verbose:print(p)
            with p.open() as f:
                json_data = json.load(f)
                self.add_json(p, json_data)
                files_read += 1
                pass
            pass
        return files_read
    #f create_album
    def create_album(self, uniq_id_str:str) -> Album:
        uniq_id = UniqueAlbumId.from_str(uniq_id_str)
        album = Album(uniq_id=uniq_id)
        self.albums[uniq_id] = album
        return album
    #f create_disc
    def create_disc(self, uniq_id_str:str) -> Disc:
        uniq_id = UniqueDiscId.from_str(uniq_id_str)
        disc = Disc(uniq_id=uniq_id)
        self.discs[uniq_id] = disc
        return disc
    #f find_or_create_album
    def find_or_create_album(self, album_id_str:str, permit_duplicates:bool) -> Album:
        album = self.find_album_id(album_id_str)
        if album is not None and not permit_duplicates:
            raise Exception(f"Duplicate album id {album_id_str} in database")
        if album is None: album = self.create_album(album_id_str)
        return album
    #f find_or_create_disc
    def find_or_create_disc(self, disc_id_str:str, permit_duplicates:bool) -> Disc:
        disc = self.find_disc_id(disc_id_str)
        if disc is not None and not permit_duplicates:
            raise Exception(f"Duplicate disc id {disc_id_str} in database")
        if disc is None: disc = self.create_disc(disc_id_str)
        return disc
    #f add_json
    def add_json(self, json_path:Path, json:Json, permit_duplicates:bool=False) -> None:
        assert type(json)==dict
        json_dict = cast(Dict[str,Any], json)
        if "albums" in json_dict:
            for (k,v) in json_dict["albums"].items():
                album = self.find_or_create_album(k, permit_duplicates=permit_duplicates)
                album.from_json(v)
                album.set_json_path(json_path)
                pass
            pass
        if "discs" in json_dict:
            for (k,v) in json_dict["discs"].items():
                disc = self.find_or_create_disc(k, permit_duplicates=permit_duplicates)
                disc.from_json(v)
                disc.set_json_path(json_path)
                disc_album = self.album_of_disc(disc)
                disc.set_album(disc_album)
                pass
            pass
        pass
    #f albums_as_json
    def albums_as_json(self, album_ids:List[UniqueAlbumId]) -> Json:
        result = {}
        album_ids.sort()
        for album_id in album_ids:
            v = self.albums[album_id]
            k = str(album_id)
            result[k] = v.as_json()
            pass
        return result
    #f discs_as_json
    def discs_as_json(self, disc_ids:List[UniqueDiscId]) -> Json:
        disc_ids.sort()
        result = {}
        for disc_id in disc_ids:
            v = self.discs[disc_id]
            k = str(disc_id)
            result[k] = v.as_json()
            pass
        return result
    #f iter_albums
    def iter_albums(self) -> Iterable[Tuple[UniqueAlbumId, Album]]:
        for (k,v) in self.albums.items():
            yield(k,v)
            pass
        pass
    #f iter_discs
    def iter_discs(self) -> Iterable[Tuple[UniqueDiscId, Disc]]:
        for (k,v) in self.discs.items():
            yield(k,v)
            pass
        pass
    #f enumerate_json_paths
    def enumerate_json_paths(self, root_path:Path, must_use_root:bool=False) -> Dict[str,Tuple[Path,List[UniqueAlbumId],List[UniqueDiscId]]]:
        """
        Run through the database and find all the json paths required to write out
        If a json path is effectively none (".") then put it in library.json?
        """
        json_files : Dict[str,Tuple[Path,List[UniqueAlbumId],List[UniqueDiscId]]] = {}
        str_root_path = str(root_path)
        if must_use_root:
            json_files[str_root_path] = (root_path, [], [])
            pass
        p = Path()
        str_p = str(p)
        for (album_id, album) in self.iter_albums():
            path = album.json_path
            s = str(path)
            if s==str_p: (s,path) = (str_root_path, root_path)
            if s not in json_files: json_files[s] = (path, [],[])
            json_files[s][1].append(album_id)
            pass
        for (disc_id, disc) in self.iter_discs():
            path = disc.json_path
            s = str(path)
            if s==str_p: (s,path) = (str_root_path, root_path)
            if s not in json_files: json_files[s] = (path, [],[])
            json_files[s][2].append(disc_id)
            pass
        return json_files
    #f write_json_files
    def write_json_files(self, root_path:Path, must_use_root:bool=False) -> None:
        """
        Write out all changed json files
        """
        json_files = self.enumerate_json_paths(root_path, must_use_root)
        for (s,(path,album_ids,disc_ids)) in json_files.items():
            json_data = {"albums":self.albums_as_json(album_ids),
                         "discs" :self.discs_as_json(disc_ids),
            }
            json_str = json.dumps(json_data, indent=1).encode("utf8")
            must_write = True
            path = self.joinpath(path)
            if path.is_file():
                json_hash = sha1_of(json_str)
                with path.open("rb") as f:
                    file_hash = sha1_of(f.read())
                    pass
                if json_hash==file_hash: must_write=False
                pass
            if must_write:
                print(f"Must write {path} as its data is modified")
                with path.open("wb") as f:
                    f.write(json_str)
                    pass
                pass
            else:
                print(f"Not writing {path} as its data is unmodified")
                pass
            pass
        pass
    #f as_single_json
    def as_single_json(self) -> Json:
        result = {"albums":self.albums_as_json(list(self.albums.keys())),
                  "discs":self.discs_as_json(list(self.discs.keys())),
                  }
        return result
    #f find_album_id
    def find_album_id(self, album_id:str) -> Optional[Album]:
        for (k,v) in self.albums.items():
            if k.matches_uniq_id_str(album_id): return v
        return None
    #f find_album_of_musicbrainz_release_id
    def find_album_of_musicbrainz_release_id(self, musicbrainz_release_id:str) -> Optional[Album]:
        for (k,v) in self.albums.items():
            if v.musicbrainz_release_id == musicbrainz_release_id:
                return v
            pass
        return None
    #f discs_with_musicbrainz_id
    def discs_with_musicbrainz_id(self, musicbrainz_id:str) -> Iterable[Disc]:
        for (k,v) in self.discs.items():
            if v.musicbrainz_id == musicbrainz_id:
                yield v
            pass
        pass
    #f discs_with_cddb_id
    def discs_with_cddb_id(self, cddb_id:str) -> Iterable[Disc]:
        for (k,v) in self.discs.items():
            if v.cddb_id == cddb_id:
                yield v
            pass
        pass
    #f find_disc_id
    def find_disc_id(self, disc_id:str) -> Optional[Disc]:
        for (k,v) in self.discs.items():
            if k.matches_uniq_id_str(disc_id): return v
        return None
    #f album_of_disc
    def album_of_disc(self, disc:Disc) -> Optional[Album]:
        album = disc.album
        if album is None and (disc.album_uniq_id != ""):
            album = self.find_album_id(disc.album_uniq_id)
            pass
        if album is None and (disc.musicbrainz_release_id!=""):
            album = self.find_album_of_musicbrainz_release_id(disc.musicbrainz_release_id)
            pass
        return album
    #f fetch_mb_disc_data
    def fetch_mb_disc_data(self, disc:Optional[Disc]=None, disc_id:Optional[str]=None) -> bool:
        if disc is None and disc_id is not None:
            disc = self.find_disc_id(disc_id)
            pass
        if disc is None: return False
        if disc.musicbrainz_id=="": return False
        try:
            mb = MusicbrainzRecordings.of_query(disc.musicbrainz_id)
            pass
        except:
            return False
        pressing = mb.find_pressing(disc.musicbrainz_id)
        if pressing is None: return False
        for (number,dd) in pressing.iter_download_track_data():
            disc.add_download_track_data(number, dd)
            pass
        disc.add_download_data(pressing.get_media_download_data())
        disc.add_download_data(pressing.get_release_download_data())
        album = self.album_of_disc(disc)
        if album is None: album = self.create_album(disc.album_uniq_id)
        album.add_download_data(pressing.get_album_download_data())
        disc.set_album(album)
        return True
    #f find_discs_of_disc_info
    def find_discs_of_disc_info(self, disc_info:DiscInfo) -> List[Disc]:
        disc_uids = set()
        mb_id = disc_info.musicbrainz_id.mb_id
        cddb_id = disc_info.cddb_id.cddb_id
        if mb_id!="":
            for d in self.discs_with_musicbrainz_id(mb_id):
                disc_uids.add(d.uniq_id)
                pass
            pass
        if cddb_id!="":
            for d in self.discs_with_cddb_id(cddb_id):
                disc_uids.add(d.uniq_id)
                pass
            pass
        discs = []
        for uid in disc_uids:
            discs.append(self.discs[uid])
            pass
        return discs
    #f find_or_create_disc_of_disc_info
    def find_or_create_disc_of_disc_info(self, disc_info:DiscInfo, src_directory:Path) -> Tuple[int,Optional[Disc]]:
        discs = self.find_discs_of_disc_info(disc_info)
        for d in discs:
            if d.src_directory == str(src_directory):
                return (-1,d)
            pass
        return (len(discs),None)
    #f All done
    pass

