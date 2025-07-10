import cv2
import numpy as np
import pandas as pd
from scipy.signal import find_peaks, savgol_filter

LEAD_LABELS = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]

def remove_ecg_grid(image_gray):
    thresh = cv2.adaptiveThreshold(
        image_gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=21, C=7
    )
    line_length_pixels = int(image_gray.shape[1] * 0.2)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (line_length_pixels, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, line_length_pixels))
    horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
    grid_mask = cv2.add(horizontal_lines, vertical_lines)
    grid_removed = cv2.subtract(thresh, grid_mask)
    repair_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    grid_removed = cv2.morphologyEx(grid_removed, cv2.MORPH_CLOSE, repair_kernel)
    return grid_removed

def segment_ecg_leads(image_rgb):
    h, w = image_rgb.shape[:2]
    mid_x = w // 2
    left_col = image_rgb[:, :mid_x]
    right_col = image_rgb[:, mid_x:]

    def split_column(col_img):
        row_h = col_img.shape[0] // 6
        return [col_img[i * row_h: (i + 1) * row_h, :] for i in range(6)]

    leads = split_column(left_col) + split_column(right_col)
    return {label: img for label, img in zip(LEAD_LABELS, leads)}

def estimate_heart_rate_and_intervals_from_lead(lead_img, fs=500, base_prominence=10, use_smoothing=True):
    gray = cv2.cvtColor(lead_img, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    binary = cv2.threshold(255 - blurred, 100, 255, cv2.THRESH_BINARY)[1]
    kernel = np.ones((1, 3), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, None, None, None, None, 0

    points = np.vstack([cnt.squeeze() for cnt in contours if cnt.shape[0] > 10])
    if points.ndim != 2:
        return None, None, None, None, None, 0

    x_vals, y_vals = points[:, 0], points[:, 1]
    x_unique, indices = np.unique(x_vals, return_index=True)
    y_unique = y_vals[indices]
    waveform = np.interp(np.arange(lead_img.shape[1]), x_unique, y_unique)
    waveform = -waveform  # ECG peaks up for peak detection

    if use_smoothing:
        window_length = min(21, len(waveform) // 2 * 2 + 1)
        waveform = savgol_filter(waveform, window_length, polyorder=2)

    adaptive_prominence = 0.2 * (np.max(waveform) - np.min(waveform))
    prominence = max(adaptive_prominence, base_prominence)
    peaks, _ = find_peaks(waveform, distance=int(0.4 * fs), prominence=prominence, width=5)

    if len(peaks) < 2:
        return None, None, None, None, None, len(peaks)

    rr_intervals = np.diff(peaks) / fs
    avg_rr = np.mean(rr_intervals) if len(rr_intervals) > 0 else None
    heart_rate = 60 / avg_rr if avg_rr else None
    qrs_duration = np.mean([(min(peak + int(0.05 * fs), len(waveform)) - max(peak - int(0.05 * fs), 0)) / fs for peak in peaks]) if len(peaks) > 0 else None
    qt_interval = np.mean([(min(peak + int(0.2 * fs), len(waveform)) - peak) / fs for peak in peaks]) if len(peaks) > 0 else None
    pr_interval = np.mean([(peak - max(peak - int(0.1 * fs), 0)) / fs for peak in peaks]) if len(peaks) > 0 else None

    return heart_rate, avg_rr, qrs_duration, qt_interval, pr_interval, len(peaks)

def ecg_image_to_features(image_bytes, fs=500):
    # Decode image
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image bytes. Is it a valid image?")
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Remove grid
    _ = remove_ecg_grid(image_gray)  # Optionally, use grid-removed image for segmentation if needed
    # Segment leads
    leads = segment_ecg_leads(image_rgb)
    # Extract features per lead
    results = []
    for label, lead_img in leads.items():
        heart_rate, rr_interval, qrs_duration, qt_interval, pr_interval, num_peaks = estimate_heart_rate_and_intervals_from_lead(
            lead_img, fs=fs)
        results.append({
            "Lead": label,
            "Heart Rate (BPM)": heart_rate,
            "RR Interval (s)": rr_interval,
            "QRS Duration (s)": qrs_duration,
            "QT Interval (s)": qt_interval,
            "PR Interval (s)": pr_interval,
            "Detected Peaks": num_peaks
        })
    return pd.DataFrame(results)