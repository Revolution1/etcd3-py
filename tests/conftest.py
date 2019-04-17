import sys

collect_ignore = []
if sys.version_info[0] < 3:  # pragma: no cover
    collect_ignore.append("test_py3")
