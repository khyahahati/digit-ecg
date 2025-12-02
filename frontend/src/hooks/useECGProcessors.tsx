export async function processECGImage(image: File) {
  console.log("Mock processing of ECG image:", image.name);
  
  // Return mock data matching your expected format
  return {
    waveform: Array.from({ length: 100 }, (_, i) => Math.sin(i / 5) * 2),
    timeStamps: Array.from({ length: 100 }, (_, i) => i * 0.1),
    heartRate: Math.floor(Math.random() * 40) + 60, // Random heart rate (60-100)
    dataframe: Array.from({ length: 100 }, (_, i) => ({
      time: i * 0.1,
      voltage: Math.sin(i / 5) * 2
    }))
  };
}