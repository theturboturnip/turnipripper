import subprocess
import hashlib
import base64
from libturnipripper import CDDB

# Data Classes
class DiscInfo:
    """ Contains info about the data on a CD. """
    def __init__(self, id, track_lengths, total_length_seconds, musicbrainz_string, cdrecord_output):
        self.id = id
        self.track_lengths = track_lengths
        self.total_length = total_length_seconds
        self.cdrecord_output = cdrecord_output
        self.musicbrainz_string = musicbrainz_string
        pass
    def as_CDDB_track_info(self):
        return [int(self.id, 16), len(self.track_lengths)] + self.track_lengths + [self.total_length]
    def as_disc_info(self):
        return f"{len(self.track_lengths)} "+(" ".join([str(x) for x in self.track_lengths])) + " "+str(self.total_length)
    def as_musicbrainz(self):
        musicbrainz_data = [int(x) for x in self.musicbrainz_string.split(" ")]
        if len(musicbrainz_data)==0: return ("","")
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
        return (self.musicbrainz_string,mb_id)
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
        self.tracks = []
        for i in range(len(disc_info.track_lengths)):
            self.tracks.append(cddb_track_info.get("TTITLE" + str(i), "Track " + str(i + 1)))

    def as_CDDB_track_info(self):
        return self.disc_info.as_CDDB_track_info()
    def as_disc_info(self):
        return self.disc_info.as_disc_info()
    def as_musicbrainz(self):
        return self.disc_info.as_musicbrainz()
    def cdrecord_output(self):
        return self.disc_info.cdrecord_output
    def __str__(self):
        to_return = "Album: {}\nArtist: {}\nTrack Names: \n".format(self.title, self.artist)
        highest_track = len(self.tracks)
        highest_digits = (highest_track//10) + 1
        format_str = "\t{0:0"+str(highest_digits)+"d}. {1}\n"
        for i in range(len(self.tracks)):
            to_return += format_str.format(i+1, self.tracks[i])
        return to_return

    @staticmethod
    def create_null(disc_info):
        return CDInfo(CDDB.DTitlePattern(0, 1), disc_info, {"DISCID": disc_info.id, "DTITLE": "None / None"})

def get_disc_info():
    """
    Creates a DiscInfo based on the disc that's currently in the CD Drive
    """
    cmd_output = subprocess.getoutput(["cd-discid"]).split(" ")
    try:
        ntracks = int(cmd_output[1])
        pass
    except:
        raise RuntimeError("cd-discid did not return useful information - is it installed? (%s)"%str(cmd_output))
    if len(cmd_output) - 3 != ntracks:
        raise RuntimeError("DiscID mismatch between reported track count and amount of tracks given")
    musicbrainz_string = subprocess.getoutput(["cd-discid --musicbrainz"])
    try:
        cdrecord_output = subprocess.getoutput(["cdrecord dev=/dev/cdrom -toc"])
        pass
    except Exception as e:
        print(f"Failed to get cdrecord output - is it installed - it is nice to record this in the source directory...:\n{e}")
        cdrecord_output = ""
        pass
    return DiscInfo(cmd_output[0], [int(x) for x in cmd_output[2:-1]], int(cmd_output[-1]), musicbrainz_string, cdrecord_output)
