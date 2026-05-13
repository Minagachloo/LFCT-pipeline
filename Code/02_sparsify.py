import os
import csv
import math
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(ROOT, "Input")
OUTPUT_DIR = os.path.join(ROOT, "Output")
GAPS = [2, 4, 8]

EXTRA_COLS = ["ancestor_SPOT_ID", "ancestor_FRAME", "displacement"]


def parse_xml(xml_path):
    root = ET.parse(xml_path).getroot()

    # Pull every attribute TrackMate stores for each spot.
    spots = {}
    for sif in root.find(".//AllSpots").findall("SpotsInFrame"):
        frame = int(sif.attrib["frame"])
        for spot in sif.findall("Spot"):
            row = dict(spot.attrib)
            row["FRAME"] = frame
            spots[int(spot.attrib["ID"])] = row

    # Map each spot to its parent and its TRACK_ID.
    child_parent = {}
    track_map = {}
    for track in root.iterfind(".//AllTracks/Track"):
        tid = track.attrib["TRACK_ID"]
        for edge in track.findall("Edge"):
            src = int(edge.attrib["SPOT_SOURCE_ID"])
            tgt = int(edge.attrib["SPOT_TARGET_ID"])
            if src not in spots or tgt not in spots:
                continue
            track_map[src] = tid
            track_map[tgt] = tid
            fsrc = spots[src]["FRAME"]
            ftgt = spots[tgt]["FRAME"]
            if fsrc < ftgt:
                child_parent[tgt] = src
            elif fsrc > ftgt:
                child_parent[src] = tgt

    for sid, row in spots.items():
        row["TRACK_ID"] = track_map.get(sid, "")

    return spots, child_parent


def find_visible_ancestor(sid, child_parent, spots, visible_frames):
    current = sid
    while True:
        parent = child_parent.get(current)
        if parent is None:
            return None
        if spots[parent]["FRAME"] in visible_frames:
            return parent
        current = parent


def gap_rows(spots, child_parent, gap):
    all_frames = sorted({s["FRAME"] for s in spots.values()})
    first_frame = all_frames[0]
    visible_frames = {f for f in all_frames if (f - first_frame) % gap == 0}

    rows = []
    for sid, s in spots.items():
        if s["FRAME"] not in visible_frames:
            continue
        row = dict(s)
        anc = find_visible_ancestor(sid, child_parent, spots, visible_frames)
        if anc is not None:
            dx = float(s["POSITION_X"]) - float(spots[anc]["POSITION_X"])
            dy = float(s["POSITION_Y"]) - float(spots[anc]["POSITION_Y"])
            row["ancestor_SPOT_ID"] = anc
            row["ancestor_FRAME"] = spots[anc]["FRAME"]
            row["displacement"] = round(math.sqrt(dx * dx + dy * dy), 4)
        else:
            row["ancestor_SPOT_ID"] = ""
            row["ancestor_FRAME"] = ""
            row["displacement"] = ""
        rows.append(row)

    rows.sort(key=lambda r: (r["FRAME"], int(r["ID"])))
    return rows


def write_csv(rows, csv_path):
    priority = ["ID", "FRAME", "TRACK_ID", "POSITION_X", "POSITION_Y"]
    keys = set().union(*(r.keys() for r in rows))
    cols = (
        [k for k in priority if k in keys]
        + sorted(keys - set(priority) - set(EXTRA_COLS))
        + EXTRA_COLS
    )
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for fname in sorted(os.listdir(INPUT_DIR)):
        if not fname.endswith(".xml"):
            continue
        xml_path = os.path.join(INPUT_DIR, fname)
        base = fname.replace(".xml", "")
        spots, child_parent = parse_xml(xml_path)
        for gap in GAPS:
            rows = gap_rows(spots, child_parent, gap)
            csv_path = os.path.join(OUTPUT_DIR, f"{base}_gap{gap}.csv")
            write_csv(rows, csv_path)
            print(f"GAP={gap}: {len(rows)} spots → {csv_path}")


if __name__ == "__main__":
    main()
