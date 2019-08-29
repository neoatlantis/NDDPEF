#!/usr/bin/env python3

import subprocess
from subprocess import PIPE
import math
import hashlib
import base64
import binascii
import tempfile
import datetime
import json
import struct
import uuid
import mimetypes
from lxml.etree import Element, SubElement, tostring, fromstring

from nacl.secret import SecretBox




class NDDPEFEncoder:

    W = 210
    H = 297
    MARGIN = 15
    COL = 6
    ROW = 7
    DATA_Y_OFFSET = 40 # mm

    def __init__(self):
        self.CODE_SIZE = (self.W - 2 * self.MARGIN) / self.COL
        self.svg = Element("svg", {
            "width": "%smm" % self.W,
            "height": "%smm" % self.H,
            "viewBox": "0 0 %s %s" % (self.W, self.H),
        })
        self.__subelement( # background
            "rect",
            x="0", y="0",
            width=str(self.W),
            height=str(self.H),
            fill="white"
        )
        self.__xCursor = -1
        self.__yCursor = 0
        self.metadata = {
            "mimetype": "application/octet-stream",
            "uuid": str(uuid.uuid4()),
            "creation": datetime.datetime.utcnow().isoformat() + "Z",
        }

    def __subelement(self, name, **kvargs):
        return SubElement(self.svg, name, kvargs)

    def __getLimit(self, eccLevel):
        return int({
            "L": 5768,
            "M": 4504,
            "Q": 3176,
            "H": 2504,
        }[eccLevel] / 8)

    def _addHeader(self):
        g = self.__subelement(
            "g", 
            transform="translate(%s %s)" % (self.MARGIN + 5, self.MARGIN)
        )
        boxW, boxH = self.W - 2 * self.MARGIN - 5, self.DATA_Y_OFFSET - 10
        SubElement(
            g, "rect", x="0", y="0",
            width=str(boxW),
            height=str(boxH),
            stroke="black",
            fill="white"
        )
        keys = ["filename", "", "", "uuid", "mimetype", "digest", "creation"]
        h = 1.5 
        l = 40
        for i in range(0, len(keys)):
            y = (i+1.5) * h * 2.5
            s = SubElement(g, "text", x="2", y=str(y))
            s.set("font-size", str(h/5) + "em")
            s.set("font-family", "monospace")
            s.text = keys[i].upper()
            if keys[i] in self.metadata:
                s = SubElement(g, "text", x=str(l), y=str(y))
                s.set("font-size", str(h/5) + "em")
                s.set("font-family", "monospace")
                s.text = str(self.metadata[keys[i]])
        
        qrcodeSize = 25
        qrcode = self.__getMetaQRCode(size=qrcodeSize)
        qrcode.set("transform", "translate(%s %s)" % (boxW - qrcodeSize - 2.5, 2.5))
        g.append(qrcode)

    def _addSyncLine(self):
        g = Element("g")
        h = 2
        g.set("transform", "translate(5 %s)" % (self.MARGIN + self.DATA_Y_OFFSET-2*h))
        self.svg.append(g)
        count = math.ceil(self.CODE_SIZE * self.ROW / h) + 4
        #(self.H - 2 * self.MARGIN - self.DATA_Y_OFFSET) / (16 * self.ROW)
        for i in range(0, count, 2):
            SubElement(
                g, "rect", x="0", y=str(i*h),
                width="10", height=str(h), fill="black")

    def _addFootnote(self):
        def line(text, i):
            s = self.__subelement( "text",
                x=str(self.MARGIN+5), y=str(self.H - 0.8 * self.MARGIN + i)
            )
            s.set("font-size", "0.25em")
            s.set("font-family", "sans-serif")
            s.text = text
        line("Paperized with NDDPEF, a Python tool written by NeoAtlantis <aurichalka@gmail.com>.", 0)
        line("To destroy the document quickly: destroy the QRCode and UUID in header box.", 4)

    def __getQRCode(self, data, eccLevel):
        cmd = [
            "qrencode", "-o", "-", "-l", eccLevel, "-t", "svg",
            "-8",
            "--background=00000000",
            "-m", "0",
            "-s", "1"
        ]
        p = subprocess.Popen(cmd, stdin=PIPE, stdout=PIPE)
        output, _ = p.communicate(data)
        return output

    def __getMetaQRCode(self, size=25):
        data = json.dumps(self.metadata).encode("ascii")
        qrSVG = fromstring(self.__getQRCode(data, eccLevel="Q"))
        qrSVG.set("width", str(size))
        qrSVG.set("height", str(size))
        g = Element("g")
        g.append(qrSVG)
        return g

    def _addDataQRCode(self, data, eccLevel="L"):
        qrSVG = fromstring(self.__getQRCode(data, eccLevel))

        self.__xCursor += 1
        if self.__xCursor >= self.COL:
            self.__xCursor = 0
            self.__yCursor += 1
        if self.__yCursor >= self.ROW:
            raise Exception("Data too much.")

        realCodeSize = self.CODE_SIZE * 0.9
        qrSVG.set("width", str(realCodeSize))
        qrSVG.set("height", str(realCodeSize))

        x, y = self.MARGIN + 4, self.MARGIN + self.DATA_Y_OFFSET
        x += self.CODE_SIZE * (self.__xCursor + 0.5) - realCodeSize / 2
        y += self.CODE_SIZE * (self.__yCursor + 0.5) - realCodeSize / 2

        g = self.__subelement("g", transform="translate(%s %s)" % (x, y))
        g.append(qrSVG)
        self.svg.append(g)

    def __str__(self):
        return tostring(self.svg, pretty_print=True).decode("utf-8")

    def finish(self):
        self._addHeader()
        self._addSyncLine()
        self._addFootnote()
        return self

    def saveSVG(self, filename):
        open(filename, "w+").write(str(self))

    def saveEPS(self, filename):
        with tempfile.NamedTemporaryFile(mode="w+", delete=True) as f:
            f.write(str(self))
            subprocess.call(["inkscape", "-E", filename, f.name])

    def savePDF(self, filename):
        with tempfile.NamedTemporaryFile(mode="w+", delete=True) as f:
            f.write(str(self))
            subprocess.call(["rsvg-convert", "-f", "pdf", "-o", filename, f.name])

    def read(self, filename, eccLevel="L"):
        mimeType = mimetypes.guess_type(filename, strict=False)[0]
        if mimeType: self.metadata["mimetype"] = mimeType
        return self.data(open(filename, "rb").read(), eccLevel=eccLevel)

    def data(self, data, eccLevel="L"):
        assert type(data) == bytes
        assert eccLevel in "LMQH"

        # Encrypt the file data. We do not want to really keep this data very
        # confidential, so the key is used simply from UUID and reduced to 
        # 128-bits security. This encryption is only for making the paper
        # easy destroyable: just destroying the header will be sufficient.
        # It provides no protection, if the paper was photographed before.

        digest = hashlib.sha256(data).digest()
        encryptKey = self.metadata["uuid"].replace("-", "").encode("ascii")
        nonce = b"0" * SecretBox.NONCE_SIZE # we never reuse a key, no worry
        data = bytes(SecretBox(encryptKey).encrypt(data))

        self.metadata["digest"] = "sha256/96:" + digest.hex()[:24]
        tag = digest[:4]

        totalSlices = self.ROW * self.COL
        dataSizePerSlice = math.ceil(len(data) / totalSlices)
        sliceSize = int((dataSizePerSlice + 5) * 1.25) + 2
        if sliceSize > self.__getLimit(eccLevel):
            raise Exception("File too large.")
        offset = 0
        i = 0
        while data:
            sliceData = data[:dataSizePerSlice]
            data = data[dataSizePerSlice:]
            # embed sliceData
            headerData = bytes([i]) + tag  # sequence number + data tag
            embedData = headerData + sliceData
            self._addDataQRCode(
                b"[" + base64.b85encode(embedData) + b"]",
                eccLevel=eccLevel
            )
            i += 1
        return self

if __name__ == "__main__":
    import os
    x = NDDPEFEncoder()

#    x.data(os.urandom(11000)).finish().saveSVG("test.svg")
    x.read("qrgen.py").finish().saveSVG("test.svg")
    x.savePDF("test.pdf")

