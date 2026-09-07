import { useState, useEffect } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, PenLine, Loader2, Briefcase, User, Building2, TrendingUp, ThumbsUp, ThumbsDown, Info } from "lucide-react";
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
  const [boards, setBoards] = useState<JobResult[]>([]);
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
      setBoards([]);
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
          } else if (event.type === 'board') {
            setBoards((prev) => [...prev, {
              id: String(Math.random()),
              company: event.boardName,
              jobTitle: `Search Results on ${event.boardName}`,
              url: event.url,
              linkedin: "",
              isBoard: true
            } as JobResult]);
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

  const handleFeedback = (profileId: string, type: 'up' | 'down') => {
    setFeedback(prev => ({ ...prev, [profileId]: type }));
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex justify-center mb-2">
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

      <Tabs defaultValue="companies" className="w-full">
        <div className="flex justify-center mb-6">
          <TabsList>
            <TabsTrigger value="companies">Companies ({results.length})</TabsTrigger>
            <TabsTrigger value="boards">Job Boards ({boards.length})</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="companies" className="mt-0">
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

                <div className="mt-3 flex items-center justify-between gap-2 border-t border-border/50 pt-3">
                  {result.linkedin ? (
                    <a
                      href={result.linkedin.startsWith("http") ? result.linkedin : `https://${result.linkedin}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs font-medium text-primary hover:underline inline-flex items-center gap-1 hover:opacity-80 transition-opacity"
                    >
                      View Job <ExternalLink className="w-3 h-3" />
                    </a>
                  ) : (
                    <span className="text-xs font-medium text-muted-foreground inline-flex items-center gap-1">
                      View Job <ExternalLink className="w-3 h-3" />
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
                          <div className="text-sm text-foreground leading-relaxed">
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
          </div>
        </TabsContent>

        <TabsContent value="boards" className="mt-0">
          {loading && boards.length === 0 && (
            <div className="flex flex-col items-center justify-center py-10 gap-3 animate-pulse">
              <div className="flex items-end gap-1 text-primary">
                <User className="w-8 h-8 animate-bounce" />
                <Briefcase className="w-5 h-5 mb-1" />
              </div>
              <p className="text-muted-foreground text-sm font-medium tracking-wide uppercase">finding matches for you</p>
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {boards.map((result) => (
              <div
                key={result.id}
                className="group rounded-xl border border-border bg-card hover:border-primary/30 hover:bg-card/80 transition-all duration-200 p-5 flex flex-col gap-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 min-w-0 flex-1">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                      <Briefcase className="w-5 h-5 text-primary" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="text-sm font-semibold text-foreground truncate">{result.company}</h3>
                      <p className="text-xs text-muted-foreground truncate">{result.jobTitle}</p>
                    </div>
                  </div>
                </div>
                {result.url && (
                  <Button variant="outline" size="sm" asChild className="w-full gap-1.5 mt-auto">
                    <a href={result.url} target="_blank" rel="noopener noreferrer">
                      View Jobs <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </Button>
                )}
              </div>
            ))}
            {boards.length === 0 && !loading && (
              <div className="col-span-1 md:col-span-2 rounded-xl border border-dashed border-border bg-card/50 flex flex-col items-center justify-center py-16 gap-3">
                <Briefcase className="w-10 h-10 text-muted-foreground/40" />
                <p className="text-muted-foreground text-sm">No job boards discovered.</p>
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>

      {results.length === 0 && Object.keys(activeJobs).length === 0 && boards.length === 0 && !loading && (
        <div className="rounded-xl border border-dashed border-border bg-card/50 flex flex-col items-center justify-center py-16 gap-3">
          <Briefcase className="w-10 h-10 text-muted-foreground/40" />
          <p className="text-muted-foreground text-sm">No matched jobs found for your profile.</p>
        </div>
      )}
    </div>
  );
};

export default ResultsTab;
