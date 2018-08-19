#!/usr/bin/env python3

import lib
import os

def create_directory(path):
    if not os.path.isdir(path):
        os.makedirs(path)

vgmdb_server = lib.CDDBServer("http://vgmdb.net/~cddb", lib.CDDBDTitlePattern(artist_index = 2, album_index = 1))
normal_server = lib.CDDBServer("http://freedb.freedb.org/~cddb/cddb.cgi")
cddb_interface = lib.CDDBInterface(vgmdb_server, 6, "samuel", "host")
cd_info = lib.get_cd_info(cddb_interface)

print(cd_info)
SOURCE_ROOT = "./test/source"
LIBRARY_ROOT = "./test/library"
source = os.path.join(SOURCE_ROOT, cd_info.id)

create_directory(source)
create_directory(LIBRARY_ROOT)
lib.rip(cd_info, source)
lib.transcode_with_metadata(cd_info, source_directory = source, output_directory = LIBRARY_ROOT, extra_options = ["-compression_level", "12"])
