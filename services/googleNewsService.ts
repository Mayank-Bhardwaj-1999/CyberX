import { Article } from '../types/news';

export interface GoogleNewsArticle {
  title: string;
  url: string;
  description: string;
  source: string;
  publishedAt: string;
  urlToImage?: string;
}

export class GoogleNewsService {
  private static readonly BASE_URL = 'https://news.google.com/rss/search';
  private static readonly DEFAULT_PARAMS = {
    hl: 'en-IN',
    gl: 'IN',
    ceid: 'IN:en'
  };
  // Simple in-memory caches to avoid recomputing heuristics for identical title+desc pairs
  private static categoryCache: Map<string,string[]> = new Map();
  private static sectorCache: Map<string,string[]> = new Map();

  /**
   * Search Google News for cybersecurity-related articles
   */
  static async searchCyberSecurityNews(query: string, limit: number = 20): Promise<Article[]> {
    try {
      // Enhance query with cybersecurity context
      const enhancedQuery = this.enhanceQueryWithCyberContext(query);
      
      // Build search URL
      const searchUrl = this.buildSearchUrl(enhancedQuery);
      
      // Since we can't directly access Google News RSS from React Native due to CORS,
      // we'll use our backend as a proxy
      const response = await fetch(
        `${process.env.EXPO_PUBLIC_API_URL}/api/google-news/search`,
        {
          method: 'POST',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            query: enhancedQuery,
            limit,
            searchUrl
          })
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ API Error response:', errorText);
        throw new Error(`Google News search failed: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      
      const transformedArticles = this.transformGoogleNewsToArticles(data.articles || []);
      
      return transformedArticles;
    } catch (error) {
      console.error('💥 GoogleNewsService error:', error);
      throw error;
    }
  }

  /**
   * Enhance user query with cybersecurity context
   */
  private static enhanceQueryWithCyberContext(query: string): string {
    const cyberKeywords = [
      'cybersecurity', 'cyber security', 'malware', 'ransomware', 'phishing',
      'data breach', 'cyber attack', 'hacking', 'security vulnerability',
      'cyber threat', 'information security', 'cyber crime', 'data leak',
      'security incident', 'cyber espionage', 'network security'
    ];

    const queryLower = query.toLowerCase();
    const hasCyberKeyword = cyberKeywords.some(keyword => 
      queryLower.includes(keyword)
    );

    if (!hasCyberKeyword) {
      // Add cybersecurity context to the query
      return `${query} cybersecurity OR "cyber security" OR malware OR "data breach"`;
    }

    return query;
  }

  /**
   * Build Google News search URL
   */
  private static buildSearchUrl(query: string): string {
    const params = new URLSearchParams({
      q: query,
      ...this.DEFAULT_PARAMS
    });

    return `${this.BASE_URL}?${params.toString()}`;
  }

  /**
   * Transform Google News articles to our Article format
   */
  private static transformGoogleNewsToArticles(googleArticles: GoogleNewsArticle[]): Article[] {
    return googleArticles.map(article => {
      const key = (article.title + '|' + article.description).toLowerCase();
      let categories = this.categoryCache.get(key);
      if(!categories){
        categories = this.extractCategories(article.title, article.description);
        this.categoryCache.set(key, categories);
      }
      let affectedSectors = this.sectorCache.get(key);
      if(!affectedSectors){
        affectedSectors = this.deriveAffectedSectors(article.title, article.description);
        this.sectorCache.set(key, affectedSectors);
      }
      return ({
      source: {
        id: this.extractSourceId(article.source),
        name: article.source
      },
      author: null,
      title: this.cleanTitle(article.title),
      description: article.description,
      summary: null,
      url: article.url,
      urlToImage: article.urlToImage || null,
      publishedAt: article.publishedAt,
      content: article.description,
      threatLevel: this.assessThreatLevel(article.title, article.description),
      categories,
      affectedSectors,
    });
    });
  }

  /**
   * Extract source ID from source name
   */
  private static extractSourceId(sourceName: string): string {
    return sourceName.toLowerCase()
      .replace(/[^a-z0-9]/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');
  }

  /**
   * Clean article title from Google News format
   */
  private static cleanTitle(title: string): string {
    // Remove source name if it's appended at the end
    return title.replace(/ - [^-]+$/, '').trim();
  }

  /**
   * Assess threat level based on content
   */
  private static assessThreatLevel(title: string, description: string): 'low' | 'medium' | 'high' | 'critical' {
    const content = `${title} ${description}`.toLowerCase();
    
    const criticalKeywords = ['ransomware', 'zero-day', 'critical vulnerability', 'mass breach'];
    const highKeywords = ['data breach', 'cyber attack', 'malware', 'hacking'];
    const mediumKeywords = ['phishing', 'vulnerability', 'security flaw', 'cyber threat'];
    
    if (criticalKeywords.some(keyword => content.includes(keyword))) {
      return 'critical';
    }
    
    if (highKeywords.some(keyword => content.includes(keyword))) {
      return 'high';
    }
    
    if (mediumKeywords.some(keyword => content.includes(keyword))) {
      return 'medium';
    }
    
    return 'low';
  }

  /**
   * Extract categories from content
   */
  private static extractCategories(title: string, description: string): string[] {
    const content = `${title} ${description}`.toLowerCase();
    const categories: string[] = [];

    const categoryMap = {
      'malware': ['malware', 'virus', 'trojan', 'ransomware'],
  'ransomware': ['ransomware'],
      'data-breach': ['data breach', 'data leak', 'information leak'],
      'phishing': ['phishing', 'social engineering', 'email scam'],
      'vulnerability': ['vulnerability', 'exploit', 'security flaw'],
      'cyber-attack': ['cyber attack', 'hacking', 'cyber warfare'],
      'privacy': ['privacy', 'gdpr', 'data protection'],
      'mobile-security': ['mobile', 'android', 'ios', 'smartphone'],
      'enterprise': ['enterprise', 'corporate', 'business security']
    };

    Object.entries(categoryMap).forEach(([category, keywords]) => {
      if (keywords.some(keyword => content.includes(keyword))) {
        categories.push(category);
      }
    });

  // Deduplicate while preserving order
  const deduped = Array.from(new Set(categories));
  return deduped.length > 0 ? deduped : ['general'];
  }

  /**
   * Derive affected sectors based on keywords (lightweight heuristic)
   */
  private static deriveAffectedSectors(title: string, description: string): string[] {
    const text = `${title} ${description}`.toLowerCase();
    const sectorMap: Record<string,string[]> = {
      telecommunications: ['cisco','huawei','ericsson','nokia','5g','telecom','isp','broadband','fiber'],
      finance: ['bank','financial','fintech','payment','visa','mastercard','swift','atm','cryptocurrency','crypto exchange','defi'],
      healthcare: ['hospital','healthcare','clinic','patient data','medical','pharma','fda'],
      government: ['government','ministry','federal','agency','defense','army','navy','air force','state department'],
      energy: ['energy','oil','gas','pipeline','nuclear','power plant','renewable','grid'],
      education: ['university','school','education','campus','student records'],
      retail: ['retail','e-commerce','shopify','amazon','store','point of sale','pos'],
      manufacturing: ['factory','manufacturing','industrial','ics','scada','ot network','production line'],
      technology: ['software','technology','tech giant','cloud service','saas','data center','datacenter'],
      transportation: ['airport','airline','railway','transport','logistics','shipping','port','maritime'],
      media: ['media','news outlet','broadcast','streaming platform','television','press']
    };
    const matched: string[] = [];
    Object.entries(sectorMap).forEach(([sector, keywords]) => {
      if (keywords.some(k => text.includes(k))) matched.push(sector);
    });
    return matched.length ? Array.from(new Set(matched)) : ['general'];
  }

  /**
   * Get trending cybersecurity topics
   */
  static async getTrendingTopics(): Promise<string[]> {
    const trendingQueries = [
      'recent malware attacks',
      'data breaches 2025',
      'cybersecurity news today',
      'ransomware attacks',
      'phishing campaigns',
      'zero-day vulnerabilities',
      'cyber threats India',
      'security incidents',
      'hacking news',
      'cyber crime reports'
    ];

    return trendingQueries;
  }

  /**
   * Get suggested queries based on user input
   */
  static getSuggestedQueries(input: string): string[] {
    if (!input) return [];
    const base = [
      'zero day','ransomware','phishing campaign','data breach','APT group','DDoS attack','supply chain attack','malware variant','CVE exploit','critical vulnerability','nation state cyber','zero trust','OWASP Top 10','firmware security','cloud misconfiguration','privilege escalation','insider threat','dark web leak','threat intelligence','patch tuesday'
    ];
    const dynamicTemplates = [
      `${input} ransomware`,
      `${input} data breach`,
      `${input} vulnerability`,
      `${input} malware`,
      `${input} phishing`,
      `${input} cyber attack`,
      `${input} exploit`,
      `${input} zero day`
    ];
    const lower = input.toLowerCase();
    const starts = base.filter(b=>b.startsWith(lower));
    const includes = base.filter(b=>!b.startsWith(lower) && b.includes(lower));
    const combined = [...starts, ...includes, ...dynamicTemplates];
    return Array.from(new Set(combined)).slice(0,8);
  }
}
