#a Imports
import subprocess
import re
from pathlib import Path
from .disc_info import DiscInfo

import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast

#a Classes
#c RippedTrack
class RippedTrack(object):
    #f Properties
    path : Path
    compressed : bool
    track_number: int # from 0
    wav_file_re = re.compile("track([0-9]+)\.cdda\.wav")
    flac_file_re = re.compile("track([0-9]+)\.flac")
    #f path_track_number
    @classmethod
    def path_track_number(cls, path:Path) -> Optional[int]:
        m = cls.wav_file_re.match(path.name)
        if m is not None: return int(m.group(1))-1
        m = cls.flac_file_re.match(path.name)
        if m is not None: return int(m.group(1))-1
        return None
    #f path_is_compressed
    @staticmethod
    def path_is_compressed(path:Path) -> bool:
        return path.suffix==".flac"
    #f path_as_compressed
    def path_as_compressed(self) -> Path:
        return self.path.with_suffix("").with_suffix("").with_suffix(".flac")
    #f __init__
    def __init__(self, path:Path) -> None:
        self.path = path
        tn = self.path_track_number(self.path)
        if tn is None: raise Exception(f"Bad track path {self.path} - could not determine a track number for it")
        self.track_number = tn
        self.compressed = self.path_is_compressed(self.path)
        pass
    #f compress
    def compress(self, track_count:int) -> None:
        if self.compressed: return
        ffmpeg_command = ["ffmpeg", "-i", "{input_path}", "-c:a", "flac",
                          "-compression_level", "12",
                          "-metadata", "track={track}/{track_count}",
                          "-y", "-v", "24",
                          "{output_path}"]
        output_path = self.path_as_compressed()
        translated_ffmpeg_command = [x.format(input_path = self.path,
                                              output_path = output_path,
                                              track = self.track_number,
                                              track_count = track_count)
                                     for x in ffmpeg_command]
        try:
            print(f"Using ffmpeg to compress {self.path} to {output_path}")
            completed = subprocess.run(translated_ffmpeg_command)
            pass
        except:
            raise RuntimeError("ffmpeg did not transcode correctly - is it installed?")
        if completed.returncode!=0:
            raise RuntimeError("ffmpeg did not transcode correctly")
        self.path.unlink()
        self.path = output_path
        self.compressed = True
        pass
    #f __str__
    def __str__(self) -> str:
        r = f"{self.track_number}:{self.compressed}:{self.path}"
        return r
    #f All done
    pass

#c Ripper
class Ripper(object):
    #v Properties
    device : str
    rip_directory : Path
    disc_info:DiscInfo
    
    #f __init__
    def __init__(self, device:str, rip_directory:Path, disc_info:DiscInfo):
        self.device = device
        self.rip_directory = rip_directory
        self.disc_info = disc_info
        pass
    #f create_directory_if_required
    def create_directory_if_required(self):
        if not self.rip_directory.exists():
            self.rip_directory.mkdir()
            pass
        if not self.rip_directory.is_dir():
            raise Exception("Rip path {self.rip_directory} is not a directory, and it must be!")
        pass
    #f list_ripped_tracks
    def list_ripped_tracks(self) -> List[RippedTrack]:
        r = []
        for p in self.rip_directory.glob(r"*.wav"):
            r.append(RippedTrack(p))
            pass
        for p in self.rip_directory.glob(r"*.flac"):
            r.append(RippedTrack(p))
            pass
        return r
    #f rip_span
    def rip_span(self, start:int, end:int) -> None:
        """ Rips a zero-indexed, inclusive set of tracks from the CD. """
        print(f"Rip tracks {start+1} {end+1} from {self.device} to {self.rip_directory}")
        # CDParanoia takes 1-indexed track indices.
        if start == end:
            span_str = str(start + 1)
            pass
        else:
            span_str = "{}-{}".format(start + 1, end + 1)
            pass
        try:
            # cdparanoia puts its progress on stderr, which means we cannot pipe stderr for use if the command fails
            completed = subprocess.run(["cdparanoia", "-L", "--force-cdrom-device", self.device, "-B", "--output-wav", span_str], cwd=self.rip_directory)
            pass
        except:
            raise RuntimeError("cdparanoia did not rip correctly - is it installed?")
        if completed.returncode!=0:
            raise RuntimeError("cdparanoia did not rip correctly")
        pass
    #f compress_files
    def compress_files(self):
        ripped = self.list_ripped_tracks()
        for rt in ripped:
            rt.compress(self.disc_info.num_tracks)
            pass
        pass

    #f find_spans_to_rip
    def find_spans_to_rip(self, ripped:List[RippedTrack]) -> List[Tuple[int,int]]:
        num_tracks = self.disc_info.num_tracks
        track_numbers_ripped = set()
        for rt in ripped: track_numbers_ripped.add(rt.track_number)
        last_ripped_index = -1
        spans_to_rip = []
        for i in range(num_tracks):
            if i not in track_numbers_ripped: continue
            # This track has been ripped.
            # If the last track that we know was ripped wasn't the last one...
            if last_ripped_index != i - 1:
                # Rip the span of tracks that haven't been ripped yet.
                # Starting at 1 after the last known ripped track,
                # and ending one before the previous track.
                spans_to_rip.append((last_ripped_index + 1, i - 1))
                pass
            last_ripped_index = i
            pass
        # If there are still tracks left to be ripped, rip them.
        if last_ripped_index != num_tracks - 1:
            spans_to_rip.append((last_ripped_index + 1, num_tracks - 1))
            pass
        return spans_to_rip
    #f rip
    def rip(self):
        self.create_directory_if_required()
        ripped = self.list_ripped_tracks()
        spans_to_rip = self.find_spans_to_rip(ripped)
        if spans_to_rip==[]:
            print("All tracks already ripped")
            pass
        for (s,e) in spans_to_rip:
            self.rip_span(s,e)
            pass
        pass
    #f All done
    pass

