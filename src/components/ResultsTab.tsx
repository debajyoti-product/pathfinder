import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowUpRight, PenLine, Loader2, Briefcase, User, Building2, TrendingUp, Info } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { JobResult, ProfileData, ProfileLead } from "@/lib/mockData";
import { streamDiscoverJobs } from "@/lib/api";

interface ResultsTabProps {
  profile: ProfileData | null;
  onGenerate: (result: JobResult, pocName?: string, pocLinkedin?: string) => void;
}

interface JobStatus {
  company: string;
  status: string;
  removing?: boolean;
}

const ResultsTab = ({ profile, onGenerate }: ResultsTabProps) => {
  const [results, setResults] = useState<JobResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState("Discovering matched jobs...");
  const [activeJobs, setActiveJobs] = useState<Record<string, JobStatus>>({});
  const [stats, setStats] = useState<{searched: number, passed: number, rejected: number} | null>(null);

  useEffect(() => {
    let active = true;
    
    async function initStream() {
      if (!profile) return;
      setLoading(true);
      setResults([]);
      setStatus("Scanning jobs for matches & discovering profiles...");

      await streamDiscoverJobs(
        profile,
        (event) => {
          if (!active) return;
          
          if (event.type === 'job') {
            setResults((prev) => [...prev, event]);
            setActiveJobs((prev) => {
              const next = { ...prev };
              delete next[event.id];
              return next;
            });
          } else if (event.type === 'status') {
            setActiveJobs((prev) => ({
              ...prev,
              [event.jobId]: { company: event.company, status: event.status }
            }));
          } else if (event.type === 'remove') {
            setActiveJobs((prev) => {
              if (!prev[event.jobId]) return prev;
              return {
                ...prev,
                [event.jobId]: { ...prev[event.jobId], removing: true }
              };
            });
            setTimeout(() => {
              if (active) {
                setActiveJobs((prev) => {
                  const next = { ...prev };
                  delete next[event.jobId];
                  return next;
                });
              }
            }, 500); // 500ms fade out
          } else if (event.type === 'stats') {
            setStats({
              searched: event.searched,
              passed: event.passed,
              rejected: event.rejected
            });
          }
        },
        () => {
           if (active) {
             setLoading(false);
             setStatus("Discovery complete.");
           }
        },
        (err) => {
           if (active) {
             console.error("Discovery error:", err);
             setLoading(false);
             setStatus("Discovery complete with some errors.");
           }
        }
      );
    }
    
    initStream();
    return () => { active = false; };
  }, [profile]);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          {loading && (
            <div className="animate-spin rounded-full h-5 w-5 border-2 border-primary border-t-transparent border-dotted" />
          )}
          <h2 className="text-xl font-bold">Jobs ({results.length})</h2>
        </div>
        
        <Dialog>
          <DialogTrigger asChild>
            <button className="text-xs text-muted-foreground hover:text-foreground transition-colors cursor-pointer outline-none flex items-center gap-1.5 bg-muted/30 px-3 py-1.5 rounded-full border border-border/50">
              <Info className="w-3.5 h-3.5" /> Exclusion criteria
            </button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px] bg-background/80 backdrop-blur-xl border-border/50">
            <DialogHeader>
              <DialogTitle>Exclusion Criteria</DialogTitle>
            </DialogHeader>
            <div className="text-sm text-muted-foreground pt-2">
              <ul className="list-disc pl-5 space-y-2">
                <li>Expired or closed jobs</li>
                <li>Don't match seniority/experience level</li>
                <li>Different role</li>
                <li>Don't match remote work (if applicable)</li>
              </ul>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="mt-0">
        {loading && results.length === 0 && (
          <div className="flex flex-col items-center justify-center py-10 gap-3 animate-pulse">
            <div className="flex items-end gap-1 text-primary">
              <User className="w-8 h-8 animate-bounce" />
              <Briefcase className="w-5 h-5 mb-1" />
            </div>
            <p className="text-muted-foreground text-sm font-medium tracking-wide uppercase">finding matches for you</p>
          </div>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {results.map((result) => (
            <div
              key={result.id}
              className="group rounded-xl border border-border bg-card hover:border-primary/30 hover:bg-card/80 transition-all duration-200 p-4 flex flex-col gap-3 text-sm"
            >
              {/* Header */} 
              <div className="flex flex-col gap-3 flex-1 min-w-0">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 min-w-0 flex-1">
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[hsl(221,83%,53%)]/15 to-[hsl(160,84%,20%)]/20 border border-primary/20 flex items-center justify-center shrink-0">
                      <Building2 className="w-5 h-5 text-primary" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="text-sm font-semibold text-foreground truncate">{result.company}</h3>
                      <p className="text-xs text-muted-foreground truncate">{result.jobTitle}</p>
                    </div>
                  </div>
                  {result.requiredExperience && (
                    <Badge variant="outline" className="text-[10px] bg-muted/50 border-border text-muted-foreground shrink-0">
                      {result.requiredExperience}
                    </Badge>
                  )}
                </div>

                <div className="mt-3 flex items-center justify-between gap-2 border-t border-border/50 pt-3">
                  {result.linkedin ? (
                    <a
                      href={result.linkedin.startsWith("http") ? result.linkedin : `https://${result.linkedin}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs font-semibold text-transparent bg-clip-text bg-gradient-to-r from-[hsl(221,83%,53%)] to-[hsl(160,84%,20%)] hover:underline inline-flex items-center gap-1 hover:opacity-80 transition-opacity"
                    >
                      View Job <ArrowUpRight className="w-3.5 h-3.5 text-primary" />
                    </a>
                  ) : (
                    <span className="text-xs font-medium text-muted-foreground inline-flex items-center gap-1">
                      View Job <ArrowUpRight className="w-3.5 h-3.5" />
                    </span>
                  )}
                  {result.confidence && (
                    <Dialog>
                      <DialogTrigger asChild>
                        <Badge
                          variant="secondary"
                          className={`text-[10px] shrink-0 cursor-pointer hover:opacity-80 transition-opacity ${
                            result.confidence >= 0.85
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                              : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                          }`}
                        >
                          {Math.round(result.confidence * 100)}% fit
                        </Badge>
                      </DialogTrigger>
                      {result.reason && (
                        <DialogContent className="sm:max-w-md">
                          <DialogHeader>
                            <DialogTitle className="text-emerald-400">{Math.round(result.confidence * 100)}% Match Insights</DialogTitle>
                          </DialogHeader>
                          <div className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                            {result.reason}
                          </div>
                        </DialogContent>
                      )}
                    </Dialog>
                  )}
                </div>
              </div>

              {/* Contacts */}
              <div className="space-y-3 pt-3 border-t border-border/50">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Discovered Profiles</h4>
                {(!result.pocProfiles || result.pocProfiles.length === 0) ? (
                   <p className="text-xs text-muted-foreground italic">Unable to find Linkedin POC.</p>
                ) : (
                    <div className="grid gap-2">
                     {result.pocProfiles.map((poc, idx) => {
                       const pKey = poc.id || `${result.id}-poc-${idx}`;
                       return (
                          <div key={pKey} className="flex justify-between items-center bg-muted/40 p-2 rounded-lg border border-border/50 min-w-0">
                            <div className="flex flex-col min-w-0 flex-1 overflow-hidden">
                              <div className="flex items-center gap-2 text-sm font-medium min-w-0">
                                <User className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                                <span className="truncate">{poc.name || "Unknown"}</span>
                              </div>
                              <div className="text-xs text-muted-foreground truncate pl-5 max-w-full">
                                {poc.currentRole}
                              </div>
                            </div>
                            {poc.linkedinUrl && (
                              <div className="flex pl-2 shrink-0">
                                <a
                                  href={poc.linkedinUrl.startsWith("http") ? poc.linkedinUrl : `https://${poc.linkedinUrl}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-primary hover:bg-primary/10 p-1.5 rounded-full transition-colors flex items-center justify-center"
                                >
                                  <ArrowUpRight className="w-4 h-4" />
                                </a>
                              </div>
                            )}
                          </div>
                        );
                     })}
                   </div>
                )}
              </div>

              {/* Action */}
              <Button
                size="sm"
                onClick={() => onGenerate(result)}
                className="w-full gap-1.5 bg-gradient-to-r from-[hsl(221,83%,53%)] to-[hsl(160,84%,20%)] text-white hover:opacity-95 shadow-sm mt-auto font-medium"
              >
                <PenLine className="w-3.5 h-3.5" />
                Generate Draft
              </Button>
            </div>
          ))}
          </div>
        </div>

      {results.length === 0 && Object.keys(activeJobs).length === 0 && !loading && (
        <div className="rounded-xl border border-dashed border-border bg-card/50 flex flex-col items-center justify-center py-16 gap-3">
          <Briefcase className="w-10 h-10 text-muted-foreground/40" />
          <p className="text-muted-foreground text-sm">No matched jobs found for your profile.</p>
        </div>
      )}
    </div>
  );
};

export default ResultsTab;
