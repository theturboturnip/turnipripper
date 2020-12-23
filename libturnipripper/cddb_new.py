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


def decode_string(bytestr, encodings):
    for encoding in encodings:
        try:
            return bytestr.decode(encoding)
        except UnicodeDecodeError as err:
            exception = err
    print(bytestr)
    print(exception)
    return False

#c CddbDiscInfo
class CddbDiscInfo(DataClass):
    json_prop_types : ClassVar[Dict[str,type]] = {"disc_id":str, "genre":str, "title":str}
    data_class_type : ClassVar[str] = "CddbDiscInfo"
    genre : str
    disc_id : str # should be the string of the cddb_id
    title : str
    cddb_id : "CddbID"
    def __init__(self, cddb_id:"CddbId") -> None:
        self.cddb_id = cddb_id
        self.disc_id = ""
        self.genre = ""
        self.title = ""
        pass

#c CddbServer
class CddbServer(object):
    """
    Describes an interface to a given CDDB server.
    Use query(disc_info) to ask the server about what data matches a given disc.
    Use read(disc_info, cddb_cd_info) to ask the server about the track data for a given instance of CD data.
    """
    offsets_hdr_re = re.compile(r'#\s*Track frame offsets')
    offsets_data_re = re.compile(r'#\s*(?P<offset>\d+)')
    len_re = re.compile(r'#\s*Disc length:\s*(\d+)\s*seconds')
    revis_re = re.compile(r'#\s*Revision:\s*(\d+)')
    submit_re = re.compile(r'#\s*Submitted via:\s*(.+)')
    keyword_re = re.compile(r'([^=]+)=(.*)')
    #f __init__
    def __init__(self, server, user, host, proto=6):
        self.client_name = "turnip-ripper"
        self.client_version = "v1"
        self.server = server
        self.proto = proto
        self.user = user
        self.host = host
        self.hello = f"{self.user}+{self.host}+{self.client_name}+{self.client_version}"
        pass
    #f query
    def query(self, cddb_id:"CddbId") -> List[Any]:
        query_str = cddb_id.string
        query_str = urllib.parse.quote_plus(query_str.rstrip())
        url = f"{self.server}?cmd=cddb+query+{query_str}&hello={self.hello}&proto={self.proto}";
        try:
            # print(f"Request :{url}:")
            response = urllib.request.urlopen(url)
            pass
        except Exception as e:
            raise Exception(f"Failed in cddb query '{url}': {e}")
        # Four elements in header: status, category, disc-id, title
        header = decode_string(response.readline(), ["utf8"]).split(' ', 3)
        header[0] = int(header[0])
        result = []
        if header[0] == 200:
            disc = CddbDiscInfo(cddb_id)
            disc.set(genre=header[1], disc_id=header[2], title=header[3])
            result.append(disc)
            pass
        elif header[0] == 211 or header[0] == 210:  # multiple matches
            result = []
            for line in response.readlines():
                line = decode_string(line, ["utf8"])
                if not line: continue
                line = line.rstrip()
                if line == '.': break
                match = line.split(' ', 2)
                disc = CddbDiscInfo(cddb_id)
                disc.set(genre=match[0], disc_id=match[1], title=match[2])
                result.append(disc)
                pass
            pass
        else:
            pass
        return (header[0], result)
    #f parse_read_reply
    def parse_read_reply(self, comments:str):
        result = {}
        track_offsets = []
        in_track_offsets = False
        result['track_offsets']=track_offsets
        for line in comments:
            if in_track_offsets:
                offset_match = self.offsets_data_re.match(line)
                if offset_match is not None:
                    track_offsets.append(int(offset_match.group('offset')))
                    pass
                else:
                    in_track_offsets = False
                    pass
                pass
            if self.offsets_hdr_re.match(line):
                in_track_offsets = True
                pass
            keyword_match = self.keyword_re.match(line)
            if keyword_match:
                (keyword, data) = keyword_match.groups()

                if keyword in result:
                    result[keyword] = result[keyword] + data
                else:
                    result[keyword] = data
                continue

            len_match = self.len_re.match(line)
            if len_match:
                result['disc_len'] = int(len_match.group(1))
                continue

            revis_match = self.revis_re.match(line)
            if revis_match:
                result['revision'] = int(revis_match.group(1))
                continue

            submit_match = self.submit_re.match(line)
            if submit_match:
                result['submitted_via'] = submit_match.group(1)
                continue

        return result
    #f try_read_in_genre
    def try_read_in_genre(self, genre:str, disc_id:str) -> bool:
        url = f"{self.server}?cmd=cddb+read+{genre}+{disc_id}&hello={self.hello}&proto={self.proto}"
        try:
            response = urllib.request.urlopen(url)
            pass
        except:
            return False
        header = decode_string(response.readline(), ["utf8"]).split(' ')
        return int(header[0])==210
    #f read
    def read(self, disc:CddbDiscInfo) -> Any:
        url = f"{self.server}?cmd=cddb+read+{disc.genre}+{disc.disc_id}&hello={self.hello}&proto={self.proto}"
        print(url)
        try:
            # print(f"Request :{url}:")
            response = urllib.request.urlopen(url)
            pass
        except Exception as e:
            raise Exception(f"Failed in cddb read '{url}': {e}")
        header = decode_string(response.readline(), ["utf8"]).split(' ', 3)
        header[0] = int(header[0])
        if header[0] == 210 or header[0] == 417:  # success or access denied
            reply = []

            for line in response.readlines():
                line = decode_string(line, ["utf8"]).rstrip()
                if not line: continue
                if line == '.': break
                line = line.replace(r'\t', "\t")
                line = line.replace(r'\n', "\n")
                line = line.replace(r'\\', "\\")
                reply.append(line)
                pass

            if header[0] == 210:            # success, parse the reply
                return [header[0], self.parse_read_reply(reply)]
            else:                           # access denied. :(
                return [header[0], reply]
        else:
            return [header[0], None]
        pass
    #f All done
    pass

#c CDInfo
class CDInfo:
    """ Contains info about the metadata of the tracks on a CD """
    def __init__(self, title_pattern, disc_info, cddb_track_info):
        self.disc_info = disc_info
        self.id = cddb_track_info["DISCID"]
        split_name = cddb_track_info["DTITLE"].split(" / ")
        # TODO: Handle the case where the pattern has invalid indices
        try:
            if len(split_name)==1: split_name.append(split_name[0])
            self.title = split_name[title_pattern.album_index]
            self.artist = split_name[title_pattern.artist_index]
            pass
        except Exception as e:
            raise Exception(f"Failed to parse track title info for id {self.id} of {split_name}")
        self.disc_info.title  = self.title
        self.disc_info.artist = self.artist
        self.tracks = []
        for i in range(disc_info.num_tracks):
            self.tracks.append(cddb_track_info.get("TTITLE" + str(i), "Track " + str(i + 1)))
            self.disc_info.tracks[i].set_title(self.tracks[i])
            pass
        pass

    
    #f All done
    pass

#c CddbServerList
class CddbServerList(object):
    servers : List[CddbServer]
    genres : ClassVar[List[str]] = ["blues", "classical", "country", "folk", "jazz", "misc", "newage", "reggae", "rock", "soundtrack"]
    def __init__(self) -> None:
        self.servers = []
        pass
    def add_server(self, server:str, user:str, proto:int=6):
        self.servers.append( CddbServer(server, proto, user) )
        pass
    def guess_cddb_ids(self, disc_id:str) -> List["CddbId"]:
        result = set()
        for s in self.servers:
            for g in self.genres:
                if g not in result:
                    if s.try_read_in_genre(g,disc_id):
                        result.add(g)
                        pass
                    pass
                pass
            pass
        print(disc_id,result)
        return result
    def get_cddb_cd_info(self, cddb_id:"CddbId"):
        result = []
        for s in self.servers:
            header, available_options = s.query(cddb_id)
            result.extend(available_options)
            pass
        return result
    def read_cddb_cd_info(self, discs:List[CddbDiscInfo]):
        result = []
        for s in self.servers:
            for d in discs:
                print(s.read(d))
                pass
            pass
        return result
    pass

#c CddbID
T = TypeVar('T', bound='CddbID')
class CddbID(DataClass):
    #v Properties
    json_prop_types : ClassVar[Dict[str,type]] = {}
    data_class_type : ClassVar[str] = "CddbId"
    string : str
    cddb_id : str
    offsets : List[int]
    last_sector : int
    last_sector_error : int
    
    #f __init__
    def __init__(self, string:str) -> None:
        self.string = string
        self.cddb_id = ""
        self.offsets = []
        self.last_sector = 0
        self.last_sector_error = 0
        self.postset_string = self.extract_data
        pass
    #f of_disc
    @classmethod
    def of_disc(cls:Type[T], tracks:List[Any]) -> T:
        if tracks==[]: return cls("")
        d = cls("")
        d.offsets = [t.offset for t in tracks]
        d.last_sector = tracks[-1].offset + tracks[-1].sectors
        csum = sum([sum([int(j) for j in list(str(i//75))]) for i in d.offsets]) % 255
        cd_len = (d.last_sector - d.offsets[0])//75
        d.cddb_id = f"{csum:02x}{cd_len:04x}{len(d.offsets):02x}"
        d.string = f"{d.cddb_id} {len(d.offsets)} "
        d.string += " ".join([str(o) for o in d.offsets])
        d.string += f" {d.last_sector//75}"
        # 040cd212 18 150 26015 38464 48627 68170 88165 103005 126862 140072 158965 164937 176260 190682 209952 218515 226970 231152 235790 3284
        return d
    #f extract_data
    def extract_data(self) -> None:
        string_list = self.string.split(" ")
        if len(string_list)<2: return
        self.cddb_id = string_list[0]
        num_tracks = int(string_list[1])
        if num_tracks+3 != len(string_list): return
        offsets = [int(s) for s in string_list[2:-1]]
        length_in_seconds = int(string_list[-1])
        last_sector_min = length_in_seconds*75
        self.offsets = offsets
        self.last_sector = last_sector_min
        self.last_sector_error = 74 # for now
        pass
    #f __str__
    def __str__(self) -> str:
        r = f"CddbId:{self.cddb_id}:{self.offsets}:{self.last_sector}:{self.last_sector_error}:{self.string}:"
        return r
    #f All done
    pass
