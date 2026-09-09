import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { X, Plus, Check, RotateCcw, MapPin, CheckCircle2, Circle } from "lucide-react";
import { ProfileData, defaultProfile, experienceOptions } from "@/lib/mockData";

interface ProfileTabProps {
  initialProfile?: ProfileData | null;
  onConfirm: (profile: ProfileData) => void;
  onCancel: () => void;
}

const ProfileTab = ({ initialProfile, onConfirm, onCancel }: ProfileTabProps) => {
  const [profile, setProfile] = useState<ProfileData>(initialProfile || { ...defaultProfile });

  useEffect(() => {
    if (initialProfile) {
      // Ensure experience is synced on first load
      const activeRoles = initialProfile.roles.filter(r => r.active);
      const totalExp = activeRoles.reduce((sum, r) => sum + r.yearsExp, 0);
      
      let exactRange = initialProfile.experienceRange;
      if (totalExp >= 1) { // Only override if we have data to avoid resetting manual choices if already correct
          if (totalExp >= 12) exactRange = "12+ years";
          else if (totalExp >= 8) exactRange = "8-12 years";
          else if (totalExp >= 5) exactRange = "5-8 years";
          else if (totalExp >= 3) exactRange = "3-5 years";
          else if (totalExp >= 1) exactRange = "1-3 years";
      }

      setProfile({
        ...initialProfile,
        actualYears: totalExp,
        experienceRange: exactRange
      });
    }
  }, [initialProfile]);
  const [newSkill, setNewSkill] = useState("");
  const [newTool, setNewTool] = useState("");
  const [newRole, setNewRole] = useState("");

  const addSkill = () => {
    if (newSkill.trim() && !profile.coreSkills.includes(newSkill.trim())) {
      setProfile((p) => ({ ...p, coreSkills: [...p.coreSkills, newSkill.trim()] }));
      setNewSkill("");
    }
  };

  const removeSkill = (skill: string) => {
    setProfile((p) => ({ ...p, coreSkills: p.coreSkills.filter((s) => s !== skill) }));
  };

  const addTool = () => {
    if (newTool.trim() && !profile.tools.includes(newTool.trim())) {
      setProfile((p) => ({ ...p, tools: [...p.tools, newTool.trim()] }));
      setNewTool("");
    }
  };

  const removeTool = (tool: string) => {
    setProfile((p) => ({ ...p, tools: p.tools.filter((t) => t !== tool) }));
  };

  const toggleRole = (index: number) => {
    const newRoles = [...profile.roles];
    newRoles[index].active = !newRoles[index].active;
    updateProfileFromRoles(newRoles);
  };

  const removeDetailedRole = (index: number) => {
    const newRoles = profile.roles.filter((_, i) => i !== index);
    updateProfileFromRoles(newRoles);
  };

  const updateProfileFromRoles = (newRoles: typeof profile.roles) => {
    const activeRoles = newRoles.filter(r => r.active);
    const totalExp = activeRoles.reduce((sum, r) => sum + r.yearsExp, 0);
    
    let exactRange = "0-1 years";
    if (totalExp >= 12) exactRange = "12+ years";
    else if (totalExp >= 8) exactRange = "8-12 years";
    else if (totalExp >= 5) exactRange = "5-8 years";
    else if (totalExp >= 3) exactRange = "3-5 years";
    else if (totalExp >= 1) exactRange = "1-3 years";

    setProfile(p => ({
      ...p,
      roles: newRoles,
      targetRoles: activeRoles.map(r => r.title),
      actualYears: totalExp,
      experienceRange: exactRange
    }));
  };

  const addRole = () => {
    if (newRole.trim()) {
      const newRoles = [...profile.roles, { title: newRole.trim(), yearsExp: 0, active: true }];
      updateProfileFromRoles(newRoles);
      setNewRole("");
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 flex-1 flex flex-col w-full">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">Profile Preview</h2>
          <p className="text-muted-foreground text-sm mt-1">Refine your target roles and experience summary.</p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-[hsl(221,83%,53%)] to-[hsl(160,84%,20%)]">{profile.experienceRange}</div>
          <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Total Relevant Experience</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Identified Roles (Left, 2/3 width) */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Identified Roles</h3>
            <span className="text-[10px] bg-gradient-to-r from-[hsl(221,83%,53%)]/10 to-[hsl(160,84%,20%)]/15 text-primary border border-primary/20 px-2 py-0.5 rounded-full font-semibold">Toggle to adjust total experience</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {profile.roles.map((role, idx) => (
              <button
                key={idx}
                onClick={() => toggleRole(idx)}
                className={`group relative flex flex-col items-start p-3.5 rounded-xl border-2 transition-all duration-200 text-left outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                  role.active
                    ? 'bg-primary/5 border-primary shadow-sm ring-1 ring-primary/20'
                    : 'bg-card border-border hover:border-primary/50'
                }`}
              >
                <div className="flex items-start gap-3 w-full">
                  <div className="mt-0.5 shrink-0">
                    {role.active ? (
                      <CheckCircle2 className="w-4 h-4 text-primary" />
                    ) : (
                      <Circle className="w-4 h-4 text-muted-foreground group-hover:text-primary/50 transition-colors" />
                    )}
                  </div>
                  <div className="flex flex-col flex-1 min-w-0 pr-6">
                    <span className={`text-sm leading-tight ${role.active ? 'text-transparent bg-clip-text bg-gradient-to-r from-[hsl(221,83%,53%)] to-[hsl(160,84%,20%)] font-bold' : 'font-semibold text-foreground'}`}>
                      {role.title}
                    </span>
                    <span className={`text-xs mt-1 font-medium ${role.active ? 'text-primary/80' : 'text-muted-foreground'}`}>
                      {role.yearsExp} {role.yearsExp === 1 ? 'year' : 'years'} exp
                    </span>
                  </div>
                  <div
                    onClick={(e) => { e.stopPropagation(); removeDetailedRole(idx); }}
                    className="absolute top-2 right-2 p-1.5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-muted text-muted-foreground hover:text-foreground"
                  >
                    <X className="w-3.5 h-3.5" />
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Experience Range (Right, 1/3 width) */}
        <div className="lg:col-span-1 rounded-xl border border-border bg-card p-5 space-y-4 h-full">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Experience Range</h3>
          <div className="grid grid-cols-2 gap-2">
            {(() => {
              const maxExp = (initialProfile?.roles || []).reduce((sum, r) => sum + r.yearsExp, 0);
              let maxRangeIndex = 0;
              if (maxExp >= 12) maxRangeIndex = 5;
              else if (maxExp >= 8) maxRangeIndex = 4;
              else if (maxExp >= 5) maxRangeIndex = 3;
              else if (maxExp >= 3) maxRangeIndex = 2;
              else if (maxExp >= 1) maxRangeIndex = 1;
              
              const visibleOptions = experienceOptions.slice(0, Math.min(experienceOptions.length, maxRangeIndex + 2));
              
              return visibleOptions.map((opt) => (
                <button
                  key={opt}
                  onClick={() => setProfile((p) => ({ ...p, experienceRange: opt }))}
                  className={`
                    px-2 py-2 rounded-lg text-xs font-medium transition-all duration-200
                    ${
                      profile.experienceRange === opt
                        ? "bg-primary text-primary-foreground glow-sm shadow-md"
                        : "bg-muted text-muted-foreground hover:text-foreground hover:bg-secondary"
                    }
                  `}
                >
                  {opt}
                </button>
              ));
            })()}
          </div>
        </div>
      </div>

      {/* Skills Hierarchy (Full Width Below) */}
      <div className="rounded-xl border border-border bg-card p-5 space-y-6">
            <>
              {/* Core Competencies */}
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Core Competencies</h3>
                <div className="flex flex-wrap items-center gap-2">
                  {profile.coreSkills.map((skill) => (
                    <Badge key={skill} className="gap-1.5 pr-1.5 bg-gradient-to-r from-[hsl(221,83%,53%)] to-[hsl(160,84%,20%)] text-white border-none py-1.5 px-3.5 rounded-full text-sm font-medium shadow-sm">
                      {skill}
                      <button onClick={() => removeSkill(skill)} className="hover:text-white/80 transition-colors bg-white/20 rounded-full p-0.5">
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </Badge>
                  ))}
                  {profile.coreSkills.length === 0 && <span className="text-sm text-muted-foreground italic">None detected</span>}
                  
                  <div className="flex items-center gap-2 bg-secondary/50 rounded-full pl-3 pr-1 py-1 border border-border/50 ml-2">
                    <input
                      type="text"
                      value={newSkill}
                      onChange={(e) => setNewSkill(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && addSkill()}
                      placeholder="Add competency..."
                      className="bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none w-32"
                    />
                    <Button size="icon" variant="default" onClick={addSkill} className="h-6 w-6 rounded-full bg-primary text-primary-foreground">
                      <Plus className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              </div>

              {/* Tools & Technologies */}
              <div className="space-y-3 pt-4 border-t border-border/50">
                <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Tools & Technologies</h3>
                <div className="flex flex-wrap items-center gap-2">
                  {profile.tools.map((tool) => (
                    <Badge key={tool} variant="outline" className="gap-1.5 pr-1.5 border-border bg-muted/30 text-muted-foreground py-1 px-3 rounded-full font-normal">
                      {tool}
                      <button onClick={() => removeTool(tool)} className="hover:text-destructive transition-colors">
                        <X className="w-3 h-3" />
                      </button>
                    </Badge>
                  ))}
                  
                  <div className="flex items-center gap-2 bg-secondary/50 rounded-full pl-3 pr-1 py-1 border border-border/50 ml-2">
                    <input
                      type="text"
                      value={newTool}
                      onChange={(e) => setNewTool(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && addTool()}
                      placeholder="Add tool..."
                      className="bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none w-24"
                    />
                    <Button size="icon" variant="default" onClick={addTool} className="h-6 w-6 rounded-full bg-primary text-primary-foreground">
                      <Plus className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              </div>
            </>
      </div>

      {/* Location + Remote Toggle + Actions */}
      <div className="sticky bottom-0 z-40 bg-background/95 backdrop-blur-md flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 py-4 border-t border-border mt-auto">
        <div className="flex items-center h-10 gap-4">
          <div className="flex items-center gap-2 h-full">
            <MapPin className="w-5 h-5 text-muted-foreground" />
            <Input 
              className="w-[180px] bg-muted/40 border-border/50" 
              placeholder="e.g. Bangalore" 
              value={profile.location || ""}
              onChange={(e) => setProfile(p => ({ ...p, location: e.target.value }))}
            />
          </div>
          <div className="flex items-center gap-3 border-l border-border/60 pl-4 h-full">
            <Switch
              checked={profile.remoteOnly}
              onCheckedChange={(checked) => setProfile((p) => ({ ...p, remoteOnly: checked }))}
            />
            <span className="text-sm text-foreground font-medium">Remote only</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={onCancel} className="gap-2 border-border text-muted-foreground hover:text-foreground">
            <RotateCcw className="w-4 h-4" />
            Cancel
          </Button>
          <Button onClick={() => onConfirm(profile)} className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90 glow-sm">
            <Check className="w-4 h-4" />
            Confirm Profile
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ProfileTab;
