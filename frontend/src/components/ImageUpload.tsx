import { useDropzone } from 'react-dropzone';

interface ImageUploadProps {
  onImageUpload: (file: File) => void;
}

export default function ImageUpload({ onImageUpload }: ImageUploadProps) {
  const { getRootProps, getInputProps } = useDropzone({
    accept: { 'image/*': ['.png', '.jpg', '.jpeg'] },
    maxFiles: 1,
    onDrop: (acceptedFiles) => onImageUpload(acceptedFiles[0]),
  });

  return (
    <div {...getRootProps()} className="image-upload">
      <input {...getInputProps()} />
      <p>Drag & drop an ECG image here, or click to select</p>
    </div>
  );
}