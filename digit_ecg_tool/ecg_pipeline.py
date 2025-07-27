import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import pandas as pd
import os
from typing import Dict, Union

# Import hardcoded lead coordinates from ecg_lead_coords.py
from ecg_lead_coords import HARDCODED_LEAD_COORDS

try:
    import pytesseract
    from pytesseract import Output
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("Warning: pytesseract not installed. Lead label OCR will be unavailable.")

LEAD_NAMES = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']

class ECGDigitizer:
    def __init__(self):
        self.ecg_image = None
        self.gray_image = None
        self.binary_image = None
        self.ecg_signals = {}
        self.time_scale = 0.04  # 25mm/s (0.04s/mm)
        self.voltage_scale = 0.1  # 10mm/mV (0.1mV/mm)
        self.grid_size = 20  # pixels per mm (default)
        self.heart_rates = {}
        self.lead_positions = None
        self.best_lead = None
        self.min_signal_length = 100

    def load_image(self, image_bytes: bytes) -> np.ndarray:
        self.ecg_image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        if self.ecg_image is None:
            raise ValueError("Could not decode image from bytes")
        self.gray_image = cv2.cvtColor(self.ecg_image, cv2.COLOR_BGR2GRAY)
        return self.gray_image

    def preprocess_image(self) -> np.ndarray:
        # Use Otsu threshold for robust binarization
        _, self.binary_image = cv2.threshold(
            self.gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        return self.binary_image

    def detect_leads(self):
        self.lead_positions = HARDCODED_LEAD_COORDS
        return self.lead_positions

    def debug_visualize_lead_boxes(self, show_labels=True, save_path=None):
        img_copy = self.ecg_image.copy()
        for lead, (x1, y1, x2, y2) in self.lead_positions.items():
            color = (0, 255, 0)
            cv2.rectangle(img_copy, (x1, y1), (x2, y2), color, 2)
            if show_labels:
                cv2.putText(img_copy, lead, (x1+5, y1+25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        plt.figure(figsize=(16, 8))
        plt.imshow(cv2.cvtColor(img_copy, cv2.COLOR_BGR2RGB))
        plt.title("Detected Lead Regions (Green=Hardcoded)")
        plt.axis('off')
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path)
        plt.show()

    def process_image(self, image_bytes: bytes, debug_visualize=False) -> Dict[str, np.ndarray]:
        try:
            self.load_image(image_bytes)
            self.preprocess_image()
            self.detect_leads()
            if debug_visualize:
                self.debug_visualize_lead_boxes()
            return self.extract_all_signals()
        except Exception as e:
            print(f"Error in process_image: {str(e)}")
            return {}

    def extract_all_signals(self) -> Dict[str, np.ndarray]:
        results = {}
        nrows, ncols = 4, 3  # for 12-lead display
        fig, axs = plt.subplots(nrows, ncols, figsize=(16, 12))
        grid_ignore_pixels = 8  # ignore this many pixels from the bottom (adjust as needed)
        jump_threshold = 18     # max allowed jump in pixels between columns

        for idx, lead in enumerate(LEAD_NAMES):
            row, col = divmod(idx, ncols)
            if lead not in self.lead_positions:
                axs[row, col].axis('off')
                continue

            x1, y1, x2, y2 = self.lead_positions[lead]
            lead_img = self.binary_image[y1:y2, x1:x2]

            xs = np.arange(lead_img.shape[1])
            ys = []
            prev_y = None

            for x in xs:
                col_pixels = lead_img[:lead_img.shape[0]-grid_ignore_pixels, x]
                white_runs = np.where(col_pixels > 0)[0]

                # If there are multiple white runs, pick the one closest to prev_y
                if len(white_runs) > 0:
                    if prev_y is not None:
                        # Pick y closest to prev_y
                        y_trace = white_runs[np.argmin(np.abs(white_runs - prev_y))]
                        # Don't allow big jumps
                        if abs(y_trace - prev_y) > jump_threshold:
                            y_trace = prev_y
                    else:
                        # Heuristic: pick the one near the center (ECG is rarely at top or bottom)
                        y_trace = white_runs[np.argmin(np.abs(white_runs - (len(col_pixels)//2)))]
                    ys.append(y_trace)
                    prev_y = y_trace
                else:
                    # No white pixels, use previous or nan
                    ys.append(prev_y if prev_y is not None else np.nan)
            ys = np.array(ys)

            # Interpolate missing values
            if np.any(np.isnan(ys)):
                not_nan = ~np.isnan(ys)
                ys = np.interp(xs, xs[not_nan], ys[not_nan])

            # Median and Savitzky-Golay smoothing
            ys = signal.medfilt(ys, kernel_size=7)
            if len(ys) >= 21:
                ys = signal.savgol_filter(ys, 21, 3)

            # Convert x to time and y to voltage (invert y axis)
            x_time = (xs / self.grid_size) * self.time_scale
            y_voltage = ((lead_img.shape[0] - grid_ignore_pixels - ys) / self.grid_size) * self.voltage_scale
            results[lead] = np.column_stack((x_time, y_voltage))

            # Plot for diagnostics
            axs[row, col].imshow(lead_img, cmap='gray')
            axs[row, col].plot(xs, ys, color='lime', linewidth=1, label="Extracted trace (pixels)")
            axs[row, col].set_title(f"{lead} - Trace (contour-follow)")
            axs[row, col].axis('off')

        plt.tight_layout()
        fig.suptitle("Contour-following ECG Trace Extraction from Binary Images", fontsize=16)
        plt.show()
        self.ecg_signals = results
        return results

    def enhanced_pan_tompkins(self, ecg_signal: np.ndarray) -> np.ndarray:
        try:
            ecg_normalized = (ecg_signal - np.min(ecg_signal)) / (np.max(ecg_signal) - np.min(ecg_signal))
            nyquist = 0.5 * 250
            low = 5 / nyquist
            high = 15 / nyquist
            b, a = signal.butter(4, [low, high], btype='bandpass')
            filtered = signal.filtfilt(b, a, ecg_normalized)
            derivative = np.gradient(filtered)
            squared = derivative ** 2
            window_size = int(0.15 * 250)
            integrated = np.convolve(squared, np.ones(window_size)/window_size, mode='same')
            min_distance = int(0.6 * 250)
            min_height = 0.5 * np.max(integrated)
            peaks, _ = signal.find_peaks(
                integrated,
                distance=min_distance,
                height=min_height,
                prominence=0.3,
                width=20
            )
            return peaks
        except Exception as e:
            print(f"Peak detection error: {str(e)}")
            return np.array([])

    def calculate_heart_rate(self, lead_name: str = None) -> Union[float, None]:
        if not self.ecg_signals:
            print("No ECG signals available for analysis")
            return None
        target_leads = [lead_name] if lead_name else LEAD_NAMES
        for lead in target_leads:
            if lead not in self.ecg_signals:
                continue
            y = self.ecg_signals[lead][:, 1]
            x = self.ecg_signals[lead][:, 0]
            try:
                peaks = self.enhanced_pan_tompkins(y)
                if len(peaks) < 2:
                    continue
                rr_intervals = np.diff(x[peaks])
                hr = 60 / np.mean(rr_intervals)
                if 40 <= hr <= 180:
                    self.best_lead = lead
                    print(f"Detected HR: {hr:.1f} BPM from lead {lead}")
                    return hr
            except Exception as e:
                print(f"HR detection attempt failed for lead {lead}: {str(e)}")
                continue
        print("Warning: Could not detect reliable peaks in any lead")
        return None

def calculate_heart_rate_from_signal(time_series: np.ndarray, voltage_series: np.ndarray) -> float:
    try:
        peaks, _ = signal.find_peaks(
            voltage_series,
            height=np.mean(voltage_series) + 2*np.std(voltage_series),
            distance=int(0.5*250)
        )
        if len(peaks) >= 2:
            rr_intervals = np.diff(time_series[peaks])
            hr = 60 / np.mean(rr_intervals)
            if 40 <= hr <= 180:
                return hr
    except Exception as e:
        print(f"HR calculation from signal failed: {str(e)}")
    return np.nan

def ecg_image_to_features(image_bytes: bytes, debug_visualize=False) -> pd.DataFrame:
    digitizer = ECGDigitizer()
    try:
        signals = digitizer.process_image(image_bytes, debug_visualize=debug_visualize)
        if not signals or len(signals) == 0:
            raise ValueError("No signals extracted")
        features = {}
        valid_leads = [lead for lead, sig in signals.items() if sig is not None and len(sig) > 0]
        if not valid_leads:
            raise ValueError("No valid leads extracted")
        min_len = min(len(signals[lead]) for lead in valid_leads)
        for lead in valid_leads:
            signal_data = signals[lead][:min_len]
            features[f'{lead}_time'] = signal_data[:, 0]
            features[f'{lead}_voltage'] = signal_data[:, 1]
        df = pd.DataFrame(features)
        hr = digitizer.calculate_heart_rate()
        if hr is None and digitizer.best_lead:
            best_lead = digitizer.best_lead
            hr = calculate_heart_rate_from_signal(
                df[f'{best_lead}_time'].values,
                df[f'{best_lead}_voltage'].values
            )
        if hr is None:
            for lead in valid_leads:
                if f'{lead}_time' in df.columns:
                    hr = calculate_heart_rate_from_signal(
                        df[f'{lead}_time'].values,
                        df[f'{lead}_voltage'].values
                    )
                    if not np.isnan(hr):
                        print(f"Calculated HR from lead {lead} fallback: {hr:.1f} BPM")
                        break
        df['heart_rate_bpm'] = hr if not np.isnan(hr) else np.nan
        return df
    except Exception as e:
        print(f"Error processing ECG: {str(e)}")
        return pd.DataFrame()