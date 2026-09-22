import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";
import type { Skill } from "../types/api";

export default function SkillRadar({ skills }: { skills: Skill[] }) {
  const data = skills.map((s) => ({
    subject: s.name,
    level: Math.round(s.level * 100),
  }));

  if (data.length < 3) {
    return (
      <div className="flex items-center justify-center h-64 text-sm text-muted font-mono border border-dashed border-rule rounded-lg">
        Add at least 3 skills to see the radar.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <RadarChart data={data}>
        <PolarGrid stroke="var(--color-rule)" />
        <PolarAngleAxis
          dataKey="subject"
          tick={{ fill: "var(--color-muted)", fontSize: 11, fontFamily: "IBM Plex Mono, monospace" }}
        />
        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
        <Radar
          dataKey="level"
          stroke="var(--color-teal)"
          fill="var(--color-teal)"
          fillOpacity={0.25}
          strokeWidth={2}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
