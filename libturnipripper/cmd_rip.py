#a Imports
from pathlib import Path
from .config import Config
from .db_disc import Disc
from .database import Database
from .disc_info import DiscInfo
from .rip import Ripper
from .command import Command, CommandArgs
from .musicbrainz import MusicbrainzID

import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast

import subprocess

#a Command subclasses
#c RipArgs
class RipArgs(CommandArgs):
    device:str
    directory:str
    rerip:bool
    pass

#c RipCommand    
class RipCommand(Command):
    #v Properties
    name = "rip"
    parser_args = {
        ("--device",):{"type":str, "default":"/dev/cdrom", "help":"Use <device> (default /dev/cdrom)"},
        ("--uniq_id",):{"type":str, "default":"", "help":"Uniqued id for the database for the disc"},
        ("--rerip",):{"action":"store_true", "default":False, "help":"Re-rip the data from CD even if it has already been stored)"},
        ("--no_musicbrainz",):{"action":"store_true", "default":False, "help":"Do not try to fetch data from musicbrainz"},
        ("--no_cddb",):{"action":"store_true", "default":False, "help":"Do not try to fetch data from cddb"},
        ("--read_disc_info",):{"action":"store_true", "default":False, "help":"Read a disc_info.txt file in the directory rather than scanning the drive)"},
        ("directory",):{"type":str, "default":"", "nargs":"?", "help":"Use <directory> to store wav/flacc rather than "},
        }
    args_class = RipArgs
    args       : RipArgs
    #f do_command
    def do_command(self) -> None:
        db = Database.from_config(self.config.database)
        if self.args.read_disc_info:
            if self.args.directory is None: raise Exception("Read disc info requires a directory")
            rip_directory = db.joinpath(self.config.rip.joinpath(self.args.directory))
            disc_info = DiscInfo.from_disc_info_file(rip_directory)
            pass
        else:
            disc_info = DiscInfo.from_device(self.args.device)
            pass
        self.args.verbose_out("info",f"Disc in {self.args.device}: {disc_info}")
        subdirectory = self.args.directory
        if subdirectory=="":
            if self.config.rip.default_dir=="cddb":
                subdirectory = disc_info.cddb_id.cddb_id
                pass
            else:
                subdirectory = disc_info.musicbrainz_id.mb_id
                pass
            pass
        rip_directory = db.joinpath(self.config.rip.joinpath(subdirectory))

        uniq_id_str = ""
        if self.args.uniq_id!="": uniq_id_str=self.args.uniq_id
        (matches, opt_disc) = db.find_or_create_disc_of_disc_info(disc_info, subdirectory)
        # Set disc.json_path
        # Set disc.src_directory
        if matches<0: # Disc already in system at same rip directory
            assert opt_disc is not None
            disc = opt_disc
            pass
        elif matches==0: # Disc not in system
            disc = db.create_disc(uniq_id_str=uniq_id_str)
            disc.src_directory = str(subdirectory)
            if self.config.database.discs_in_own_json():
                disc.json_path = db.relative_path(rip_directory.joinpath(self.config.database.json_disc))
                pass
            pass
        else: # Disc in system but none have same rip directory
            print(matches, opt_disc)
            raise Exception("Disc may already be in system")
            pass
        disc.update_from_disc_info(disc_info)
        if not self.args.no_musicbrainz:
            print(f"Fetching from musicbrainz id {disc.musicbrainz_id}")
            if db.fetch_mb_disc_data(disc):
                print("Fetched okay")
                pass
            else:
                print("Failed to fetch")
                pass
            pass
        if self.config.database.primary_is_json():
            db.write_json_files(self.config.database.json_root)
            pass
        else:
            db.update_sqlite3(db_path=db.joinpath(self.config.database.dbfile))
            pass

        self.args.verbose_out("info",f"Rip to directory {rip_directory}")
        if rip_directory.exists() and not self.args.rerip:
            raise Exception(f"Path {rip_directory} already exists and not a rerip")
        ripper = Ripper(self.args.device, rip_directory, disc_info)
        ripper.create_directory_if_required()
        disc_info.write_disc_info(rip_directory, force_overwrite=True)
        ripper.rip()
        ripper.compress_files()
        pass
    #f all done
    pass

