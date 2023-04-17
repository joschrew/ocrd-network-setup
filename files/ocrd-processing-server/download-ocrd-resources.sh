#!/usr/bin/bash -e
#
# This downloads the ocrd-resources. A container is used so that all processors independend from
# local setup will be downloaded.
#
# Updates are not planned, they should be done with `ocrd resmgr` on the vm itself. Purpose of this
# script is only to make the initial download of models

DEST="/home/cloud/.local/share/ocrd-resources"

mkdir -p $DEST

# Download ocrd resources
docker run --rm -v "$DEST:/usr/local/share/ocrd-resources" -- ocrd/all:maximum ocrd resmgr download -a '*'

# Download tesserocr-recognize resources (apperently isn't covered/downloaded with previous call)
docker run --rm -v "$DEST:/usr/local/share/ocrd-resources" -- ocrd/all:maximum ocrd resmgr download -a '*'
docker run --rm -v "$DEST/ocrd-tesserocr-recognize:/usr/local/share/tessdata" -- ocrd/all:maximum ocrd resmgr download ocrd-tesserocr-recognize '*'
