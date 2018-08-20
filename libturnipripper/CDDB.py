import subprocess
import re
import os.path

#!/usr/bin/env python3
"""
Module for retrieving CDDB v1 data from CDDB servers via HTTP

Written 17 Nov 1999 by Ben Gertzfield <che@debian.org>
This work is released under the GNU GPL, version 2 or later.

Modified August 2018 by Samuel Stark to be class-based an expected output encodings parameter in read() and query()
and to make fully compatible with Python 3.6
"""

import urllib.request, urllib.parse, urllib.error
import string
import socket
import os
import struct
import re
import chardet

from . import data

def decode_string(bytestr, encodings):
    for encoding in encodings:
        try:
            return bytestr.decode(encoding)
        except UnicodeDecodeError as err:
            exception = err
    print(bytestr)
    raise exception

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

    response = urllib.request.urlopen(url)

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
            line = decode_string(line, expected_output_encodings).rstrip()

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
    def __init__(self, address, dtitle_pattern = None):
        self.address = address
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
        return query(disc_info.as_CDDB_track_info(), self.server.address, self.user, self.host, self.client_name, self.client_version, expected_output_encodings=["shift-jis", "euc-jp", "utf8"])
    def read_cddb_track_info(self, cddb_cd_info):
        return read(cddb_cd_info["category"], cddb_cd_info["disc_id"], self.server.address, self.user, self.host, self.client_name, self.client_version, expected_output_encodings=["shift-jis", "euc-jp", "utf8"])[1]
    def read(self, disc_info, cddb_cd_info):
        return data.CDInfo(self.server.dtitle_pattern, disc_info, self.read_cddb_track_info(cddb_cd_info))

# CDDB Functions
def get_disc_info():
    """
    Creates a DiscInfo based on the disc that's currently in the CD Drive
    """
    cmd_output = subprocess.getoutput(["cd-discid"]).split(" ")
    if len(cmd_output) - 3 != int(cmd_output[1]):
        raise RuntimeError("discid mismatch between reported track count and amount of tracks given")
    return data.DiscInfo(cmd_output[0], [int(x) for x in cmd_output[2:-1]], int(cmd_output[-1]))
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
            i += 1
        selection = None
        while selection == None or selection >= len(available_options) or selection < 0:
            try:
                selection = int(input("Selection: "))
            except Exception:
                print('\r', end='')
                pass
        return available_options[selection]
    else:
        raise RuntimeError("Couldn't find data for CD")
def get_cd_info(cddb_interface):
    """
    Returns the CDInfo for the CD in the disc drive.
    """
    disc_info = get_disc_info()
    cddb_cd_info = get_cddb_cd_info(cddb_interface, disc_info)
    return cddb_interface.read(disc_info, cddb_cd_info)
