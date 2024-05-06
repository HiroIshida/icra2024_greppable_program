import re
import urllib.request
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple

import requests
import yaml
from bs4 import BeautifulSoup


class SessionType(Enum):
    ORAL = "Oral Session"
    POSTER = "Poster Session"
    AWARD = "Award Session"
    KEYNOTE = "Keynote Session"
    PLENARY = "Plenary Session"
    EXPO = "Expo Session"


@dataclass
class Presentation:
    ptitle: str
    time: str
    id_: str
    session_summary: str
    authors: List[Tuple[str, str]]
    abstract: str


@dataclass
class Session:
    stitle: str
    stype_name: str  # for serialization
    stime: Optional[str]
    chair: Optional[Tuple[str, str]]
    cochair: Optional[Tuple[str, str]]
    presentations: List[Presentation]
    stype: SessionType

    def summary_str(self) -> str:
        return f"{self.stitle} ({self.stype_name})"

    def __post_init__(self):
        assert self.stitle is not None
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

        tr_content = html[start_index : end_index + 5]
        tr_contents.append(tr_content.strip())

        start_index = end_index + 5

    return tr_contents


def append_presentations(contents: List[str], session: Session) -> None:
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
        time = None
        id_ = None
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

            # time and id
            if "pHdr" in c and "Add to My Program" in c and "Paper" in c:
                pattern = r'<a name=".*?">(.*?)</a>'
                match = re.search(pattern, c)
                if match:
                    assert time is None, "Time already exists"
                    assert id_ is None, "ID already exists"
                    time_id = match.group(1)
                    time, id_ = time_id.split(", Paper")

        assert len(authors) > 0
        if session.stype in (SessionType.PLENARY, SessionType.KEYNOTE):
            assert len(authors) == 1
            assert abstract is None
        elif session.stype == SessionType.EXPO:
            assert abstract is None
        else:
            assert abstract is not None
        presentations.append(
            Presentation(
                ptitle=ptitle,
                authors=authors,
                abstract=abstract,
                session_summary=session.summary_str(),
                time=time,
                id_=id_,
            )
        )
    session.stime = presentations[0].time  # all times are same
    session.presentations = presentations


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
            chair_pattern = (
                r'Chair: <a href=".*?">(.*?)</a></td><td class="r">(.*?)</td>'
            )
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

    session = Session(
        stitle=title,
        stime=None,
        stype_name=st.value,
        chair=chair,
        cochair=cochair,
        presentations=[],
        stype=st,
    )
    # stime will be filled later
    append_presentations(tr_contents, session)
    return session


def create_session_list(html_string: str) -> List[Session]:
    tr_contents = extract_tr_contents(html_content)
    indices_session_start = []
    session_types = []
    for i, c in enumerate(tr_contents):
        if 'class="sHdr"' in c:
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
            session_wise_tr_contents.append(
                tr_contents[index : indices_session_start[i + 1]]
            )
    len(session_wise_tr_contents)

    assert len(session_types) == len(session_wise_tr_contents)
    session_list = []
    for st, contents in zip(session_types, session_wise_tr_contents):
        if st == SessionType.PLENARY:
            continue  # skip plenary sessions
        session = extract_session_instances(contents, st)
        session_list.append(session)
    return session_list


def fetch_html(url):
    html_cache_dir = Path("/tmp/icra24_html_cache")
    html_cache_path = html_cache_dir / Path(url).name
    if html_cache_path.exists():
        print(f"Reading from cache: {html_cache_path}")
        with open(html_cache_path, "r") as f:
            html_content = f.read()
    else:
        print(f"Fetching {url}")
        with urllib.request.urlopen(url) as response:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            html_content = str(soup)

        html_cache_dir.mkdir(exist_ok=True)
        with open(html_cache_path, "w") as f:
            f.write(html_content)
    return html_content


if __name__ == "__main__":
    url1 = "https://ras.papercept.net/conferences/conferences/ICRA24/program/ICRA24_ContentListWeb_1.html"
    url2 = "https://ras.papercept.net/conferences/conferences/ICRA24/program/ICRA24_ContentListWeb_2.html"
    url3 = "https://ras.papercept.net/conferences/conferences/ICRA24/program/ICRA24_ContentListWeb_3.html"
    days = ("tuesday", "wednesday", "thursday")
    for url, day in zip((url1, url2, url3), days):
        html_content = fetch_html(url)
        session_list = create_session_list(html_content)
        print(f"Extracted {len(session_list)} sessions from {url}")
        print(f"Dumping {day} sessions to dump/{day}_sessions.yaml")
        with open(f"dump/{day}_sessions.yaml", "w") as f:
            yaml.dump([asdict(s) for s in session_list], f, sort_keys=False)
