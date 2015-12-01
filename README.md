ISA antipirat script
====================
Description
-----------
Script is implemented in Python 3 scripting language and should be used for purposes of school project for subject ISA
at BUT FIT. Main usage is to gather peers list from the torrent server kat.cr and trackers used in its torrents announces.

Usage
-----
usage: antipirat.py [-h] ([-r RSS] [-i INPUT_ANNOUNCEMENT] [-t TORRENT_FILE])
                    [-a TRACKER_ANNONCE_URL]

optional arguments:

    -h, --help            show this help message and exit
    -r RSS, --rss RSS     Passes URL address of RSS feed to script and feed will
                        be downloaded
    -i INPUT_ANNOUNCEMENT, --input-announcement INPUT_ANNOUNCEMENT
                        Passes RSS feed that is already downloaded
    -t TORRENT_FILE, --torrent-file TORRENT_FILE
                        Already downloaded torrent file
    -a TRACKER_ANNONCE_URL, --tracker-annonce-url TRACKER_ANNONCE_URL, --tracker-announce-url TRACKER_ANNONCE_URL
                        Default announcement, all other will be overwritten


Priklady pouzitia
-----------------

    ./antipirat --help
    ./antipirat -r https://kat.cr/movies/?rss=1 
    ./antipirat -i testing_movies_announce.xml 
    ./antipirat -t turbo.kid.2015.eng.720p.webrip.esub.tamilrockers.net.torrent
    ./antipirat -t ./[kat.cr]ubuntu.15.10.desktop.64.bit.torrent -a http://torrent.ubuntu.com:6969/announce
    ./antipirat -r https://kat.cr/movies/?rss=1 -a udp://torrent.gresille.org:80/announce
    ./antipirat -i testing_movies_announce.xml
 

Implementation and data communication
-------------------------------------
All the further details are described in manual.pdf file as this script technical documentation


Makefile
========
`make`        - Will print out an appeal to run a script

`make run`    - will run a script with --help parameter

`make clean`  - deletes temporary and downloaded files

`make pack`   - creates archive `xmasek15.tgz`
