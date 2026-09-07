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
  const [research, setResearch] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [mode, setMode] = useState<'preview' | 'edit'>('preview');

  const fetchDraft = async () => {
    if (!profile) return;
    try {
      setLoading(true);
      const pocName = result.name || undefined;
      const pocRole = result.pocProfiles?.find(p => p.name === result.name)?.currentRole || undefined;
      const jobUrl = result.url || result.linkedin || undefined;
      const res = await draftEmail(profile, result.jobTitle, result.company, pocName, pocRole, jobUrl);
      setDraft(res.email);
      setResearch(res.company_intel || "");
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
    setResearch("");
    fetchDraft();
  };

  const wordCount = draft.trim().split(/\s+/).filter(Boolean).length;

  const renderRichText = (text: string) => {
    // Replace markdown links [text](url) or bare URLs with styled anchors
    // Also handling potential bare URLs that are not in markdown format
    let html = text.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, '<a href="$2" target="_blank" class="text-primary font-medium hover:underline">$1</a>');
    
    // For bare URLs, try to replace them if they aren't already in an anchor tag
    // This is a simplified regex, assuming the LLM might sometimes just spit out the URL
    html = html.replace(/(^|[^"'])(https?:\/\/[^\s]+)/g, (match, prefix, url) => {
       if (prefix.includes('<a href=')) return match; // already an anchor
       return `${prefix}<a href="${url}" target="_blank" class="text-primary font-medium hover:underline">Link</a>`;
    });
    
    html = html.replace(/\n/g, '<br />');
    
    return (
      <div 
        dangerouslySetInnerHTML={{ __html: html }} 
        className="flex-1 min-h-[350px] bg-muted/30 border border-border rounded-md p-4 text-sm leading-relaxed text-foreground overflow-y-auto font-sans" 
      />
    );
  };

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
          {result.name && (
            <>
              <span className="text-sm font-semibold text-foreground">{result.name}</span>
              <span className="text-sm text-muted-foreground"> at </span>
            </>
          )}
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
          <div className="flex-1 overflow-y-auto max-h-[450px] pr-2">
            {research ? (
              <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-secondary-foreground">
                {research}
              </pre>
            ) : (
              <div className="text-sm text-muted-foreground italic">No intel generated.</div>
            )}
          </div>
        </div>

        {/* Right: Draft Editor */}
        <div className="rounded-xl border border-border bg-card p-6 space-y-4 flex flex-col">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">Email Draft</h3>
            <div className="flex gap-2 items-center">
              <div className="flex bg-muted rounded-md p-0.5 border border-border mr-2">
                 <button 
                   onClick={() => setMode('preview')} 
                   className={`px-3 py-1 text-xs rounded-sm font-medium transition-colors ${mode === 'preview' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                 >
                   Preview
                 </button>
                 <button 
                   onClick={() => setMode('edit')} 
                   className={`px-3 py-1 text-xs rounded-sm font-medium transition-colors ${mode === 'edit' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                 >
                   Raw Edit
                 </button>
              </div>
              <Button variant="ghost" size="sm" onClick={handleRegenerate} className="gap-1.5 text-muted-foreground hover:text-foreground h-7 text-xs">
                <RefreshCw className="w-3 h-3" />
                Regenerate
              </Button>
            </div>
          </div>
          
          {mode === 'edit' ? (
            <Textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              className="flex-1 min-h-[350px] resize-none bg-muted border-border text-foreground font-mono text-sm leading-relaxed"
            />
          ) : (
            renderRichText(draft)
          )}
          
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">{wordCount} words</span>
            <Button 
              className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90"
              onClick={handleCopy}
            >
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              {copied ? "Copied!" : "Copy Draft"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DraftingTab;
