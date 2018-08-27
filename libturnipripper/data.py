import subprocess

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
        # TODO: Handle the case where the pattern has invalid indices
        self.title = split_name[title_pattern.album_index]
        self.artist = split_name[title_pattern.artist_index]
        self.tracks = []
        for i in range(len(disc_info.track_lengths)):
            self.tracks.append(cddb_track_info["TTITLE" + str(i)])

    def __str__(self):
        return "Album: {}\nArtist: {}\nTrack Names: \n\t{}\n".format(self.title, self.artist, "\n\t".join(self.tracks))

def get_disc_info():
    """
    Creates a DiscInfo based on the disc that's currently in the CD Drive
    """
    cmd_output = subprocess.getoutput(["cd-discid"]).split(" ")
    if len(cmd_output) - 3 != int(cmd_output[1]):
        raise RuntimeError("DiscID mismatch between reported track count and amount of tracks given")
    return DiscInfo(cmd_output[0], [int(x) for x in cmd_output[2:-1]], int(cmd_output[-1]))
