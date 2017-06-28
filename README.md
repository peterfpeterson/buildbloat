buildbloat
==========

Converts [ninja](https://ninja-build.org/) build logs to
[webtreemap](https://github.com/emvar/webtreemap) json files.

Run `ninja -t recompact` first ot make sure that no duplicate entries
are in the build log, and use a ninja newer than 1.4 to make sure
recompaction removes old, stale buildlog entries. Also, ``ccache``
should be disabled so it does not hide unchanged files.

Usage:

    ninja clean
    cmake .
    rm .ninja_log
    CCACHE_DISABLE=1 ninja
    buildbloat.py .ninja_log
