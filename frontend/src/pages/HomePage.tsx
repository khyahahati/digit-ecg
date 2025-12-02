import { useState } from 'react';
import ImageUpload from '../components/ImageUpload';
import ECGChart from '../components/ECGChart';
import DataFrameTable from '../components/DataFrameTable';
import ProcessingStatus from '../components/ProcessingStatus';
import DownloadButtons from '../components/DownloadButtons';

// Mock processor function (no API needed)
const mockECGProcessor = async (image: File) => {
  // Simulate processing delay
  await new Promise(resolve => setTimeout(resolve, 1500));
  
  // Generate realistic mock ECG data (keeping numbers as numbers)
  const length = 300;
  const baseline = 0.5;
  const noise = () => (Math.random() - 0.5) * 0.2;
  
  return {
    waveform: Array.from({ length }, (_, i) => {
      if (i % 50 === 0) return baseline + 1.2 + noise(); // QRS peak
      if (i % 50 === 25) return baseline + 0.3 + noise(); // P wave
      return baseline + noise(); // Baseline
    }),
    timeStamps: Array.from({ length }, (_, i) => i * 0.01), // 10ms intervals
    heartRate: Math.floor(Math.random() * 30) + 60, // 60-90 BPM
    dataframe: Array.from({ length }, (_, i) => ({
      time: i * 0.01, // Keep as number
      voltage: baseline + (i % 50 === 0 ? 1.2 : i % 50 === 25 ? 0.3 : 0) + noise() // Keep as number
    }))
  };
};

export default function HomePage() {
  const [ecgImage, setEcgImage] = useState<File | null>(null);
  const [results, setResults] = useState<{ 
    waveform: number[]; 
    timeStamps: number[]; 
    heartRate: number; 
    dataframe: { time: number; voltage: number }[] // Corrected to use numbers
  } | null>(null);
  const [status, setStatus] = useState<'idle' | 'loading' | 'error' | 'success'>('idle');

  const handleProcess = async () => {
    if (!ecgImage) return;
    setStatus('loading');
    try {
      const data = await mockECGProcessor(ecgImage);
      setResults(data);
      setStatus('success');
    } catch (error) {
      console.error("Processing error:", error);
      setStatus('error');
    }
  };

  return (
    <div className="home-page" style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h1 style={{ textAlign: 'center', color: '#2c3e50' }}>ECG Digitization Tool</h1>
      <ImageUpload onImageUpload={setEcgImage} />
      <button 
        onClick={handleProcess} 
        disabled={!ecgImage || status === 'loading'}
        style={{
          display: 'block',
          margin: '20px auto',
          padding: '10px 20px',
          backgroundColor: ecgImage && status !== 'loading' ? '#3498db' : '#95a5a6',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        {status === 'loading' ? 'Processing...' : 'Process ECG'}
      </button>
      <ProcessingStatus status={status} />
      {results && (
        <div style={{ marginTop: '30px' }}>
          <div style={{ 
            fontSize: '1.2rem', 
            fontWeight: 'bold', 
            textAlign: 'center',
            margin: '20px 0',
            color: '#e74c3c'
          }}>
            Heart Rate: {results.heartRate} BPM
          </div>
          <div style={{ height: '300px', marginBottom: '40px' }}>
            <ECGChart data={{ timeStamps: results.timeStamps, waveform: results.waveform }} />
          </div>
          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            <DataFrameTable data={results.dataframe} />
          </div>
          <DownloadButtons dataframe={results.dataframe} />
        </div>
      )}
    </div>
  );
}