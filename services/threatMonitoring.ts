import { useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { generateConsistentRiskScore, getThreatLevel } from '../utils/threatAnalysis';
import type { Article } from '../types/news';

interface ThreatAlert {
  id: string;
  article: Article;
  severity: 'low' | 'medium' | 'high' | 'critical';
  riskScore: number;
  timestamp: string;
  read: boolean;
}

interface ThreatStatistics {
  totalAlerts: number;
  criticalThreats: number;
  newAlerts24h: number;
  topThreatTypes: string[];
  riskTrend: 'increasing' | 'decreasing' | 'stable';
}

class ThreatMonitoringService {
  private static instance: ThreatMonitoringService;
  private alerts: ThreatAlert[] = [];
  private subscribers: ((alerts: ThreatAlert[]) => void)[] = [];

  static getInstance(): ThreatMonitoringService {
    if (!ThreatMonitoringService.instance) {
      ThreatMonitoringService.instance = new ThreatMonitoringService();
    }
    return ThreatMonitoringService.instance;
  }

  async initialize() {
    try {
      const stored = await AsyncStorage.getItem('threat_alerts');
      if (stored) {
        this.alerts = JSON.parse(stored);
      }
    } catch (error) {
      console.warn('Failed to load stored threat alerts:', error);
    }
  }

  async addAlert(article: Article): Promise<void> {
    const severity = getThreatLevel(article);
    const riskScore = generateConsistentRiskScore(article);
    
    // Only create alerts for medium risk and above
    if (riskScore < 50) return;

    const alert: ThreatAlert = {
      id: `${article.url}-${Date.now()}`,
      article,
      severity,
      riskScore,
      timestamp: new Date().toISOString(),
      read: false,
    };

    this.alerts.unshift(alert);
    
    // Keep only last 100 alerts
    if (this.alerts.length > 100) {
      this.alerts = this.alerts.slice(0, 100);
    }

    await this.persistAlerts();
    this.notifySubscribers();
  }

  async processArticles(articles: Article[]): Promise<void> {
    const existing = new Set(this.alerts.map(a => a.article.url));
    
    for (const article of articles) {
      if (!existing.has(article.url)) {
        await this.addAlert(article);
      }
    }
  }

  getStatistics(): ThreatStatistics {
    const now = new Date();
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    
    const criticalThreats = this.alerts.filter(a => a.severity === 'critical').length;
    const newAlerts24h = this.alerts.filter(a => new Date(a.timestamp) >= yesterday).length;
    
    // Analyze threat types
    const threatTypes: Record<string, number> = {};
    this.alerts.forEach(alert => {
      const content = `${alert.article.title} ${alert.article.description || ''}`.toLowerCase();
      if (content.includes('ransomware')) threatTypes.ransomware = (threatTypes.ransomware || 0) + 1;
      else if (content.includes('phishing')) threatTypes.phishing = (threatTypes.phishing || 0) + 1;
      else if (content.includes('malware')) threatTypes.malware = (threatTypes.malware || 0) + 1;
      else if (content.includes('breach')) threatTypes.breach = (threatTypes.breach || 0) + 1;
      else if (content.includes('vulnerability')) threatTypes.vulnerability = (threatTypes.vulnerability || 0) + 1;
      else threatTypes.other = (threatTypes.other || 0) + 1;
    });

    const topThreatTypes = Object.entries(threatTypes)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 3)
      .map(([type]) => type);

    // Calculate risk trend
    const recent = this.alerts.filter(a => new Date(a.timestamp) >= yesterday);
    const older = this.alerts.filter(a => {
      const date = new Date(a.timestamp);
      return date < yesterday && date >= new Date(now.getTime() - 48 * 60 * 60 * 1000);
    });

    const recentAvgRisk = recent.length > 0 ? recent.reduce((sum, a) => sum + a.riskScore, 0) / recent.length : 0;
    const olderAvgRisk = older.length > 0 ? older.reduce((sum, a) => sum + a.riskScore, 0) / older.length : 0;

    let riskTrend: ThreatStatistics['riskTrend'] = 'stable';
    if (recentAvgRisk > olderAvgRisk + 5) riskTrend = 'increasing';
    else if (recentAvgRisk < olderAvgRisk - 5) riskTrend = 'decreasing';

    return {
      totalAlerts: this.alerts.length,
      criticalThreats,
      newAlerts24h,
      topThreatTypes,
      riskTrend,
    };
  }

  getAlerts(): ThreatAlert[] {
    return [...this.alerts];
  }

  async markAsRead(alertId: string): Promise<void> {
    const alert = this.alerts.find(a => a.id === alertId);
    if (alert) {
      alert.read = true;
      await this.persistAlerts();
      this.notifySubscribers();
    }
  }

  async clearOldAlerts(): Promise<void> {
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    this.alerts = this.alerts.filter(alert => new Date(alert.timestamp) >= thirtyDaysAgo);
    await this.persistAlerts();
    this.notifySubscribers();
  }

  subscribe(callback: (alerts: ThreatAlert[]) => void): () => void {
    this.subscribers.push(callback);
    return () => {
      const index = this.subscribers.indexOf(callback);
      if (index > -1) {
        this.subscribers.splice(index, 1);
      }
    };
  }

  private async persistAlerts(): Promise<void> {
    try {
      await AsyncStorage.setItem('threat_alerts', JSON.stringify(this.alerts));
    } catch (error) {
      console.warn('Failed to persist threat alerts:', error);
    }
  }

  private notifySubscribers(): void {
    this.subscribers.forEach(callback => callback([...this.alerts]));
  }
}

// Hook to use threat monitoring
export function useThreatMonitoring() {
  const [alerts, setAlerts] = useState<ThreatAlert[]>([]);
  const [statistics, setStatistics] = useState<ThreatStatistics>({
    totalAlerts: 0,
    criticalThreats: 0,
    newAlerts24h: 0,
    topThreatTypes: [],
    riskTrend: 'stable',
  });

  useEffect(() => {
    const service = ThreatMonitoringService.getInstance();
    
    // Initialize service
    service.initialize().then(() => {
      setAlerts(service.getAlerts());
      setStatistics(service.getStatistics());
    });

    // Subscribe to updates
    const unsubscribe = service.subscribe((newAlerts) => {
      setAlerts(newAlerts);
      setStatistics(service.getStatistics());
    });

    return unsubscribe;
  }, []);

  return {
    alerts,
    statistics,
    markAsRead: (alertId: string) => ThreatMonitoringService.getInstance().markAsRead(alertId),
    processArticles: (articles: Article[]) => ThreatMonitoringService.getInstance().processArticles(articles),
  };
}

export type { ThreatAlert, ThreatStatistics };
export default ThreatMonitoringService;
