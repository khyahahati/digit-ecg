import pandas as pd
from digit_ecg_tool.ecg_pipeline import ecg_image_to_features

def main():
    # 1. Path to a sample ECG image (JPEG/PNG)
    img_path = "sample_ecg.jpg"  # Change to your own file

    # 2. Read file as bytes
    with open(img_path, "rb") as f:
        img_bytes = f.read()

    # 3. Run the pipeline
    df = ecg_image_to_features(img_bytes)

    # 4. Print the result
    print(df)
    # Optionally, save to CSV to inspect
    df.to_csv("test_ecg_results.csv", index=False)
    print("Results saved to test_ecg_results.csv")

if __name__ == "__main__":
    main()