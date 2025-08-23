export interface Article {
  source: {
    id: string | null;
    name: string;
  };
  author: string | null;
  title: string;
  description: string | null;
  summary: string | null;
  url: string;
  urlToImage: string | null;
  publishedAt: string;
  content: string | null;
  scraped_at?: string;
  // New fields for enhanced features
  threatLevel?: 'low' | 'medium' | 'high' | 'critical';
  categories?: string[];
  affectedSectors?: string[]; // heuristic sector impact (e.g., telecommunications, finance)
  aiAnalysis?: {
    threatType: string;
    affectedSectors: string[];
    riskScore: number;
    recommendations: string[];
  };
}

export interface NewsResponse {
  status: string;
  totalResults: number;
  articles: Article[];
  query?: string;
  source?: string;
}

export interface Category {
  name: string;
  pic: string;
}

export interface Source {
  id: string;
  name: string;
  pic: string;
}

// New interfaces for enhanced features
export interface ThreatAnalysis {
  threatType: 'malware' | 'phishing' | 'data-breach' | 'ransomware' | 'vulnerability' | 'social-engineering' | 'insider-threat' | 'apt' | 'other';
  severity: 'low' | 'medium' | 'high' | 'critical';
  affectedIndustries: string[];
  riskScore: number; // 0-100
  recommendations: string[];
  cveIds?: string[];
  iocIndicators?: string[];
}

export interface NewsCategory {
  id: string;
  name: string;
  icon: string;
  color: string;
  description: string;
}

export interface ThreatLevel {
  level: 'low' | 'medium' | 'high' | 'critical';
  color: string;
  icon: string;
  description: string;
}
