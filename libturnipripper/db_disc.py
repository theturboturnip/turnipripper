#a Imports
from pathlib import Path
import json
import sqlite3
from .data_class import DataClass, str_add_to_set, str_set_as_list
from .unique_id import UniqueId
from .db_album import Album

from .db_types import *
import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast

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

