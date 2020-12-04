import subprocess
import os.path
import hashlib
import base64
from libturnipripper import CDDB

# Data Classes
class TrackInfo:
    def __init__(self, number):
        self.number = number
        self.lba = 0
        self.lba_extent = 0
        self.length_seconds = 0
        self.title = "Unknown track"
        pass
    def set_title(self, title):
        self.title = title
        pass
    pass
class DiscInfo:
    """ Contains info about the data on a CD. """
    def __init__(self, cddb_id, track_lengths=[], total_length_seconds=0, musicbrainz_string="", cdrecord_output=""):
        self.cddb_id = cddb_id
        self.num_tracks = len(track_lengths)
        self.track_lengths = track_lengths
        self.total_length = total_length_seconds
        self.cdrecord_output = cdrecord_output
        self.musicbrainz_string = musicbrainz_string
        self.artist = "Unknown artist"
        self.title = "Unknown title"
        self.tracks = [TrackInfo(i) for i in range(self.num_tracks)]
        pass
    def write_disc_info(self, source_directory, force_overwrite=False):
        disc_info_filename = os.path.join(source_directory,"disc_info.txt")
        if os.path.exists(disc_info_filename) and not force_overwrite:
            # raise Exception("Cannot write disc info - it already exists")
            pass
        with open(disc_info_filename,"w") as f:
            print(f"{self.cddb_id} {self.as_disc_info()}",file=f)
            print(f"cddb: {self.as_CDDB_track_info()}",file=f)
            print(f"musicbrainz: {self.as_musicbrainz()}",file=f)
            print(f"\nCD record:\n{self.cdrecord_output}",file=f)
            pass
        pass
    def read_disc_info(self, source_directory):
        disc_info_filename = os.path.join(source_directory,"disc_info.txt")
        with open(disc_info_filename) as f:
            for l in f:
                if l[0:8]==self.cddb_id:
                    self.read_disc_info_string(l[8:])
                    pass
                elif l[0:6]=="cddb: ":
                    self.read_CDDB_track_info_string(l[6:])
                    pass
                elif l[0:13]=="musicbrainz: ":
                    self.read_musicbrainz_string(l[13:])
                    pass
                else:
                    pass
                pass
            pass
        pass
    def as_CDDB_track_info(self):
        return [int(self.cddb_id, 16), len(self.track_lengths)] + self.track_lengths + [self.total_length]
    def read_CDDB_track_info_string(self, s):
        pass
    def as_disc_info(self):
        return f"{len(self.track_lengths)} "+(" ".join([str(x) for x in self.track_lengths])) + " "+str(self.total_length)
    def read_disc_info_string(self, s):
        s = s.strip()
        data = [int(x) for x in s.split(" ")]
        if data[0] != len(data)-2:
            raise Exception("Bad disc info string when reading disc_info")
        self.track_lengths = data[1:-1]
        self.total_length = data[-1]
        self.num_tracks = data[0]-2
        self.tracks = [TrackInfo(i) for i in range(self.num_tracks)]
        pass
    def musicbrainz_id(self):
        musicbrainz_data = [int(x) for x in self.musicbrainz_string.split(" ")]
        first=1
        last=musicbrainz_data[0]
        offsets = [musicbrainz_data[-1]]
        offsets.extend(musicbrainz_data[1:-1])
        sha = hashlib.sha1()
        sha.update(f"{first:02X}{last:02x}".encode("utf8"))
        for i in range(100):
            off=0
            if i<len(offsets): off=offsets[i]
            sha.update(f"{off:08X}".encode("utf8"))
            pass
        mb_id = base64.b64encode(sha.digest(),altchars=b"._").replace(b"=",b"-").decode("utf8")
        return mb_id
    def as_musicbrainz(self):
        if self.musicbrainz_string=="": return ("","")
        mb_id = self.musicbrainz_id()
        return (self.musicbrainz_string,mb_id)
    def read_musicbrainz_string(self, s):
        s=s.strip()
        if s[0]!='(' or s[-1]!=')':
            raise Exception("Bad musicbrainz string when reading disc_info")
        data = s[1:-1].split(",")
        if len(data)!=2:
            raise Exception("Bad musicbrainz string when reading disc_info")
        data = [x.strip() for x in data]
        did_mb_id = data[1][1:-1]
        if data[0][0]!="'" or data[0][-1]!="'":
            raise Exception("Bad musicbrainz string when reading disc_info")
        self.musicbrainz_string = data[0][1:-1]
        mb_id = self.musicbrainz_id()
        if mb_id!=did_mb_id:
            raise Exception(f"Mismatch in musicbrainz id when reading disc_info (read {did_mb_id} calculated {mb_id})")
        pass
class CDInfo:
    """ Contains info about the metadata of the tracks on a CD """
    def __init__(self, title_pattern, disc_info, cddb_track_info):
        self.disc_info = disc_info
        self.id = cddb_track_info["DISCID"]
        split_name = cddb_track_info["DTITLE"].split(" / ")
        # TODO: Handle the case where the pattern has invalid indices
        try:
            if len(split_name)==1: split_name.append(split_name[0])
            self.title = split_name[title_pattern.album_index]
            self.artist = split_name[title_pattern.artist_index]
            pass
        except Exception as e:
            raise Exception(f"Failed to parse track title info for id {self.id} of {split_name}")
        self.disc_info.title  = self.title
        self.disc_info.artist = self.artist
        self.tracks = []
        for i in range(disc_info.num_tracks):
            self.tracks.append(cddb_track_info.get("TTITLE" + str(i), "Track " + str(i + 1)))
            self.disc_info.tracks[i].set_title(self.tracks[i])
            pass
        pass

    def as_CDDB_track_info(self):
        return self.disc_info.as_CDDB_track_info()
    def as_disc_info(self):
        return self.disc_info.as_disc_info()
    def as_musicbrainz(self):
        return self.disc_info.as_musicbrainz()
    def cdrecord_output(self):
        return self.disc_info.cdrecord_output
    def __str__(self):
        to_return = "ID: {}\nAlbum: {}\nArtist: {}\nTrack Names: \n".format(self.id, self.title, self.artist)
        highest_track = len(self.tracks)
        highest_digits = (highest_track//10) + 1
        format_str = "\t{0:0"+str(highest_digits)+"d}. {1}\n"
        for i in range(len(self.tracks)):
            to_return += format_str.format(i+1, self.tracks[i])
        return to_return

    @staticmethod
    def create_null(disc_info):
        return CDInfo(CDDB.DTitlePattern(0, 1), disc_info, {"DISCID": disc_info.cddb_id, "DTITLE": "None / None"})

def get_disc_info(device_name):
    """
    Creates a DiscInfo based on the disc that's currently in the CD Drive
    """
    cmd_output = subprocess.getoutput([f"cd-discid {device_name}"]).split(" ")
    try:
        ntracks = int(cmd_output[1])
        pass
    except:
        raise RuntimeError("cd-discid did not return useful information - is it installed? (%s)"%str(cmd_output))
    if len(cmd_output) - 3 != ntracks:
        raise RuntimeError("DiscID mismatch between reported track count and amount of tracks given")
    musicbrainz_string = subprocess.getoutput([f"cd-discid --musicbrainz {device_name}"])
    try:
        cdrecord_output = subprocess.getoutput([f"cdrecord dev={device_name} -toc"])
        pass
    except Exception as e:
        print(f"Failed to get cdrecord output - is it installed - it is nice to record this in the source directory...:\n{e}")
        cdrecord_output = ""
        pass
    return DiscInfo(cmd_output[0], [int(x) for x in cmd_output[2:-1]], int(cmd_output[-1]), musicbrainz_string, cdrecord_output)

def read_disc_info_from_source(source_directory, cddb_id):
    """
    Read disc info from a file 
    """
    disc_info = DiscInfo(cddb_id)
    disc_info.read_disc_info(os.path.join(source_directory,cddb_id))
    return disc_info
