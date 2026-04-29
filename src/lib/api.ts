import { ProfileData, JobResult, CompanyResearch } from "./mockData";

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
  
  // Map roles from backend
  const parsedRoles = (data.roles || []).map((r: any) => ({
    title: r.title,
    yearsExp: r.years_exp,
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
    coreSkills: data.skills || [],
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
  onJobFound: (job: JobResult) => void, 
  onComplete: () => void,
  onError: (err: string) => void
) {
  const payload = {
    job_title: profile.targetRoles[0] || "Product Manager",
    skills: profile.coreSkills,
    actual_years_exp: Math.round(profile.actualYears || 0),
    search_range: [profile.experienceRange],
    industry: profile.industry || "General",
    location: profile.location || "India",
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
            } else {
              onJobFound(data as JobResult);
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

export async function draftEmail(profile: ProfileData, jobTitle: string, company: string): Promise<{email: string, news: any[]}> {
  const payload = {
    job_title: profile.targetRoles[0] || "Engineer",
    skills: profile.coreSkills,
    actual_years_exp: profile.actualYears || 0,
    search_range: [profile.experienceRange],
    industry: profile.industry || "General",
  };

  const res = await fetch("/api/draft-email", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ profile: payload, job_title: jobTitle, company }),
  });

  if (!res.ok) throw new Error("Failed to draft email");
  return await res.json();
}
