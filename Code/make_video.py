import os
import re
import cv2
import numpy as np
import tifffile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(ROOT, "Input")
OUTPUT_DIR = os.path.join(ROOT, "Output")
GAPS = [1, 2, 4, 8]
BLUR_SIZE = 101  
FPS = 5

PC_PERCENTILES = (0, 100)
RFP_PERCENTILES = (1, 99.9)


def normalize_percentile(img, low_pct, high_pct):
    low = np.percentile(img, low_pct)
    high = np.percentile(img, high_pct)
    if high == low:
        return np.zeros_like(img, dtype=np.uint8)
    img = np.clip(img, low, high)
    return ((img - low) / (high - low) * 255).astype(np.uint8)


def merge_frame(pc_img, rfp_img):
    pc_norm = normalize_percentile(pc_img, *PC_PERCENTILES)
    rfp_norm = normalize_percentile(rfp_img, *RFP_PERCENTILES)

    rfp_bg = cv2.GaussianBlur(rfp_norm, (BLUR_SIZE, BLUR_SIZE), 0)
    rfp_corrected = cv2.subtract(rfp_norm, rfp_bg)
    _, mask = cv2.threshold(rfp_corrected, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    rfp_corrected[mask == 0] = 0

    h, w = pc_norm.shape
    merged = np.zeros((h, w, 3), dtype=np.uint8)
    merged[:, :, 0] = pc_norm
    merged[:, :, 1] = pc_norm
    merged[:, :, 2] = np.clip(
        pc_norm.astype(np.int32) + rfp_corrected.astype(np.int32), 0, 255
    ).astype(np.uint8)
    return merged


def make_video(pc_files, rfp_files, gap, out_path):
    indices = list(range(0, len(pc_files), gap))
    sample = tifffile.imread(pc_files[0])
    h, w = sample.shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video = cv2.VideoWriter(out_path, fourcc, FPS, (w, h))
    for i in indices:
        pc_img = tifffile.imread(pc_files[i])
        rfp_img = tifffile.imread(rfp_files[i])
        video.write(merge_frame(pc_img, rfp_img))
    video.release()
    return len(indices)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    pc_folders = sorted(
        d for d in os.listdir(INPUT_DIR)
        if re.match(r"FLD_\d+_pc$", d)
    )

    for pc_name in pc_folders:
        fld_num = re.match(r"FLD_(\d+)_pc", pc_name).group(1)
        pc_dir = os.path.join(INPUT_DIR, pc_name)
        rfp_dir = os.path.join(INPUT_DIR, f"FLD_{fld_num}_rfp")
        if not os.path.isdir(rfp_dir):
            print(f"skip FLD_{fld_num}: no matching rfp folder")
            continue

        pc_files = sorted(
            os.path.join(pc_dir, f) for f in os.listdir(pc_dir) if f.endswith(".tif")
        )
        rfp_files = sorted(
            os.path.join(rfp_dir, f) for f in os.listdir(rfp_dir) if f.endswith(".tif")
        )
        n = min(len(pc_files), len(rfp_files))
        pc_files = pc_files[:n]
        rfp_files = rfp_files[:n]

        for gap in GAPS:
            out_path = os.path.join(OUTPUT_DIR, f"FLD_{fld_num}_video_gap{gap}.mp4")
            n_written = make_video(pc_files, rfp_files, gap, out_path)
            print(f"FLD_{fld_num} GAP={gap}: {n_written} frames → {out_path}")


if __name__ == "__main__":
    main()
