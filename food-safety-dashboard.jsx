import { useState, useMemo, useEffect, useCallback } from "react";
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Treemap } from "recharts";
import { AlertTriangle, Shield, Search, Filter, TrendingUp, Globe, Activity, Bell, ChevronDown, ChevronRight, Eye, Download, RefreshCw, Clock, Zap, BarChart2, PieChart as PieChartIcon, Map, FileText, Settings, AlertCircle, CheckCircle, Info, X, ExternalLink, Database, Cpu, BookOpen, Star, ArrowUp, ArrowDown, Minus } from "lucide-react";

// ============================================================
// DATA LAYER - Simulated food safety alerts from real sources
// ============================================================

// Sources from official spreadsheet: רשימת מקורות זמנית לכלי מודיעין גלוי
const SOURCES = [
  // Category 1: Recalls & Alerts (ריקולים והתראות)
  { id: "fda_enforcement", name: "FDA - Recall Enforcement Reports", region: "USA", type: "api", category: "recalls_alerts", url: "https://open.fda.gov/apis/food/enforcement/", status: "active", lastSync: "2026-04-13T09:15:00Z", alertCount: 1523, ratings: { timeliness: 4, quality: 5, relevance: 4 }, pushMethod: "RSS, API", contentType: "Recalls - all food types and violations" },
  { id: "fda_import_alerts", name: "FDA - Import Alerts", region: "USA", type: "scrape", category: "recalls_alerts", url: "https://www.fda.gov/industry/import-alerts/search-import-alerts", status: "active", lastSync: "2026-04-13T08:00:00Z", alertCount: 872, ratings: { timeliness: 4, quality: 4, relevance: 4 }, pushMethod: "Search engine only", contentType: "Import alerts - all food types" },
  { id: "fda_safety_alerts", name: "FDA - Safety Alerts", region: "USA", type: "scrape", category: "recalls_alerts", url: "https://www.fda.gov/food/recalls-outbreaks-emergencies/alerts-advisories-safety-information", status: "active", lastSync: "2026-04-13T07:30:00Z", alertCount: 345, ratings: { timeliness: 3, quality: 5, relevance: 4 }, pushMethod: "Feed page", contentType: "Food safety" },
  { id: "fda_recalls_page", name: "FDA - Recalls & Market Withdrawals", region: "USA", type: "rss", category: "recalls_alerts", url: "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts", status: "active", lastSync: "2026-04-13T09:00:00Z", alertCount: 1891, ratings: { timeliness: 4, quality: 5, relevance: 3 }, pushMethod: "RSS + weekly mailing list", contentType: "Recalls - all food types + other products" },
  { id: "usda_fsis", name: "USDA - FSIS", region: "USA", type: "api", category: "recalls_alerts", url: "https://www.fsis.usda.gov/recalls", status: "active", lastSync: "2026-04-13T07:45:00Z", alertCount: 689, ratings: { timeliness: 4, quality: 5, relevance: 3 }, pushMethod: "API", contentType: "Meat and eggs, all violation types" },
  { id: "rasff", name: "RASFF Window", region: "Europe", type: "scrape", category: "recalls_alerts", url: "https://webgate.ec.europa.eu/rasff-window/screen/search", status: "active", lastSync: "2026-04-13T08:30:00Z", alertCount: 2847, ratings: { timeliness: 4, quality: 5, relevance: 4 }, pushMethod: "Search engine with filters", contentType: "All food types and violations" },
  { id: "infosan", name: "INFOSAN", region: "Global", type: "email", category: "recalls_alerts", url: "https://www.who.int/activities/international-food-safety-authorities-network", status: "active", lastSync: "2026-04-13T04:00:00Z", alertCount: 198, ratings: { timeliness: 3, quality: 5, relevance: 4 }, pushMethod: "Email (Israel team)", contentType: "All food types and violations" },
  { id: "cdc_food_safety", name: "CDC - Food Safety (USDA+FDA Aggregate)", region: "USA", type: "rss", category: "recalls_alerts", url: "https://tools.cdc.gov/medialibrary/index.aspx#/feed/id/379374", status: "active", lastSync: "2026-04-13T09:30:00Z", alertCount: 1205, ratings: { timeliness: 4, quality: 5, relevance: 4 }, pushMethod: "RSS", contentType: "Recalls - all food types and violations" },

  // Category 2: Investigations & Morbidity Data (חקירות ונתוני תחלואה)
  { id: "fda_cares", name: "FDA - CARES Reports", region: "USA", type: "api", category: "investigations_morbidity", url: "https://open.fda.gov/apis/food/event/", status: "active", lastSync: "2026-04-13T06:00:00Z", alertCount: 412, ratings: { timeliness: 3, quality: 5, relevance: 3 }, pushMethod: "API", contentType: "Food safety events, cosmetics and more" },
  { id: "fda_core_outbreaks", name: "FDA - Outbreak Investigation (CORE)", region: "USA", type: "scrape", category: "investigations_morbidity", url: "https://www.fda.gov/food/outbreaks-foodborne-illness/investigations-foodborne-illness-outbreaks", status: "active", lastSync: "2026-04-13T05:30:00Z", alertCount: 156, ratings: { timeliness: 3, quality: 5, relevance: 4 }, pushMethod: "Feed page", contentType: "Microbiological outbreaks, foodborne illness" },
  { id: "cdc_outbreaks", name: "CDC - Outbreaks", region: "USA", type: "scrape", category: "investigations_morbidity", url: "https://www.cdc.gov/foodborne-outbreaks/outbreaks/", status: "active", lastSync: "2026-04-13T08:15:00Z", alertCount: 278, ratings: { timeliness: 4, quality: 5, relevance: 4 }, pushMethod: "Dashboard + Feed", contentType: "Microbiological outbreaks, foodborne illness" },
  { id: "usda_outbreak_inv", name: "USDA - Outbreak Investigations", region: "USA", type: "scrape", category: "investigations_morbidity", url: "https://www.fsis.usda.gov/food-safety/foodborne-illness-and-disease/outbreaks/outbreak-investigations-response", status: "active", lastSync: "2026-04-13T04:30:00Z", alertCount: 89, ratings: { timeliness: 3, quality: 5, relevance: 3 }, pushMethod: "Feed page", contentType: "Microbiological outbreaks, foodborne illness" },

  // Category 3: Regulation & Risk Management (רגולציה וניהול סיכונים)
  { id: "who_news", name: "WHO - Food Safety News", region: "Global", type: "scrape", category: "regulation_risk", url: "https://www.who.int/news", status: "active", lastSync: "2026-04-13T03:00:00Z", alertCount: 134, ratings: { timeliness: 3, quality: 5, relevance: 4 }, pushMethod: "News page", contentType: "Codex Alimentarius, foodborne illness" },
  { id: "efsa", name: "EFSA", region: "Europe", type: "rss", category: "regulation_risk", url: "https://www.efsa.europa.eu/en/rss", status: "active", lastSync: "2026-04-13T06:30:00Z", alertCount: 567, ratings: { timeliness: 4, quality: 5, relevance: 4 }, pushMethod: "Mailing list + RSS + News", contentType: "Regulation and risk management" },
  { id: "efsa_journal", name: "EFSA Journal", region: "Europe", type: "rss", category: "regulation_risk", url: "https://efsa.onlinelibrary.wiley.com/loi/18314732", status: "active", lastSync: "2026-04-12T22:00:00Z", alertCount: 234, ratings: { timeliness: 3, quality: 5, relevance: 4 }, pushMethod: "Mailing list + RSS", contentType: "Regulatory research" },
  { id: "us_federal_register", name: "USA Federal Register - Food Safety", region: "USA", type: "rss", category: "regulation_risk", url: "https://www.federalregister.gov/food-safety", status: "active", lastSync: "2026-04-13T07:00:00Z", alertCount: 189, ratings: { timeliness: 4, quality: 5, relevance: 3 }, pushMethod: "Mailing list + RSS", contentType: "Legislation updates & regulatory documents" },
];

const HAZARD_CATEGORIES = {
  biological: { label: "Biological", color: "#ef4444", icon: "🦠" },
  chemical: { label: "Chemical", color: "#f97316", icon: "⚗️" },
  physical: { label: "Physical", color: "#eab308", icon: "🔩" },
  allergen: { label: "Allergen", color: "#a855f7", icon: "⚠️" },
  fraud: { label: "Food Fraud", color: "#6366f1", icon: "🔍" },
  regulatory: { label: "Regulatory", color: "#3b82f6", icon: "📋" },
};

const RISK_LEVELS = {
  critical: { label: "Critical", color: "#dc2626", bg: "#fef2f2", border: "#fecaca", score: "9-10" },
  high: { label: "High", color: "#ea580c", bg: "#fff7ed", border: "#fed7aa", score: "7-8" },
  medium: { label: "Medium", color: "#ca8a04", bg: "#fefce8", border: "#fef08a", score: "4-6" },
  low: { label: "Low", color: "#16a34a", bg: "#f0fdf4", border: "#bbf7d0", score: "1-3" },
};

const PRODUCT_CATEGORIES = [
  "Dairy", "Meat & Poultry", "Seafood", "Fruits & Vegetables", "Grains & Cereals",
  "Beverages", "Confectionery", "Spices & Herbs", "Nuts & Seeds", "Processed Foods",
  "Baby Food", "Dietary Supplements", "Animal Feed", "Food Additives", "Packaging"
];

const COUNTRIES = [
  "United States", "Germany", "France", "United Kingdom", "Italy", "Spain",
  "Netherlands", "Canada", "Australia", "Japan", "South Korea", "Belgium",
  "Poland", "Sweden", "Switzerland", "Israel", "Brazil", "China", "India", "Turkey"
];

// Generate realistic alert data
function generateAlerts(count = 150) {
  const hazardTypes = Object.keys(HAZARD_CATEGORIES);
  const riskLevels = Object.keys(RISK_LEVELS);
  const sources = SOURCES.map(s => s.id);
  const statuses = ["new", "under_review", "confirmed", "resolved", "escalated"];

  const alertTemplates = [
    { hazard: "biological", titles: ["Salmonella contamination in {product}", "Listeria monocytogenes detected in {product}", "E. coli O157:H7 outbreak linked to {product}", "Campylobacter in {product} from {country}", "Norovirus contamination in {product}"] },
    { hazard: "chemical", titles: ["Pesticide residues above MRL in {product}", "Heavy metals (lead) in {product}", "Unauthorized food additive in {product}", "Aflatoxin contamination in {product}", "Ethylene oxide residues in {product}"] },
    { hazard: "physical", titles: ["Metal fragments found in {product}", "Glass contamination in {product}", "Plastic pieces in {product}", "Foreign body in {product} from {country}"] },
    { hazard: "allergen", titles: ["Undeclared milk allergen in {product}", "Undeclared peanuts in {product}", "Missing allergen labeling on {product}", "Gluten not declared in {product}"] },
    { hazard: "fraud", titles: ["Suspected adulteration of {product}", "Mislabeling of origin for {product}", "Fraudulent organic certification for {product}", "Species substitution in {product}"] },
    { hazard: "regulatory", titles: ["Unauthorized novel food: {product}", "Non-compliant labeling on {product}", "Import rejection: {product} from {country}", "Unauthorized GMO in {product}"] },
  ];

  const alerts = [];
  const now = new Date("2026-04-13T10:00:00Z");

  for (let i = 0; i < count; i++) {
    const template = alertTemplates[Math.floor(Math.random() * alertTemplates.length)];
    const product = PRODUCT_CATEGORIES[Math.floor(Math.random() * PRODUCT_CATEGORIES.length)];
    const country = COUNTRIES[Math.floor(Math.random() * COUNTRIES.length)];
    const titleTemplate = template.titles[Math.floor(Math.random() * template.titles.length)];
    const title = titleTemplate.replace("{product}", product.toLowerCase()).replace("{country}", country);

    const daysAgo = Math.floor(Math.random() * 90);
    const date = new Date(now - daysAgo * 86400000);
    const riskIdx = Math.random();
    const risk = riskIdx < 0.08 ? "critical" : riskIdx < 0.25 ? "high" : riskIdx < 0.6 ? "medium" : "low";
    const riskScore = risk === "critical" ? 9 + Math.random() : risk === "high" ? 7 + Math.random() * 2 : risk === "medium" ? 4 + Math.random() * 3 : 1 + Math.random() * 3;

    // Classification confidence (hybrid approach)
    const classMethod = Math.random() > 0.4 ? "llm" : "rule_based";
    const confidence = classMethod === "llm" ? 0.75 + Math.random() * 0.24 : 0.6 + Math.random() * 0.35;

    alerts.push({
      id: `ALERT-${String(2026000 + i).padStart(7, "0")}`,
      title,
      hazardCategory: template.hazard,
      riskLevel: risk,
      riskScore: Math.round(riskScore * 10) / 10,
      product,
      country,
      source: sources[Math.floor(Math.random() * sources.length)],
      date: date.toISOString(),
      status: statuses[Math.floor(Math.random() * statuses.length)],
      classificationMethod: classMethod,
      confidence: Math.round(confidence * 100) / 100,
      affectedCountries: Array.from({ length: 1 + Math.floor(Math.random() * 4) }, () => COUNTRIES[Math.floor(Math.random() * COUNTRIES.length)]),
      description: `Automated alert generated from source monitoring. Classification performed using ${classMethod === "llm" ? "LLM-based analysis" : "rule-based keyword matching"}. Confidence: ${Math.round(confidence * 100)}%.`,
      trending: Math.random() > 0.85,
    });
  }

  return alerts.sort((a, b) => new Date(b.date) - new Date(a.date));
}

// Generate trend data
function generateTrendData() {
  const months = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr"];
  return months.map((month, i) => ({
    month,
    biological: 30 + Math.floor(Math.random() * 40),
    chemical: 20 + Math.floor(Math.random() * 30),
    physical: 5 + Math.floor(Math.random() * 15),
    allergen: 15 + Math.floor(Math.random() * 25),
    fraud: 5 + Math.floor(Math.random() * 10),
    regulatory: 10 + Math.floor(Math.random() * 15),
    total: 0,
  })).map(d => ({ ...d, total: d.biological + d.chemical + d.physical + d.allergen + d.fraud + d.regulatory }));
}

function generateRegionData() {
  return [
    { name: "Europe", alerts: 487, critical: 12, high: 45, trend: "up" },
    { name: "North America", alerts: 389, critical: 8, high: 38, trend: "stable" },
    { name: "Asia", alerts: 234, critical: 15, high: 42, trend: "up" },
    { name: "Oceania", alerts: 89, critical: 2, high: 8, trend: "down" },
    { name: "Middle East", alerts: 67, critical: 4, high: 11, trend: "up" },
    { name: "South America", alerts: 123, critical: 6, high: 19, trend: "stable" },
  ];
}

// ============================================================
// UI COMPONENTS
// ============================================================

const Badge = ({ children, variant = "default", className = "" }) => {
  const styles = {
    default: "bg-gray-100 text-gray-700 border border-gray-200",
    critical: "bg-red-100 text-red-800 border border-red-200",
    high: "bg-orange-100 text-orange-800 border border-orange-200",
    medium: "bg-yellow-100 text-yellow-800 border border-yellow-200",
    low: "bg-green-100 text-green-800 border border-green-200",
    info: "bg-blue-100 text-blue-800 border border-blue-200",
    active: "bg-emerald-100 text-emerald-800 border border-emerald-200",
    delayed: "bg-amber-100 text-amber-800 border border-amber-200",
    llm: "bg-purple-100 text-purple-800 border border-purple-200",
    rule_based: "bg-cyan-100 text-cyan-800 border border-cyan-200",
    trending: "bg-rose-100 text-rose-800 border border-rose-200 animate-pulse",
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${styles[variant] || styles.default} ${className}`}>
      {children}
    </span>
  );
};

// ============================================================
// MAIN DASHBOARD
// ============================================================

export default function FoodSafetyDashboard() {
  const [alerts] = useState(() => generateAlerts(200));
  const [trendData] = useState(() => generateTrendData());
  const [regionData] = useState(() => generateRegionData());
  const [activeTab, setActiveTab] = useState("overview");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRisk, setSelectedRisk] = useState("all");
  const [selectedHazard, setSelectedHazard] = useState("all");
  const [selectedSource, setSelectedSource] = useState("all");
  const [selectedCountry, setSelectedCountry] = useState("all");
  const [selectedTimeRange, setSelectedTimeRange] = useState("30");
  const [expandedAlert, setExpandedAlert] = useState(null);
  const [showMethodology, setShowMethodology] = useState(false);

  // Filter alerts
  const filteredAlerts = useMemo(() => {
    const cutoff = new Date("2026-04-13T10:00:00Z");
    cutoff.setDate(cutoff.getDate() - parseInt(selectedTimeRange));

    return alerts.filter(a => {
      if (selectedRisk !== "all" && a.riskLevel !== selectedRisk) return false;
      if (selectedHazard !== "all" && a.hazardCategory !== selectedHazard) return false;
      if (selectedSource !== "all" && a.source !== selectedSource) return false;
      if (selectedCountry !== "all" && a.country !== selectedCountry) return false;
      if (new Date(a.date) < cutoff) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        return a.title.toLowerCase().includes(q) || a.product.toLowerCase().includes(q) || a.country.toLowerCase().includes(q) || a.id.toLowerCase().includes(q);
      }
      return true;
    });
  }, [alerts, selectedRisk, selectedHazard, selectedSource, selectedCountry, selectedTimeRange, searchQuery]);

  // Compute stats
  const stats = useMemo(() => {
    const total = filteredAlerts.length;
    const critical = filteredAlerts.filter(a => a.riskLevel === "critical").length;
    const high = filteredAlerts.filter(a => a.riskLevel === "high").length;
    const trending = filteredAlerts.filter(a => a.trending).length;
    const avgConfidence = filteredAlerts.length > 0 ? Math.round(filteredAlerts.reduce((s, a) => s + a.confidence, 0) / filteredAlerts.length * 100) : 0;
    const llmClassified = filteredAlerts.filter(a => a.classificationMethod === "llm").length;

    const byHazard = {};
    Object.keys(HAZARD_CATEGORIES).forEach(h => {
      byHazard[h] = filteredAlerts.filter(a => a.hazardCategory === h).length;
    });

    const byCountry = {};
    filteredAlerts.forEach(a => {
      byCountry[a.country] = (byCountry[a.country] || 0) + 1;
    });

    const byProduct = {};
    filteredAlerts.forEach(a => {
      byProduct[a.product] = (byProduct[a.product] || 0) + 1;
    });

    return { total, critical, high, trending, avgConfidence, llmClassified, byHazard, byCountry, byProduct };
  }, [filteredAlerts]);

  const hazardPieData = useMemo(() =>
    Object.entries(stats.byHazard).map(([key, value]) => ({
      name: HAZARD_CATEGORIES[key].label,
      value,
      color: HAZARD_CATEGORIES[key].color,
    })).filter(d => d.value > 0),
  [stats.byHazard]);

  const topCountriesData = useMemo(() =>
    Object.entries(stats.byCountry)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([name, value]) => ({ name: name.length > 12 ? name.substring(0, 12) + "..." : name, fullName: name, value })),
  [stats.byCountry]);

  const topProductsData = useMemo(() =>
    Object.entries(stats.byProduct)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8)
      .map(([name, value]) => ({ name, value })),
  [stats.byProduct]);

  const riskDistData = useMemo(() => [
    { name: "Critical", value: filteredAlerts.filter(a => a.riskLevel === "critical").length, color: "#dc2626" },
    { name: "High", value: filteredAlerts.filter(a => a.riskLevel === "high").length, color: "#ea580c" },
    { name: "Medium", value: filteredAlerts.filter(a => a.riskLevel === "medium").length, color: "#ca8a04" },
    { name: "Low", value: filteredAlerts.filter(a => a.riskLevel === "low").length, color: "#16a34a" },
  ], [filteredAlerts]);

  const COLORS = ["#ef4444", "#f97316", "#eab308", "#a855f7", "#6366f1", "#3b82f6"];

  const tabs = [
    { id: "overview", label: "Overview", icon: Activity },
    { id: "alerts", label: "Alert Feed", icon: Bell },
    { id: "trends", label: "Trends", icon: TrendingUp },
    { id: "sources", label: "Sources", icon: Database },
    { id: "methodology", label: "Methodology", icon: Cpu },
  ];

  return (
    <div
      className="min-h-screen bg-gray-50"
      dir="rtl"
      lang="he"
      style={{ fontFamily: "'Heebo', 'Inter', 'Segoe UI', -apple-system, sans-serif" }}
    >
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-600 rounded-lg">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">FoodSafe Intelligence</h1>
                <p className="text-xs text-gray-500">Israel Health Security Dept. | Food Safety Alert Monitoring System</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span>Live Monitoring</span>
              </div>
              <span className="text-xs text-gray-400">Last sync: {new Date().toLocaleTimeString()}</span>
              <button className="p-2 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors">
                <RefreshCw className="w-4 h-4 text-gray-600" />
              </button>
            </div>
          </div>

          {/* Tabs */}
          <nav className="flex gap-1 mt-3 -mb-px">
            {tabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-t-lg transition-colors ${activeTab === tab.id ? "bg-gray-50 text-red-700 border-b-2 border-red-600" : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"}`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Critical Alert Banner */}
        {stats.critical > 0 && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <div className="flex-1">
              <span className="font-semibold text-red-800">{stats.critical} Critical Alert{stats.critical > 1 ? "s" : ""}</span>
              <span className="text-red-600 text-sm ms-2">requiring immediate attention in the selected time range</span>
            </div>
            <button onClick={() => { setSelectedRisk("critical"); setActiveTab("alerts"); }} className="text-sm font-medium text-red-700 hover:text-red-900 underline">
              View All
            </button>
          </div>
        )}

        {/* Filters Bar */}
        <div className="mb-6 p-4 bg-white rounded-xl border border-gray-200 shadow-sm">
          <div className="flex flex-wrap gap-3 items-center">
            <div className="relative flex-1 min-w-64">
              <Search className="absolute end-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search alerts by keyword, product, country, or ID..."
                dir="auto"
                className="w-full ps-10 pe-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
              />
            </div>
            <select value={selectedRisk} onChange={e => setSelectedRisk(e.target.value)} className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-red-500">
              <option value="all">All Risk Levels</option>
              {Object.entries(RISK_LEVELS).map(([k, v]) => <option key={k} value={k}>{v.label} ({v.score})</option>)}
            </select>
            <select value={selectedHazard} onChange={e => setSelectedHazard(e.target.value)} className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-red-500">
              <option value="all">All Hazard Types</option>
              {Object.entries(HAZARD_CATEGORIES).map(([k, v]) => <option key={k} value={k}>{v.icon} {v.label}</option>)}
            </select>
            <select value={selectedSource} onChange={e => setSelectedSource(e.target.value)} className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-red-500">
              <option value="all">All Sources</option>
              {SOURCES.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
            <select value={selectedTimeRange} onChange={e => setSelectedTimeRange(e.target.value)} className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-red-500">
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="60">Last 60 days</option>
              <option value="90">Last 90 days</option>
            </select>
          </div>
        </div>

        {/* ===== OVERVIEW TAB ===== */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {[
                { label: "Total Alerts", value: stats.total, icon: Bell, color: "text-gray-700", bg: "bg-gray-50" },
                { label: "Critical", value: stats.critical, icon: AlertTriangle, color: "text-red-700", bg: "bg-red-50" },
                { label: "High Risk", value: stats.high, icon: AlertCircle, color: "text-orange-700", bg: "bg-orange-50" },
                { label: "Trending", value: stats.trending, icon: TrendingUp, color: "text-rose-700", bg: "bg-rose-50" },
                { label: "Avg Confidence", value: `${stats.avgConfidence}%`, icon: CheckCircle, color: "text-emerald-700", bg: "bg-emerald-50" },
                { label: "LLM Classified", value: stats.llmClassified, icon: Cpu, color: "text-purple-700", bg: "bg-purple-50" },
              ].map((kpi, i) => {
                const Icon = kpi.icon;
                return (
                  <div key={i} className={`${kpi.bg} rounded-xl p-4 border border-gray-100`}>
                    <div className="flex items-center gap-2 mb-2">
                      <Icon className={`w-4 h-4 ${kpi.color}`} />
                      <span className="text-xs font-medium text-gray-500">{kpi.label}</span>
                    </div>
                    <div className={`text-2xl font-bold ${kpi.color}`}>{kpi.value}</div>
                  </div>
                );
              })}
            </div>

            {/* Charts Row 1 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Trend Over Time */}
              <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
                <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-red-600" />
                  Alert Trends (Last 7 Months)
                </h3>
                <ResponsiveContainer width="100%" height={280}>
                  <AreaChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
                    <Area type="monotone" dataKey="biological" stackId="1" stroke="#ef4444" fill="#ef444440" name="Biological" />
                    <Area type="monotone" dataKey="chemical" stackId="1" stroke="#f97316" fill="#f9731640" name="Chemical" />
                    <Area type="monotone" dataKey="allergen" stackId="1" stroke="#a855f7" fill="#a855f740" name="Allergen" />
                    <Area type="monotone" dataKey="physical" stackId="1" stroke="#eab308" fill="#eab30840" name="Physical" />
                    <Area type="monotone" dataKey="fraud" stackId="1" stroke="#6366f1" fill="#6366f140" name="Fraud" />
                    <Area type="monotone" dataKey="regulatory" stackId="1" stroke="#3b82f6" fill="#3b82f640" name="Regulatory" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Hazard Distribution Pie */}
              <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
                <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                  <PieChartIcon className="w-4 h-4 text-red-600" />
                  Hazard Type Distribution
                </h3>
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie data={hazardPieData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={3} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                      {hazardPieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Charts Row 2 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Top Countries */}
              <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
                <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                  <Globe className="w-4 h-4 text-red-600" />
                  Top Alert Origins by Country
                </h3>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={topCountriesData} layout="vertical" margin={{ left: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis type="number" tick={{ fontSize: 11 }} />
                    <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={100} />
                    <Tooltip formatter={(v, n, p) => [v, p.payload.fullName || "Alerts"]} />
                    <Bar dataKey="value" fill="#dc2626" radius={[0, 4, 4, 0]} name="Alerts" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Risk Distribution + Regions */}
              <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
                <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                  <BarChart2 className="w-4 h-4 text-red-600" />
                  Risk Level Distribution
                </h3>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={riskDistData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]} name="Alerts">
                      {riskDistData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Regional Overview */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
              <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <Globe className="w-4 h-4 text-red-600" />
                Regional Alert Summary
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                {regionData.map(region => (
                  <div key={region.name} className="p-3 bg-gray-50 rounded-lg border border-gray-100">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700">{region.name}</span>
                      {region.trend === "up" ? <ArrowUp className="w-3 h-3 text-red-500" /> : region.trend === "down" ? <ArrowDown className="w-3 h-3 text-green-500" /> : <Minus className="w-3 h-3 text-gray-400" />}
                    </div>
                    <div className="text-xl font-bold text-gray-800">{region.alerts}</div>
                    <div className="flex gap-2 mt-1">
                      <span className="text-xs text-red-600">{region.critical} critical</span>
                      <span className="text-xs text-orange-600">{region.high} high</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Critical & High Alerts */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
              <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-600" />
                Recent High-Priority Alerts
              </h3>
              <div className="space-y-2">
                {filteredAlerts.filter(a => a.riskLevel === "critical" || a.riskLevel === "high").slice(0, 8).map(alert => (
                  <div key={alert.id} className={`flex items-center gap-3 p-3 rounded-lg border ${alert.riskLevel === "critical" ? "bg-red-50 border-red-200" : "bg-orange-50 border-orange-200"}`}>
                    <span className="text-lg">{HAZARD_CATEGORIES[alert.hazardCategory]?.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-800 truncate">{alert.title}</span>
                        {alert.trending && <Badge variant="trending">Trending</Badge>}
                      </div>
                      <div className="flex gap-2 mt-0.5">
                        <span className="text-xs text-gray-500">{alert.id}</span>
                        <span className="text-xs text-gray-400">|</span>
                        <span className="text-xs text-gray-500">{SOURCES.find(s => s.id === alert.source)?.name}</span>
                        <span className="text-xs text-gray-400">|</span>
                        <span className="text-xs text-gray-500">{new Date(alert.date).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <Badge variant={alert.riskLevel}>{RISK_LEVELS[alert.riskLevel]?.label} ({alert.riskScore})</Badge>
                    <Badge variant={alert.classificationMethod}>{alert.classificationMethod === "llm" ? "LLM" : "Rules"} {Math.round(alert.confidence * 100)}%</Badge>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ===== ALERT FEED TAB ===== */}
        {activeTab === "alerts" && (
          <div className="space-y-3">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-500">Showing {filteredAlerts.length} alerts</p>
              <div className="flex gap-2">
                <button className="text-xs px-3 py-1.5 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-1">
                  <Download className="w-3 h-3" /> Export CSV
                </button>
              </div>
            </div>

            {filteredAlerts.slice(0, 50).map(alert => (
              <div key={alert.id} className={`bg-white rounded-xl border shadow-sm transition-all cursor-pointer hover:shadow-md ${alert.riskLevel === "critical" ? "border-red-300" : alert.riskLevel === "high" ? "border-orange-200" : "border-gray-200"}`}>
                <div className="p-4" onClick={() => setExpandedAlert(expandedAlert === alert.id ? null : alert.id)}>
                  <div className="flex items-start gap-3">
                    <div className="text-xl mt-0.5">{HAZARD_CATEGORIES[alert.hazardCategory]?.icon}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium text-gray-800">{alert.title}</span>
                        {alert.trending && <Badge variant="trending">Trending</Badge>}
                      </div>
                      <div className="flex flex-wrap gap-x-3 gap-y-1 mt-1.5">
                        <span className="text-xs text-gray-500 flex items-center gap-1"><FileText className="w-3 h-3" />{alert.id}</span>
                        <span className="text-xs text-gray-500 flex items-center gap-1"><Globe className="w-3 h-3" />{alert.country}</span>
                        <span className="text-xs text-gray-500 flex items-center gap-1"><Database className="w-3 h-3" />{SOURCES.find(s => s.id === alert.source)?.name}</span>
                        <span className="text-xs text-gray-500 flex items-center gap-1"><Clock className="w-3 h-3" />{new Date(alert.date).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                      <Badge variant={alert.riskLevel}>
                        Risk: {RISK_LEVELS[alert.riskLevel]?.label} ({alert.riskScore})
                      </Badge>
                      <Badge variant={alert.classificationMethod}>
                        {alert.classificationMethod === "llm" ? "LLM" : "Rule-Based"} | {Math.round(alert.confidence * 100)}%
                      </Badge>
                      <Badge variant="default">{alert.product}</Badge>
                    </div>
                    <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${expandedAlert === alert.id ? "rotate-180" : ""}`} />
                  </div>
                </div>

                {expandedAlert === alert.id && (
                  <div className="px-4 pb-4 border-t border-gray-100 pt-3">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h4 className="text-xs font-semibold text-gray-500 uppercase mb-1">Description</h4>
                        <p className="text-sm text-gray-700">{alert.description}</p>
                      </div>
                      <div>
                        <h4 className="text-xs font-semibold text-gray-500 uppercase mb-1">Affected Countries</h4>
                        <div className="flex flex-wrap gap-1">
                          {alert.affectedCountries.map((c, i) => <Badge key={i} variant="info">{c}</Badge>)}
                        </div>
                      </div>
                      <div>
                        <h4 className="text-xs font-semibold text-gray-500 uppercase mb-1">Classification Details</h4>
                        <div className="text-sm text-gray-700">
                          <p>Method: <strong>{alert.classificationMethod === "llm" ? "LLM-Based (Hybrid)" : "Rule-Based Keywords"}</strong></p>
                          <p>Confidence: <strong>{Math.round(alert.confidence * 100)}%</strong></p>
                          <p>Hazard: <strong>{HAZARD_CATEGORIES[alert.hazardCategory]?.label}</strong></p>
                        </div>
                      </div>
                      <div>
                        <h4 className="text-xs font-semibold text-gray-500 uppercase mb-1">Risk Scoring</h4>
                        <div className="text-sm text-gray-700">
                          <p>Score: <strong>{alert.riskScore}/10</strong></p>
                          <p>Level: <strong style={{ color: RISK_LEVELS[alert.riskLevel]?.color }}>{RISK_LEVELS[alert.riskLevel]?.label}</strong></p>
                          <p>Status: <strong className="capitalize">{alert.status.replace("_", " ")}</strong></p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
            {filteredAlerts.length > 50 && (
              <p className="text-center text-sm text-gray-500 py-4">Showing 50 of {filteredAlerts.length} alerts. Apply filters to narrow results.</p>
            )}
          </div>
        )}

        {/* ===== TRENDS TAB ===== */}
        {activeTab === "trends" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
                <h3 className="font-semibold text-gray-800 mb-4">Monthly Alert Volume by Hazard Type</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
                    <Bar dataKey="biological" stackId="a" fill="#ef4444" name="Biological" />
                    <Bar dataKey="chemical" stackId="a" fill="#f97316" name="Chemical" />
                    <Bar dataKey="allergen" stackId="a" fill="#a855f7" name="Allergen" />
                    <Bar dataKey="physical" stackId="a" fill="#eab308" name="Physical" />
                    <Bar dataKey="fraud" stackId="a" fill="#6366f1" name="Fraud" />
                    <Bar dataKey="regulatory" stackId="a" fill="#3b82f6" name="Regulatory" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
                <h3 className="font-semibold text-gray-800 mb-4">Total Alert Volume Trend</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Line type="monotone" dataKey="total" stroke="#dc2626" strokeWidth={3} dot={{ r: 5 }} name="Total Alerts" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Top Products */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
              <h3 className="font-semibold text-gray-800 mb-4">Most Affected Product Categories</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={topProductsData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#dc2626" radius={[4, 4, 0, 0]} name="Alerts" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Classification Method Performance */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
              <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-purple-600" />
                Classification Method Comparison
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                  <h4 className="font-medium text-purple-800 mb-2">LLM-Based Classification</h4>
                  <div className="space-y-2 text-sm text-gray-700">
                    <p>Alerts classified: <strong>{stats.llmClassified}</strong></p>
                    <p>Avg confidence: <strong>{Math.round(filteredAlerts.filter(a => a.classificationMethod === "llm").reduce((s, a) => s + a.confidence, 0) / Math.max(1, stats.llmClassified) * 100)}%</strong></p>
                    <p className="text-xs text-gray-500 mt-2">Uses semantic analysis for complex, multi-factor alerts where keyword matching is insufficient. Handles novel hazards and emerging risks.</p>
                  </div>
                </div>
                <div className="p-4 bg-cyan-50 rounded-lg border border-cyan-200">
                  <h4 className="font-medium text-cyan-800 mb-2">Rule-Based Classification</h4>
                  <div className="space-y-2 text-sm text-gray-700">
                    <p>Alerts classified: <strong>{stats.total - stats.llmClassified}</strong></p>
                    <p>Avg confidence: <strong>{Math.round(filteredAlerts.filter(a => a.classificationMethod === "rule_based").reduce((s, a) => s + a.confidence, 0) / Math.max(1, stats.total - stats.llmClassified) * 100)}%</strong></p>
                    <p className="text-xs text-gray-500 mt-2">Pattern-matched using regulatory keyword dictionaries. Fast, deterministic, and transparent. Ideal for well-known hazard patterns.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ===== SOURCES TAB ===== */}
        {activeTab === "sources" && (
          <div className="space-y-4">
            {/* Sources by Category */}
            {[
              { key: "recalls_alerts", title: "Recalls & Alerts", titleHe: "ריקולים והתראות", icon: AlertTriangle, color: "red" },
              { key: "investigations_morbidity", title: "Investigations & Morbidity Data", titleHe: "חקירות ונתוני תחלואה", icon: Activity, color: "orange" },
              { key: "regulation_risk", title: "Regulation & Risk Management", titleHe: "רגולציה וניהול סיכונים", icon: Shield, color: "blue" },
            ].map(cat => {
              const CatIcon = cat.icon;
              const catSources = SOURCES.filter(s => s.category === cat.key);
              return (
                <div key={cat.key} className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
                  <h3 className="font-semibold text-gray-800 mb-1 flex items-center gap-2">
                    <CatIcon className={`w-4 h-4 text-${cat.color}-600`} />
                    {cat.title}
                    <span className="text-xs font-normal text-gray-400">({cat.titleHe})</span>
                    <Badge variant="default">{catSources.length} sources</Badge>
                  </h3>
                  <div className="space-y-2 mt-3">
                    {catSources.map(source => (
                      <div key={source.id} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg border border-gray-100 hover:bg-gray-100 transition-colors">
                        <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${source.status === "active" ? "bg-green-500" : "bg-amber-500"}`} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-medium text-gray-800 text-sm">{source.name}</span>
                            <Badge variant={source.type === "api" ? "info" : source.type === "rss" ? "active" : source.type === "email" ? "llm" : "default"}>{source.type.toUpperCase()}</Badge>
                            <Badge variant="default">{source.region}</Badge>
                          </div>
                          <div className="flex gap-3 mt-1 flex-wrap">
                            <span className="text-xs text-gray-500">{source.contentType}</span>
                            <span className="text-xs text-gray-400">|</span>
                            <span className="text-xs text-gray-500">Push: {source.pushMethod}</span>
                          </div>
                        </div>
                        {/* Quality Ratings */}
                        <div className="flex gap-3 flex-shrink-0 text-center">
                          {[
                            { label: "Timely", val: source.ratings.timeliness },
                            { label: "Quality", val: source.ratings.quality },
                            { label: "Relevant", val: source.ratings.relevance },
                          ].map(r => (
                            <div key={r.label} className="flex flex-col items-center">
                              <span className="text-xs text-gray-400">{r.label}</span>
                              <div className="flex gap-0.5 mt-0.5">
                                {[1,2,3,4,5].map(i => (
                                  <Star key={i} className={`w-3 h-3 ${i <= r.val ? "text-yellow-400 fill-yellow-400" : "text-gray-200"}`} />
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                        <div className="text-end flex-shrink-0">
                          <div className="text-lg font-bold text-gray-700">{source.alertCount.toLocaleString("he-IL")}</div>
                          <div className="text-xs text-gray-400">alerts</div>
                        </div>
                        <a href={source.url} target="_blank" rel="noopener" className="text-gray-400 hover:text-red-600">
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}

            {/* Planned Category */}
            <div className="bg-white rounded-xl border border-gray-200 border-dashed p-5 shadow-sm opacity-70">
              <h3 className="font-semibold text-gray-500 mb-1 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-gray-400" />
                Innovations & Trends in Food Industry
                <span className="text-xs font-normal text-gray-400">(חידושים ומגמות בייצור, צריכה ותעשיית המזון)</span>
                <Badge variant="default">Planned</Badge>
              </h3>
              <p className="text-sm text-gray-400 mt-2">Sources for this category are pending identification. This will cover innovation trends in food production, consumption, and industry.</p>
            </div>

            {/* Source Coverage Summary */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
              <h3 className="font-semibold text-gray-800 mb-4">Coverage Summary</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { region: "USA", sources: SOURCES.filter(s => s.region === "USA"), coverage: "Comprehensive" },
                  { region: "Europe", sources: SOURCES.filter(s => s.region === "Europe"), coverage: "Strong" },
                  { region: "Global", sources: SOURCES.filter(s => s.region === "Global"), coverage: "Supplementary" },
                ].map(item => (
                  <div key={item.region} className="p-3 bg-gray-50 rounded-lg border border-gray-100">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium text-gray-800 text-sm">{item.region}</h4>
                      <Badge variant={item.coverage === "Comprehensive" ? "active" : item.coverage === "Strong" ? "info" : "default"}>
                        {item.coverage}
                      </Badge>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{item.sources.map(s => s.name.split(" - ")[0]).filter((v,i,a) => a.indexOf(v) === i).join(", ")}</p>
                    <div className="text-lg font-bold text-gray-700 mt-1">{item.sources.length} sources</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ===== METHODOLOGY TAB ===== */}
        {activeTab === "methodology" && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-800 mb-2 flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-red-600" />
                System Architecture & Methodology
              </h3>
              <p className="text-sm text-gray-600 mb-6">This tool addresses the research question: How can LLMs be used to collect, consolidate, classify, and rank information from heterogeneous sources for automatic identification of food safety alerts and trends?</p>

              {/* Pipeline Steps */}
              <div className="space-y-4">
                {[
                  {
                    step: 1, title: "Data Collection", icon: Database, color: "blue",
                    desc: "Automated ingestion from 12+ heterogeneous sources including regulatory databases (RASFF, FDA, FSIS, EFSA, FSANZ, CFIA, FSA UK), scientific advisories (BfR, ANSES), international networks (WHO INFOSAN), and news aggregators.",
                    details: "Methods: RSS feed parsing, REST API integration (FDA/FSIS APIs), scheduled web scraping with respect for robots.txt, structured data extraction from HTML/XML. Sources are polled at configurable intervals (15 min to 24 hr)."
                  },
                  {
                    step: 2, title: "Consolidation & Deduplication", icon: Filter, color: "purple",
                    desc: "Raw alerts from multiple sources are normalized into a unified schema, deduplicated using fuzzy matching (TF-IDF + cosine similarity), and enriched with metadata.",
                    details: "Entity resolution links the same incident across sources (e.g., a RASFF notification and an FDA recall for the same product). Temporal alignment ensures events are properly sequenced."
                  },
                  {
                    step: 3, title: "Classification (Hybrid)", icon: Cpu, color: "green",
                    desc: "Two-tier classification pipeline: Rule-based for well-known patterns, LLM-based for complex/novel hazards.",
                    details: "Rule-based: Keyword dictionaries + regex patterns for known hazard types (Salmonella, Listeria, allergen terms, etc.). LLM-based: Semantic classification using transformer models for ambiguous text, novel hazards, or multi-factor incidents. The system routes alerts based on initial keyword confidence. Based on research by Springer (2025) on AI-driven risk assessment using RASFF data, transformer models like BERT/RoBERTa achieve 97.8-97.9% accuracy."
                  },
                  {
                    step: 4, title: "Risk Scoring & Ranking", icon: AlertTriangle, color: "red",
                    desc: "Multi-factor risk scoring matrix based on WHO/FAO frameworks: severity, likelihood, population exposure, vulnerable populations, and spread potential.",
                    details: "Risk Score = w1*Severity + w2*Likelihood + w3*Exposure + w4*Vulnerability + w5*SpreadPotential. Weights calibrated from RASFF historical data. Scores mapped to 4-tier system: Critical (9-10), High (7-8), Medium (4-6), Low (1-3). Inspired by the FAO food safety risk assessment framework and the PMC risk classification matrix for AI-supported risk identification."
                  },
                  {
                    step: 5, title: "Trend Detection", icon: TrendingUp, color: "orange",
                    desc: "Time-series analysis to identify emerging patterns, seasonal variations, and anomalous spikes in specific hazard-product-country combinations.",
                    details: "Statistical methods: Moving averages, Z-score anomaly detection, seasonal decomposition. LLM summarization of emerging trends for executive briefings. Cross-referencing geographic spread patterns with trade data."
                  },
                  {
                    step: 6, title: "Explainable Outputs", icon: Eye, color: "indigo",
                    desc: "Following interpretable AI principles (Cynthia Rudin, 2022), all classifications include confidence scores and explanation of the reasoning chain.",
                    details: "Every alert shows: classification method used (LLM vs. rule-based), confidence percentage, key factors driving the risk score, and source provenance. This transparency enables human analysts to verify and override automated decisions."
                  },
                ].map(item => {
                  const Icon = item.icon;
                  return (
                    <div key={item.step} className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <div className={`w-10 h-10 rounded-full bg-${item.color}-100 flex items-center justify-center flex-shrink-0`} style={{ backgroundColor: `var(--${item.color}, #e5e7eb)` }}>
                          <span className="text-sm font-bold text-gray-700">{item.step}</span>
                        </div>
                        {item.step < 6 && <div className="w-0.5 h-full bg-gray-200 mt-1" />}
                      </div>
                      <div className="pb-6 flex-1">
                        <h4 className="font-semibold text-gray-800 flex items-center gap-2">
                          <Icon className="w-4 h-4 text-gray-500" />
                          {item.title}
                        </h4>
                        <p className="text-sm text-gray-700 mt-1">{item.desc}</p>
                        <p className="text-xs text-gray-500 mt-2 p-3 bg-gray-50 rounded-lg border border-gray-100">{item.details}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Research References */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h3 className="font-semibold text-gray-800 mb-4">Research Foundations & References</h3>
              <div className="space-y-3">
                {[
                  { title: "AI-Driven Risk Assessment in Food Safety Using EU RASFF Database", source: "Springer, Food and Bioprocess Technology, 2025", relevance: "Transformer models (BERT/RoBERTa) for RASFF alert classification with 97.9% accuracy" },
                  { title: "LLM-based Classification of Requirements in Food-Safety Regulations", source: "arXiv / Empirical Software Engineering, 2025", relevance: "Framework for using LLMs to classify food safety regulatory provisions" },
                  { title: "Risk Classification of Food Incidents Using AI-Supported Risk Identification", source: "PMC, 2024", relevance: "Risk evaluation matrix framework adapted for AI-based food incident classification" },
                  { title: "FAO Food Safety Risk Assessment Framework", source: "FAO/WHO, OpenKnowledge", relevance: "International standards for food safety risk scoring methodology" },
                  { title: "Interpretable Machine Learning for Decision Support Systems", source: "Cynthia Rudin, 2022", relevance: "Principles for transparent, explainable AI in critical decision systems" },
                  { title: "Multimodal LLMs for Food Safety Detection", source: "ScienceDirect, 2026", relevance: "Review of multi-source data fusion for food safety applications" },
                ].map((ref, i) => (
                  <div key={i} className="p-3 bg-gray-50 rounded-lg border border-gray-100">
                    <p className="text-sm font-medium text-gray-800">{ref.title}</p>
                    <p className="text-xs text-gray-500">{ref.source}</p>
                    <p className="text-xs text-blue-600 mt-1">Relevance: {ref.relevance}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white mt-8">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="text-xs text-gray-400">
            FoodSafe Intelligence v1.0 | Israel Health Security Department | Hybrid AI Classification Engine
          </div>
          <div className="flex items-center gap-4 text-xs text-gray-400">
            <span>Sources: {SOURCES.length} active</span>
            <span>Pipeline: Collection + Classification</span>
            <span>Method: Rule-Based + LLM Hybrid</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
