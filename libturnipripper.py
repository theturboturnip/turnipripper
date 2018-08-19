#!/usr/bin/env python3

import subprocess
import urllib
import CDDB
import re
import os.path

# Data Classes
class DiscInfo:
    """ Contains info about the data on a CD. """
    def __init__(self, id, track_lengths, total_length_seconds):
        self.id = id
        self.track_lengths = track_lengths
        self.total_length = total_length_seconds
    def as_CDDB_track_info(self):
        return [int(self.id, 16), len(self.track_lengths)] + self.track_lengths + [self.total_length]
class CDInfo:
    """ Contains info about the metadata of the tracks on a CD """
    def __init__(self, title_pattern, disc_info, cddb_track_info):
        self.id = cddb_track_info["DISCID"]
        split_name = cddb_track_info["DTITLE"].split(" / ")
        self.title = split_name[title_pattern.album_index]
        self.artist = split_name[title_pattern.artist_index]
        self.tracks = []
        for i in range(len(disc_info.track_lengths)):
            self.tracks.append(cddb_track_info["TTITLE" + str(i)])

    def __str__(self):
        return "Album: {}\nArtist: {}\nTrack Names: \n\t{}\n".format(self.title, self.artist, "\n\t".join(self.tracks))

# CDDB Classes
class CDDBDTitlePattern:
    """ 
    Describes how a given servereturns the DTITLE parameter. 
    It is assumed that the server returns an array of data delimited by " / ",
    and the arguments for this class show which indices the artist and album names are contained in.
    """ 
    def __init__(self, artist_index = 0, album_index = 1):
        self.artist_index = artist_index
        self.album_index = album_index
class CDDBServer:
    """
    Describes a CDDB server, with an address and a title pattern.
    The CDDB server much be accessible with HTTP, so it may be that the address requires "/~cddb/cddb.cgi" appended to the end.
    """
    def __init__(self, address, dtitle_pattern = None):
        self.address = address
        if dtitle_pattern == None:
            self.dtitle_pattern = CDDBDTitlePattern()
        else:
            self.dtitle_pattern = dtitle_pattern
class CDDBInterface:
    """
    Describes an interface to a given CDDB server.
    Use query(disc_info) to ask the server about what data matches a given disc.
    Use read(disc_info, cddb_cd_info) to ask the server about the track data for a given instance of CD data.
    """
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

# CDDB Functions
def get_disc_info():
    """
    Creates a DiscInfo based on the disc that's currently in the CD Drive
    """
    cmd_output = subprocess.getoutput(["cd-discid"]).split(" ")
    if len(cmd_output) - 3 != int(cmd_output[1]):
        raise RuntimeError("discid mismatch between reported track count and amount of tracks given")
    return DiscInfo(cmd_output[0], [int(x) for x in cmd_output[2:-1]], int(cmd_output[-1]))
def get_cddb_cd_info(cddb_interface, disc_info):
    """
    Asks the server for information about the given disc,
    asking the user to resolve any conflicts where a disc ID has multiple sets of data.
    """
    # TODO: This should be able to fallback on different servers if one server doesn't have the data the user wants.
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
def get_cd_info(cddb_interface):
    """
    Returns the CDInfo for the CD in the disc drive.
    """
    disc_info = get_disc_info()
    cddb_cd_info = get_cddb_cd_info(cddb_interface, disc_info)
    return cddb_interface.read(disc_info, cddb_cd_info)

# Ripping/Transcoding functions
def ripped_track_filename(index):
    """ 
    Converts an array index (starting at 0) into the corresponding
    output filename of a track ripped by CDParanoia
    """
    return "track{0:02d}.cdda.wav".format(index + 1)
def create_directory(path):
    """ Creates the directory and all parent directories in the path, if they don't already exist. """
    if not os.path.isdir(path):
        os.makedirs(path)
def rip(cd_info, source_directory):
    """
    Rips all tracks from a CD that haven't been ripped yet.
    Stores them in source_directory. Will not create any subfolders for different albums.
    """
    def rip_span(rip_span_start, rip_span_end):
        """ Rips a zero-indexed, inclusive set of tracks from the CD. """
        # CDParanoia takes 1-indexed track indices.
        if rip_span_start == rip_span_end:
            span_str = str(rip_span_start + 1)
        else:
            span_str = "{}-{}".format(rip_span_start + 1, rip_span_end + 1)
        subprocess.run(["cdparanoia", "-B", span_str], check=True, cwd=source_directory)
    
    filenames = os.listdir(source_directory)
    last_ripped_index = -1
    for i in range(len(cd_info.tracks)):
        if ripped_track_filename(i) not in filenames:
            # This track hasn't been ripped.
            continue
        # This track has been ripped.
        # If the last track that we know was ripped wasn't the last one...
        if last_ripped_index != i - 1:
            # Rip the span of tracks that haven't been ripped yet.
            # Starting at 1 after the last known ripped track,
            # and ending one before the previous track.
            rip_span(last_ripped_index + 1, i - 1)
        last_ripped_index = i
    # If there are still tracks left to be ripped, rip them.
    if last_ripped_index != len(cd_info.tracks) - 1:
        rip_span(last_downloaded_index + 1, len(cd_info.tracks) - 1)
def transcode_with_metadata(cd_info, source_directory, output_directory, output_format, ffmpeg = "ffmpeg", extra_options = [], output_ext = None):
    """
    Takes all tracks that have been ripped from the source_directory, and converts them to the given format.
    Also attaches the correct metadata based on the CDInfo.
    Tracks are saved in the output_directory. Like rip(), no subfolders are created.
    """
    create_directory(output_directory)
    if output_ext == None:
        output_ext = output_format
    ffmpeg_command = ["ffmpeg", "-i", "{input_filename}", "-c:a", output_format,
                      *extra_options,
                      "-metadata", "title={title}",
                      "-metadata", "artist={artist}",
                      "-metadata", "album={album}",
                      "-metadata", "track={track}/{track_count}",
                      "-y",
                      "{output_filename}"]
    output_filename_format = "{track:02d} - {title}.{output_ext}"
    for i in range(len(cd_info.tracks)):
        input_filename = os.path.join(source_directory, ripped_track_filename(i))
        if not os.path.isfile(input_filename):
            raise RuntimeError("Couldn't find file " + input_filename)
        output_filename = os.path.join(output_directory, output_filename_format.format(
            title = cd_info.tracks[i],
            track = i + 1,
            output_ext = output_ext
        ))
        translated_ffmpeg_command = [x.format(input_filename = input_filename,
                                              title = cd_info.tracks[i],
                                              artist = cd_info.artist,
                                              album = cd_info.title,
                                              output_filename = output_filename,
                                              track = i + 1,
                                              track_count = len(cd_info.tracks))
                                     for x in ffmpeg_command]
        subprocess.run(translated_ffmpeg_command, check=True)
def rip_and_transcode(cd_info, source_root_directory, output_root_directory, output_format, ffmpeg = "ffmpeg", extra_options = [], output_ext = None):
    """
    Combines rip() and transcode_with_metadata() into a single function.
    """
    source_directory = os.path.join(source_root_directory, cd_info.id)
    output_directory = os.path.join(output_root_directory, cd_info.artist, cd_info.title)
    rip(cd_info, source_directory)
    transcode_with_metadata(cd_info, source_directory, output_directory, output_format, ffmpeg, extra_options, output_ext)
