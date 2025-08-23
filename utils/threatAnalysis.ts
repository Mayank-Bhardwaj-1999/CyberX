import type { ThreatAnalysis, NewsCategory, ThreatLevel } from '../types/news';

// Threat level configurations
export const THREAT_LEVELS: Record<string, ThreatLevel> = {
  low: {
    level: 'low',
    color: '#10B981', // Green
    icon: 'shield',
    description: 'Minimal risk'
  },
  medium: {
    level: 'medium',
    color: '#F59E0B', // Amber
    icon: 'warning',
    description: 'Moderate risk'
  },
  high: {
    level: 'high',
    color: '#EF4444', // Red
    icon: 'error',
    description: 'High risk'
  },
  critical: {
    level: 'critical',
    color: '#7C2D12', // Dark red
    icon: 'security',
    description: 'Critical threat'
  }
};

// News categories for cybersecurity
export const NEWS_CATEGORIES: NewsCategory[] = [
  {
    id: 'malware',
    name: 'Malware',
    icon: 'bug-report',
    color: '#EC4899',
    description: 'Malicious software threats'
  },
  {
    id: 'phishing',
    name: 'Phishing',
    icon: 'email',
    color: '#8B5CF6',
    description: 'Social engineering attacks'
  },
  {
    id: 'data-breach',
    name: 'Data Breach',
    icon: 'storage',
    color: '#06B6D4',
    description: 'Data security incidents'
  },
  {
    id: 'ransomware',
    name: 'Ransomware',
    icon: 'lock',
    color: '#DC2626',
    description: 'Ransomware attacks'
  },
  {
    id: 'vulnerability',
    name: 'Vulnerabilities',
    icon: 'security',
    color: '#F59E0B',
    description: 'Security vulnerabilities'
  },
  {
    id: 'apt',
    name: 'APT',
    icon: 'visibility',
    color: '#7C3AED',
    description: 'Advanced Persistent Threats'
  },
  {
    id: 'social-engineering',
    name: 'Social Engineering',
    icon: 'psychology',
    color: '#059669',
    description: 'Human manipulation attacks'
  },
  {
    id: 'insider-threat',
    name: 'Insider Threat',
    icon: 'person',
    color: '#DC2626',
    description: 'Internal security threats'
  }
];

// Keywords for threat type detection
const THREAT_KEYWORDS = {
  malware: ['malware', 'virus', 'trojan', 'worm', 'spyware', 'adware', 'rootkit', 'backdoor'],
  phishing: ['phishing', 'spear phishing', 'whaling', 'vishing', 'smishing', 'email scam'],
  'data-breach': ['data breach', 'data leak', 'information leak', 'stolen data', 'compromised data'],
  ransomware: ['ransomware', 'crypto locker', 'file encryption', 'ransom demand'],
  vulnerability: ['vulnerability', 'cve', 'zero-day', 'exploit', 'patch', 'security flaw'],
  'social-engineering': ['social engineering', 'manipulation', 'psychological', 'human factor'],
  'insider-threat': ['insider', 'employee', 'internal', 'disgruntled', 'privileged access'],
  apt: ['apt', 'advanced persistent threat', 'nation state', 'state-sponsored', 'cyber espionage']
};

// Critical keywords that indicate high severity
const CRITICAL_KEYWORDS = ['critical', 'urgent', 'breaking', 'breach', 'attack', 'ransomware', 'zero-day', 'exploit in the wild'];
const HIGH_SEVERITY_KEYWORDS = ['vulnerability', 'exploit', 'malware', 'phishing', 'data leak', 'compromise'];
const MEDIUM_SEVERITY_KEYWORDS = ['threat', 'suspicious', 'warning', 'alert', 'patch'];

// Generate consistent risk score based on article content
export function generateConsistentRiskScore(article: any): number {
  const content = `${article.title || ''} ${article.description || ''} ${article.content || ''}`.toLowerCase();
  const url = article.url || '';
  
  // Create a simple hash from URL to ensure consistency
  let hash = 0;
  for (let i = 0; i < url.length; i++) {
    const char = url.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  
  // Use hash to create consistent base score (40-60)
  const baseScore = 40 + (Math.abs(hash) % 21);
  
  // Add points based on content analysis
  let severityBonus = 0;
  
  if (CRITICAL_KEYWORDS.some(keyword => content.includes(keyword))) {
    severityBonus = 35; // 75-95 range
  } else if (HIGH_SEVERITY_KEYWORDS.some(keyword => content.includes(keyword))) {
    severityBonus = 20; // 60-80 range  
  } else if (MEDIUM_SEVERITY_KEYWORDS.some(keyword => content.includes(keyword))) {
    severityBonus = 10; // 50-70 range
  }
  
  // Add small hash-based variation
  const hashVariation = (Math.abs(hash) % 10) - 5;
  
  const finalScore = Math.min(95, Math.max(5, baseScore + severityBonus + hashVariation));
  return Math.round(finalScore);
}

// Get consistent threat level based on content
export function getThreatLevel(article: any): 'low' | 'medium' | 'high' | 'critical' {
  const score = generateConsistentRiskScore(article);
  
  if (score >= 80) return 'critical';
  if (score >= 60) return 'high';
  if (score >= 40) return 'medium';
  return 'low';
}

// Get threat level color
export function getThreatLevelColor(level: string, colors: any) {
  switch (level) {
    case 'critical': return colors?.critical || '#DC2626';
    case 'high': return colors?.vulnerability || '#EF4444';
    case 'medium': return colors?.threat || '#F59E0B';
    case 'low': return colors?.security || '#10B981';
    default: return colors?.security || '#10B981';
  }
}

// Analyze article for threat type and details
export function analyzeArticleThreat(article: any): ThreatAnalysis {
  const content = `${article.title || ''} ${article.description || ''} ${article.content || ''}`.toLowerCase();
  
  // Determine primary threat type
  let threatType: any = 'other';
  let maxMatches = 0;
  
  Object.entries(THREAT_KEYWORDS).forEach(([type, keywords]) => {
    const matches = keywords.filter(keyword => content.includes(keyword)).length;
    if (matches > maxMatches) {
      maxMatches = matches;
      threatType = type;
    }
  });
  
  const riskScore = generateConsistentRiskScore(article);
  const severity = getThreatLevel(article);
  
  // Determine affected industries based on content
  const affectedIndustries = [];
  if (content.includes('financial') || content.includes('bank') || content.includes('payment')) {
    affectedIndustries.push('Financial Services');
  }
  if (content.includes('healthcare') || content.includes('hospital') || content.includes('medical')) {
    affectedIndustries.push('Healthcare');
  }
  if (content.includes('government') || content.includes('federal') || content.includes('municipal')) {
    affectedIndustries.push('Government');
  }
  if (content.includes('energy') || content.includes('power') || content.includes('utility')) {
    affectedIndustries.push('Energy & Utilities');
  }
  if (content.includes('retail') || content.includes('e-commerce') || content.includes('shopping')) {
    affectedIndustries.push('Retail');
  }
  if (affectedIndustries.length === 0) {
    affectedIndustries.push('General');
  }
  
  // Generate recommendations based on threat type and severity
  const recommendations = generateRecommendations(threatType, severity);
  
  return {
    threatType,
    severity,
    affectedIndustries,
    riskScore,
    recommendations
  };
}

// Generate recommendations based on threat analysis
function generateRecommendations(threatType: any, severity: string): string[] {
  const baseRecommendations = ['Monitor threat intelligence feeds', 'Update security policies', 'Review incident response procedures'];
  
  const threatSpecificRecs: Record<string, string[]> = {
    malware: ['Update antivirus definitions', 'Scan all systems', 'Block malicious domains'],
    phishing: ['Train staff on email security', 'Implement email filtering', 'Verify sender authenticity'],
    'data-breach': ['Audit data access logs', 'Encrypt sensitive data', 'Implement data loss prevention'],
    ransomware: ['Test backup systems', 'Segment network access', 'Deploy endpoint detection'],
    vulnerability: ['Apply security patches', 'Conduct vulnerability scans', 'Update affected systems'],
    apt: ['Enhance monitoring', 'Review privileged access', 'Implement threat hunting'],
    'social-engineering': ['Security awareness training', 'Verify requests via alternate channels', 'Implement approval workflows'],
    'insider-threat': ['Monitor privileged users', 'Implement least privilege', 'Review access controls']
  };
  
  const severityRecs: Record<string, string[]> = {
    critical: ['Activate incident response team', 'Consider emergency patching', 'Alert senior management'],
    high: ['Prioritize remediation', 'Increase monitoring', 'Review similar systems'],
    medium: ['Schedule remediation', 'Monitor for indicators', 'Update security controls'],
    low: ['Add to security backlog', 'Monitor for changes', 'Review periodically']
  };
  
  const recommendations = [...baseRecommendations];
  if (threatSpecificRecs[threatType]) {
    recommendations.push(...threatSpecificRecs[threatType]);
  }
  if (severityRecs[severity]) {
    recommendations.push(...severityRecs[severity]);
  }
  
  return recommendations.slice(0, 5); // Limit to 5 recommendations
}

// Industry keywords
const INDUSTRY_KEYWORDS = {
  'financial': ['bank', 'banking', 'finance', 'financial', 'credit card', 'payment', 'investment'],
  'healthcare': ['hospital', 'healthcare', 'medical', 'patient', 'health', 'pharmaceutical'],
  'government': ['government', 'federal', 'state', 'municipal', 'public sector', 'agency'],
  'retail': ['retail', 'e-commerce', 'online store', 'shopping', 'merchant'],
  'technology': ['tech', 'software', 'hardware', 'it', 'technology', 'startup'],
  'energy': ['energy', 'power', 'utility', 'grid', 'oil', 'gas'],
  'education': ['education', 'school', 'university', 'college', 'academic'],
  'manufacturing': ['manufacturing', 'industrial', 'factory', 'production', 'supply chain']
};

export function getThreatLevelConfig(level: string): ThreatLevel {
  return THREAT_LEVELS[level] || THREAT_LEVELS.low;
}

export function getCategoryConfig(categoryId: string): NewsCategory | undefined {
  return NEWS_CATEGORIES.find(cat => cat.id === categoryId);
}

export function getAllCategories(): NewsCategory[] {
  return NEWS_CATEGORIES;
}
