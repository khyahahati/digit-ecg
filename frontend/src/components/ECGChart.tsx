import { Line } from 'react-chartjs-2';
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);

interface ECGChartProps {
  data: {
    timeStamps: number[];
    waveform: number[];
  };
}

export default function ECGChart({ data }: ECGChartProps) {
  const chartData = {
    labels: data.timeStamps.map(t => t.toFixed(2)),
    datasets: [{
      label: 'ECG Waveform (mV)',
      data: data.waveform,
      borderColor: '#3b82f6',
      tension: 0.1,
    }],
  };

  return <Line data={chartData} />;
}