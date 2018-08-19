#!/usr/bin/env python3

import lib

vgmdb_server = lib.CDDBServer("http://vgmdb.net/~cddb", lib.CDDBDTitlePattern(artist_index = 2, album_index = 1))
normal_server = lib.CDDBServer("http://freedb.freedb.org/~cddb/cddb.cgi")
cddb_interface = lib.CDDBInterface(normal_server, 6, "samuel", "host")
print(lib.get_cd_info(cddb_interface))
