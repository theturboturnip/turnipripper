#!/usr/bin/env python3
"""
Module for retrieving CDDB v1 data from CDDB servers via HTTP

Written 17 Nov 1999 by Ben Gertzfield <che@debian.org>
This work is released under the GNU GPL, version 2 or later.

Modified August 2018 by Samuel Stark to be class-based, to add an expected output encodings parameter in read() and query()
and to make fully compatible with Python 3.6
"""

import urllib.request, urllib.parse, urllib.error
import string
import socket
import os
import struct
import re
import chardet

# from . import data
import subprocess
import re
import os.path


def decode_string(bytestr, encodings):
    for encoding in encodings:
        try:
            return bytestr.decode(encoding)
        except UnicodeDecodeError as err:
            exception = err
    print(bytestr)
    print(exception)
    return False

def query(track_info, server_url,
          user, host, client_name,
          client_version, proto = 6, expected_output_encodings=["utf8"]):

    disc_id = track_info[0]
    num_tracks = track_info[1]

    query_str = (('%08lx %d ') % (disc_id, num_tracks))

    for i in track_info[2:]:
        query_str = query_str + ('%d ' % i)

    query_str = urllib.parse.quote_plus(query_str.rstrip())

    url = "%s?cmd=cddb+query+%s&hello=%s+%s+%s+%s&proto=%i" % \
          (server_url, query_str, user, host, client_name,
           client_version, proto)

    try:
        response = urllib.request.urlopen(url)
        pass
    except Exception as e:
        raise Exception(f"Failed in cddb query '{url}': {e}")

    # Four elements in header: status, category, disc-id, title
    header = decode_string(response.readline(), expected_output_encodings).split(' ', 3)

    header[0] = int(header[0])

    if header[0] == 200:                # OK
        result = {'category': header[1], 'disc_id': header[2], 'title':
                  header[3]}

        return [header[0], result]

    elif header[0] == 211 or header[0] == 210:  # multiple matches
        result = []

        for line in response.readlines():
            line = decode_string(line, expected_output_encodings)

            if not line:
                continue # Decode failed

            line = line.rstrip()

            if line == '.':             # end of matches
                break
                # otherwise:
                # split into 3 pieces, not 4
                # (thanks to bgp for the fix!)
            match = line.split(' ', 2)

            result.append({'category': match[0], 'disc_id': match[1], 'title':
                           match[2]})

        return [header[0], result]

    else:
        return [header[0], None]


def read(category, disc_id, server_url,
         user, host, client_name,
         client_version, proto = 6, expected_output_encodings=["utf8"]):

    url = "%s?cmd=cddb+read+%s+%s&hello=%s+%s+%s+%s&proto=%i" % \
          (server_url, category, disc_id, user, host, client_name,
           client_version, proto)

    response = urllib.request.urlopen(url)

    header = decode_string(response.readline(), expected_output_encodings).rstrip().split(' ', 3)

    header[0] = int(header[0])
    if header[0] == 210 or header[0] == 417:  # success or access denied
        reply = []

        for line in response.readlines():
            line = decode_string(line, expected_output_encodings).rstrip()

            if not line:
                continue

            if line == '.':
                break

            line = line.replace(r'\t', "\t")
            line = line.replace(r'\n', "\n")
            line = line.replace(r'\\', "\\")

            reply.append(line)

        if header[0] == 210:            # success, parse the reply
            return [header[0], parse_read_reply(reply)]
        else:                           # access denied. :(
            return [header[0], reply]
    else:
        return [header[0], None]


def parse_read_reply(comments):

    len_re = re.compile(r'#\s*Disc length:\s*(\d+)\s*seconds')
    revis_re = re.compile(r'#\s*Revision:\s*(\d+)')
    submit_re = re.compile(r'#\s*Submitted via:\s*(.+)')
    keyword_re = re.compile(r'([^=]+)=(.*)')

    result = {}

    for line in comments:
        keyword_match = keyword_re.match(line)
        if keyword_match:
            (keyword, data) = keyword_match.groups()

            if keyword in result:
                result[keyword] = result[keyword] + data
            else:
                result[keyword] = data
            continue

        len_match = len_re.match(line)
        if len_match:
            result['disc_len'] = int(len_match.group(1))
            continue

        revis_match = revis_re.match(line)
        if revis_match:
            result['revision'] = int(revis_match.group(1))
            continue

        submit_match = submit_re.match(line)
        if submit_match:
            result['submitted_via'] = submit_match.group(1)
            continue

    return result


# CDDB Classes
class DTitlePattern:
    """ 
    Describes how a given servereturns the DTITLE parameter. 
    It is assumed that the server returns an array of data delimited by " / ",
    and the arguments for this class show which indices the artist and album names are contained in.
    """ 
    def __init__(self, artist_index = 0, album_index = 1):
        self.artist_index = artist_index
        self.album_index = album_index
class Server:
    """
    Describes a CDDB server, with an address and a title pattern.
    The CDDB server much be accessible with HTTP, so it may be that the address requires "/~cddb/cddb.cgi" appended to the end.
    """
    def __init__(self, address, dtitle_pattern = None, encodings = ["utf8"]):
        self.address = address
        self.encodings = encodings
        if dtitle_pattern == None:
            self.dtitle_pattern = DTitlePattern()
        else:
            self.dtitle_pattern = dtitle_pattern
class Interface:
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
        return query(disc_info.as_CDDB_track_info(), self.server.address, self.user, self.host, self.client_name, self.client_version, expected_output_encodings=self.server.encodings)
    def read_cddb_track_info(self, cddb_cd_info):
        return read(cddb_cd_info["category"], cddb_cd_info["disc_id"], self.server.address, self.user, self.host, self.client_name, self.client_version, expected_output_encodings=self.server.encodings)[1]
    def read(self, disc_info, cddb_cd_info):
        try:
            info = data.CDInfo(self.server.dtitle_pattern, disc_info, self.read_cddb_track_info(cddb_cd_info))
            pass
        except Exception as e:
            raise Exception(f"Failed to create CDInfo from {disc_info} and {cddb_cd_info}: {e}")
        return info

# CDDB Functions
def get_cddb_cd_info(cddb_interface, disc_info):
    """
    Asks the server for information about the given disc.
    """
    header, available_options = cddb_interface.query(disc_info)
    if header == 200:
        return [available_options]
    elif header == 210 or header == 211:
        return available_options
    else:
        #raise RuntimeError("Couldn't find data for CD")
        return []
def get_cd_info(cddb_interface, disc_info = None, cddb_cd_info = None):
    """
    Returns the CDInfo for the CD in the disc drive.
    """
    if disc_info == None:
        disc_info = get_disc_info()

    if cddb_cd_info == None:
        cddb_cd_info = get_cddb_cd_info(cddb_interface, disc_info)
    if isinstance(cddb_cd_info, (list,)):
        return [cddb_interface.read(disc_info, single_cd_info) for single_cd_info in cddb_cd_info]
    return cddb_interface.read(disc_info, cddb_cd_info)




import json
def new_query(mb_id):
    url = f"https://musicbrainz.org/ws/2/discid/{mb_id}?fmt=json&inc=recordings"
    try:
        response = urllib.request.urlopen(url)
        pass
    except Exception as e:
        raise Exception(f"Failed in musicbrainz query '{url}': {e}")

    # Four elements in header: status, category, disc-id, title
    expected_output_encodings=["utf8"]
    header = decode_string(response.readline(), expected_output_encodings)
    return json.loads(header)

mb_id = "VBy6o5XYjSz_H1rNbLZG5IPujDQ-"
mb_id = "0dep0oaie9KXtUyF7rxJR2LG3Kw-"
mb_id = "Jm1prrQcJ8F2RGhQA_0cijBCjUI-"
mb_id = "lXa3V7_Sui0eQEyX6Ko.eYpnJf8-"
mb_id = ".Glpv6NWyVDxYJh6yzJJb.WpJiE-"
data = new_query(mb_id)
print(list(data.keys()))
if 'id' not in data:
    raise Exception(f"musicbrainz: expected 'id' in returned data but one was not present")
if 'releases' not in data:
    raise Exception(f"musicbrainz: expected 'releases' in returned data but one was not present")
releases = data['releases']
release = releases[0]
print(list(release.keys()))
country = release['country']
date    = release['date']
media   = release['media']
title   = release['title']
mb_release_id   = release['id']
print(date, title, mb_release_id, country)
# print(media) # media should be a list of e.g. disc pressings
n = 1
for m in media:
    if 'discs' in m:
        for disc_pressing in m['discs']: # disc_pressing may be the one we want!
            if disc_pressing['id'] == mb_id:
                media_n = n
                disc_title = m['title']
                disc_of_set = m['position']
                disc_track_offsets = disc_pressing['offsets']
                disc_track_details = m['tracks']
                disc_track_offset = m['track-offset']
                pass
            pass
        pass
    n += 1
    pass
print(title, disc_title, disc_of_set, disc_track_offset, disc_track_offsets)
for dtd in disc_track_details:
    track_number = dtd['number']
    track_position = dtd['position']
    track_title = dtd['title']
    track_rec_length = dtd['recording']['length']
    track_rec_title = dtd['recording']['title']
    print(track_number, track_position, track_rec_length, track_title, track_rec_title)
    pass

