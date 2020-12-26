import subprocess
from pathlib import Path
import hashlib
import base64
from .musicbrainz import MusicbrainzID
from .cddb_new import CddbID

import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast


# Data Classes
class TrackInfo:
    def __init__(self, number, lba:int=0, lba_extent:int=0):
        self.number = number
        self.lba_extent = lba_extent
        self.lba_offset = lba
        pass
    pass

#c DiscInfo
class DiscInfo:
    """ Contains info about the data on a CD. """
    num_tracks: int
    total_length : int # in seconds
    tracks: List[TrackInfo]
    musicbrainz_id   : MusicbrainzID
    cddb_id : CddbID
    #f __init__
    def __init__(self, cddb_id, musicbrainz_id, track_offsets=[], total_length=0, cdrecord_output=""):
        self.cddb_id = cddb_id
        self.musicbrainz_id = musicbrainz_id
        self.num_tracks    = len(track_offsets)
        self.total_length = total_length
        self.cdrecord_output = cdrecord_output
        self.tracks = [TrackInfo(i, lba=track_offsets[i]) for i in range(self.num_tracks)]
        pass
    #f from_device
    @classmethod
    def from_device(cls, device_name:str):
        cddb_string = subprocess.getoutput([f"cd-discid {device_name}"])
        cmd_output = cddb_string.split(" ")
        try:
            ntracks = int(cmd_output[1])
            pass
        except:
            raise RuntimeError("cd-discid did not return useful information - is it installed? (%s)"%str(cmd_output))
        if len(cmd_output) - 3 != ntracks:
            raise RuntimeError("DiscID mismatch between reported track count and amount of tracks given")
        cddb_id = CddbID(cddb_string)
        cddb_id.extract_data()
        track_lengths = [int(x) for x in cmd_output[2:-1]]
        total_length_seconds = int(cmd_output[-1])
        musicbrainz_string = subprocess.getoutput([f"cd-discid --musicbrainz {device_name}"])
        musicbrainz_id = MusicbrainzID(musicbrainz_string)
        try:
            cdrecord_output = subprocess.getoutput([f"cdrecord dev={device_name} -toc"])
            pass
        except Exception as e:
            print(f"Failed to get cdrecord output - is it installed - it is nice to record this in the source directory...:\n{e}")
            cdrecord_output = ""
            pass
        return cls(cddb_id, musicbrainz_id, track_lengths, total_length_seconds, cdrecord_output)
    #f from_disc_info_file
    @classmethod
    def from_disc_info_file(cls, source_directory:Path):
        disc_info = cls(cddb_id=CddbID(""), musicbrainz_id=MusicbrainzID(""))
        disc_info.read_disc_info(source_directory)
        return disc_info
    #f write_disc_info
    def write_disc_info(self, source_directory:Path, force_overwrite=False):
        disc_info_path = source_directory.joinpath("disc_info.txt")
        if disc_info_path.exists() and not force_overwrite:
            raise Exception("Cannot write disc info - it already exists")
            pass
        with disc_info_path.open("w") as f:
            print(f"{self.cddb_id} {self.as_disc_info()}",file=f)
            print(f"num_tracks: {self.num_tracks}",file=f)
            print(f"offsets: {[t.lba_offset for t in self.tracks]}",file=f)
            print(f"extents: {[t.lba_extent for t in self.tracks]}",file=f)
            print(f"total_length: {self.total_length}",file=f)
            print(f"cddb: {self.as_CDDB_track_info()}",file=f)
            print(f"musicbrainz: {self.as_musicbrainz()}",file=f)
            print(f"\nCD record:\n{self.cdrecord_output}",file=f)
            pass
        pass
    #f read_disc_info
    def read_disc_info(self, source_directory:Path):
        disc_info_path = source_directory.joinpath("disc_info.txt")
        with disc_info_path.open("r") as f:
            for l in f:
                if l[0:8]==self.cddb_id:
                    self.read_disc_info_string(l[8:])
                    pass
                elif l[0:6]=="cddb: ":
                    self.read_CDDB_track_info_string(l[6:])
                    pass
                elif l[0:13]=="musicbrainz: ":
                    self.read_musicbrainz_string(l[13:])
                    pass
                elif l[0:12]=="num_tracks: ":
                    self.read_num_tracks(l[12:])
                    pass
                elif l[0:9]=="offsets: ":
                    self.read_offsets(l[9:])
                    pass
                elif l[0:9]=="extents: ":
                    self.read_extents(l[9:])
                    pass
                elif l[0:14]=="total_length: ":
                    self.read_total_length(l[14:])
                    pass
                elif l[0:10]=="CD record:":
                    self.cdrecord_output = ""
                    for l in f:
                        self.cdrecord_output += l
                        pass
                    pass
                else:
                    pass
                pass
            pass
        pass
    #f as_CDDB_track_info
    def as_CDDB_track_info(self):
        return [self.cddb_id.as_int(), self.num_tracks] + [t.lba_offset for t in self.tracks] + [self.total_length]
    #f int_list_of_string
    @staticmethod
    def int_list_of_string(s:str) -> List[int]:
        s=s.strip()
        if s[0]!='[' or s[-1]!=']':
            raise Exception(f"Bad string list {s} of ints when reading disc_info")
        return [int(x) for x in s[1:-1].split(",")]
    #f read_num_tracks
    def read_num_tracks(self, s:str) -> None:
        self.num_tracks = int(s)
        self.tracks = [TrackInfo(i) for i in range(self.num_tracks)]
        pass
    #f read_total_length
    def read_total_length(self, s:str) -> None:
        self.total_length = int(s)
        self.create_cddb_id()
        pass
    #f read_extents
    def read_extents(self, s:str) -> None:
        extents = self.int_list_of_string(s)
        if len(extents)!=self.num_tracks: return
        for i in range(self.num_tracks):
            self.tracks[i].lba_extent = extents[i]
            pass
        self.create_musicbrainz_id()
        pass
    #f read_offsets
    def read_offsets(self, s:str) -> None:
        offsets = self.int_list_of_string(s)
        if len(offsets)!=self.num_tracks: return
        for i in range(self.num_tracks):
            self.tracks[i].lba_offset = offsets[i]
            pass
        self.create_cddb_id()
        pass
    #f create_cddb_id
    def create_cddb_id(self):
        self.cddb_id = CddbID.of_offsets_length(track_offsets=[t.lba_offset for t in self.tracks], length_in_seconds=self.total_length)
        pass
    #f create_musicbrainz_id
    def create_musicbrainz_id(self):
        self.musicbrainz_id = MusicbrainzID.of_offsets_last_extent(offsets=[t.lba_offset for t in self.tracks], last_extent=self.tracks[-1].lba_extent)
        pass
    #f read_CDDB_track_info
    def read_CDDB_track_info_string(self, s:str) -> None:
        cddb_data = self.int_list_of_string(s)
        if len(cddb_data)<2: return
        cddb_id_int = cddb_data[0]
        num_tracks = cddb_data[1]
        if len(cddb_data)!=3+num_tracks: return
        track_offsets = cddb_data[2:-1]
        total_length = cddb_data[-1]
        print(track_offsets)
        if self.num_tracks==0:
            self.num_tracks = num_tracks
            self.tracks = [TrackInfo(i, lba=track_offsets[i]) for i in range(self.num_tracks)]
            self.total_length = total_length
            pass
        self.create_cddb_id()
        pass
    def create_cddb_id(self):
        self.cddb_id = CddbID.of_offsets_length(track_offsets=[t.lba_offset for t in self.tracks], length_in_seconds=self.total_length)
        pass
    #f as_disc_info
    def as_disc_info(self):
        return f"{self.num_tracks} "+(" ".join([str(t.lba_extent) for t in self.tracks])) + " "+str(self.total_length)
    #f read_disc_info_string
    def read_disc_info_string(self, s):
        s = s.strip()
        data = [int(x) for x in s.split(" ")]
        if data[0] != len(data)-2:
            raise Exception("Bad disc info string when reading disc_info")
        self.track_lengths = data[1:-1]
        self.total_length = data[-1]
        self.num_tracks = data[0]-2
        self.tracks = [TrackInfo(i) for i in range(self.num_tracks)]
        pass
    #f as_musicbrainz
    def as_musicbrainz(self):
        return (self.musicbrainz_id.string, self.musicbrainz_id.mb_id)
    #f read_musicbrainz_string
    def read_musicbrainz_string(self, s):
        s=s.strip()
        if s[0]!='(' or s[-1]!=')':
            raise Exception("Bad musicbrainz string when reading disc_info")
        data = s[1:-1].split(",")
        if len(data)!=2:
            raise Exception("Bad musicbrainz string when reading disc_info")
        data = [x.strip() for x in data]
        did_mb_id = data[1][1:-1]
        if data[0][0]!="'" or data[0][-1]!="'":
            raise Exception("Bad musicbrainz string when reading disc_info")
        musicbrainz_string = data[0][1:-1]
        self.musicbrainz_id = MusicbrainzID(musicbrainz_string)
        if self.musicbrainz_id.mb_id!=did_mb_id:
            # raise Exception(f"Mismatch in musicbrainz id when reading disc_info (read {did_mb_id} calculated {self.musicbrainz_id})")
            pass
        if self.num_tracks==0 or self.num_tracks==self.musicbrainz_id.num_tracks():
            self.tracks = [TrackInfo(i) for i in range(self.num_tracks)]
            for (n,s,e) in self.musicbrainz_id.offset_extents():
                self.tracks[n].lba_offset = s
                self.tracks[n].lba_extent = e
                pass
            pass
        pass
    #f __str__
    def __str__(self) -> str:
        r = f"{self.musicbrainz_id} {self.cddb_id}"
        return r
    #f All done
    pass
