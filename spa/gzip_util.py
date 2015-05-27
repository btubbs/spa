import zlib
import struct
import time

def parse_encoding_header(header):
    """
    Break up the `HTTP_ACCEPT_ENCODING` header into a dict of the form,
    {'encoding-name':qvalue}.
    """
    encodings = {'identity':1.0}

    for encoding in header.split(","):
        if(encoding.find(";") > -1):
            encoding, qvalue = encoding.split(";")
            encoding = encoding.strip()
            qvalue = qvalue.split('=', 1)[1]
            if(qvalue != ""):
                encodings[encoding] = float(qvalue)
            else:
                encodings[encoding] = 1
        else:
            encodings[encoding] = 1
    return encodings


def gzip_requested(accept_encoding_header):

    """
    Check to see if the client can accept gzipped output, and whether or
    not it is even the preferred method. If `identity` is higher, then no
    gzipping should occur.
    """
    encodings = parse_encoding_header(accept_encoding_header)

    # Do the actual comparisons
    if('gzip' in encodings):
        return encodings['gzip'] >= encodings['identity']

    elif('*' in encodings):
        return encodings['*'] >= encodings['identity']

    else:
        return False


# After much Googling and gnashing of teeth, this function stolen from
# cherrypy.lib.encoding seems to be the most straightforward way to do gzip
# encoding of a stream without loading the whole thing into memory at once.
def compress(chunks, compress_level, close=True):
    """
    Compress 'chunks' at the given compress_level, where 'chunks' is an iterable
    over chunks of bytes.  If close=True, then look for .close() method on chunks
    and call that when done iterating.
    """
    try:
        # See http://www.gzip.org/zlib/rfc-gzip.html
        yield '\x1f\x8b'       # ID1 and ID2: gzip marker
        yield '\x08'           # CM: compression method
        yield '\x00'           # FLG: none set
        # MTIME: 4 bytes
        yield struct.pack("<L", int(time.time()) & int('FFFFFFFF', 16))
        yield '\x02'           # XFL: max compression, slowest algo
        yield '\xff'           # OS: unknown

        crc = zlib.crc32("")
        size = 0
        zobj = zlib.compressobj(compress_level,
                                zlib.DEFLATED, -zlib.MAX_WBITS,
                                zlib.DEF_MEM_LEVEL, 0)
        for chunk in chunks:
            size += len(chunk)
            crc = zlib.crc32(chunk, crc)
            yield zobj.compress(chunk)
        yield zobj.flush()

        # CRC32: 4 bytes
        yield struct.pack("<L", crc & int('FFFFFFFF', 16))
        # ISIZE: 4 bytes
        yield struct.pack("<L", size & int('FFFFFFFF', 16))
    finally:
        if close and hasattr(chunks, 'close'):
            chunks.close()
