import { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Compass, User, List, PenTool } from "lucide-react";
import HomeTab from "@/components/HomeTab";
import ProfileTab from "@/components/ProfileTab";
import ResultsTab from "@/components/ResultsTab";
import DraftingTab from "@/components/DraftingTab";
import { ProfileData, JobResult } from "@/lib/mockData";

const Index = () => {
  const [activeTab, setActiveTab] = useState("home");
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [draftTarget, setDraftTarget] = useState<JobResult | null>(null);

  const handleUpload = () => {
    setActiveTab("profile");
  };

  const handleConfirm = (p: ProfileData) => {
    setProfile(p);
    setActiveTab("results");
  };

  const handleCancel = () => {
    setActiveTab("home");
  };

  const handleGenerate = (result: JobResult) => {
    setDraftTarget(result);
    setActiveTab("drafting");
  };

  const handleBackToResults = () => {
    setDraftTarget(null);
    setActiveTab("results");
  };

  const tabs = [
    { value: "home", label: "Home", icon: Compass },
    { value: "profile", label: "Profile", icon: User },
    { value: "results", label: "Results", icon: List },
    { value: "drafting", label: "Drafting", icon: PenTool },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Compass className="w-4.5 h-4.5 text-primary-foreground" />
            </div>
            <span className="text-lg font-bold tracking-tight text-foreground">Pathfinder</span>
          </div>
          <div className="text-xs text-muted-foreground font-medium tracking-wide uppercase">
            AI Career Agent
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-6xl mx-auto px-6 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-muted/50 border border-border p-1 mb-8">
            {tabs.map((tab) => (
              <TabsTrigger
                key={tab.value}
                value={tab.value}
                className="gap-2 data-[state=active]:bg-card data-[state=active]:text-foreground data-[state=active]:shadow-sm text-muted-foreground"
              >
                <tab.icon className="w-4 h-4" />
                <span className="hidden sm:inline">{tab.label}</span>
              </TabsTrigger>
            ))}
          </TabsList>

          <TabsContent value="home">
            <HomeTab onUpload={handleUpload} />
          </TabsContent>

          <TabsContent value="profile">
            <ProfileTab onConfirm={handleConfirm} onCancel={handleCancel} />
          </TabsContent>

          <TabsContent value="results">
            <ResultsTab onGenerate={handleGenerate} />
          </TabsContent>

          <TabsContent value="drafting">
            {draftTarget && (
              <DraftingTab result={draftTarget} onBack={handleBackToResults} />
            )}
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default Index;
