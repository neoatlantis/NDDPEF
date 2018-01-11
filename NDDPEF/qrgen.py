#!/usr/bin/env python3

import subprocess
import base64

def getQRCodeInDataURI(data):
    cmd = [
        "qrencode",
        "-o", "-", 
        "-l", "L",
        "-t", "PNG",
        "-m", "5",
        "-s", "3",
        data
    ]
    imgdata = subprocess.check_output(cmd)
    return "data:image/png;base64,%s" %\
        base64.b64encode(imgdata).decode('ascii')
