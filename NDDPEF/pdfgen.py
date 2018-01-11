#!/usr/bin/env python3

import math
import pdfkit
from datetime import datetime, timezone

nowdate = lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def showFingerprint(f):
    return "%s %s<br />%s %s" % (f[0:8], f[8:16], f[16:24], f[24:32])

def getPDF(e, filename=False, w=3, title=""):
    insertImage = lambda d, z="": '<img src="%s" %s/>' % (d, z)

    imgIndex = e.getIndex()
    imgSlices = e.getSlices()
    fingerprint = showFingerprint(e.fingerprint)
    total = len(imgSlices)

    slicesTable = []
    hmax = math.ceil(total / w)
    for i in range(0, hmax):
        slicesTable.append(imgSlices[i * w:][:w])

    metahtml = """
    <table class="meta" width="100%%">
        <tr>
        <td align="left" valign="top">
            <span class="item">Metadata</span><br />
            %s
        </td>
        <td class="lb" width="40%%" align="left" valign="top">
            <span class="item">Title</span><br />%s<br /><p>
            <span class="item">Comment</span>
        </td>
        <td class="lb" align="right" valign="top">
            <span class="item">Total blocks</span><br />%d<p>
            <span class="item">Fingerprint</span><br />
            %s
            <p>
            <span class="item">Date</span><br />%s
        </td>
        </tr>
    </table>
    """ % (
        insertImage(imgIndex, 'style="max-height: 10em"'),
        title,
        total,
        fingerprint,
        nowdate()
    )

    html = """
    <html>
        <head>
            <style>
                @import url('https://fonts.googleapis.com/css?family=Share+Tech+Mono');
                hr {border: 0.5px solid black}
                .meta td{ padding: 0.5em; }
                td.lb {
                    border-style: solid; border-width: 0px 0px 0px 1px;
                }
                .item{
                    text-decoration: underline;
                }
                .meta {
                    font-family: 'Share Tech Mono', monospace;
                    font-size: 16pt;
                }
                #data img{
                    max-width: 100%%;
                    max-height: 100%%;
                    width: auto;
                    height: auto;
                }
            </style>
        </head>
        <body>
            <div class="meta">
                NeoAtlantis Digital Data Paper Exchange Format
            </div>
            <hr />
            %s
            <hr />
            <div id="data">
            <table> %s </table>
            </div>
            <hr />
            <span class="meta">
                <span class="item">Signature and/or Postscript</span>
            </span>
        </body>
    </html>
    """ % (
        metahtml,
        "".join([
            "<tr>%s</tr>" % 
            "".join(["<td>%s</td>" % insertImage(i) for i in row])
            for row in slicesTable
        ])
    )

#    print(html)

    return pdfkit.from_string(html, filename)
