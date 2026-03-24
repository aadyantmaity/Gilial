import {
  LayoutDashboard,
  Database,
  Layers,
  Settings,
  Activity,
  Zap,
  HardDrive,
  Brain,
  Archive,
  RefreshCw,
  Search,
} from "lucide-react";
import styles from "./dashboard.module.css";

const navItems = [
  { label: "Overview", icon: LayoutDashboard, active: true },
  { label: "Memory Layers", icon: Layers },
  { label: "Compression", icon: Zap },
  { label: "Databases", icon: Database },
  { label: "Activity", icon: Activity },
  { label: "Settings", icon: Settings },
];

const stats = [
  { label: "Total Memories", value: "12,847", meta: "+342 this week" },
  { label: "Compression Ratio", value: "3.2x", meta: "Avg across layers" },
  { label: "Active Layers", value: "5", meta: "2 pending merge" },
  { label: "Storage Used", value: "1.8 GB", meta: "of 10 GB allocated" },
];

const activities = [
  { text: "Compression cycle completed on Layer 3", time: "2 min ago", active: true },
  { text: "Merged 47 similar memories in semantic cluster", time: "15 min ago", active: true },
  { text: "Low-value pruning removed 12 entries", time: "1 hour ago", active: false },
  { text: "New memory layer created: project-context", time: "3 hours ago", active: false },
  { text: "Pinecone sync completed successfully", time: "5 hours ago", active: false },
];

const layers = [
  { name: "Short-term", desc: "Recent conversation context", icon: Brain, count: "2,341", size: "180 MB" },
  { name: "Long-term", desc: "Persistent knowledge base", icon: HardDrive, count: "8,102", size: "1.2 GB" },
  { name: "Compressed", desc: "Merged & summarized clusters", icon: Archive, count: "2,404", size: "320 MB" },
];

export default function DashboardPage() {
  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <div className={styles.sidebarHeader}>
          <span className={styles.logo}>
            Gilial <span className={styles.logoAccent}>Dashboard</span>
          </span>
        </div>
        <nav className={styles.sidebarNav}>
          {navItems.map((item) => (
            <a
              key={item.label}
              className={item.active ? styles.navItemActive : styles.navItem}
              href="#"
            >
              <item.icon className={styles.navIcon} />
              {item.label}
            </a>
          ))}
        </nav>
        <div className={styles.sidebarFooter}>
          Gilial v0.1.0
        </div>
      </aside>

      <div className={styles.main}>
        <header className={styles.header}>
          <h1 className={styles.headerTitle}>Overview</h1>
          <div className={styles.headerActions}>
            <button className={styles.headerBtn}>
              <Search size={14} />
              Search memories
            </button>
            <button className={styles.headerBtn}>
              <RefreshCw size={14} />
              Sync
            </button>
          </div>
        </header>

        <main className={styles.content}>
          <div className={styles.statsGrid}>
            {stats.map((stat) => (
              <div key={stat.label} className={styles.statCard}>
                <div className={styles.statLabel}>{stat.label}</div>
                <div className={styles.statValue}>{stat.value}</div>
                <div className={styles.statMeta}>{stat.meta}</div>
              </div>
            ))}
          </div>

          <div className={styles.panelsGrid}>
            <div className={styles.panel}>
              <div className={styles.panelHeader}>
                <h2 className={styles.panelTitle}>Recent Activity</h2>
                <span className={styles.badge}>Live</span>
              </div>
              <div className={styles.activityList}>
                {activities.map((item, i) => (
                  <div key={i} className={styles.activityItem}>
                    <div className={item.active ? styles.activityDot : styles.activityDotMuted} />
                    <div>
                      <div className={styles.activityText}>{item.text}</div>
                      <div className={styles.activityTime}>{item.time}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className={styles.panel}>
              <div className={styles.panelHeader}>
                <h2 className={styles.panelTitle}>Memory Layers</h2>
                <span className={styles.badge}>3 Active</span>
              </div>
              <div className={styles.layersList}>
                {layers.map((layer) => (
                  <div key={layer.name} className={styles.layerRow}>
                    <div className={styles.layerInfo}>
                      <div className={styles.layerIcon}>
                        <layer.icon />
                      </div>
                      <div>
                        <div className={styles.layerName}>{layer.name}</div>
                        <div className={styles.layerDesc}>{layer.desc}</div>
                      </div>
                    </div>
                    <div className={styles.layerMeta}>
                      <div className={styles.layerCount}>{layer.count}</div>
                      <div className={styles.layerSize}>{layer.size}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
