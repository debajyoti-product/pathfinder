import { useCallback, useState } from "react";
import { Upload, FileText, Loader2 } from "lucide-react";

interface HomeTabProps {
  onUpload: (file: File) => void;
  isUploading?: boolean;
}

const HomeTab = ({ onUpload, isUploading = false }: HomeTabProps) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isUploading) setIsDragging(true);
  }, [isUploading]);

  const handleDragOut = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      if (isUploading) return;
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        onUpload(e.dataTransfer.files[0]);
      }
    },
    [onUpload, isUploading]
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (isUploading) return;
    if (e.target.files && e.target.files.length > 0) {
      onUpload(e.target.files[0]);
    }
  };

  if (isUploading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-6">
        <div className="w-16 h-16 rounded-md border-2 border-[#F5C518] flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-[#F5C518] animate-spin" />
        </div>
        <div className="text-center space-y-2">
          <h3 className="text-xl font-semibold text-foreground">Reading Resume</h3>
          <p className="text-muted-foreground">Extracting experience & skills</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh]">
      <label
        onDragEnter={handleDragIn}
        onDragLeave={handleDragOut}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`
          relative group cursor-pointer w-full max-w-lg
          transition-all duration-300 ease-out
          ${isDragging ? "scale-[1.02]" : ""}
        `}
      >
        {/* Corner markers */}
        <div className="absolute -top-2 -left-2 w-3 h-3 border-l-2 border-t-2 border-foreground/20" />
        <div className="absolute -top-2 -right-2 w-3 h-3 border-r-2 border-t-2 border-foreground/20" />
        <div className="absolute -bottom-2 -left-2 w-3 h-3 border-l-2 border-b-2 border-foreground/20" />
        <div className="absolute -bottom-2 -right-2 w-3 h-3 border-r-2 border-b-2 border-foreground/20" />
        
        <div className={`w-full h-full p-12 flex flex-col items-center gap-5 text-center transition-all border-2 border-dashed rounded-md ${
          isDragging ? 'border-[#F5C518] bg-[#F5C518]/5' : 'border-border hover:border-[#F5C518]/50'
        }`}>
          <input type="file" className="hidden" accept=".pdf" onChange={handleFileChange} />
          
          <div
            className={`
              p-4 rounded-md transition-all duration-300
              bg-[#F5C518] text-[#1a1a1a]
              ${isDragging ? "scale-110" : "group-hover:scale-105"}
            `}
          >
            {isDragging ? (
              <FileText className="w-7 h-7" strokeWidth={2} />
            ) : (
              <Upload className="w-7 h-7" strokeWidth={2} />
            )}
          </div>
          
          <div>
            <p className="text-foreground font-bold text-lg tracking-tight">
              {isDragging ? "Release to upload" : "Drop your resume"}
            </p>
            <p className="text-muted-foreground text-xs mt-1.5 font-semibold tracking-wider uppercase">
              PDF only — max 10MB
            </p>
          </div>
        </div>
      </label>
    </div>
  );
};

export default HomeTab;
