interface ProcessingStatusProps {
  status: 'idle' | 'loading' | 'error' | 'success';
}

export default function ProcessingStatus({ status }: ProcessingStatusProps) {
  return (
    <div className={`status ${status}`}>
      {status === 'loading' && <div className="spinner">Processing ECG...</div>}
      {status === 'error' && <div className="error">Processing failed. Try again.</div>}
    </div>
  );
}