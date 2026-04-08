export interface ProfileData {
  coreSkills: string[];
  targetRoles: string[];
  experienceRange: string;
  remoteOnly: boolean;
}

export interface JobResult {
  id: string;
  company: string;
  name: string;
  jobTitle: string;
  linkedin: string;
}

export interface CompanyResearch {
  companyName: string;
  snippets: string[];
}

export const defaultProfile: ProfileData = {
  coreSkills: ["React", "TypeScript", "Node.js", "Python", "System Design"],
  targetRoles: ["Senior Frontend Engineer", "Full-Stack Developer", "Staff Engineer"],
  experienceRange: "3-5 years",
  remoteOnly: false,
};

export const experienceOptions = [
  "0-1 years",
  "1-3 years",
  "3-5 years",
  "5-8 years",
  "8-12 years",
  "12+ years",
];

export const mockResults: JobResult[] = [
  { id: "1", company: "Stripe", name: "Sarah Chen", jobTitle: "Engineering Manager", linkedin: "linkedin.com/in/sarah-chen" },
  { id: "2", company: "Linear", name: "Marcus Webb", jobTitle: "Senior Frontend Engineer", linkedin: "linkedin.com/in/marcus-webb" },
  { id: "3", company: "Vercel", name: "Anya Patel", jobTitle: "Staff Engineer", linkedin: "linkedin.com/in/anya-patel" },
  { id: "4", company: "Figma", name: "Jake Morrison", jobTitle: "Product Engineer", linkedin: "linkedin.com/in/jake-morrison" },
  { id: "5", company: "Notion", name: "Elena Voss", jobTitle: "Full-Stack Developer", linkedin: "linkedin.com/in/elena-voss" },
  { id: "6", company: "Ramp", name: "David Kim", jobTitle: "Frontend Lead", linkedin: "linkedin.com/in/david-kim" },
];

export const mockResearch: Record<string, CompanyResearch> = {
  Stripe: {
    companyName: "Stripe",
    snippets: [
      "Stripe recently launched Stripe Tax, automating sales tax collection for online businesses globally.",
      "The company raised its latest round at a $65B valuation, focusing on embedded finance.",
      "Stripe Connect now supports 46+ countries, enabling marketplace platforms to process payments.",
      "New product: Stripe Identity — real-time identity verification for fraud prevention.",
    ],
  },
  Linear: {
    companyName: "Linear",
    snippets: [
      "Linear raised a $35M Series B, emphasizing their focus on developer-first project management.",
      "The team shipped Linear Insights — real-time project analytics for engineering teams.",
      "Linear's API v2 now supports GraphQL subscriptions for real-time collaboration.",
      "Company culture focuses on craft and quality, with a fully remote team of 60+.",
    ],
  },
  Vercel: {
    companyName: "Vercel",
    snippets: [
      "Vercel launched v0 — an AI-powered UI generation tool that creates React components from prompts.",
      "Next.js 15 introduced partial pre-rendering, blending static and dynamic content.",
      "Vercel's edge network expanded to 30+ regions globally.",
      "The company is investing heavily in AI-native development workflows.",
    ],
  },
  Figma: {
    companyName: "Figma",
    snippets: [
      "Figma launched Dev Mode, bridging the gap between design and development workflows.",
      "After the Adobe acquisition fell through, Figma doubled down on independent growth.",
      "FigJam AI now auto-generates diagrams and brainstorming boards.",
      "Figma's plugin ecosystem surpassed 5,000 community plugins.",
    ],
  },
  Notion: {
    companyName: "Notion",
    snippets: [
      "Notion AI launched Q&A, allowing users to ask questions about their workspace content.",
      "The company surpassed $250M ARR with 30M+ users worldwide.",
      "Notion Projects added Gantt charts and sprint planning for engineering teams.",
      "New API improvements enable deeper third-party integrations.",
    ],
  },
  Ramp: {
    companyName: "Ramp",
    snippets: [
      "Ramp became the fastest-growing corporate card in the US, surpassing $10B in annualized spend.",
      "Launched Ramp Intelligence — AI-powered expense categorization and savings recommendations.",
      "Ramp's bill pay product now handles $1B+ in monthly payments.",
      "The company focuses on building finance automation tools for mid-market companies.",
    ],
  },
};

export function generateDraft(name: string, company: string, jobTitle: string): string {
  return `Hi ${name},

I came across your profile and was impressed by the work ${company} is doing. I'm particularly interested in the ${jobTitle} role and believe my background aligns well with your team's needs.

With experience in modern frontend architecture, performance optimization, and cross-functional collaboration, I'm confident I could contribute meaningfully to ${company}'s mission.

I'd love to connect and learn more about your team's current challenges and goals. Would you be open to a brief conversation this week?

Best regards,
[Your Name]`;
}
