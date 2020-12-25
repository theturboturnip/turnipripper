#a Imports
import subprocess
import re
from pathlib import Path
from .config import Config
from .database import Database
from .disc_info import DiscInfo
from .db_disc import Disc

import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast

#a Classes
#c Encoder
class Encoder(object):
    #v Properties
    db : Database
    config : Config
    output_format : ClassVar[str]="mp3"
    output_ext    : ClassVar[str]=""
    extra_options : List[str]
    #f __init__
    def __init__(self, database:Database, config:Config, extra_options:List[str]=[]) -> None:
        self.db = database
        self.config = config
        self.extra_options = extra_options
        pass
    #f encode
    def encode(self, disc:Disc, track_list:List[int]=[], force_if_newer:bool=False) -> None:
        if track_list==[]:
            track_list = range(disc.num_tracks)
            pass
        source_path = self.db.joinpath(self.config.rip.joinpath(disc.src_directory))
        output_path = self.db.joinpath(self.config.encode.output_root)
        output_path = output_path.joinpath(Path(disc.src_directory))
        print(source_path, output_path)
        output_ext = self.output_ext
        if output_ext=="": output_ext=self.output_format
        for i in track_list:
            input_file = source_path.joinpath(f"track{i+1:02d}.flac")
            if not input_file.is_file(): raise Exception(f"Couldn't find file {input_file}")
            output_filename = "{track:02d} - {title}.{output_ext}".format(
                title = disc.get_track_title(i), track = i+1, output_ext = output_ext)
            # print(output_filename.replace(
            output_file = output_path.joinpath(output_filename)
            ffmpeg_command = ["ffmpeg", "-i", str(input_file), "-c", self.output_format,
                              "-loglevel", "warning",
                              "-hide_banner",
                              "-stats",
                              *self.extra_options,
                              "-y"]
            for (k,v) in disc.iter_metadata(i):
                ffmpeg_command.append("-metadata")
                ffmpeg_command.append(f"{k}={v}")
                pass
            ffmpeg_command.append(str(output_file))
            try:
                #print(ffmpeg_command)
                completed = subprocess.run(ffmpeg_command)
                pass
            except:
                raise RuntimeError("ffmpeg did not transcode correctly - is it installed?")
            if completed.returncode!=0:
                raise RuntimeError("ffmpeg did not transcode correctly")
            pass
        pass
    pass
    #f All done
    pass

