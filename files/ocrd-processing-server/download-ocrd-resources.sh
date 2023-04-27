#!/usr/bin/bash -e
#
# ocrd-tesserocr-recognize is called seperatly (in addition to download '*'), otherwise models
# are not put into venv/share/tessdata

. /home/cloud/repos/ocrd_all/venv/bin/activate
ocrd resmgr download '*'
ocrd resmgr download ocrd-tesserocr-recognize '*'
deactivate
