#a Imports
from pathlib import Path
from .data_class import DataClass, str_add_to_set, str_set_as_list
from .unique_id import UniqueId

import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast

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
        "num_discs":int,
        "musicbrainz_release_id":str,
        "downloaded_titles":str,
        "downloaded_artists":str,
        "json_path":None
    }
    sql_columns     : ClassVar[List[Tuple[str,type]]] = [
        ("!uniq_id",str),
        ("label",str),
        ("artist",str),
        ("title",str),
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
    num_discs : int
    musicbrainz_release_id:str # Should be a unique value for each album, but might not be
    downloaded_titles : str
    downloaded_artists : str
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
        self.musicbrainz_release_id = ""
        self.num_discs = 0
        self.downloaded_titles = ""
        self.downloaded_artists = ""
        self.json_path = Path()
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
    #f add_download_data
    def add_download_data(self, dd:Dict[str, Any]) -> None:
        if "num_discs" in dd: self.num_discs = dd["num_discs"]
        if "title" in dd:  self.downloaded_titles = str_add_to_set(self.downloaded_titles, dd["title"])
        if "artist" in dd: self.downloaded_artists = str_add_to_set(self.downloaded_artists, dd["artist"])
        if "musicbrainz_release_id" in dd: self.musicbrainz_release_id = dd['musicbrainz_release_id']
        pass
    pass

