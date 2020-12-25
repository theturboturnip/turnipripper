#a Imports
import json
from pathlib import Path

from .database import Database, DatabaseOpenError
from .command import Command, CommandArgs

import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast

#a Command subclasses
#c DatabaseInitArgs
class DatabaseInitArgs(CommandArgs):
    json:str
    pass
    
#c DatabaseInitCommand
class DatabaseInitCommand(Command):
    #v Properties
    name = "init"
    args_class = DatabaseInitArgs
    args       : DatabaseInitArgs
    parser_args = {
        }
    #f do_command
    def do_command(self) -> None:
        db = None
        try:
            # The following will fail with DatabaseOpenError if files do not exist
            # It will fail with DatabaseConfigError if config is bad
            db = Database.from_config(self.config.database)
            pass
        except DatabaseOpenError:
            pass
        if db is not None:
            raise Exception("Database already exists, it would be bad form to init again")
        db = Database(self.config.database)
        if self.config.database.primary_is_json():
            json_path = Path(self.config.database.json_root)
            db.write_json_files(json_path, must_use_root=True)
            pass
        else:
            db.create_sqlite3(db_path=db.joinpath(self.config.database.dbfile))
            pass
        pass
    #f All done
    pass

#c DatabaseExportArgs
class DatabaseExportArgs(CommandArgs):
    format:str
    file:str
    pass
    
#c DatabaseExportCommand
class DatabaseExportCommand(Command):
    #v Properties
    name = "export"
    args_class = DatabaseExportArgs
    args       : DatabaseExportArgs
    parser_args = {
        ("--format",):{
            "default":"",
            "help":"Format to output in, json or sqlite3",
        },
        ("--file",):{
            "default":"",
            "help":"File to export as required",
            "metavar":"FILE",
        },
        }
    #f do_command
    def do_command(self) -> None:
        if self.args.file=="": raise Exception("File must be specified")
        db = Database.from_config(self.config.database)
        db_path = Path(self.args.file)
        if db_path.exists(): raise Exception(f"File {db_path} already exists, will not overwrite")
        if self.args.format=="json":
            with db_path.open("w") as f:
                json.dump(db.as_single_json(), f, indent=1)
                pass
            pass
        elif self.args.format=="sqlite3":
            db.create_sqlite3(db_path)
            db.update_sqlite3(db_path)
            pass
        else: 
            raise Exception(f"Bad format {self.args.format} - must be json or sqlite3")
        pass
    #f All done
    pass

#c DatabaseCommand
class DatabaseCommand(Command):
    #v Properties
    name = "database"
    parser_args = {
        }
    subcommands = [DatabaseInitCommand, DatabaseExportCommand]
    #f all done
    pass

