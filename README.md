NeoAtlantis Digital Data Paper Exchange Format(NDDPEF) v1
=========================================================

NDDPEF is a format customized by @NeoAtlantis for storing small data on a piece
of paper. Currently around 14kB of arbitary data can be stored relative
reliably.

Usage
=====

This tools requires following packages installed on your system:

1. `wkhtmltopdf`
2. `qrencode`

To install NDDPEF, use PyPI:

```
$ sudo pip3 install NDDPEF
```

To encode a file, use command:

```
python3 -m NDDPEF encode <FILENAME GOES HERE>
```

See `python3 -m NDDPEF -h` for more description on usage.
