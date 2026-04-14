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
        <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center animate-pulse">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
        </div>
        <div className="text-center space-y-2">
          <h3 className="text-xl font-semibold text-foreground">Reading Resume</h3>
          <p className="text-muted-foreground">Extracting experience and skills with Gemini...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-8">
      <label
        onDragEnter={handleDragIn}
        onDragLeave={handleDragOut}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`
          relative group cursor-pointer w-full max-w-lg rounded-2xl border-2 border-dashed p-12
          transition-all duration-300 ease-out
          ${
            isDragging
              ? "border-primary bg-primary/5 glow-md scale-[1.02]"
              : "border-border hover:border-primary/40 hover:bg-muted/30 hover:glow-sm"
          }
        `}
      >
        <input type="file" className="hidden" accept=".pdf" onChange={handleFileChange} />
        <div className="flex flex-col items-center gap-4 text-center">
          <div
            className={`
              p-4 rounded-2xl transition-all duration-300
              ${isDragging ? "bg-primary/15 text-primary" : "bg-muted text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary"}
            `}
          >
            {isDragging ? (
              <FileText className="w-8 h-8" />
            ) : (
              <Upload className="w-8 h-8" />
            )}
          </div>
          <div>
            <p className="text-foreground font-medium text-base">
              {isDragging ? "Release to upload" : "Drop your resume here"}
            </p>
            <p className="text-muted-foreground text-sm mt-1">
              PDF only — max 10MB
            </p>
          </div>
        </div>
      </label>
    </div>
  );
};

export default HomeTab;
