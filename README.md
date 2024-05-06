ICRA's [online program](https://ras.papercept.net/conferences/conferences/ICRA24/program/) is not very computer-friendly.
This script parses the program in python dict and then dump them into yaml files day-wise.

Usage (dump)
```bash
pip install beautifulsoup4
python3 parse.py
```

Usage example (search)
```bash
grep -i "stitle.*planning" dump/*.yaml -A2
```
Output
```
dump/thursday_sessions.yaml:- stitle: <b>Motion Planning I</b>
dump/thursday_sessions.yaml-  stype_name: Oral Session
dump/thursday_sessions.yaml-  stime: 10:30-12:00
--
dump/thursday_sessions.yaml:- stitle: <b>Path Planning for Multiple Mobile Robots or Agents I</b>
dump/thursday_sessions.yaml-  stype_name: Oral Session
dump/thursday_sessions.yaml-  stime: 10:30-12:00
--
...
...
dump/wednesday_sessions.yaml:- stitle: <b>Motion and Path Planning III</b>
dump/wednesday_sessions.yaml-  stype_name: Oral Session
dump/wednesday_sessions.yaml-  stime: 16:30-18:00
--
dump/wednesday_sessions.yaml:- stitle: <b>Manipulation Planning</b>
dump/wednesday_sessions.yaml-  stype_name: Oral Session
dump/wednesday_sessions.yaml-  stime: 16:30-18:00
```
