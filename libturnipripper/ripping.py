import subprocess
import re
import os.path

# Ripping/Transcoding functions
def ripped_track_filename(index):
    """ 
    Converts an array index (starting at 0) into the corresponding
    output filename of a track that the program rips
    """
    return "track{0:02d}.flac".format(index + 1)
def cdparanoia_source_ripped_track_filename(index):
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
        subprocess.run(["cdparanoia", "-B", "--output-wav", span_str], check=True, cwd=source_directory)
        
        wav_files = []
        tracks = range(rip_span_start, rip_span_end + 1)
        for i in tracks: # Inclusive range, range() returns exclusive at the end
            wav_files.append(cdparanoia_source_ripped_track_filename(i))
        # Transcode the WAVs to FLACs with the metadata
        transcode_with_metadata(cd_info,
                                source_directory, source_directory,
                                "flac", extra_options = ["-compression_level", "12"],
                                input_filename_generator = cdparanoia_source_ripped_track_filename,
                                output_filename_format = "track{track:02d}.flac",
                                tracks = tracks)
        for wav_file in wav_files:
            os.remove(os.path.join(source_directory, wav_file))
        
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
        rip_span(last_ripped_index + 1, len(cd_info.tracks) - 1)
def transcode_with_metadata(cd_info, source_directory, output_directory, output_format, ffmpeg = "ffmpeg", extra_options = [], output_ext = None, input_filename_generator = ripped_track_filename, output_filename_format = "{track:02d} - {title}.{output_ext}", tracks = []):
    """
    Takes all tracks that have been ripped from the source_directory, and converts them to the given format.
    Also attaches the correct metadata based on the CDInfo.
    Tracks are saved in the output_directory. Like rip(), no subfolders are created.
    """
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
    if tracks == []:
        tracks = range(len(cd_info.tracks))
        
    for i in tracks:
        input_filename = os.path.join(source_directory, input_filename_generator(i))
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
    create_directory(source_directory)
    output_directory = os.path.join(output_root_directory, cd_info.artist, cd_info.title)
    create_directory(output_directory)
    rip(cd_info, source_directory)
    transcode_with_metadata(cd_info, source_directory, output_directory, output_format, ffmpeg, extra_options, output_ext)
