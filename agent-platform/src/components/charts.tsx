"use client";
import {
  Area, AreaChart, Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid, Cell,
} from "recharts";
import { TREND, CATEGORY_PERF } from "@/lib/data";

const tip = {
  contentStyle: {
    background: "var(--bg-elev)", border: "1px solid var(--border)",
    borderRadius: 12, fontSize: 12, color: "var(--fg)",
  },
  labelStyle: { color: "var(--muted)" },
};

export function TrendChart() {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={TREND} margin={{ left: -20, right: 8, top: 8 }}>
        <defs>
          <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.5} />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="g2" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent-3)" stopOpacity={0.4} />
            <stop offset="100%" stopColor="var(--accent-3)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
        <XAxis dataKey="month" stroke="var(--muted)" fontSize={12} tickLine={false} axisLine={false} />
        <YAxis stroke="var(--muted)" fontSize={12} tickLine={false} axisLine={false} />
        <Tooltip {...tip} />
        <Area type="monotone" dataKey="evaluations" stroke="var(--accent)" strokeWidth={2} fill="url(#g1)" />
        <Area type="monotone" dataKey="success" stroke="var(--accent-3)" strokeWidth={2} fill="url(#g2)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function CategoryChart() {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={CATEGORY_PERF} margin={{ left: -20, right: 8, top: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
        <XAxis dataKey="category" stroke="var(--muted)" fontSize={10} tickLine={false} axisLine={false} interval={0} angle={-25} textAnchor="end" height={56} />
        <YAxis stroke="var(--muted)" fontSize={12} tickLine={false} axisLine={false} domain={[0, 100]} />
        <Tooltip {...tip} cursor={{ fill: "var(--fg)", opacity: 0.04 }} />
        <Bar dataKey="score" radius={[6, 6, 0, 0]}>
          {CATEGORY_PERF.map((_, i) => (
            <Cell key={i} fill={i % 2 ? "var(--accent-2)" : "var(--accent)"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
