# -*- coding: utf-8 -*-
# Licence: GPL v.3 http://www.gnu.org/licenses/gpl.html
# The main script contains minimum code to speed up launching on slower systems

import os
import sys
from xbmcaddon import Addon

sys.path.insert(0, os.path.join(Addon().getAddonInfo('path').decode('utf-8'), 'resources', 'lib'))

from core import router

if __name__ == '__main__':
    router(sys.argv[2][1:])
