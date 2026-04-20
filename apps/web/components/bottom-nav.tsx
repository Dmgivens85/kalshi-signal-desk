"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  { href: "/", label: "Feed", icon: "●" },
  { href: "/paper", label: "Paper", icon: "◍" },
  { href: "/automation", label: "Auto", icon: "◐" },
  { href: "/approvals", label: "Approvals", icon: "◆" },
  { href: "/positions", label: "Positions", icon: "◌" },
  { href: "/risk", label: "Risk", icon: "▲" }
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="bottom-nav" aria-label="Primary">
      {items.map((item) => {
        const isActive =
          item.href === "/" ? pathname === "/" : pathname === item.href || pathname.startsWith(`${item.href}/`);
        return (
          <Link className={`bottom-link${isActive ? " is-active" : ""}`} href={item.href} key={item.href}>
            <span aria-hidden="true">{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
