import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ArrowLeft, Copy, Send, Newspaper } from "lucide-react";
import { JobResult, mockResearch, generateDraft } from "@/lib/mockData";
import { toast } from "sonner";

interface DraftingTabProps {
  result: JobResult;
  onBack: () => void;
}

const DraftingTab = ({ result, onBack }: DraftingTabProps) => {
  const [draft, setDraft] = useState(generateDraft(result.name, result.company, result.jobTitle));
  const research = mockResearch[result.company];

  const handleCopy = () => {
    navigator.clipboard.writeText(draft);
    toast.success("Draft copied to clipboard");
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={onBack} className="gap-1.5 text-muted-foreground hover:text-foreground">
          <ArrowLeft className="w-4 h-4" />
          Back to Results
        </Button>
        <div className="h-4 w-px bg-border" />
        <div>
          <span className="text-sm text-muted-foreground">Drafting for </span>
          <span className="text-sm font-semibold text-foreground">{result.name}</span>
          <span className="text-sm text-muted-foreground"> at </span>
          <span className="text-sm font-semibold text-primary">{result.company}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-[500px]">
        {/* Left: Research */}
        <div className="rounded-xl border border-border bg-card p-6 space-y-5 flex flex-col">
          <div className="flex items-center gap-2">
            <Newspaper className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">Company Intel</h3>
          </div>
          <div className="space-y-3 flex-1">
            {research?.snippets.map((snippet, i) => (
              <div key={i} className="flex gap-3 p-3 rounded-lg bg-muted/50 border border-border/50">
                <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2 shrink-0" />
                <p className="text-sm text-secondary-foreground leading-relaxed">{snippet}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Draft Editor */}
        <div className="rounded-xl border border-border bg-card p-6 space-y-4 flex flex-col">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">Email Draft</h3>
            <div className="flex gap-2">
              <Button variant="ghost" size="sm" onClick={handleCopy} className="gap-1.5 text-muted-foreground hover:text-foreground">
                <Copy className="w-3.5 h-3.5" />
                Copy
              </Button>
            </div>
          </div>
          <Textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            className="flex-1 min-h-[350px] resize-none bg-muted border-border text-foreground font-mono text-sm leading-relaxed"
          />
          <Button className="w-full gap-2 bg-primary text-primary-foreground hover:bg-primary/90 glow-sm">
            <Send className="w-4 h-4" />
            Send Draft
          </Button>
        </div>
      </div>
    </div>
  );
};

export default DraftingTab;
