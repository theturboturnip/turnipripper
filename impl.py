#!/usr/bin/env python3

import libturnipripper.CDDB
import libturnipripper.ripping
import os

vgmdb_server = libturnipripper.CDDB.Server("http://vgmdb.net/~cddb", libturnipripper.CDDB.DTitlePattern(artist_index = 2, album_index = 1))
normal_server = libturnipripper.CDDB.Server("http://freedb.freedb.org/~cddb/cddb.cgi")
cddb_interface = libturnipripper.CDDB.Interface(vgmdb_server, 6, "samuel", "host")
cd_info = libturnipripper.CDDB.get_cd_info(cddb_interface)

print(cd_info)
SOURCE_ROOT = "./test/source"
LIBRARY_ROOT = "./test/library"
libturnipripper.ripping.rip_and_transcode(cd_info, SOURCE_ROOT, LIBRARY_ROOT, "mp3")
