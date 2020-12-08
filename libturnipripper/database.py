#a Imports
import os.path
import hashlib
import base64
import json
from libturnipripper import musicbrainz
from libturnipripper.data_class import DataClass, str_add_to_set

import typing
from typing import Optional, ClassVar, TypeVar, Type, Union, List, Dict, Set, Any, cast
Json = Union[List[Any], Dict[str,Any], str, int]

#a Classes
#c UniqueId
T = TypeVar('T', bound='UniqueId')
class UniqueId:
    class_str: ClassVar[str] = ""
    class_last : ClassVar[int] = 0
    uniq_id : int = 0
    uniq_str : str
    @classmethod
    def update_last(cls, uniq_id:int) -> None:
        if uniq_id <= cls.class_last: cls.class_last = uniq_id+1
        pass
    @classmethod
    def get_next(cls) -> int:
        n = cls.class_last
        cls.update_last(n)
        return n
    def __init__(self, uniq_id:Optional[int]=None, uniq_str:Optional[str]=None) -> None:
        if uniq_str is not None:
            self.uniq_str = uniq_str
            self.uniq_id = -1
            pass
        elif uniq_id is not None:
            self.uniq_id = uniq_id
            self.update_last(uniq_id)
            pass
        else:
            self.uniq_id = self.get_next()
            pass
        if self.uniq_id>=0:
            self.uniq_str = f"{self.class_str}.{self.uniq_id:04d}"
            pass
        pass
    def __str__(self) -> str:
        return self.uniq_str
    def matches_uniq_id_str(self, string:str) -> bool:
        return self.uniq_str == string
    @classmethod
    def from_str(cls:Type[T], string:str) -> T:
        if string=="": return cls()
        l = len(cls.class_str)
        if l+1<len(string) and (string[:l+1] == (cls.class_str+".")):
            uniq_id = int(string[l+1:])
            return cls(uniq_id=uniq_id)
        return cls(uniq_str=string)
    pass

class UniqueAlbumId(UniqueId):
    class_str = "alb"
    pass
class UniqueDiscId(UniqueId):
    class_str = "disc"
    pass

#c Album
class Album(DataClass):
    json_prop_types : ClassVar[Dict[str,type]] = {"label":str, "artist":str, "title":str, "num_discs":int, "musicbrainz_release_id":str, "downloaded_titles":str, "downloaded_artists":str, }
    data_class_type : ClassVar[str] = "Album"
    uniq_id   : UniqueAlbumId
    label     : str
    artist    : str
    title     : str
    num_discs : int
    musicbrainz_release_id:str # Should be a unique value for each album, but might not be
    downloaded_titles : str
    downloaded_artists : str
    children  : List["Disc"]
    def __init__(self, uniq_id:Optional[UniqueAlbumId]=None):
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
        self.children = []
        pass
    #f add_download_data
    def add_download_data(self, dd:Dict[str, Any]) -> None:
        if "num_discs" in dd: self.num_discs = dd["num_discs"]
        if "title" in dd:  self.downloaded_titles = str_add_to_set(self.downloaded_titles, dd["title"])
        if "artist" in dd: self.downloaded_artists = str_add_to_set(self.downloaded_artists, dd["artist"])
        if "musicbrainz_release_id" in dd: self.musicbrainz_release_id = dd['musicbrainz_release_id']
        pass
    pass

#c Disc
class Disc(DataClass):
    #v Properties
    json_prop_types : ClassVar[Dict[str,type]] = {"cddb_id":str, "num_tracks":int, "src_directory":str, "album_uniq_id":str, "artist":str, "title":str, "musicbrainz_string":str, "musicbrainz_id":str, "musicbrainz_release_id":str, "total_length":int, "disc_of_set":int, "downloaded_titles":str, "downloaded_artists":str, "rip_data":str, "rip_date":str, "rip_time":str, "tracks":type(lambda x:x)}
    data_class_type : ClassVar[str] = "Disc"
    uniq_id   : UniqueDiscId
    cddb_id       : str
    num_tracks    : int
    src_directory : str
    album_uniq_id : str
    artist        : str
    title         : str
    musicbrainz_string : str
    musicbrainz_id : str
    musicbrainz_release_id : str # Musicbrainz 'release' id (e.g. 211ce24f-6de3-4f3c-a62c-7c3b0eff7569) of the album that this disc is part of, if known
    total_length : int
    disc_of_set  : int
    rip_data : str
    rip_date : str
    rip_time : str
    downloaded_titles : str
    downloaded_artists : str
    album         : Optional[Album]
    tracks        : List["Track"]
    """ Contains info about the data on a CD. """
    #f __init__
    def __init__(self, uniq_id:Optional[UniqueDiscId]=None):
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
        self.artist = "Unknown artist"
        self.title = "Unknown title"
        self.disc_of_set = 1
        self.downloaded_artists = ""
        self.downloaded_titles = ""
        self.rip_data = ""
        self.rip_date = ""
        self.rip_time = ""
        self.album = None
        self.tracks = []
        self.postset_num_tracks = self.update_track_list
        pass
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
        pass
    #f as_json
    def as_json(self) -> Json:
        json = DataClass.as_json(self)
        json = cast(Dict[str,Json], json)
        tracks_json = []
        for t in self.tracks:
            tracks_json.append(t.as_json())
            pass
        json["tracks"] = tracks_json
        return json
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
        if number-1>=self.num_tracks:
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
    json_prop_types : ClassVar[Dict[str,type]] = {"number":int, "offset":int, "sectors":int, "length_seconds":int, "title":str, "output_title":str, "downloaded_titles":str, "downloaded_artists":str}
    data_class_type : ClassVar[str] = "Track"
    number       : int
    offset       : int # number of sectors from start of disc
    sectors      : int # number of sectors long
    length_seconds : int
    title        : str
    downloaded_titles : str
    downloaded_artists : str
    disc         : Optional[Disc]
    output_title : str
    
    #f __init__
    def __init__(self, disc:Disc, number:int):
        self.disc = disc
        self.number = number
        self.offset = 0
        self.sectors = 0
        self.length_seconds = 0
        self.title  = ""
        self.artist = ""
        self.downloaded_titles = ""
        self.downloaded_artists = ""
        self.postset_number = self.create_output_title
        self.output_title = f"Track {self.number} of {self.disc.num_tracks}{self.disc.disc_of_set_str()}"
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
        if self.title=="":
            if self.disc is None:
                self.output_title = f"Track {self.number}"
                pass
            else:
                self.output_title = f"Track {self.number} of {self.disc.num_tracks}{self.disc.disc_of_set_str()}"
                pass
            pass
        pass
    #f All done
    pass

#a Database
#c Database
class Database(object):
    albums  : Dict[UniqueAlbumId, Album]
    discs   : Dict[UniqueDiscId, Disc]
    tracks  : Dict[UniqueDiscId, List[Track]]
    #f __init__
    def __init__(self) -> None:
        self.albums = {}
        self.discs = {}
        self.tracks = {}
        pass
    #f create_album
    def create_album(self, uniq_id_str:str) -> Album:
        uniq_id = UniqueAlbumId.from_str(uniq_id_str)
        album = Album(uniq_id=uniq_id)
        self.albums[uniq_id] = album
        return album
    #f add_json
    def add_json(self, json:Json, permit_duplicates:bool=False) -> None:
        assert type(json)==dict
        json_dict = cast(Dict[str,Any], json)
        if "albums" in json_dict:
            for (k,v) in json_dict["albums"].items():
                album = self.find_album_id(k)
                if album is not None and not permit_duplicates:
                    raise Exception(f"Duplicate album id {k} in database")
                if album is None: album = self.create_album(k)
                album.from_json(v)
                pass
            pass
        if "discs" in json_dict:
            for (k,v) in json_dict["discs"].items():
                disc = self.find_disc_id(k)
                if disc is not None and not permit_duplicates:
                    raise Exception(f"Duplicate disc id {k} in database")
                if disc is None:
                    uniq_disc_id = UniqueDiscId.from_str(k)
                    disc = Disc(uniq_id=uniq_disc_id)
                    self.discs[uniq_disc_id] = disc
                    pass
                disc.from_json(v)
                album = self.album_of_disc(disc)
                disc.set_album(album)
                pass
            pass
        pass
    #f albums_as_json
    def albums_as_json(self) -> Json:
        result = {}
        for (k,v) in self.albums.items():
            result[str(k)] = v.as_json()
            pass
        return result
    #f discs_as_json
    def discs_as_json(self) -> Json:
        result = {}
        for (k,v) in self.discs.items():
            result[str(k)] = v.as_json()
            pass
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
    def fetch_mb_disc_data(self, disc_id:str) -> bool:
        disc = self.find_disc_id(disc_id)
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

#a Blah
mb_id = "VBy6o5XYjSz_H1rNbLZG5IPujDQ-"
mb_id = "0dep0oaie9KXtUyF7rxJR2LG3Kw-"
mb_id = "Jm1prrQcJ8F2RGhQA_0cijBCjUI-"
mb_id = "lXa3V7_Sui0eQEyX6Ko.eYpnJf8-"
mb_id = ".Glpv6NWyVDxYJh6yzJJb.WpJiE-"
db = Database()
with open("library/library.json") as f:
    json_data = json.load(f)
    db.add_json(json_data)
    pass

print(db.fetch_mb_disc_data("disc.0000"))
print(db.fetch_mb_disc_data("disc.0001"))

with open("library/library_out.json","w") as f:
    json_data = {}
    json_data["albums"] = db.albums_as_json()
    json_data["discs"]  = db.discs_as_json()
    json.dump(json_data, f, indent=1)
    pass


