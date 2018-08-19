#!/usr/bin/env python3

import subprocess
import urllib
import CDDB
import re
import os.path

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
        self.id = cddb_track_info["DISCID"]
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
        if len(available_options) == 1:
            return available_options[0]
        print("Choices:")
        i = 0
        for option in available_options:
            print("%d: %s" % (i, available_options[i]["title"]))
        selection = None
        while selection == None or selection >= len(available_options) or selection < 0:
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

def ripped_track_filename(index):
    return "track{0:02d}.cdda.wav".format(index + 1)

def rip(cd_info, source_directory = "./"):
    def rip_span(span_str):
        subprocess.run(["cdparanoia", "-B", span_str], check=True, cwd=source_directory)
    
    filenames = os.listdir(source_directory)
    #track_is_downloaded = [False] * len(cd_info.tracks)
    last_downloaded_index = -1
    for i in range(len(cd_info.tracks)):
        if ripped_track_filename(i) in filenames:
            #track_is_downloaded[i] = True
            if last_downloaded_index + 1 != i:
                # Download the tracks that haven't been installed yet
                span_to_rip = str(last_downloaded_index + 1 + 1)
                if (i - 1) > last_downloaded_index + 1:
                    span_to_rip += "-" + str(i - 1 + 1)
                rip_span(span_to_rip)
            last_downloaded_index = i
    if last_downloaded_index != len(cd_info.tracks) - 1:
        rip_span(str(last_downloaded_index + 1 + 1) + "-" + str(len(cd_info.tracks)))
def transcode_with_metadata(cd_info, source_directory = "./source/", output_directory = "./", ffmpeg = "ffmpeg", output_format = "flac", extra_options = [], output_ext = None):
    if output_ext == None:
        output_ext = output_format
    ffmpeg_command = ["ffmpeg", "-i", "{input_filename}", "-c:a", output_format,
                      *extra_options,
                      "-metadata", "title=\"{title}\"",
                      "-metadata", "artist=\"{artist}\"",
                      "-metadata", "album=\"{album}\"",
                      "-y",
                      "{output_filename}"]
    output_filename_format = "{index:02d} - {title}.{output_ext}"
    for i in range(len(cd_info.tracks)):
        input_filename = os.path.join(source_directory, ripped_track_filename(i))
        if not os.path.isfile(input_filename):
            raise RuntimeError("Couldn't find file " + input_filename)
        output_filename = os.path.join(output_directory, output_filename_format.format(
            title = cd_info.tracks[i],
            index = i+1,
            output_ext = output_ext
        ))
        translated_ffmpeg_command = [x.format(input_filename = input_filename,
                                              title = cd_info.tracks[i],
                                              artist = cd_info.artist,
                                              album = cd_info.title,
                                              output_filename = output_filename)
                                     for x in ffmpeg_command]
        subprocess.run(translated_ffmpeg_command, check=True)
