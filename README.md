ICRA's [online program](https://ras.papercept.net/conferences/conferences/ICRA24/program/) is not very computer-friendly.
This script parses the program in python dict and then dump them into yaml files day-wise.
(Maybe this script can be useful for other IEEE conferences as well, where the program is hosted on papercept.net.)

### Usage (dump)
```bash
pip3 install -e . -v
python3 -m icra.parse
```
### Usage example (grep)
```bash
grep -i "stitle.*planning" dump/*.yaml -A2
```

### Usage example (search)
```bash
python3 -m icra.search --author "okada.*kei"
python3 -m icra.search --ptitle "planning" --author "kavraki"
```
![image](https://github.com/HiroIshida/icra2024_greppable_program/assets/38597814/f7ac048b-70bc-44e9-8425-0840ae5cd4ef)

