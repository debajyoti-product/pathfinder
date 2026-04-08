import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { X, Plus, Check, RotateCcw } from "lucide-react";
import { ProfileData, defaultProfile, experienceOptions } from "@/lib/mockData";

interface ProfileTabProps {
  onConfirm: (profile: ProfileData) => void;
  onCancel: () => void;
}

const ProfileTab = ({ onConfirm, onCancel }: ProfileTabProps) => {
  const [profile, setProfile] = useState<ProfileData>({ ...defaultProfile });
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

  const addRole = () => {
    if (newRole.trim() && !profile.targetRoles.includes(newRole.trim())) {
      setProfile((p) => ({ ...p, targetRoles: [...p.targetRoles, newRole.trim()] }));
      setNewRole("");
    }
  };

  const removeRole = (role: string) => {
    setProfile((p) => ({ ...p, targetRoles: p.targetRoles.filter((r) => r !== role) }));
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">Profile Preview</h2>
        <p className="text-muted-foreground text-sm mt-1">Review and refine the data extracted from your resume.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Core Skills */}
        <div className="rounded-xl border border-border bg-card p-5 space-y-4">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Core Skills</h3>
          <div className="flex flex-wrap gap-2">
            {profile.coreSkills.map((skill) => (
              <Badge key={skill} variant="secondary" className="gap-1.5 pr-1.5 bg-secondary text-secondary-foreground">
                {skill}
                <button onClick={() => removeSkill(skill)} className="hover:text-destructive transition-colors">
                  <X className="w-3 h-3" />
                </button>
              </Badge>
            ))}
          </div>
          <div className="flex gap-2">
            <Input
              value={newSkill}
              onChange={(e) => setNewSkill(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addSkill()}
              placeholder="Add skill..."
              className="h-8 text-sm bg-muted border-border"
            />
            <Button size="sm" variant="ghost" onClick={addSkill} className="h-8 px-2 text-primary hover:text-primary hover:bg-primary/10">
              <Plus className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Target Roles */}
        <div className="rounded-xl border border-border bg-card p-5 space-y-4">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Target Roles</h3>
          <div className="flex flex-wrap gap-2">
            {profile.targetRoles.map((role) => (
              <Badge key={role} variant="secondary" className="gap-1.5 pr-1.5 bg-secondary text-secondary-foreground">
                {role}
                <button onClick={() => removeRole(role)} className="hover:text-destructive transition-colors">
                  <X className="w-3 h-3" />
                </button>
              </Badge>
            ))}
          </div>
          <div className="flex gap-2">
            <Input
              value={newRole}
              onChange={(e) => setNewRole(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addRole()}
              placeholder="Add role..."
              className="h-8 text-sm bg-muted border-border"
            />
            <Button size="sm" variant="ghost" onClick={addRole} className="h-8 px-2 text-primary hover:text-primary hover:bg-primary/10">
              <Plus className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Experience Range */}
        <div className="rounded-xl border border-border bg-card p-5 space-y-4">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Experience Range</h3>
          <div className="flex flex-wrap gap-2">
            {experienceOptions.map((opt) => (
              <button
                key={opt}
                onClick={() => setProfile((p) => ({ ...p, experienceRange: opt }))}
                className={`
                  px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200
                  ${
                    profile.experienceRange === opt
                      ? "bg-primary text-primary-foreground glow-sm"
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
