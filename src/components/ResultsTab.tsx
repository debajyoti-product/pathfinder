import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, PenLine, Loader2, Briefcase, User, Building2, TrendingUp, ThumbsUp, ThumbsDown } from "lucide-react";
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

  const [feedback, setFeedback] = useState<Record<string, 'up' | 'down'>>({});

  useEffect(() => {
    let active = true;
    
    async function initStream() {
      if (!profile) return;
      setLoading(true);
      setResults([]);
      setStatus("Scanning job boards for matches & discovering profiles...");

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
            setLoading(false);
          } else if (event.type === 'status') {
            setActiveJobs((prev) => ({
              ...prev,
              [event.jobId]: { company: event.company, status: event.status }
            }));
            setLoading(false);
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

  const handleFeedback = (profileId: string, type: 'up' | 'down') => {
    setFeedback(prev => ({ ...prev, [profileId]: type }));
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col gap-1">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-foreground">Job Results for You</h2>
            <p className="text-muted-foreground text-sm mt-1">
              {results.length > 0
                ? "Includes job links & potential referral profiles"
                : "Scanning the market for perfect matches..."}
            </p>
          </div>
          {results.length > 0 && (
            <Badge variant="secondary" className="gap-1.5 bg-primary/10 text-primary border-primary/20">
              <TrendingUp className="w-3 h-3" />
              {results.length} match{results.length !== 1 ? "es" : ""}
            </Badge>
          )}
        </div>
        
        {/* Funnel Stats */}
        {stats && (
          <div className="text-xs text-muted-foreground mt-2 bg-muted/30 px-3 py-2 rounded-md border border-border/50 inline-block w-fit">
            Searched <strong>{stats.searched}</strong> postings &rarr; <strong>{stats.searched - stats.rejected}</strong> matched criteria &rarr; <strong>{stats.passed}</strong> passed quality checks
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {results.map((result) => (
            <div
              key={result.id}
              className="group rounded-xl border border-border bg-card hover:border-primary/30 hover:bg-card/80 transition-all duration-200 p-5 flex flex-col gap-4"
            >
              {/* Header */} 
              <div className="flex flex-col gap-3 flex-1 min-w-0">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 min-w-0 flex-1">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
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



                <div className="flex items-center justify-between">
                  {result.linkedin && (
                    <a
                      href={result.linkedin.startsWith("http") ? result.linkedin : `https://${result.linkedin}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-primary hover:underline inline-flex items-center gap-1 font-medium"
                    >
                      View Job <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                  {result.confidence && (
                    <div className="relative group/badge flex items-center justify-center">
                      <Badge
                        variant="secondary"
                        className={`text-[10px] shrink-0 cursor-help ${
                          result.confidence >= 0.85
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                        }`}
                      >
                        {Math.round(result.confidence * 100)}% fit
                      </Badge>
                      {/* Reason Tooltip */}
                      {result.reason && (
                        <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 w-48 p-2 bg-popover text-popover-foreground text-xs rounded shadow-lg border border-border opacity-0 group-hover/badge:opacity-100 pointer-events-none transition-opacity z-10 break-words text-center">
                          {result.reason}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Contacts */}
              <div className="space-y-3 pt-3 border-t border-border/50">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Discovered Profiles</h4>
                {(!result.pocProfiles || result.pocProfiles.length === 0) ? (
                   <p className="text-xs text-muted-foreground italic">No specific profiles found.</p>
                ) : (
                   <div className="grid gap-2">
                     {result.pocProfiles.map((poc, idx) => {
                       const pKey = poc.id || `${result.id}-poc-${idx}`;
                       const fBack = feedback[pKey];
                       return (
                          <div key={pKey} className="flex justify-between items-center bg-muted/40 p-2 rounded-lg border border-border/50 min-w-0">
                            <div className="flex flex-col min-w-0 flex-1 overflow-hidden">
                              <div className="flex items-center gap-2 text-sm font-medium min-w-0">
                                <User className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                                <span className="truncate">{poc.name || "Unknown"}</span>
                                {poc.linkedinUrl && (
                                  <a
                                    href={poc.linkedinUrl.startsWith("http") ? poc.linkedinUrl : `https://${poc.linkedinUrl}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-primary hover:underline inline-flex items-center gap-0.5 text-xs font-normal shrink-0"
                                  >
                                    <ExternalLink className="w-2.5 h-2.5 ml-1" />
                                  </a>
                                )}
                              </div>
                              <div className="text-xs text-muted-foreground truncate pl-5 max-w-full">
                                {poc.currentRole}
                              </div>
                            </div>
                             <div className="flex gap-1 pl-2">
                               <Button 
                                 variant="ghost" 
                                 size="icon" 
                                 className="h-7 w-7 text-primary hover:bg-primary/10"
                                 title="Draft message for this contact"
                                 onClick={() => onGenerate(result, poc.name, poc.linkedinUrl)}
                               >
                                 <PenLine className="w-3.5 h-3.5" />
                               </Button>
                               <Button 
                                 variant="ghost" 
                                 size="icon" 
                                 className={`h-7 w-7 ${fBack === 'up' ? 'text-emerald-500 bg-emerald-500/10' : 'text-muted-foreground hover:text-emerald-500'}`}
                                 onClick={() => handleFeedback(pKey, 'up')}
                               >
                                 <ThumbsUp className="w-3.5 h-3.5" />
                               </Button>
                               <Button 
                                 variant="ghost" 
                                 size="icon" 
                                 className={`h-7 w-7 ${fBack === 'down' ? 'text-destructive bg-destructive/10' : 'text-muted-foreground hover:text-destructive'}`}
                                 onClick={() => handleFeedback(pKey, 'down')}
                               >
                                 <ThumbsDown className="w-3.5 h-3.5" />
                               </Button>
                             </div>
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
                className="w-full gap-1.5 bg-primary text-primary-foreground hover:bg-primary/90 mt-auto"
              >
                <PenLine className="w-3.5 h-3.5" />
                Generate Draft
              </Button>
            </div>
          ))}
          {/* Active Evaluation Skeletons */}
          {Object.entries(activeJobs).map(([jobId, job]) => (
            <div 
              key={jobId} 
              className={`rounded-xl border border-primary/20 bg-card/40 p-5 flex flex-col gap-4 shadow-[0_0_15px_rgba(var(--primary),0.1)] transition-all duration-500 ${
                job.removing ? 'opacity-0 scale-95' : 'opacity-100 scale-100'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                  <Loader2 className="w-5 h-5 text-primary animate-spin" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-semibold text-foreground truncate">{job.company || "Unknown Company"}</h3>
                  <p className="text-xs text-primary font-medium truncate animate-pulse mt-0.5">{job.status}</p>
                </div>
              </div>
              <div className="space-y-2 mt-2">
                <div className="h-3 w-3/4 bg-muted/60 rounded" />
                <div className="h-3 w-1/2 bg-muted/60 rounded" />
              </div>
              <div className="h-8 w-full bg-muted/30 rounded-lg mt-auto" />
            </div>
          ))}
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
