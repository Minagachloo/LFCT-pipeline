import os
import csv
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.patches as patches

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(ROOT, "Input")
OUTPUT_DIR = os.path.join(ROOT, "Output")
GAPS = [1, 2, 4, 8]

NODE_RADIUS = 0.28
FRAME_SPACING = 1.2
LINEAGE_BUFFER = 2.0
MIN_TREE_HEIGHT = 2.5

COLORS = {
    "normal": "#4A90E2",
    "division_parent": "#8B4513",
    "daughter_cell": "#FFD700",
}


def read_spots(csv_path):
    spots = {}
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            sid = int(row["ID"])
            anc = row.get("ancestor_SPOT_ID", "")
            spots[sid] = {
                "frame": int(row["FRAME"]),
                "x": float(row["POSITION_X"]),
                "y": float(row["POSITION_Y"]),
                "parent": int(anc) if anc else None,
            }
    return spots


def build_lineages(spots):
    children = defaultdict(list)
    for sid, s in spots.items():
        if s["parent"] is not None:
            children[s["parent"]].append(sid)

    roots = sorted(
        [sid for sid, s in spots.items() if s["parent"] is None],
        key=lambda sid: (spots[sid]["frame"], sid),
    )
    lineage = {}
    for lid, root in enumerate(roots):
        stack = [root]
        while stack:
            sid = stack.pop()
            lineage[sid] = lid
            stack.extend(children.get(sid, []))

    types = {sid: "normal" for sid in spots}
    for sid, kids in children.items():
        if len(kids) > 1:
            types[sid] = "division_parent"
            for k in kids:
                types[k] = "daughter_cell"

    return lineage, dict(children), types


def _walk(sid, children, local_y, counter):
    kids = children.get(sid, [])
    if not kids:
        local_y[sid] = counter[0]
        counter[0] += 1
        return
    for k in kids:
        _walk(k, children, local_y, counter)
    ys = [local_y[k] for k in kids]
    local_y[sid] = (min(ys) + max(ys)) / 2


def layout_y(spots, lineage, children):
    # Each lineage is laid out from local y=0 (top of its band), then placed
    # under the previous lineage so trees stack downward.
    by_lid = defaultdict(list)
    for sid, lid in lineage.items():
        by_lid[lid].append(sid)
    roots = {lid: next(sid for sid in sids if spots[sid]["parent"] is None)
             for lid, sids in by_lid.items()}

    y = {}
    current_top = 0

    for lid in sorted(by_lid):
        local_y = {}
        _walk(roots[lid], children, local_y, [0])

        height = max(local_y.values()) - min(local_y.values())
        height = max(height, MIN_TREE_HEIGHT)

        for sid, ly in local_y.items():
            y[sid] = current_top - ly

        current_top -= (height + LINEAGE_BUFFER)

    return y, current_top


def render(spots, lineage, children, types, gap, png_path):
    y, axis_y = layout_y(spots, lineage, children)

    # Evenly space the visible frames on the x-axis. The frame number is
    # shown as the label, not used as the coordinate.
    frames = sorted({s["frame"] for s in spots.values()})
    frame_to_x = {f: i * FRAME_SPACING for i, f in enumerate(frames)}

    n_lid = len(set(lineage.values()))
    fig_w = max(8, min(24, len(frames) * 0.6))
    fig_h = max(4, min(25, abs(axis_y) * 0.5))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    # Edges. A division edge (parent has >1 children) is drawn in red.
    for sid, s in spots.items():
        if s["parent"] is None:
            continue
        p = spots[s["parent"]]
        is_div_edge = len(children.get(s["parent"], [])) > 1
        color = "#D32F2F" if is_div_edge else "#666666"
        ax.plot(
            [frame_to_x[p["frame"]], frame_to_x[s["frame"]]],
            [y[s["parent"]], y[sid]],
            color=color, linewidth=0.6, zorder=1,
        )

    # Nodes coloured by type.
    for sid, s in spots.items():
        ax.add_patch(patches.Circle(
            (frame_to_x[s["frame"]], y[sid]),
            NODE_RADIUS, facecolor=COLORS[types[sid]],
            edgecolor="white", linewidth=0.8, zorder=2,
        ))

    # Frame axis at the bottom with actual frame numbers as labels.
    ax.text(-0.3, axis_y + 0.1, "Frame", fontsize=10, fontweight="bold",
            color="#333", ha="right", va="center")
    for f in frames:
        x = frame_to_x[f]
        ax.plot([x, x], [axis_y - 0.1, axis_y + 0.1], color="#333", linewidth=1.0)
        ax.text(x, axis_y - 0.3, str(f), fontsize=6, ha="center", va="top",
                color="#333")
    ax.plot([0, (len(frames) - 1) * FRAME_SPACING], [axis_y, axis_y],
            color="#333", linewidth=1)

    ax.set_title(f"GAP={gap} lineage tree — {n_lid} lineages",
                 fontsize=13, fontweight="bold")
    ax.set_xlim(-1, (len(frames) - 1) * FRAME_SPACING + 1)
    ax.set_ylim(axis_y - 1.5, 1.5)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(png_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for fname in sorted(os.listdir(INPUT_DIR)):
        if not fname.endswith(".xml"):
            continue
        base = fname.replace(".xml", "")
        for gap in GAPS:
            if gap == 1:
                csv_in = os.path.join(OUTPUT_DIR, f"{base}.csv")
            else:
                csv_in = os.path.join(OUTPUT_DIR, f"{base}_gap{gap}.csv")
            if not os.path.exists(csv_in):
                print(f"skip: {csv_in} not found")
                continue
            spots = read_spots(csv_in)
            lineage, children, types = build_lineages(spots)
            png_out = os.path.join(OUTPUT_DIR, f"{base}_gap{gap}_lineage.png")
            render(spots, lineage, children, types, gap, png_out)
            n_lid = len(set(lineage.values()))
            n_div = sum(1 for t in types.values() if t == "division_parent")
            print(f"GAP={gap}: {len(spots)} spots, {n_lid} lineages, "
                  f"{n_div} divisions → {png_out}")


if __name__ == "__main__":
    main()
