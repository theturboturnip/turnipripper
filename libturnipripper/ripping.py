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
def escape_directory_name(directory_name):
    return re.sub(r"[/\\]", "-", directory_name) # This will handle Unicode correctly
def rip_directly(disc_info, cd_info, device, source_directory, ffmpeg="ffmpeg"):
    """
    Rips all tracks from a CD that haven't been ripped yet.
    Stores them in source_directory. Will not create any subfolders for different albums.
    """
    def rip_span(rip_span_start, rip_span_end):
        """ Rips a zero-indexed, inclusive set of tracks from the CD. """
        # CDParanoia takes 1-indexed track indices.
        if rip_span_start == rip_span_end:
            span_str = str(rip_span_start + 1)
            pass
        else:
            span_str = "{}-{}".format(rip_span_start + 1, rip_span_end + 1)
            pass
        try:
            # cdparanoia puts its progress on stderr, which means we cannot pipe stderr for use if the command fails
            completed = subprocess.run(["cdparanoia", "--force-cdrom-device", device, "-B", "--output-wav", span_str], cwd=source_directory)
            pass
        except:
            raise RuntimeError("cdparanoia did not rip correctly - is it installed?")
        if completed.returncode!=0:
            raise RuntimeError("cdparanoia did not rip correctly")
        wav_files = []
        tracks = range(rip_span_start, rip_span_end + 1)
        for i in tracks: # Inclusive range, range() returns exclusive at the end
            wav_files.append(cdparanoia_source_ripped_track_filename(i))
            pass
        # Transcode the WAVs to FLACs with the metadata
        transcode_with_metadata_directly(disc_info,
                                         source_directory, source_directory,
                                         "flac",
                                         ffmpeg = ffmpeg,
                                         extra_options = ["-compression_level", "12"],
                                         input_filename_generator = cdparanoia_source_ripped_track_filename,
                                         output_filename_format = "track{track:02d}.flac",
                                         tracks = tracks,)
        for wav_file in wav_files:
            os.remove(os.path.join(source_directory, wav_file))
        
    filenames = os.listdir(source_directory)
    last_ripped_index = -1
    tracks_that_were_ripped = []
    for i in range(disc_info.num_tracks):
        if ripped_track_filename(i) not in filenames:
            # This track hasn't been ripped. It will be in the future
            tracks_that_were_ripped.append(i)
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
    if last_ripped_index != disc_info.num_tracks - 1:
        rip_span(last_ripped_index + 1, disc_info.num_tracks - 1)
    print("Ripped {0:d} tracks, {1:d} were already ripped".format(len(tracks_that_were_ripped), disc_info.num_tracks - len(tracks_that_were_ripped)))
    pass

def transcode_with_metadata_directly(disc_info,
                                     source_directory,
                                     output_directory,
                                     output_format,
                                     ffmpeg = "ffmpeg",
                                     extra_options = [],
                                     output_ext = None,
                                     input_filename_generator = ripped_track_filename,
                                     output_filename_format = "{track:02d} - {title}.{output_ext}", tracks = []):
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
        tracks = range(disc_info.num_tracks)
        pass
        
    for i in tracks:
        input_filename = os.path.join(source_directory, input_filename_generator(i))
        if not os.path.isfile(input_filename):
            raise RuntimeError("Couldn't find file " + input_filename)
        output_filename = os.path.join(output_directory, escape_directory_name(output_filename_format.format(
            title = disc_info.tracks[i].title,
            track = i + 1,
            output_ext = output_ext
        )))
        translated_ffmpeg_command = [x.format(input_filename = input_filename,
                                              title = disc_info.tracks[i].title,
                                              artist = disc_info.artist,
                                              album = disc_info.title,
                                              output_filename = output_filename,
                                              track = i + 1,
                                              track_count = disc_info.num_tracks)
                                     for x in ffmpeg_command]
        try:
            completed = subprocess.run(translated_ffmpeg_command)
            pass
        except:
            raise RuntimeError("ffmpeg did not transcode correctly - is it installed?")
        if completed.returncode!=0:
            raise RuntimeError("ffmpeg did not transcode correctly")

        pass
    pass

def rip_directory(source_root_directory, disc_info):
    return os.path.join(source_root_directory, escape_directory_name(disc_info.cddb_id))

def rip_to_subdir(disc_info, cd_info, device, source_root_directory, ffmpeg="ffmpeg", force_overwrite=False):
    """
    Wraps rip_directly to rip to a source directory within the root
    """
    source_directory = rip_directory(source_root_directory, disc_info)
    create_directory(source_directory)
    disc_info.write_disc_info(source_directory, force_overwrite)
    if cd_info is not None:
        with open(os.path.join(source_directory,"cd_info.txt"),"w") as f:
            print(f"{cd_info}",file=f)
            pass
        pass
    rip_directly(disc_info, cd_info, device, source_directory, ffmpeg)
    return source_directory
def rip_and_transcode(disc_info, cd_info, device, source_root_directory, output_root_directory, output_format, ffmpeg = "ffmpeg", extra_options = [], output_ext = None):
    """
    Combines rip() and transcode_with_metadata() into a single function.
    """
    source_directory = rip_to_subdir(disc_info, cd_info, device, source_root_directory, ffmpeg)
    output_directory = os.path.join(output_root_directory, escape_directory_name(disc_info.artist), escape_directory_name(disc_info.title))
    create_directory(output_directory)
    transcode_with_metadata_directly(disc_info, source_directory, output_directory, output_format, ffmpeg, extra_options, output_ext)
