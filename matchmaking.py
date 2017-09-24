#!/usr/bin/env python

# this only works on linux

import daemon
from matchmakingserver import main

with daemon.DaemonContext():
    main()
