import { saveAs } from 'file-saver';

interface DownloadButtonsProps {
  dataframe: { time: number; voltage: number }[];
}

export default function DownloadButtons({ dataframe }: DownloadButtonsProps) {
  const downloadCSV = () => {
    const csv = [
      'Time (s),Voltage (mV)',
      ...dataframe.map(row => `${row.time.toFixed(2)},${row.voltage.toFixed(2)}`)
    ].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    saveAs(blob, 'ecg_data.csv');
  };

  return (
    <div className="download-buttons">
      <button onClick={downloadCSV}>Download CSV</button>
    </div>
  );
}