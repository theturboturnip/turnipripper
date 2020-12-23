#a Imports
import re
from pathlib import Path
from .data_class import DataClass, str_add_to_set, str_set_as_list
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
        "num_discs":int,
        "musicbrainz_release_id":str,
        "downloaded_titles":str,
        "downloaded_artists":str,
        "output_title":str,
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
        self.musicbrainz_release_id = ""
        self.num_discs = 0
        self.downloaded_titles = ""
        self.downloaded_artists = ""
        self.postset_title = self.create_output_title
        self.postset_downloaded_titles = self.create_output_title
        self.json_path = Path()
        self.output_title = ""
        self.create_output_title()
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
        pass
    #f add_download_data
    def add_download_data(self, dd:Dict[str, Any]) -> None:
        if "num_discs" in dd: self.num_discs = dd["num_discs"]
        if "title" in dd:  self.downloaded_titles = str_add_to_set(self.downloaded_titles, dd["title"])
        if "artist" in dd: self.downloaded_artists = str_add_to_set(self.downloaded_artists, dd["artist"])
        if "musicbrainz_release_id" in dd: self.musicbrainz_release_id = dd['musicbrainz_release_id']
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
        else:
            self.output_title = "unknown album"
            pass
        pass
    #f All done
    pass

class AlbumFilter:
    order_key : str = ""
    order_keys : ClassVar[Dict[str,str]] = {
        "title":"output_title",
        "id":"uniq_id",
        }
    filter_keys: ClassVar[Dict[str,Tuple[str,str]]] = {
        "title":("re","output_title"),
        "id":   ("re","uniq_id"),
        }
    filters : List[Callable[[Any],bool]]
    def __init__(self) -> None:
        self.filters = []
        self.order_key = ""
        pass
    def order_by(self, order_key:str) -> None:
        if order_key not in self.order_keys:
            raise Exception("Cannot order by {order_key}")
        self.order_key = order_key
        pass
    def add_filter(self, which:str, value:str) -> None:
        if which not in self.filter_keys:
            raise Exception(f"Unknown filter '{which}'")
        (filter_type, attr) = self.filter_keys[which]
        value_re = re.compile(value)
        def re_filter(x:object, attr=attr, value_re=value_re) -> bool:
            return value_re.search(str(getattr(x,attr))) != None
        self.filters.append(re_filter)
        pass
    def apply(self, album:Album) -> Optional[str]:
        for f in self.filters:
            if not f(album): return None
        if self.order_key in self.order_keys:
            return str(getattr(album, self.order_keys[self.order_key]))
        return str(album.uniq_id)
    pass
class AlbumSet:
    things : Dict[UniqueAlbumId,Tuple[Album,str]]
    def __init__(self) -> None:
        self.things = {}
        pass
    def add_if(self, filter:AlbumFilter, album:Album) -> None:
        order_by = filter.apply(album)
        if order_by is not None:
            self.add(album, order_by)
            pass
        pass
    def add(self, album:Album, order_by:str) -> None:
        if album.uniq_id not in self.things:
            self.things[album.uniq_id] = (album, order_by)
            pass
        pass
    def iter_ordered(self) -> Iterable[Album]:
        l = []
        for (k,(album,order_by)) in self.things.items():
            l.append((album,order_by))
            pass
        l.sort(key=lambda x:x[1])
        for (album,order_by) in l:
            yield(album)
            pass
        pass
    pass
