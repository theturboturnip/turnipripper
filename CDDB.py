#!/usr/bin/env python3
"""
Module for retrieving CDDB v1 data from CDDB servers via HTTP

Written 17 Nov 1999 by Ben Gertzfield <che@debian.org>
This work is released under the GNU GPL, version 2 or later.

Modified by Samuel Stark to include an expected output encodings parameter in read() and query()
and to make fully compatible with Python 3.6
"""

import urllib.request, urllib.parse, urllib.error
import string
import socket
import os
import struct
import re

name = 'CDDB.py'
version = 1.4

if 'EMAIL' in os.environ:
    (default_user, hostname) = string.split(os.environ['EMAIL'], '@')
else:
    default_user = os.geteuid() or os.environ['USER'] or 'user'
    hostname = socket.gethostname() or 'host'

# Use protocol version 5 to get DYEAR and DGENRE fields.
proto = 5
default_server = 'http://freedb.freedb.org/~cddb/cddb.cgi'

def decode_string(bytestr, encodings):
    for encoding in encodings:
        try:
            return bytestr.decode(encoding)
        except UnicodeDecodeError as err:
            exception = err
    raise exception

def query(track_info, server_url=default_server,
          user=default_user, host=hostname, client_name=name,
          client_version=version, expected_output_encodings=["utf8"]):

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


def read(category, disc_id, server_url=default_server,
         user=default_user, host=hostname, client_name=name,
         client_version=version, expected_output_encodings=["utf8"]):

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
