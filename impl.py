#!/usr/bin/env python3

import libturnipripper as lib
import os

vgmdb_server = lib.CDDBServer("http://vgmdb.net/~cddb", lib.CDDBDTitlePattern(artist_index = 2, album_index = 1))
normal_server = lib.CDDBServer("http://freedb.freedb.org/~cddb/cddb.cgi")
cddb_interface = lib.CDDBInterface(vgmdb_server, 6, "samuel", "host")
cd_info = lib.get_cd_info(cddb_interface)

print(cd_info)
SOURCE_ROOT = "./test/source"
LIBRARY_ROOT = "./test/library"
lib.rip_and_transcode(cd_info, SOURCE_ROOT, LIBRARY_ROOT, "mp3")
