#a Imports
import re
from pathlib import Path
from .data_class import DataClass, DataClassFilter, DataClassSet, str_add_to_set, str_set_as_list
from .unique_id import UniqueId

import typing
from typing import Callable, Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast

#a Classes
#c UniqueAlbumId
class UniqueAlbumId(UniqueId):
    class_str = "alb"
    pass

#c Album
class Album(DataClass):
    #v Properties
    json_prop_types = {
        "label":str,
        "artist":str,
        "title":str,
        "genre":str,
        "num_discs":int,
        "musicbrainz_release_id":str,
        "downloaded_titles":str,
        "downloaded_artists":str,
        "output_title":str,
        "json_path":None
    }
    json_edit_types = {
        "user":{"label","title","artist","num_discs","downloaded_titles","downloaded_artists"},
    }
    sql_columns     : ClassVar[List[Tuple[str,type]]] = [
        ("!uniq_id",str),
        ("label",str),
        ("artist",str),
        ("title",str),
        ("genre",str),
        ("num_discs",int),
        ("musicbrainz_release_id",str),
        ("downloaded_titles",str),
        ("downloaded_artists",str),
        ("json_path",str),
    ]
    data_class_type = "Album"
    sql_table_name  = "album"
    uniq_id   : UniqueAlbumId
    label     : str
    artist    : str
    title     : str
    genre     : str
    num_discs : int
    discs     : Dict[int, int]
    disc_offsets : List[int]
    musicbrainz_release_id:str # Should be a unique value for each album, but might not be
    downloaded_titles : str
    downloaded_artists : str
    output_title : str
    json_path : Path
    #f __init__
    def __init__(self, uniq_id:Optional[UniqueAlbumId]=None):
        super().__init__()
        if uniq_id is not None:
            self.uniq_id = uniq_id
            pass
        else:
            self.uniq_id = UniqueAlbumId()
            pass
        self.label = ""
        self.artist = ""
        self.title = ""
        self.genre = ""
        self.musicbrainz_release_id = ""
        self.num_discs = 0
        self.discs = {}
        self.disc_offsets = []
        self.downloaded_titles = ""
        self.downloaded_artists = ""
        self.postset_title = self.create_outputs
        self.postset_downloaded_titles = self.create_outputs
        self.postset_artists = self.create_outputs
        self.postset_downloaded_artists = self.create_outputs
        self.json_path = Path()
        self.output_title = ""
        self.create_outputs()
        pass
    #f add_disc
    def add_disc(self, disc:Any, disc_of_set:int, num_tracks:int) -> None:
        if disc_of_set in self.discs:
            print(f"Duplicate disc of set {disc_of_set} for album {self.uniq_id}; new is {disc.uniq_id}")
            pass
        self.discs[disc_of_set] = num_tracks
        pass
    #f resolve_data
    def resolve_data(self) -> None:
        self.disc_offsets = []
        k = list(self.discs.keys())
        k.sort()
        last = 0
        while k != []:
            disc_of_set = k.pop(0)
            while disc_of_set > len(self.disc_offsets):
                self.disc_offsets.append(last)
                pass
            if disc_of_set == len(self.disc_offsets):
                last += self.discs[disc_of_set]
                self.disc_offsets.append(last)
                pass
            pass
        # print(f"Resolve album {self.uniq_id}, {self.disc_offsets}")
        self.create_outputs()
        pass
    #f track_offset_and_total
    def track_offset_and_total(self, disc_of_set:int) -> Optional[Tuple[int, int]]:
        if (disc_of_set > 0) and (disc_of_set < len(self.disc_offsets)):
            return (self.disc_offsets[disc_of_set-1], self.disc_offsets[-1])
        return None
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
        pass
    #f add_download_data
    def add_download_data(self, dd:Dict[str, Any]) -> None:
        if "num_discs" in dd: self.num_discs = dd["num_discs"]
        if "title" in dd:  self.downloaded_titles = str_add_to_set(self.downloaded_titles, dd["title"])
        if "artist" in dd: self.downloaded_artists = str_add_to_set(self.downloaded_artists, dd["artist"])
        if "musicbrainz_release_id" in dd: self.musicbrainz_release_id = dd['musicbrainz_release_id']
        self.create_outputs()
        pass
    #f create_outputs
    def create_outputs(self) -> None:
        if self.title!="":
            self.output_title = self.title
            pass
        elif self.downloaded_titles!="":
            self.output_title = str_set_as_list(self.downloaded_titles)[0]
            pass
        else:
            self.output_title = "unknown album"
            pass
        if self.artist!="":
            self.output_artist = self.artist
            pass
        elif self.downloaded_artists!="":
            self.output_artist = str_set_as_list(self.downloaded_artists)[0]
            pass
        else:
            self.output_artist = f"Unknown artist"
            pass
        pass
    #f All done
    pass

#c AlbumFilter
class AlbumFilter(DataClassFilter):
    order_keys = {
        "title":"output_title",
        "genre":"genre",
        "id":"uniq_id",
        "musicbrainz":"musicbrainz_release_id",
        }
    filter_keys = {
        "title":("re","output_title"),
        "genre":   ("re","genre"),
        "id":   ("re","uniq_id"),
        "musicbrainz":("re","musicbrainz_release_id"),
        }
    pass

#c AlbumSet
class AlbumSet(DataClassSet):
    pass
