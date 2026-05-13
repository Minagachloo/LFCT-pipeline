import os
import csv
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(ROOT, "Input")
OUTPUT_DIR = os.path.join(ROOT, "Output")


def extract(xml_path, csv_path):
    root = ET.parse(xml_path).getroot()

    # First pass: collect spot rows and remember each spot's frame.
    rows = []
    frame_of = {}
    for sif in root.iter("SpotsInFrame"):
        frame = int(sif.attrib["frame"])
        for spot in sif.findall("Spot"):
            row = dict(spot.attrib)
            row["FRAME"] = frame
            rows.append(row)
            frame_of[row["ID"]] = frame

    # Use the edges in <AllTracks> to fill TRACK_ID and ancestor_SPOT_ID.
    # The earlier-frame endpoint is the parent of the later-frame one.
    track_of = {}
    parent_of = {}
    for track in root.iterfind(".//AllTracks/Track"):
        tid = track.attrib["TRACK_ID"]
        for edge in track.findall("Edge"):
            src = edge.attrib["SPOT_SOURCE_ID"]
            tgt = edge.attrib["SPOT_TARGET_ID"]
            track_of[src] = tid
            track_of[tgt] = tid
            if frame_of[src] < frame_of[tgt]:
                parent_of[tgt] = src
            elif frame_of[src] > frame_of[tgt]:
                parent_of[src] = tgt

    for row in rows:
        row["TRACK_ID"] = track_of.get(row["ID"], "")
        row["ancestor_SPOT_ID"] = parent_of.get(row["ID"], "")

    keys = set().union(*(r.keys() for r in rows))
    first = ["ID", "FRAME", "TRACK_ID", "ancestor_SPOT_ID",
             "POSITION_X", "POSITION_Y"]
    cols = first + sorted(keys - set(first))

    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} spots → {csv_path}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for fname in sorted(os.listdir(INPUT_DIR)):
        if fname.endswith(".xml"):
            extract(
                os.path.join(INPUT_DIR, fname),
                os.path.join(OUTPUT_DIR, fname.replace(".xml", ".csv")),
            )


if __name__ == "__main__":
    main()
