#!/usr/bin/env python3

import hashlib
import base64
import json

from .qrgen import getQRCodeInDataURI as qrencode

sha256 = lambda i: base64.b64encode(hashlib.sha256(i).digest()).decode('ascii')[:8]
fingerprint = lambda i: hashlib.sha256(i).hexdigest().upper()[:32]


W = 6
H = 6
EACH_LENGTH = 500

class NddpefEncoder:
    """Divide the original data into slices, and generate an index block
    for the whole data.

        fingerprint: the SHA256 hash of original data
        slices: an array of strings containing base-85 encoded and in
                `EACH_LENGTH` divided slices of original data
        checksums: SHA-256 checksums of slices

    Slices are then converted into QR codes identified by their checksums.
    With index block known, it's easy to reconstruct the slices back and
    resume into original data file.
    """

    def __init__(self, data, filename=None):
        assert type(data) == bytes

        if filename:
            assert type(filename) == str and len(filename) < 128
        else:
            filename = ""

        # preprocessing data

        self.filename = filename
        self.fingerprint = fingerprint(data)
        
        # slice data
        
        self.slices = []
        self.checksums = []

        data = base64.b85encode(data)
        if len(data) > W * H * EACH_LENGTH:
            raise Exception("Input data too long.")

        while data:
            s = data[:EACH_LENGTH]
            self.slices.append(s.decode('ascii'))
            self.checksums.append(sha256(s))
            data = data[EACH_LENGTH:]

    def getIndex(self):
        data = {
            "version": 1,
            "fingerprint": self.fingerprint,
            "checksums": self.checksums,
            "filename": self.filename,
        }
        dataj = json.dumps(data)
        return qrencode(dataj)

    def getSlices(self):
        ret = []

        imax = len(self.slices)
        for i in range(0, imax):
            checksum = self.checksums[i]
            data = self.slices[i]

            data = ".%s..%s." % (checksum, data)
            ret.append(qrencode(data))
            
        return ret
