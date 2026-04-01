"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Shield,
  LayoutDashboard,
  Crosshair,
  Swords,
} from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/techniques", label: "Technique Catalog", icon: Crosshair },
  { href: "/campaign", label: "Campaign", icon: Swords },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-60 flex-col border-r"
      style={{
        backgroundColor: "var(--bg-secondary)",
        borderColor: "var(--border-color)",
      }}
    >
      <div className="flex items-center gap-3 px-5 py-6 border-b"
        style={{ borderColor: "var(--border-color)" }}
      >
        <Shield className="h-7 w-7" style={{ color: "var(--accent)" }} />
        <div>
          <h1 className="text-sm font-bold tracking-wide"
            style={{ color: "var(--text-primary)" }}
          >
            Adversary Planner
          </h1>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            LLM Red Team Engine
          </p>
        </div>
      </div>

      <nav className="flex-1 py-4">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className="flex items-center gap-3 px-5 py-2.5 text-sm transition-colors"
              style={{
                color: active ? "var(--accent)" : "var(--text-secondary)",
                backgroundColor: active ? "var(--accent-dim)" : "transparent",
                borderRight: active ? "2px solid var(--accent)" : "2px solid transparent",
              }}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="px-5 py-4 border-t text-xs"
        style={{
          borderColor: "var(--border-color)",
          color: "var(--text-muted)",
        }}
      >
        v0.1.0 &middot; Powered by garak
      </div>
    </aside>
  );
}
