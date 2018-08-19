#!/usr/bin/env python3

import subprocess
import urllib
import CDDB
import re

class DiscInfo:
    def __init__(self, id, track_lengths, total_length_seconds):
        self.id = id
        self.track_lengths = track_lengths
        self.total_length = total_length_seconds
        print("DiscInfo has id %s, %d tracks" % (id, len(track_lengths)))
    def as_CDDB_track_info(self):
        return [int(self.id, 16), len(self.track_lengths)] + self.track_lengths + [self.total_length]
class CDInfo:
    def __init__(self, title_pattern, disc_info, cddb_track_info):
        split_name = cddb_track_info["DTITLE"].split(" / ")
        self.title = split_name[title_pattern.album_index]
        self.artist = split_name[title_pattern.artist_index]
        self.tracks = []
        for i in range(len(disc_info.track_lengths)):
            self.tracks.append(cddb_track_info["TTITLE" + str(i)])

    def __str__(self):
        return str({"title" : self.title, "artist" : self.artist, "tracks" : self.tracks})

class CDDBDTitlePattern:
    def __init__(self, artist_index = 0, album_index = 1):
        self.artist_index = artist_index
        self.album_index = album_index
class CDDBServer:
    def __init__(self, address, dtitle_pattern = None):
        self.address = address
        if dtitle_pattern == None:
            self.dtitle_pattern = CDDBDTitlePattern()
        else:
            self.dtitle_pattern = dtitle_pattern
class CDDBInterface:
    def __init__(self, server, proto, user, host):
        self.client_name = "turnip-ripper"
        self.client_version = "v1"
        self.server = server
        self.proto = proto
        self.user = user
        self.host = host
    def query(self, disc_info):
        return CDDB.query(disc_info.as_CDDB_track_info(), self.server.address, self.user, self.host, self.client_name, self.client_version, expected_output_encodings=["utf8", "shift-jis"])
    def read_cddb_track_info(self, cddb_cd_info):
        return CDDB.read(cddb_cd_info["category"], cddb_cd_info["disc_id"], self.server.address, self.user, self.host, self.client_name, self.client_version, expected_output_encodings=["utf8", "shift-jis"])[1]
    def read(self, disc_info, cddb_cd_info):
        return CDInfo(self.server.dtitle_pattern, disc_info, self.read_cddb_track_info(cddb_cd_info))
    
def get_disc_info():
    cmd_output = subprocess.getoutput(["cd-discid"]).split(" ")
    if len(cmd_output) - 3 != int(cmd_output[1]):
        print("discid mismatch between reported track count and amount of tracks given")
    return DiscInfo(cmd_output[0], [int(x) for x in cmd_output[2:-1]], int(cmd_output[-1]))
def get_cddb_cd_info(cddb_interface, disc_info = None):
    if disc_info == None:
        disc_info = get_disc_info()
    header, available_options = cddb_interface.query(disc_info)
    if header == 200:
        return available_options
    elif header == 210 or header == 211:
        print("Choices:")
        i = 0
        for option in available_options:
            print("%d: %s" % (i, available_options[i]["title"]))
        selection = None
        while selection == None or selection >= len(available_options):
            try:
                selection = int(input("Selection: "))
            except Exception:
                print('\r', end='')
                pass
        return available_options[i]
    else:
        return None
def get_cd_info(cddb_interface, disc_info = None, cddb_cd_info = None):
    if disc_info == None:
        disc_info = get_disc_info()
    if cddb_cd_info == None:
        cddb_cd_info = get_cddb_cd_info(cddb_interface, disc_info)
    return cddb_interface.read(disc_info, cddb_cd_info)


def rip(cd_info):
    subprocess.check_call(["cdparanoia", "-B"])
    pass
