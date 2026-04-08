import { Button } from "@/components/ui/button";
import { ExternalLink, PenLine } from "lucide-react";
import { JobResult, mockResults } from "@/lib/mockData";

interface ResultsTabProps {
  onGenerate: (result: JobResult) => void;
}

const ResultsTab = ({ onGenerate }: ResultsTabProps) => {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">Matched Contacts</h2>
        <p className="text-muted-foreground text-sm mt-1">Warm leads at companies that match your profile.</p>
      </div>

      <div className="rounded-xl border border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider px-5 py-3">Company</th>
                <th className="text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider px-5 py-3">Name</th>
                <th className="text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider px-5 py-3">Job Title</th>
                <th className="text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider px-5 py-3">LinkedIn</th>
                <th className="text-right text-xs font-semibold text-muted-foreground uppercase tracking-wider px-5 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {mockResults.map((result, i) => (
                <tr
                  key={result.id}
                  className={`border-b border-border last:border-0 transition-colors hover:bg-muted/30 ${
                    i % 2 === 0 ? "bg-card" : "bg-card/50"
                  }`}
                >
                  <td className="px-5 py-4">
                    <span className="text-sm font-semibold text-foreground">{result.company}</span>
                  </td>
                  <td className="px-5 py-4">
                    <span className="text-sm text-foreground">{result.name}</span>
                  </td>
                  <td className="px-5 py-4">
                    <span className="text-sm text-muted-foreground">{result.jobTitle}</span>
                  </td>
                  <td className="px-5 py-4">
                    <a
                      href={`https://${result.linkedin}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-primary hover:underline inline-flex items-center gap-1"
                    >
                      {result.linkedin}
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </td>
                  <td className="px-5 py-4 text-right">
                    <Button
                      size="sm"
                      onClick={() => onGenerate(result)}
                      className="gap-1.5 bg-primary text-primary-foreground hover:bg-primary/90 glow-sm"
                    >
                      <PenLine className="w-3.5 h-3.5" />
                      Generate Draft
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ResultsTab;
