import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { X, Plus, Check, RotateCcw, MapPin } from "lucide-react";
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
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">Profile Preview</h2>
          <p className="text-muted-foreground text-sm mt-1">Refine your target roles and experience summary.</p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-primary">{profile.experienceRange}</div>
          <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Total Relevant Experience</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Identified Roles (Left, 2/3 width) */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Identified Roles</h3>
            <span className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded-full font-medium">Toggle to adjust total experience</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {profile.roles.map((role, idx) => (
              <div 
                key={idx} 
                className={`flex items-center justify-between p-3 rounded-lg border transition-all duration-200 ${
                  role.active 
                    ? 'bg-secondary/50 border-primary/20 shadow-sm' 
                    : 'bg-muted/30 border-transparent opacity-60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Switch 
                    checked={role.active} 
                    onCheckedChange={() => toggleRole(idx)}
                  />
                  <div className="flex flex-col">
                    <span className="text-sm font-medium text-foreground leading-tight">{role.title}</span>
                    <span className="text-xs text-muted-foreground">{role.yearsExp} years</span>
                  </div>
                </div>
                <button 
                  onClick={() => removeDetailedRole(idx)} 
                  className="text-muted-foreground hover:text-destructive transition-colors p-1"
                >
                   <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Experience Range (Right, 1/3 width) */}
        <div className="lg:col-span-1 rounded-xl border border-border bg-card p-5 space-y-4 h-full">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Experience Range</h3>
          <div className="grid grid-cols-2 gap-2">
            {experienceOptions.map((opt) => (
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
            ))}
          </div>
        </div>
      </div>

      {/* Core Skills (Full Width Below) */}
      <div className="rounded-xl border border-border bg-card p-5 space-y-4">
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Core Skills</h3>
        <div className="flex flex-wrap items-center gap-2">
          {profile.coreSkills.map((skill) => (
            <Badge key={skill} variant="secondary" className="gap-1.5 pr-1.5 bg-secondary text-secondary-foreground py-1 px-3 rounded-full">
              {skill}
              <button onClick={() => removeSkill(skill)} className="hover:text-destructive transition-colors">
                <X className="w-3 h-3" />
              </button>
            </Badge>
          ))}
          
          <div className="flex items-center gap-2 bg-secondary/50 rounded-full pl-3 pr-1 py-1 border border-border/50">
            <input
              type="text"
              value={newSkill}
              onChange={(e) => setNewSkill(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addSkill()}
              placeholder="Add skill..."
              className="bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none w-24"
            />
            <Button size="icon" variant="default" onClick={addSkill} className="h-6 w-6 rounded-full bg-primary text-primary-foreground">
              <Plus className="w-3 h-3" />
            </Button>
          </div>
        </div>
      </div>

      {/* Remote Toggle + Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-4 border-t border-border">
        <div className="flex items-center gap-3">
          <Switch
            checked={profile.remoteOnly}
            onCheckedChange={(checked) => setProfile((p) => ({ ...p, remoteOnly: checked }))}
          />
          <span className="text-sm text-foreground font-medium">Remote only</span>
        </div>
        <div className="flex gap-3">
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
