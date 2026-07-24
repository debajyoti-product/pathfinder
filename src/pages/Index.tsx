import { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Compass, User, List, PenTool } from "lucide-react";
import HomeTab from "@/components/HomeTab";
import ProfileTab from "@/components/ProfileTab";
import ResultsTab from "@/components/ResultsTab";
import DraftingTab from "@/components/DraftingTab";
import { ProfileData, JobResult } from "@/lib/mockData";
import { parseResume } from "@/lib/api";
import { ThemeToggle } from "@/components/ThemeToggle";

const Index = () => {
  const [activeTab, setActiveTab] = useState("home");
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [draftTarget, setDraftTarget] = useState<JobResult | null>(null);
  const [resumeUploaded, setResumeUploaded] = useState(false);
  const [profileConfirmed, setProfileConfirmed] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const handleUpload = async (file: File) => {
    try {
      setIsUploading(true);
      const parsedData = await parseResume(file);
      setProfile(parsedData);
      setResumeUploaded(true);
      setActiveTab("profile");
    } catch (e: any) {
      console.error(e);
      alert(e.message || "Failed to parse resume");
    } finally {
      setIsUploading(false);
    }
  };

  const handleConfirm = (p: ProfileData) => {
    setProfile(p);
    setProfileConfirmed(true);
    setActiveTab("results");
  };

  const handleCancel = () => {
    setActiveTab("home");
  };

  const handleGenerate = (result: JobResult, pocName?: string, pocLinkedin?: string) => {
    setDraftTarget({ 
      ...result, 
      name: pocName || result.name, 
      linkedin: pocLinkedin || result.linkedin 
    });
    setActiveTab("drafting");
  };

  const handleBackToResults = () => {
    setDraftTarget(null);
    setActiveTab("results");
  };

  const tabEnabled: Record<string, boolean> = {
    home: true,
    profile: resumeUploaded,
    results: profileConfirmed,
    drafting: !!draftTarget,
  };

  const handleTabChange = (value: string) => {
    if (tabEnabled[value]) setActiveTab(value);
  };

  const tabs = [
    { value: "home", label: "Home", icon: Compass },
    { value: "profile", label: "Profile", icon: User },
    { value: "results", label: "Results", icon: List },
    { value: "drafting", label: "Drafting", icon: PenTool },
  ];

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => {
                setActiveTab("home");
                setProfile(null);
                setDraftTarget(null);
                setResumeUploaded(false);
                setProfileConfirmed(false);
              }} 
              className="flex items-center gap-2.5 hover:opacity-80 transition-opacity text-left outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-sm"
            >
              <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center">
                <Compass className="w-4 h-4 text-primary-foreground" />
              </div>
              <span className="text-lg font-bold tracking-tight text-foreground -mb-0.5">Pathfinder</span>
            </button>
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-6xl mx-auto px-6 py-8">
        <Tabs value={activeTab} onValueChange={handleTabChange}>
          <TabsList className="w-full max-w-2xl mx-auto h-auto bg-muted/30 backdrop-blur-xl border border-border/50 p-2 mb-8 rounded-full flex shadow-sm">
            {tabs.map((tab, idx) => (
              <TabsTrigger
                key={tab.value}
                value={tab.value}
                disabled={!tabEnabled[tab.value]}
                className="flex-1 rounded-full gap-2 py-2.5 data-[state=active]:bg-card data-[state=active]:text-foreground data-[state=active]:shadow-md text-muted-foreground disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-500 ease-out"
              >
                <tab.icon className="w-4 h-4" />
                <span className="hidden sm:inline font-medium tracking-wide">{tab.label}</span>
              </TabsTrigger>
            ))}
          </TabsList>

          <TabsContent value="home">
            <HomeTab onUpload={handleUpload} isUploading={isUploading} />
          </TabsContent>

          <TabsContent value="profile">
            <ProfileTab initialProfile={profile} onConfirm={handleConfirm} onCancel={handleCancel} />
          </TabsContent>

          <TabsContent value="results">
            <ResultsTab profile={profile} onGenerate={handleGenerate} />
          </TabsContent>

          <TabsContent value="drafting">
            {draftTarget && (
              <DraftingTab result={draftTarget} profile={profile} onBack={handleBackToResults} />
            )}
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default Index;
