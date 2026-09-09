import { ProfileData, JobResult, CompanyResearch } from "./mockData";

/** Round experience years: if decimal >= 0.3, round up; otherwise round down.
 *  e.g. 1.67 -> 2, 4.56 -> 5, 1.2 -> 1, 6.2 -> 6 */
function smartRoundYears(value: number): number {
  const decimal = value - Math.floor(value);
  return decimal >= 0.3 ? Math.ceil(value) : Math.floor(value);
}

export async function parseResume(file: File): Promise<ProfileData> {
  const formData = new FormData();
  formData.append("file", file);

  let res;
  try {
    res = await fetch("/api/parse-resume", {
      method: "POST",
      body: formData,
    });
  } catch (e: any) {
    console.error("Fetch Error:", e);
    throw new Error("Cannot connect to backend. Please ensure the server is running on port 8000.");
  }

  if (!res.ok) {
    let detail = "Failed to parse resume";
    try {
      const errorData = await res.json();
      detail = errorData.detail || detail;
    } catch {
      detail = `Server Error (${res.status})`;
    }
    throw new Error(detail);
  }

  const data = await res.json();
  
  // Map roles from backend experience_summary
  const parsedRoles = (data.experience_summary || []).map((summary: any) => ({
    title: summary.role_type,
    yearsExp: typeof summary.total_years_numeric === 'number' ? Number(summary.total_years_numeric.toFixed(2)) : 0,
    active: true
  }));

  const totalExp = parsedRoles.reduce((sum: number, r: any) => sum + r.yearsExp, 0);
  
  // Snap to strict UI categories based on totalExp
  let exactRange = "0-1 years";
  if (totalExp >= 12) exactRange = "12+ years";
  else if (totalExp >= 8) exactRange = "8-12 years";
  else if (totalExp >= 5) exactRange = "5-8 years";
  else if (totalExp >= 3) exactRange = "3-5 years";
  else if (totalExp >= 1) exactRange = "1-3 years";

  const targetRoles = parsedRoles.map((r: any) => r.title);

  return {
    coreSkills: data.skills?.core_competencies || [],
    tools: data.skills?.tools_technologies || [],
    targetRoles: targetRoles,
    roles: parsedRoles,
    experienceRange: exactRange,
    remoteOnly: false,
    actualYears: totalExp,
    industry: data.industry || "Software",
    location: data.location || "",
  };
}

export async function streamDiscoverJobs(
  profile: ProfileData, 
  onEvent: (event: any) => void, 
  onComplete: () => void,
  onError: (err: string) => void
) {
  const payload = {
    job_titles: profile.targetRoles.length > 0 ? profile.targetRoles : ["Product Manager"],
    skills: [...(profile.coreSkills || []), ...(profile.tools || [])],
    actual_years_exp: smartRoundYears(profile.actualYears || 0),
    search_range: [profile.experienceRange],
    industry: profile.industry || "General",
    location: profile.location || "India",
    remote_only: profile.remoteOnly || false,
  };

  try {
    const res = await fetch("/api/discover-jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile: payload }),
    });

    if (!res.ok) {
      onError("Failed to connect to Discovery API");
      onComplete();
      return;
    }

    if (!res.body) {
      onComplete();
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('event: close')) {
           onComplete();
           return;
        }
        if (line.startsWith('data: ')) {
          const dataStr = line.substring(6).trim();
          if (!dataStr || dataStr === '{}') continue;
          try {
            const data = JSON.parse(dataStr);
            if (data.error) {
              onError(data.error);
            } else if (data) {
              onEvent(data);
            }
          } catch (e) {
            console.error("SSE parse error", e);
          }
        }
      }
    }
    onComplete();
  } catch (e: any) {
    onError(e.message || "Network Error");
    onComplete();
  }
}

export async function discoverReferrals(company: string, jobTitle: string) {
  const res = await fetch("/api/discover-referrals", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ company, jobTitle }),
  });

  if (!res.ok) {
    throw new Error("Failed to discover referrals");
  }

  return (await res.json()).referrers;
}

export async function draftEmail(
  profile: ProfileData,
  jobTitle: string,
  company: string,
  pocName?: string,
  pocRole?: string,
  jobUrl?: string
): Promise<{email: string, company_intel: string}> {
  const payload = {
    job_titles: profile.targetRoles.length > 0 ? profile.targetRoles : ["Product Manager"],
    skills: [...(profile.coreSkills || []), ...(profile.tools || [])],
    actual_years_exp: smartRoundYears(profile.actualYears || 0),
    search_range: [profile.experienceRange],
    industry: profile.industry || "General",
    location: profile.location || "India",
    remote_only: profile.remoteOnly || false,
  };

  const res = await fetch("/api/draft-email", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      profile: payload,
      job_title: jobTitle,
      company,
      poc_name: pocName || null,
      poc_role: pocRole || null,
      job_url: jobUrl || null,
    }),
  });

  if (!res.ok) {
    throw new Error("Failed to draft email");
  }

  const data = await res.json();
  return {
    email: data.email,
    company_intel: data.company_intel
  };
}
