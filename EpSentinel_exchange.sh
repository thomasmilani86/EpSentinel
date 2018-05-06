#!/bin/bash

# Wait for network to settle
sleep 20

# Proceed to exchanges
scp /home/thomas/.kodi/userdata/Database/MyVideos93.db pi@192.168.0.124:EpSentinel
scp pi@192.168.0.124:EpSentinel/tpb_links.html /home/thomas/Bureau
