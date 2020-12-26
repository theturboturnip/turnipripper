#a Imports
import sys
import os
import tempfile
import subprocess

import typing
from typing import Iterable, Optional, ClassVar, TypeVar, Type, Union, List, Dict, Tuple, Set, Any, cast

#a Classes
#c Editor
class Editor(object):
    editor : ClassVar[str] = os.environ.get("EDITOR", "vim")
    def __init__(self) -> None:
        return
    def edit_string(self, input_str:str, file_type=".txt") -> Tuple[bool, str]:
        with tempfile.NamedTemporaryFile(suffix=file_type) as f:
            edit_command = [self.editor, f.name]
            f.write(input_str.encode("utf8"))
            f.flush()
            edit_rc = subprocess.call(edit_command)
            f.seek(0)
            output_str = f.read().decode("utf8")
            pass
        return (output_str!=input_str, output_str)
    pass
