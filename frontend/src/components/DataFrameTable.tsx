interface DataFrameTableProps {
  data: { time: number; voltage: number }[];
}

export default function DataFrameTable({ data }: DataFrameTableProps) {
  return (
    <table className="dataframe-table">
      <thead>
        <tr>
          <th>Time (s)</th>
          <th>Voltage (mV)</th>
        </tr>
      </thead>
      <tbody>
        {data.map((row, i) => (
          <tr key={i}>
            <td>{row.time.toFixed(4)}</td> {/* Now safely calling toFixed on numbers */}
            <td>{row.voltage.toFixed(4)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}