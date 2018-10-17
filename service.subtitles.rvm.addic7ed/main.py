# -*- coding: utf-8 -*-
# Licence: GPL v.3 http://www.gnu.org/licenses/gpl.html
# The main script contains minimum code to speed up launching on slower systems

import sys
from addic7ed.core import router

if __name__ == '__main__':
    from web_pdb import catch_post_mortem

    with catch_post_mortem():
        router(sys.argv[2][1:])
