#!/usr/bin/env python3
"""
Module for retrieving CDDB v1 data from CDDB servers via HTTP

Written 17 Nov 1999 by Ben Gertzfield <che@debian.org>
This work is released under the GNU GPL, version 2 or later.

Modified August 2018 by Samuel Stark to be class-based, to add an expected output encodings parameter in read() and query()
and to make fully compatible with Python 3.6
"""
from libturnipripper.data_class import DataClass

import urllib.request, urllib.parse, urllib.error
import string
import hashlib
import base64

# from . import data
import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast
Json = Union[List[Any], Dict[str,Any], str, int]

import subprocess
import re
import os.path

import json

DownloadData = Dict[str,Any]

#c MusicbrainzDiscPressing
class MusicbrainzDiscPressing(object):
    media : "MusicbrainzMedia"
    offsets : List[int] # offset to each track start
    sectors : int       # total sectors
    id : str
    def __init__(self, media:"MusicbrainzMedia", json:Json) -> None:
        assert type(json)==dict
        json_dict = cast(Dict[str,Any], json)
        self.media = media
        self.offsets = json_dict['offsets']
        self.sectors = json_dict['sectors']
        self.id      = json_dict['id']
        # ['offsets', 'offset-count', 'id', 'sectors']
        pass
    #f iter_download_track_data
    def iter_download_track_data(self) -> Iterable[Tuple[int, Dict[str, Any]]]:
        for i in range(len(self.media.tracks)):
            track = self.media.tracks[i]
            data = {"title":track.title, "length":track.rec_length}
            if i<len(self.offsets):   data["offset"]  = self.offsets[i]
            if i+1<len(self.offsets): data["sectors"] = self.offsets[i+1] - self.offsets[i]
            if i+1==len(self.offsets): data["sectors"] = self.sectors - self.offsets[i]
            yield (track.position,data)
            pass
        pass
    #f get_media_download_data
    def get_media_download_data(self) -> DownloadData:
        return self.media.get_download_data()
    #f get_release_download_data
    def get_release_download_data(self) -> DownloadData:
        return self.media.release.get_download_data()
    #f get_album_download_data
    def get_album_download_data(self) -> DownloadData:
        return self.media.release.get_album_download_data()
    #f All done
    pass

#c MusicbrainzTrack
class MusicbrainzTrack(object):
    number : int
    position : int
    title : str
    rec_length : int
    rec_title : str
    def __init__(self, json:Json) -> None:
        assert type(json)==dict
        json_dict = cast(Dict[str,Any], json)
        self.number   = int(json_dict['number'])
        self.position = json_dict['position']
        self.title = json_dict['title']
        self.rec_length = json_dict['recording']['length']
        self.rec_title = json_dict['recording']['title']
        pass
    def __str__(self) -> str:
        r = ""
        r += f"Track:{self.number}:{self.position}:{self.title}:{self.rec_length}:{self.rec_title}:"
        return r
    pass

#c MusicbrainzMedia
class MusicbrainzMedia(object):
    title : str
    disc_of_set : int
    tracks : List[MusicbrainzTrack]
    disc_track_offset : int
    pressings : List['MusicbrainzDiscPressing']
    #f __init__
    def __init__(self, release:"MusicbrainzRelease", json:Json) -> None:
        assert type(json)==dict
        json_dict = cast(Dict[str,Any], json)
        self.release = release
        self.title = json_dict['title']
        self.disc_of_set = json_dict['position']
        self.disc_track_offset = json_dict['track-offset']
        self.tracks = []
        for dtd in json_dict['tracks']:
            self.tracks.append(MusicbrainzTrack(dtd))
            pass
        self.pressings = []
        if 'discs' in json_dict:
            for disc_pressing in json_dict['discs']: # disc_pressing may be the one we want!
                self.add_pressing(disc_pressing)
                pass
            pass
        pass
    #f add_pressing
    def add_pressing(self, json:Json) -> None:
        pressing = MusicbrainzDiscPressing(self, json)
        self.pressings.append(pressing)
        pass
    #f find_pressing
    def find_pressing(self, mb_id:str) -> Optional[MusicbrainzDiscPressing]:
        for p in self.pressings:
            if p.id==mb_id: return p
            pass
        return None
    #f get_download_data
    def get_download_data(self) -> DownloadData:
        dd = {"disc_of_set":self.disc_of_set,
              "title":self.title}
        return dd
    #f __str__
    def __str__(self) -> str:
        r = ""
        r += f"Media:{self.disc_of_set}:{self.title}:\n"
        for t in self.tracks:
            r += f"  {t}\n"
            pass
        for p in self.pressings:
            r += f"  pressing:{p.id}\n"
            pass
        return r
    pass

#c MusicbrainzArtist
class MusicbrainzArtist(object):
    name : str
    artist_type : str
    join_to_next : str
    #f __init__
    def __init__(self, release:"MusicbrainzRelease", json:Json) -> None:
        assert type(json)==dict
        json_dict = cast(Dict[str,Any], json)
        self.release = release
        self.name = json_dict['name']
        self.artist_type = ""
        self.join_to_next = ""
        if 'joinphrase' in json_dict:
            self.join_to_next = json_dict['joinphrase']
            pass
        # json_dict example:
        # {'artist': {'name': 'Douglas Adams', 'type-id': 'b6e035f4-3ce9-331c-97df-83397230b0df', 'type': 'Person', 'disambiguation': 'English author', 'id': 'e9ed318d-8cc5-4cf8-ab77-505e39ab6ea4', 'sort-name': 'Adams, Douglas'}, 'name': 'Douglas Adams', 'joinphrase': ' read by '}
        pass
    #f __str__
    def __str__(self) -> str:
        r = ""
        r += f"Artist:{self.name}:{self.artist_type}:{self.join_to_next}:\n"
        return r
    pass

#c MusicbrainzRelease
class MusicbrainzRelease(object):
    country:str
    date:str
    title:str
    mb_release_id:str
    media : List[MusicbrainzMedia]
    artists: List[MusicbrainzArtist]
   #f __init__
    def __init__(self, json:Json) -> None:
        assert type(json)==dict
        json_dict = cast(Dict[str,Any], json)
        self.country = json_dict['country']
        self.date    = json_dict['date']
        self.title   = json_dict['title']
        self.mb_release_id   = json_dict['id']
        self.media = []
        self.artists = []
        if 'media' in json_dict:
            for m in json_dict['media']:
                self.media.append( MusicbrainzMedia(self, m) )
                pass
            pass
        if 'artist-credit' in json_dict:
            for ac in json_dict['artist-credit']:
                self.artists.append( MusicbrainzArtist(self, ac) )
                pass
            pass
        pass
    #f find_pressing
    def find_pressing(self, mb_id:str) -> Optional[MusicbrainzDiscPressing]:
        for m in self.media:
            r = m.find_pressing(mb_id)
            if r is not None: return r
            pass
        return None
    #f get_common_download_data
    def get_common_download_data(self) -> DownloadData:
        dd = {"title":self.title}
        if self.mb_release_id!="": dd["musicbrainz_release_id"] = self.mb_release_id
        if len(self.artists)>0:
            artist = ""
            for a in self.artists:
                artist += a.name
                if a.join_to_next=="": break
                artist += a.join_to_next
                pass
            dd["artist"] = artist
            pass
        return dd
    #f get_download_data
    def get_download_data(self) -> DownloadData:
        dd = self.get_common_download_data()
        return dd
    #f get_album_download_data
    def get_album_download_data(self) -> DownloadData:
        dd = self.get_common_download_data()
        dd["num_discs"] = len(self.media)
        return dd
    #f __str__
    def __str__(self) -> str:
        r = f"{self.date}:{self.country}:{self.mb_release_id}:{self.title}\n"
        for m in self.media:
            r += f"   {m}\n"
        for a in self.artists:
            r += f"   {a}\n"
        return r
    #f All done
    pass

#c MusicbrainzRecordings
T = TypeVar('T', bound='MusicbrainzRecordings')
class MusicbrainzRecordings(object):
    def __init__(self, json:Json) -> None:
        assert type(json)==dict
        json_dict = cast(Dict[str,Any], json)
        if 'id' not in json_dict:       raise Exception(f"musicbrainz: expected 'id' in returned data but one was not present")
        if 'releases' not in json_dict: raise Exception(f"musicbrainz: expected 'releases' in returned data but one was not present")
        self.releases = []
        for release in json_dict['releases']:
            self.releases.append(MusicbrainzRelease(json=release))
            pass
        pass
    #f of_query
    @classmethod
    def of_query(cls:Type[T], mb_id:str) -> T:
        url = f"https://musicbrainz.org/ws/2/discid/{mb_id}?fmt=json&inc=recordings+artist-credits"
        try:
            response = urllib.request.urlopen(url)
            pass
        except Exception as e:
            raise Exception(f"Failed in musicbrainz query '{url}': {e}")
        # Four elements in header: status, category, disc-id, title
        expected_output_encodings=["utf8"]
        header = response.readline().decode("utf8")
        return cls(json=json.loads(header))
    #f find_pressing
    def find_pressing(self, mb_id:str) -> Optional[MusicbrainzDiscPressing]:
        for release in self.releases:
            pressing = release.find_pressing(mb_id)
            if pressing is not None: return pressing
            pass
        return None
    #f __str__
    def __str__(self) -> str:
        r = ""
        for release in self.releases:
            r += f"{release}\n"
            pass
        return r
    pass

#c MusicbrainzID
T2 = TypeVar('T2', bound='MusicbrainzID')
class MusicbrainzID(DataClass):
    #v Properties
    json_prop_types = {
        "string":str,
        "mb_id":str,
        "first":int,
        "last":int,
        "offsets":None,
        }
    data_class_type = "Musicbrainz"
    string : str
    mb_id : str
    first : int
    last : int
    offsets : List[int] # [0] is last
    #f __init__
    def __init__(self, string:str) -> None:
        self.string = string
        self.first = 1
        self.last = 0
        self.offsets = [0,0]
        self.mb_id = ""
        self.postset_string = self.extract_data
        pass
    #f from_json_offsets - no need for as_json_offsets
    def from_json_offsets(self, v:List[int]) -> None:
        assert(type(v)==list)
        self.offsets = []
        for n in v:
            assert(type(n)==int)
            self.offsets.append(n)
            pass
        pass
    #f of_disc
    @classmethod
    def of_disc(cls:Type[T2], tracks:List[Any]) -> T2:
        if tracks==[]: return cls("")
        extent = tracks[-1].offset + tracks[-1].sectors
        string = f"{len(tracks)}"
        for t in tracks:
            string += f" {t.offset}"
            pass
        string += f" {extent}"
        d = cls(string)
        d.extract_data()
        return d
    #f extract_data
    def extract_data(self) -> None:
        musicbrainz_data = [int(x) for x in self.string.split(" ")]
        if len(musicbrainz_data)>0:
            self.last  = musicbrainz_data[0]
            self.offsets = [musicbrainz_data[-1]]
            self.offsets.extend(musicbrainz_data[1:-1])
            self.mb_id = self.calculate_hash()
            pass
        pass
    #f calculate_hash
    def calculate_hash(self) -> str:
        sha = hashlib.sha1()
        sha.update(f"{self.first:02X}{self.last:02x}".encode("utf8"))
        for i in range(100):
            off = 0
            if i<len(self.offsets): off=self.offsets[i]
            sha.update(f"{off:08X}".encode("utf8"))
            pass
        return base64.b64encode(sha.digest(),altchars=b"._").replace(b"=",b"-").decode("utf8")
    #f All done
    pass
    
