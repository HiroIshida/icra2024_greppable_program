from dataclasses import dataclass, asdict
from enum import Enum 
import re
from typing import List, Tuple, Optional


class SessionType(Enum):
    ORAL = "Oral Session"
    POSTER = "Poster Session"
    AWARD = "Award Session"
    KEYNOTE = "Keynote Session"
    PLENARY = "Plenary Session"
    EXPO = "Expo Session"


@dataclass
class Presentation:
    title: str
    authors: List[Tuple[str, str]]
    abstract: str


@dataclass
class Session:
    name: str
    stype: SessionType
    chair: Optional[Tuple[str, str]]
    cochair: Optional[Tuple[str, str]]
    presentations: List[Presentation]

    def __post_init__(self):
        assert self.name is not None
        if self.stype in (SessionType.POSTER, SessionType.PLENARY):
            assert self.chair is None
            assert self.cochair is None
        else:
            # one of chair or cochair should be present
            assert self.chair is not None or self.cochair is not None


def extract_tr_contents(html):
    tr_contents = []
    start_index = 0

    while True:
        start_index = html.find("<tr", start_index)
        if start_index == -1:
            break

        end_index = html.find("</tr>", start_index)
        if end_index == -1:
            break

        tr_content = html[start_index:end_index+5]
        tr_contents.append(tr_content.strip())

        start_index = end_index + 5

    return tr_contents


def extract_presentations(tr_contents: List[str], st: SessionType) -> List[Presentation]:
    # find presentations and group them
    ptitles = []
    ptitle_start_indices = []
    for i, c in enumerate(contents):
        if "pTtl" in c:
            pattern1 = r'<a href="" onclick="viewAbstract\(.*?\); return false" title="Click to show or hide the keywords and abstract \(text summary\)">(.*?)</a>'
            pattern2 = r'<span class="pTtl"> (.*?)</span>'
            match1 = re.search(pattern1, c)
            match2 = re.search(pattern2, c)
            if match1:
                ptitle = match1.group(1)
                ptitles.append(ptitle)
                ptitle_start_indices.append(i)
            elif match2:
                ptitle = match2.group(1)
                ptitles.append(ptitle)
                ptitle_start_indices.append(i)
            else:
                continue

    ptitle_end_indices = ptitle_start_indices[1:] + [len(contents)]
    presentations = []
    start_end_pairs = list(zip(ptitle_start_indices, ptitle_end_indices))
    assert len(start_end_pairs) == len(ptitles)
    for (start, end), ptitle in zip(start_end_pairs, ptitles):
        pcontent = contents[start:end]
        authors = []
        abstract = None
        for c in pcontent:

            if "ICRA24_AuthorIndexWeb" in c:
                author_pattern = r'<a href="ICRA24_AuthorIndexWeb.html#.*?" title="Click to go to the Author Index">(.*?)</a></td><td class="r">(.*?)</td>'
                author_match = re.search(author_pattern, c)
                if author_match:
                    assert abstract is None, "Abstract already exists"
                    author_name = author_match.group(1)
                    author_affiliation = author_match.group(2)
                    authors.append((author_name, author_affiliation))

            if "Abstract:" in c:
                abstract = c.split("<strong>Abstract:</strong>")[1].strip()

        assert len(authors) > 0
        if st in (SessionType.PLENARY, SessionType.KEYNOTE):
            assert len(authors) == 1
            assert abstract is None
            presentations.append(Presentation(title=ptitle, authors=authors, abstract=abstract))
        elif st == SessionType.EXPO:
            assert abstract is None
            presentations.append(Presentation(title=ptitle, authors=authors, abstract=abstract))
        else:
            assert abstract is not None
            presentations.append(Presentation(title=ptitle, authors=authors, abstract=abstract))
    return presentations


def extract_session_instances(tr_contents: List[str], st: SessionType) -> Session:
    title = None
    chair = None
    cochair = None

    for content in tr_contents:
        # find title 
        if "ICRA24_ProgramAtAGlanceWeb" in content:
            pattern = r'title=".*?">(.*?)</a>'
            match = re.search(pattern, content)
            if match:
                assert title is None, "Title already exists"
                title = match.group(1)

        # find chair and co-chair
        if "Chair:" in content:
            is_cochair = "Co-Chair:" in content
            chair_pattern = r'Chair: <a href=".*?">(.*?)</a></td><td class="r">(.*?)</td>'
            chair_match = re.search(chair_pattern, content)
            if chair_match:

                chair_name = chair_match.group(1)
                chair_affiliation = chair_match.group(2)
                if is_cochair:
                    assert cochair is None, f"Co-Chair {cochair} already exists"
                    cochair = (chair_name, chair_affiliation)
                else:
                    assert chair is None, f"Chair {chair} already exists"
                    chair = (chair_name, chair_affiliation)

    presentations = extract_presentations(tr_contents, st)
    return Session(name=title, stype=st, chair=chair, cochair=cochair, presentations=presentations)


# open "./tmp.html"
with open("./tmp.html", "r") as f:
    html_content = f.read()

tr_contents = extract_tr_contents(html_content)
indices_session_start = []
session_types = []
for i, c in enumerate(tr_contents):
    if "class=\"sHdr\"" in c:
        for session_type in SessionType:
            if session_type.value in c:
                indices_session_start.append(i)
                session_types.append(session_type)
                break

session_wise_tr_contents = []
for i, index in enumerate(indices_session_start):
    if i == len(indices_session_start) - 1:
        session_wise_tr_contents.append(tr_contents[index:])
    else:
        session_wise_tr_contents.append(tr_contents[index:indices_session_start[i+1]])
len(session_wise_tr_contents)

assert len(session_types) == len(session_wise_tr_contents)
session_list = []
for st, contents in zip(session_types, session_wise_tr_contents):
    if st == SessionType.PLENARY:
        continue  # skip plenary sessions
    session = extract_session_instances(contents, st)
    session_list.append(session)

# dump the session list as yaml
import yaml
with open("sessions.yaml", "w") as f:
    yaml.dump([asdict(s) for s in session_list], f)
