ICRA's [online program](https://ras.papercept.net/conferences/conferences/ICRA24/program/) is not very computer-friendly.
This script parses the program in python dict and then dump them into yaml files day-wise.
(Maybe this script can be useful for other IEEE conferences as well, where the program is hosted on papercept.net.)

Usage (dump)
```bash
pip3 install -e . -v
python3 -m icra.parse
```

Usage example (search)
```bash
python3 -m icra.search --author "okada.*kei"
python3 -m icra.search --ptitle "planning" --author "kavraki"
```
Usage example (grep)
```bash
grep -i "stitle.*planning" dump/*.yaml -A2

