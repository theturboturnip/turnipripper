#a Imports
from pathlib import Path
import hashlib
import base64
import json
from libturnipripper import musicbrainz
from libturnipripper.data_class import DataClass, str_add_to_set, str_set_as_list
from libturnipripper.config import DatabaseConfig
from libturnipripper.unique_id import UniqueId
from libturnipripper.db_album import UniqueAlbumId, Album
import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast
Json = Union[List[Any], Dict[str,Any], str, int]

import sqlite3

#f Useulf functions
def sha1_of(b:bytes) -> str:
    sha1 = hashlib.sha1(b)
    return sha1.hexdigest()

#a Classes
#c UniqueDiscId
class UniqueDiscId(UniqueId):
    class_str = "disc"
    pass

#c Disc
class Disc(DataClass):
    #v Properties
    json_prop_types = {
        "cddb_id":str,
        "num_tracks":int,
        "src_directory":str,
        "album_uniq_id":str,
        "artist":str,
        "title":str,
        "musicbrainz_string":str,
        "musicbrainz_id":str,
        "musicbrainz_release_id":str,
        "total_length":int,
        "disc_of_set":int,
        "downloaded_titles":str,
        "downloaded_artists":str,
        "rip_data":str,
        "rip_date":str,
        "rip_time":str,
        "tracks":None,
        "json_path":None,
    }
    data_class_type  = "Disc"
    sql_table_name   = "disc"
    sql_columns      = [
        ("!uniq_id",str),
        ("cddb_id",str),
        ("num_tracks",int),
        ("src_directory",str),
        ("album_uniq_id",str),
        ("artist",str),
        ("title",str),
        ("musicbrainz_string",str),
        ("musicbrainz_id",str),
        ("musicbrainz_release_id",str),
        ("total_length",int),
        ("disc_of_set",int),
        ("downloaded_titles",str),
        ("downloaded_artists",str),
        ("rip_data",str),
        ("rip_date",str),
        ("rip_time",str),
        ("json_path",str),
        ]
    uniq_id   : UniqueDiscId
    cddb_id       : str
    num_tracks    : int
    src_directory : str
    album_uniq_id : str
    artist        : str
    title         : str
    musicbrainz_string : str
    musicbrainz_id : str
    musicbrainz_release_id : str # Musicbrainz 'release' id (e.g. 211ce24f-6de3-4f3c-a62c-7c3b0eff7569) of the album that this disc is part of), if known
    total_length : int
    disc_of_set  : int
    rip_data : str
    rip_date : str
    rip_time : str
    downloaded_titles : str
    downloaded_artists : str
    album         : Optional[Album]
    tracks        : List["Track"]
    json_path     : Path
    """ Contains info about the data on a CD. """
    #f __init__
    def __init__(self, uniq_id:Optional[UniqueDiscId]=None):
        super().__init__()
        if uniq_id is not None:
            self.uniq_id = uniq_id
            pass
        else:
            self.uniq_id = UniqueDiscId()
            pass
        self.src_directory = ""
        self.album_uniq_id = ""
        self.cddb_id  = ""
        self.num_tracks = 0
        self.total_length = 0
        self.musicbrainz_string = ""
        self.musicbrainz_id = ""
        self.musicbrainz_release_id = ""
        self.artist = ""
        self.title  = ""
        self.disc_of_set = 1
        self.downloaded_artists = ""
        self.downloaded_titles = ""
        self.rip_data = ""
        self.rip_date = ""
        self.rip_time = ""
        self.album = None
        self.tracks = []
        self.json_path = Path()
        self.postset_num_tracks = self.update_track_list
        pass
    #f calculate_cddbid
    def calculate_cddbid(self) -> None:
        track_starts = [t.offset for t in self.tracks]
        csum = sum([sum([int(j) for j in list(str(i//75))]) for i in track_starts]) % 255
        if self.tracks!=[]:
            cd_len = (self.tracks[-1].offset + self.tracks[-1].sectors - self.tracks[0].offset)//75
            pass
        else:
            cd_len = 0
            pass
        print(f"{csum:02x}{cd_len:04x}{len(track_starts):02x} {len(track_starts)}")
        print(" ".join([str(t.offset) for t in self.tracks]))
        # 040cd212 18 150 26015 38464 48627 68170 88165 103005 126862 140072 158965 164937 176260 190682 209952 218515 226970 231152 235790 3284
        print((self.tracks[-1].offset + self.tracks[-1].sectors)//75)
        pass
    #f as_json_json_path
    def as_json_json_path(self, v:Path) -> str:
        return str(v)
    #f from_json_json_path
    def from_json_json_path(self, v:str) -> None:
        self.json_path = Path(v)
        pass
    #f set_json_path
    def set_json_path(self, json_path:Path) -> None:
        self.json_path=json_path
    #f set_album
    def set_album(self, album:Optional[Album]=None) -> None:
        self.album = album
        if album is None:
            self.album_uniq_id = ""
            pass
        else:
            self.album_uniq_id = str(album.uniq_id)
            pass
        pass
    #f update_track_list
    def update_track_list(self) -> None:
        while len(self.tracks)<self.num_tracks:
            self.tracks.append(Track(disc=self, number=1+len(self.tracks)))
            pass
        if len(self.tracks) > self.num_tracks:
            self.tracks = self.tracks[:self.num_tracks]
            pass
        for t in self.tracks:
            t.create_output_title()
            pass
        pass
    #f disc_of_set_str
    def disc_of_set_str(self) -> str:
        if self.album is None: return ""
        if self.album.num_discs==1: return ""
        return f" of disc {self.disc_of_set} of {self.album.num_discs}"
    #f from_json_tracks
    def from_json_tracks(self, json:Json) -> None:
        assert type(json)==list
        json_list = cast(List[Json], json)
        self.tracks = []
        for n in range(len(json_list)):
            track = Track(disc=self, number=n+1)
            track.from_json(json_list[n])
            self.tracks.append(track)
            pass
        for t in self.tracks:
            t.create_output_title()
            pass
        pass
    #f as_json_tracks
    def as_json_tracks(self, tracks:List["Track"]) -> List[Json]:
        tracks_json = []
        for t in tracks:
            tracks_json.append(t.as_json())
            pass
        return tracks_json
    #f sql3_insert_entry
    def sql3_insert_entry(self, sql3_cursor:sqlite3.Cursor) -> None:
        super().sql3_insert_entry(sql3_cursor)
        for t in self.tracks:
            t.sql3_insert_entry(sql3_cursor)
            pass
        pass
    #f add_download_data
    def add_download_data(self, dd:Dict[str, Any]) -> None:
        if "disc_of_set" in dd: self.disc_of_set = dd["disc_of_set"]
        if "title" in dd:  self.downloaded_titles = str_add_to_set(self.downloaded_titles, dd["title"])
        if "artist" in dd: self.downloaded_artists = str_add_to_set(self.downloaded_artists, dd["artist"])
        if "musicbrainz_release_id" in dd: self.musicbrainz_release_id = dd['musicbrainz_release_id']
        pass
    #f add_download_track_data
    def add_download_track_data(self, number:int, dd:Dict[str, Any]) -> None:
        if number==0: return
        if number>self.num_tracks:
            self.num_tracks = number
            self.update_track_list()
            pass
        if self.tracks[number-1].number != number: raise Exception(f"Bad track numbering {number} vs {self.tracks[number-1].number}")
        self.tracks[number-1].add_download_track_data(dd)
        pass
            
    #f All done
    pass

#c Track
class Track(DataClass):
    json_prop_types = {
        "number":int,
        "offset":int,
        "sectors":int,
        "length_seconds":int,
        "title":str,
        "output_title":str,
        "downloaded_titles":str,
        "downloaded_artists":str,
    }
    sql_table_name  = "tracks"
    sql_columns     = [
        ("!disc_uid",str),
        ("!number",int),
        ("offset",int),
        ("sectors",int),
        ("length_seconds",int),
        ("title",str),
        ("output_title",str),
        ("downloaded_titles",str),
        ("downloaded_artists",str),
        ]
    data_class_type = "Track"
    number       : int
    offset       : int # number of sectors from start of disc
    sectors      : int # number of sectors long
    length_seconds : int
    title        : str
    downloaded_titles : str
    downloaded_artists : str
    disc_uid     : UniqueDiscId
    output_title : str
    disc         : Disc
    
    #f __init__
    def __init__(self, disc:Disc, number:int):
        super().__init__()
        self.disc = disc
        self.disc_uid = disc.uniq_id
        self.number = number
        self.offset = 0
        self.sectors = 0
        self.length_seconds = 0
        self.title  = ""
        self.artist = ""
        self.downloaded_titles = ""
        self.downloaded_artists = ""
        self.postset_number = self.create_output_title
        self.output_title = ""
        self.create_output_title()
        pass
    #f add_download_track_data
    def add_download_track_data(self, dd:Dict[str, Any]) -> None:
        if "title" in dd:
            self.downloaded_titles  = str_add_to_set(self.downloaded_titles, dd["title"])
            pass
        if "artist" in dd:
            self.downloaded_artists  = str_add_to_set(self.downloaded_artists, dd["artist"])
            pass
        if "length" in dd:
            self.length_seconds = dd["length"]
            pass
        if "offset" in dd:
            self.offset = dd["offset"]
            pass
        if "sectors" in dd:
            self.sectors = dd["sectors"]
            pass
        self.create_output_title()
        pass
    #f create_output_title
    def create_output_title(self) -> None:
        if self.title!="":
            self.output_title = self.title
            pass
        elif self.downloaded_titles!="":
            self.output_title = str_set_as_list(self.downloaded_titles)[0]
            pass
        elif self.disc is None:
            self.output_title = f"Track {self.number}"
            pass
        else:
            self.output_title = f"Track {self.number} of {self.disc.num_tracks}{self.disc.disc_of_set_str()}"
            pass
        pass
    #f __str__
    def __str__(self) -> str:
        r = f"{self.number}:{self.offset}:{self.sectors}:{self.length_seconds}:{self.downloaded_titles}"
        return r
    #f All done
    pass

#a Database
#c Database
class Database(object):
    albums  : Dict[UniqueAlbumId, Album]
    discs   : Dict[UniqueDiscId, Disc]
    tracks  : Dict[UniqueDiscId, List[Track]]
    #f __init__
    def __init__(self, database_path:Path) -> None:
        self.database_path = database_path
        self.albums = {}
        self.discs = {}
        self.tracks = {}
        pass
    #f from_config
    @classmethod
    def from_config(cls, config:DatabaseConfig) -> "Database":
        db = cls(database_path=config.root)
        if config.primary=="json":
            for json_glob in config.json_paths:
                db.read_json_files(json_glob)
                pass
            pass
        else:
            if config.dbfile is None: raise Exception("Database has a primary of sqlite but no dbfile")
            db.read_sqlite3(db_path=config.dbfile)
            pass
        return db
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
        db_path = self.database_path.joinpath(db_path)
        print(f"Reading sqlite3 database {db_path}")
        sql3_conn   = sqlite3.connect(str(db_path))
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
    def read_json_files(self, pattern:str, subpaths:List[str]=[], verbose:bool=False) -> None:
        base_path = self.database_path.joinpath(*subpaths)
        for p in base_path.glob(pattern):
            if verbose:print(p)
            with p.open() as f:
                json_data = json.load(f)
                self.add_json(p, json_data)
                pass
            pass
        pass
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
    def enumerate_json_paths(self, root_path:Path) -> Dict[str,Tuple[Path,List[UniqueAlbumId],List[UniqueDiscId]]]:
        """
        Run through the database and find all the json paths required to write out
        If a json path is effectively none (".") then put it in library.json?
        """
        json_files : Dict[str,Tuple[Path,List[UniqueAlbumId],List[UniqueDiscId]]] = {}
        str_root_path = str(root_path)
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
    def write_json_files(self, root_path:Path) -> None:
        """
        Write out all changed json files
        """
        json_files = self.enumerate_json_paths(root_path)
        for (s,(path,album_ids,disc_ids)) in json_files.items():
            json_data = {"albums":self.albums_as_json(album_ids),
                         "discs" :self.discs_as_json(disc_ids),
            }
            json_str = json.dumps(json_data, indent=1).encode("utf8")
            must_write = True
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
    #f find_disc_of_musicbrainz_id
    def find_disc_of_musicbrainz_id(self, musicbrainz_id:str) -> Optional[Disc]:
        for (k,v) in self.discs.items():
            if v.musicbrainz_id == musicbrainz_id:
                return v
            pass
        return None
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
        mb = musicbrainz.MusicbrainzRecordings.of_query(disc.musicbrainz_id)
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
    #f All done
    pass

