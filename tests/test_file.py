import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from ecg_pipeline import ecg_image_to_features, ECGDigitizer

def visualize_ecg_with_peaks(time_values, voltage_values, lead_name, heart_rate=None):
    """Helper function to visualize ECG signal with detected peaks."""
    plt.figure(figsize=(12, 4))
    plt.plot(time_values, voltage_values, label='ECG Signal')
    
    # Add title with lead and heart rate if available
    title = f"Lead {lead_name} ECG Signal"
    if heart_rate is not None and not pd.isna(heart_rate):
        title += f" (HR: {heart_rate:.1f} BPM)"
    plt.title(title)
    
    plt.xlabel("Time (s)")
    plt.ylabel("Voltage (mV)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

def analyze_ecg(image_path: str, output_csv: str = None, show_plot: bool = True) -> pd.DataFrame:
    """Enhanced ECG analysis with robust error handling and visualization.
    
    Args:
        image_path: Path to ECG image file
        output_csv: Optional path to save results as CSV
        show_plot: Whether to display ECG plot with detected peaks
        
    Returns:
        DataFrame containing extracted ECG signals and heart rate
    """
    try:
        print(f"\n{'='*50}")
        print(f"Processing ECG image: {image_path}")
        print(f"{'='*50}")
        
        # Load image
        with open(image_path, "rb") as f:
            img_bytes = f.read()
        
        # Process ECG
        print("\nExtracting ECG signals...")
        df = ecg_image_to_features(img_bytes)
        
        if df.empty:
            print("Warning: No ECG signals could be extracted")
            return pd.DataFrame()
        
        # Get analysis results
        available_leads = [col.replace('_time', '') for col in df.columns if '_time' in col]
        hr = df['heart_rate_bpm'].iloc[0] if 'heart_rate_bpm' in df.columns else np.nan
        
        print("\nAnalysis Results:")
        print(f"- Extracted {len(available_leads)} leads")
        print(f"- Leads found: {', '.join(available_leads)}")
        
        if not pd.isna(hr):
            print(f"- Calculated Heart Rate: {hr:.1f} BPM")
        else:
            print("- Heart Rate: Could not be determined")
        
        # Save results if requested
        if output_csv:
            try:
                df.to_csv(output_csv, index=False)
                print(f"\nResults saved to {output_csv}")
            except Exception as e:
                print(f"\nWarning: Could not save results to CSV - {str(e)}")
        
        # Visualization
        if show_plot and not df.empty:
            available_leads = [col.replace('_time', '') for col in df.columns if '_time' in col]
            if available_leads:
                # Try to use best lead if digitizer provides it, otherwise use first available lead
                lead_to_plot = available_leads[0]
                # best_lead is an instance attribute, not class attribute
                # So we can't check ECGDigitizer.best_lead, must be from an instance if available
                visualize_ecg_with_peaks(
                    df[f'{lead_to_plot}_time'].values,
                    df[f'{lead_to_plot}_voltage'].values,
                    lead_to_plot,
                    hr
                )
                    
        return df
    
    except FileNotFoundError:
        print(f"\nError: Image file not found at {image_path}")
        return pd.DataFrame()
    except Exception as e:
        print(f"\nError processing ECG: {str(e)}")
        return pd.DataFrame()

if __name__ == "__main__":
    # Example usage
    input_image = r"C:\\Users\wazzu\Desktop\digit-ecg\digit-ecg\sample_dataset\Subodh Prasad Mandal.jpg"
    output_file = r"C:\Users\wazzu\Desktop\digit-ecg\digit-ecg\results\ecg_results.csv"
    
    # Run analysis
    results_df = analyze_ecg(
        image_path=input_image,
        output_csv=output_file,
        show_plot=True
    )
    
    # Additional output if results were obtained
    if not results_df.empty:
        print("\nProcessing complete. Summary of extracted data:")
        print(results_df.describe())