import cv2
import json

# List of ECG leads in standard order
LEAD_NAMES = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']

def select_rois(image_path, lead_names):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Cannot open image: {image_path}")
        return None

    print("\nInstructions:")
    print("For each lead, a window will appear.")
    print("Draw a rectangle for the waveform region using your mouse, then press ENTER or SPACE.")
    print("If you make a mistake, press 'c' to clear and redraw.")
    print("Close the window after each selection to continue to the next lead.\n")

    coords = {}
    for lead in lead_names:
        print(f"Select region for lead: {lead}")
        # Clone image for each selection
        clone = img.copy()
        # Show the image and let user select ROI
        roi = cv2.selectROI(f"Draw box for {lead}", clone, False, False)
        cv2.destroyAllWindows()
        x, y, w, h = roi
        if w == 0 or h == 0:
            print(f"Warning: No region selected for lead {lead}. Skipping.")
            continue
        coords[lead] = [int(x), int(y), int(x + w), int(y + h)]
    return coords

def save_coords(coords, out_path="C:\\Users\\wazzu\\Desktop\\digit-ecg\\digit-ecg\\digit_ecg_tool\\ecg_lead_coords.py"):
    with open(out_path, "w") as f:
        f.write("# Lead coordinates: (x1, y1, x2, y2) for each lead\n")
        f.write("HARDCODED_LEAD_COORDS = {\n")
        for lead, rect in coords.items():
            f.write(f"    \"{lead}\": {tuple(rect)},\n")
        f.write("}\n")
    print(f"\nLead coordinates saved to {out_path} (as a Python dict).")

if __name__ == "__main__":
    # Change this to your sample ECG image path
    img_path = r"C:\Users\wazzu\Desktop\digit-ecg\digit-ecg\sample_dataset\Subodh Prasad Mandal.jpg"
    coords = select_rois(img_path, LEAD_NAMES)
    if coords:
        save_coords(coords)