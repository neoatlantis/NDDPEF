#!/usr/bin/env python3

import hashlib
import base64
import json
import re

sha256 = lambda i: base64.b64encode(hashlib.sha256(i).digest()).decode('ascii')[:8]
fingerprint = lambda i: hashlib.sha256(i).hexdigest().upper()[:32]

class NddpefDecoder:

    def __init__(self, data):
        assert type(data) == str
        self.__slices = {}
        self.__indexes = {}

        self.findIndexes(data)
        self.buildSlices(data)

    def findIndexes(self, data):
        # find likely-to-be indexes
        regexp = "\\{[0-9a-zA-Z\\+\\\\\\s:\"\\[\\]\\,]+\\}"
        possibleIndexes = [
            i for i in re.findall(regexp, data)
            if "checksums" in i
        ]
        # verify using json
        indexes = []
        for each in possibleIndexes:
            try:
                parsed = json.loads(each)
                assert "fingerprint" in parsed
                assert type(parsed["fingerprint"]) == str
                assert "checksums" in parsed
                assert type(parsed["checksums"]) == list
                assert "version" in parsed
                indexes.append(parsed)
            except:
                continue
        # maybe a good index list, but we are not sure!
        for each in indexes:
            self.__indexes[each["fingerprint"]] = each["checksums"]

    def buildSlices(self, data):
        regexp = "\\.[0-9A-Za-z\\+\\\\]{8}\\.{2}[0-9a-zA-Z#%&@~_`;\\!\\$\\(\\)\\*\\+\\-\\<\\=\\>\\?\\^\\{\\|\\}]+\\."
        slices = re.findall(regexp, data)

        for each in slices:
            l = each.split("..")
            checksum = l[0][1:]
            data = l[1][:-1].encode('ascii')
            calcChecksum = sha256(data)
            if calcChecksum != checksum: continue
            self.__slices[checksum] = data

    def output(self):
        for fp in self.__indexes:
            # check requirements for a given index
            requirements = self.__indexes[fp]
            requirementsOK = True
            for sliceID in requirements:
                if sliceID not in self.__slices:
                    print("%s not found." % sliceID)
                    requirementsOK = False
                    break
            if not requirementsOK:
                continue
            # try to decode 
            print("Found one [%s], decoding..." % fp)
            try:
                data = ''.join([
                    self.__slices[i].decode('ascii') for i in requirements
                ])
                data = base64.b85decode(data)
                assert fingerprint(data) == fp
            except:
                print("Failed in decoding, ignored.")
                continue
            # save to file
            open("%s.nddpef" % fp, "wb+").write(data)
            print("Found data written to %s.nddpef" % fp)


