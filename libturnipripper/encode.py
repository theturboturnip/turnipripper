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
    source : str # if not empty then the directory to look for data in
    output_ext    : ClassVar[str]="mp3"
    extra_options : Dict[str,str]={
        "-c:a":"mp3",
    }
    #f __init__
    def __init__(self, database:Database, config:Config, source:str, extra_options:List[Tuple[str,str]]=[]) -> None:
        self.db = database
        self.config = config
        self.source = source
        self.extra_options = self.extra_options.copy()
        config_options = self.config.encode.get_encode_options()
        config_options.extend(extra_options)
        for (k,v) in config_options:
            self.extra_options[k] = v
            pass
        pass
    #f encode
    def encode(self, disc:Disc, track_list:List[int]=[], force_if_newer:bool=False) -> None:
        if track_list==[]:
            track_list = range(disc.num_tracks)
            pass
        if self.source == "":
            source_path = self.db.joinpath(self.config.rip.joinpath(disc.src_directory))
            pass
        else:
            source_path = Path(self.source).joinpath(disc.src_directory)
            pass
        output_path = self.db.joinpath(self.config.encode.output_root)
        output_path = output_path.joinpath(Path(disc.src_directory))
        if not output_path.exists():
            output_path.mkdir()
            pass
        if not output_path.is_dir():
            raise Exception("Cannot encode to {output_path] as it is not a directory")
        output_ext = self.output_ext
        for i in track_list:
            track = disc.get_track(i)
            input_file = source_path.joinpath(track.compressed_filename())
            output_file = output_path.joinpath(track.encoded_filename(encode_ext=output_ext))
            if not input_file.is_file(): raise Exception(f"Couldn't find file {input_file}")

            input_file_for_ui  = self.db.relative_path_if_possible(input_file)
            output_file_for_ui = self.db.relative_path_if_possible(output_file)
            
            if output_file.is_file():
                input_file_stat  = input_file.stat()
                output_file_stat = output_file.stat()
                if (not force_if_newer) and (output_file_stat.st_mtime > input_file_stat.st_mtime):
                    print(f"Skipping encode of '{input_file_for_ui}' as '{output_file_for_ui}' is newer (and not forced)")
                    continue
                pass

            ffmpeg_command = ["ffmpeg",
                              "-i", str(input_file),
                              "-loglevel", "warning",
                              "-hide_banner",
                              "-stats",
                              "-y", # overwrite output files
            ]
            for (k,v) in self.extra_options.items():
                ffmpeg_command.append(k)
                if v!="": ffmpeg_command.append(v)
                pass

            for (k,v) in disc.iter_metadata(i):
                ffmpeg_command.append("-metadata")
                ffmpeg_command.append(f"{k}={v}")
                pass
            ffmpeg_command.append(str(output_file))
            try:
                print(f"Using ffmpeg to encode {input_file_for_ui} to {output_file_for_ui}")
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

