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
