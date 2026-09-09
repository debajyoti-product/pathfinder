import { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Compass } from "lucide-react";
import HomeTab from "@/components/HomeTab";
import ProfileTab from "@/components/ProfileTab";
import ResultsTab from "@/components/ResultsTab";
import DraftingTab from "@/components/DraftingTab";
import { ProfileData, JobResult } from "@/lib/mockData";
import { parseResume } from "@/lib/api";

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
    { value: "home", label: "Home" },
    { value: "profile", label: "Profile" },
    { value: "results", label: "Results" },
    { value: "drafting", label: "Drafting" },
  ];

  return (
    <div className="h-screen w-screen p-4 md:p-6 bg-background flex overflow-hidden">
      <Tabs value={activeTab} onValueChange={handleTabChange} className="flex flex-1 w-full h-full gap-4 md:gap-6 overflow-hidden" orientation="vertical">
        {/* Sidebar */}
        <aside className="w-64 md:w-72 shrink-0 flex flex-col gap-4 h-full">
          {/* Logo */}
          <div className="px-2 py-1 flex items-center shrink-0">
            <button 
              onClick={() => {
                setActiveTab("home");
                setProfile(null);
                setDraftTarget(null);
                setResumeUploaded(false);
                setProfileConfirmed(false);
              }} 
              className="flex items-center gap-3 hover:opacity-80 transition-opacity text-left outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-lg"
            >
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[hsl(221,83%,53%)] to-[hsl(160,84%,20%)] flex items-center justify-center shadow-md">
                <Compass className="w-4 h-4 text-white" />
              </div>
              <span className="text-xl font-bold tracking-tight text-foreground">Pathfinder</span>
            </button>
          </div>

          {/* Navigation - Separate Enclosed Card */}
          <div className="bg-card border border-border rounded-2xl p-3 shadow-md flex-1 flex flex-col">
            <TabsList className="w-full h-auto bg-transparent border-none p-0 flex flex-col gap-1.5 shadow-none">
              {tabs.map((tab) => (
                <TabsTrigger
                  key={tab.value}
                  value={tab.value}
                  disabled={!tabEnabled[tab.value]}
                  className="w-full justify-start px-4 py-2.5 rounded-xl data-[state=active]:bg-gradient-to-r data-[state=active]:from-[hsl(221,83%,53%)] data-[state=active]:to-[hsl(160,84%,20%)] data-[state=active]:text-white data-[state=active]:shadow-sm text-muted-foreground hover:text-foreground disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:text-muted-foreground transition-all duration-300 ease-out font-semibold text-xs tracking-wider uppercase text-left"
                >
                  <span className="tracking-wider uppercase">{tab.label}</span>
                </TabsTrigger>
              ))}
            </TabsList>
          </div>
        </aside>

        {/* Main Content - Separate Enclosed Card (Center Aligned) */}
        <main className="flex-1 h-full bg-card border border-border rounded-2xl shadow-md overflow-y-auto flex flex-col items-center">
          <div className="w-full max-w-5xl p-6 lg:p-10 flex-1 flex flex-col items-center">
            <TabsContent value="home" forceMount hidden={activeTab !== "home"} className={`mt-0 w-full flex-1 flex-col items-center justify-center ${activeTab === "home" ? "flex" : "hidden"}`}>
              <HomeTab onUpload={handleUpload} isUploading={isUploading} />
            </TabsContent>

            <TabsContent value="profile" forceMount hidden={activeTab !== "profile"} className={`mt-0 w-full flex-1 flex-col ${activeTab === "profile" ? "flex" : "hidden"}`}>
              <ProfileTab initialProfile={profile} onConfirm={handleConfirm} onCancel={handleCancel} />
            </TabsContent>

            <TabsContent value="results" forceMount hidden={activeTab !== "results"} className={`mt-0 w-full flex-1 flex-col ${activeTab === "results" ? "flex" : "hidden"}`}>
              <ResultsTab profile={profile} onGenerate={handleGenerate} />
            </TabsContent>

            <TabsContent value="drafting" forceMount hidden={activeTab !== "drafting"} className={`mt-0 w-full flex-1 flex-col ${activeTab === "drafting" ? "flex" : "hidden"}`}>
              {draftTarget && (
                <DraftingTab result={draftTarget} profile={profile} onBack={handleBackToResults} />
              )}
            </TabsContent>
          </div>
        </main>
      </Tabs>
    </div>
  );
};

export default Index;
