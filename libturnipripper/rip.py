#a Imports
from .config import Config
from .database import Database
from .command import Command
from .musicbrainz import MusicbrainzID

import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast

import subprocess

#a Subprocess functions - invoke cd-discid
def get_cddb_from_device(device_name):
    (rc, cmd_output) = subprocess.getstatusoutput([f"cd-discid {device_name}"])
    return cmd_output.split(" ")[0]

def get_musicbrainz_from_device(device_name) -> MusicbrainzID:
    (rc, cmd_output) = subprocess.getstatusoutput([f"cd-discid --musicbrainz {device_name}"])
    if rc!=0: raise Exception(f"Failed to run cd-discid on device {device_name}")
    print(rc,cmd_output)
    mb_id = MusicbrainzID(cmd_output)
    mb_id.extract_data()
    return mb_id

#a Command subclasses
class RipCommand(Command):
    name = "rip"
    parser_args = {
        ("--device",):{"type":str, "default":"/dev/cdrom", "help":"Use <device> (default /dev/cdrom)"},
        ("directory",):{"type":str, "default":"", "nargs":"?", "help":"Use <directory> to store wav/flacc rather than "},
        }
    #f do_command
    def do_command(self, parser, config:Config, args) -> None:
        db = Database.from_config(config.database)
        subdirectory = args.directory
        if subdirectory=="":
            if config.rip.default_dir=="cddb":
                subdirectory = "cddb"
                pass
            else:
                mb_id = get_musicbrainz_from_device(args.device)
                subdirectory = mb_id.mb_id
                pass
            pass
        rip_directory = config.rip.source_root.joinpath(subdirectory)
        if rip_directory.exists() and not args.rerip:
            raise Exception(f"Path {source_directory} already exists and not a rerip")
        # libturnipripper.ripping.rip_to_subdir(disc_info, None, args.device, args.source_root_folder, args.ffmpeg, force_overwrite=True)
        pass
    #f all done
    pass

