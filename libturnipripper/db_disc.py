#a Imports
from pathlib import Path
import json
import sqlite3
from .data_class import DataClass, DataClassSet, DataClassFilter, str_add_to_set, str_set_as_list
from .unique_id import UniqueId
from .disc_info import DiscInfo
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
        "cddb_string":str,
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
    json_edit_types = {
        "user":{"album_uniq_id","title","artist","disc_of_set","downloaded_titles","downloaded_artists","tracks"},
        "user_no_tracks":{"album_uniq_id","title","artist","disc_of_set","downloaded_titles","downloaded_artists"},
    }
    data_class_type  = "Disc"
    sql_table_name   = "disc"
    sql_columns      = [
        ("!uniq_id",str),
        ("cddb_id",str),
        ("cddb_string",str),
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
    cddb_string   : str
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
    output_title : str
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
        self.cddb_id      = ""
        self.cddb_string  = ""
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
        self.output_title = ""
        self.postset_num_tracks = self.update_track_list
        self.postset_downloaded_titles = self.create_output_title
        self.postset_title = self.create_output_title
        pass
    #f ui_str
    def ui_str(self) -> str:
        self.create_output_title()
        return f"{self.uniq_id}:'{self.output_title}'"
    #f update_from_disc_info
    def update_from_disc_info(self, disc_info:DiscInfo) -> None:
        self.musicbrainz_id     = disc_info.musicbrainz_id.id_as_str()
        self.musicbrainz_string = disc_info.musicbrainz_id.as_string()
        self.cddb_id            = disc_info.cddb_id.id_as_str()
        self.cddb_string        = disc_info.cddb_id.as_string()
        if self.num_tracks==0:
            self.num_tracks = disc_info.num_tracks
            self.update_track_list()
            pass
        if self.num_tracks == disc_info.num_tracks:
            for i in range(self.num_tracks):
                t=disc_info.tracks[i]
                self.tracks[i].offset = t.lba_offset
                self.tracks[i].sectors = t.lba_extent
                self.tracks[i].length_seconds = (t.lba_extent+74)//75
                pass
            pass
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
            
    #f create_output_title
    def create_output_title(self) -> None:
        if self.title!="":
            self.output_title = self.title
            pass
        elif self.downloaded_titles!="":
            self.output_title = str_set_as_list(self.downloaded_titles)[0]
            pass
        else:
            self.output_title = f"{self.disc_of_set_str()}"
            pass
        pass
    #f get_title
    def get_title(self) -> str:
        self.create_output_title()
        return self.output_title
    #f get_track
    def get_track(self, track:int) -> "Track":
        return self.tracks[track]
    #f iter_metadata
    def iter_metadata(self, track:int) -> Iterable[Tuple[str,str]]:
        metadata = self.tracks[track].get_metadata()
        metadata["album"] = self.output_title
        metadata["album_artist"] = self.artist
        metadata["track"] = f"{track+1}/{self.num_tracks}"
        if self.album is not None and self.album.num_discs>1:
            metadata["disc"] = f"{self.disc_of_set}/{self.album.num_discs}"
            pass
        for (k,v) in metadata.items():
            yield((k,v))
            pass
        pass        
    #f All done
    pass

#c Track
class Track(DataClass):
    #v Properties
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
    uncompressed_filename_fmt : ClassVar[str] = "track{number:02d}.cdda.wav"
    compressed_filename_fmt   : ClassVar[str] = "track{number:02d}.flac"
    encoded_filename_fmt      : ClassVar[str] = "{number:02d} - {title}.{encode_ext}"
    
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
    #f uncompressed_filename
    def uncompressed_filename(self) -> str:
        return self.uncompressed_filename_fmt.format(number=self.number)
    #f compressed_filename
    def compressed_filename(self) -> str:
        return self.compressed_filename_fmt.format(number=self.number)
    #f encoded_filename
    def encoded_filename(self, encode_ext:str) -> str:
        self.create_output_title()
        return self.encoded_filename_fmt.format( encode_ext=encode_ext,
                                                 number =self.number,
                                                 title = self.output_title
        )
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
    #f get_title
    def get_title(self) -> str:
        self.create_output_title()
        return self.output_title
    #f get_metadata
    def get_metadata(self) -> Dict[str,str]:
        self.create_output_title()
        metadata = {"title":self.output_title,
                    "artist":"self.artist",
            }
        return metadata        
    #f __str__
    def __str__(self) -> str:
        r = f"{self.number}:{self.offset}:{self.sectors}:{self.length_seconds}:{self.downloaded_titles}"
        return r
    #f All done
    pass

#c DiscFilter
class DiscFilter(DataClassFilter):
    order_keys = {
        "title":"output_title",
        "id":"uniq_id",
        "cddb":"cddb_id",
        "musicbrainz":"musicbrainz_id",
        }
    filter_keys = {
        "title":("re","output_title"),
        "id":   ("re","uniq_id"),
        "cddb": ("re","cddb_id"),
        "musicbrainz": ("re","musicbrainz_id"),
        }
    pass

#c DiscSet
class DiscSet(DataClassSet):
    pass
