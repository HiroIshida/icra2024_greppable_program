import pickle
from icra.parse import *
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ptitle", type=str, help="regex pattern for presentation title"
    )
    parser.add_argument("--author", type=str, help="regex pattern for author")
    args = parser.parse_args()

    with open("./dump/aggregate_sessions.pkl", "rb") as f:
        aggregate = pickle.load(f)

    presentations = []
    days = []
    for day, sessions in aggregate.items():
        for session in sessions:
            for presentation in session.presentations:
                if args.ptitle is not None:
                    pattern = re.compile(args.ptitle, re.IGNORECASE)
                    if not re.search(pattern, presentation.ptitle):
                        continue

                if args.author is not None:
                    pattern = re.compile(args.author, re.IGNORECASE)
                    def match_any():
                        for author in presentation.authors:
                            if re.search(pattern, author[0]):
                                return True
                        return False
                    if not match_any():
                        continue

                presentations.append(presentation)
                days.append(day)

    print(f"Found {len(presentations)} presentations")
    for presentation, day in zip(presentations, days):
        print(f"Day: {day}")
        print(presentation)
