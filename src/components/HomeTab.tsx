import { useCallback, useState } from "react";
import { Upload, FileText, Sparkles } from "lucide-react";

interface HomeTabProps {
  onUpload: () => void;
}

const HomeTab = ({ onUpload }: HomeTabProps) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

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
      onUpload();
    },
    [onUpload]
  );

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-8">
      <div
        onDragEnter={handleDragIn}
        onDragLeave={handleDragOut}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={onUpload}
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
              PDF, DOCX, or TXT — max 10MB
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomeTab;
