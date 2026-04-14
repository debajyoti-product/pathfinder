import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ArrowLeft, Copy, Send, Newspaper, Loader2, RefreshCw, Check } from "lucide-react";
import { JobResult, ProfileData } from "@/lib/mockData";
import { draftEmail } from "@/lib/api";
import { toast } from "sonner";

interface DraftingTabProps {
  result: JobResult;
  profile: ProfileData | null;
  onBack: () => void;
}

const DraftingTab = ({ result, profile, onBack }: DraftingTabProps) => {
  const [draft, setDraft] = useState("");
  const [research, setResearch] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  const fetchDraft = async () => {
    if (!profile) return;
    try {
      setLoading(true);
      const res = await draftEmail(profile, result.jobTitle, result.company);
      setDraft(res.email);
      setResearch(res.news || []);
    } catch (e) {
      console.error(e);
      toast.error("Failed to generate draft");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDraft();
  }, [profile, result]);

  const handleCopy = () => {
    navigator.clipboard.writeText(draft);
    setCopied(true);
    toast.success("Draft copied to clipboard");
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRegenerate = () => {
    setDraft("");
    setResearch([]);
    fetchDraft();
  };

  const wordCount = draft.trim().split(/\s+/).filter(Boolean).length;

  if (loading) {
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
            <span className="text-sm font-semibold text-primary">{result.company}</span>
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-[500px]">
          {/* Skeleton intel */}
          <div className="rounded-xl border border-border bg-card p-6 space-y-4 animate-pulse">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded bg-muted" />
              <div className="h-4 w-28 bg-muted rounded" />
            </div>
            {[0, 1, 2].map((i) => (
              <div key={i} className="p-3 rounded-lg bg-muted/30 space-y-2">
                <div className="h-3 w-3/4 bg-muted rounded" />
                <div className="h-3 w-1/2 bg-muted/60 rounded" />
              </div>
            ))}
          </div>
          {/* Skeleton draft */}
          <div className="rounded-xl border border-border bg-card p-6 space-y-4 animate-pulse">
            <div className="h-4 w-24 bg-muted rounded" />
            <div className="flex-1 rounded-lg bg-muted/30 min-h-[350px] flex items-center justify-center">
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="w-6 h-6 animate-spin text-primary" />
                <p className="text-xs text-muted-foreground">Crafting high-conversion email…</p>
              </div>
            </div>
            <div className="h-9 w-full bg-muted/30 rounded-lg" />
          </div>
        </div>
      </div>
    );
  }

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
          <div className="space-y-3 flex-1 overflow-y-auto max-h-[350px] pr-2">
            {research?.length > 0 ? (
              research.map((item, i) => (
                <div key={i} className="flex gap-3 p-3 rounded-lg bg-muted/50 border border-border/50 hover:border-primary/30 transition-colors">
                  <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2 shrink-0" />
                  <div className="flex flex-col gap-1 min-w-0">
                    <a href={item.link} target="_blank" rel="noopener noreferrer" className="text-sm font-semibold text-foreground hover:text-primary transition-colors hover:underline line-clamp-2">
                      {item.title}
                    </a>
                    {item.snippet && <p className="text-xs text-secondary-foreground leading-relaxed line-clamp-2">{item.snippet}</p>}
                    {(item.source || item.date) && (
                      <span className="text-xs text-muted-foreground">{item.source} {item.date ? `· ${item.date}` : ''}</span>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-sm text-muted-foreground italic">No recent news found.</div>
            )}
          </div>
        </div>

        {/* Right: Draft Editor */}
        <div className="rounded-xl border border-border bg-card p-6 space-y-4 flex flex-col">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">Email Draft</h3>
            <div className="flex gap-2">
              <Button variant="ghost" size="sm" onClick={handleRegenerate} className="gap-1.5 text-muted-foreground hover:text-foreground h-7 text-xs">
                <RefreshCw className="w-3 h-3" />
                Regenerate
              </Button>
              <Button variant="ghost" size="sm" onClick={handleCopy} className="gap-1.5 text-muted-foreground hover:text-foreground h-7 text-xs">
                {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                {copied ? "Copied" : "Copy"}
              </Button>
            </div>
          </div>
          <Textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            className="flex-1 min-h-[350px] resize-none bg-muted border-border text-foreground font-mono text-sm leading-relaxed"
          />
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">{wordCount} words</span>
            <Button 
              className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90"
              onClick={() => {
                let url = result.linkedin;
                if (url) {
                  if (!url.startsWith("http://") && !url.startsWith("https://")) {
                    url = `https://${url}`;
                  }
                  window.open(url, "_blank");
                } else {
                  toast.error("No LinkedIn profile available for this contact.");
                }
              }}
            >
              <Send className="w-4 h-4" />
              Send Draft on LinkedIn
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DraftingTab;
