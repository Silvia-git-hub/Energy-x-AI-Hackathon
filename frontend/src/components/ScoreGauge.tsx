interface Props {
  score: number;
  label: string;
  size?: number;
}

function scoreColor(score: number): string {
  if (score >= 75) return "#00c853";
  if (score >= 50) return "#f57c00";
  if (score >= 25) return "#ffd600";
  return "#ff1744";
}

export default function ScoreGauge({ score, label, size = 140 }: Props) {
  const r = (size / 2) * 0.78;
  const cx = size / 2;
  const cy = size / 2;
  const strokeWidth = size * 0.09;
  const startAngle = -210;
  const endAngle = 30;
  const totalArc = endAngle - startAngle;
  const filledArc = (score / 100) * totalArc;
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const arcPath = (start: number, end: number) => {
    const s = { x: cx + r * Math.cos(toRad(start)), y: cy + r * Math.sin(toRad(start)) };
    const e = { x: cx + r * Math.cos(toRad(end)), y: cy + r * Math.sin(toRad(end)) };
    const largeArc = end - start > 180 ? 1 : 0;
    return `M ${s.x} ${s.y} A ${r} ${r} 0 ${largeArc} 1 ${e.x} ${e.y}`;
  };
  const color = scoreColor(score);

  return (
    <div className="bg-term-panel border border-term-border rounded p-3 flex flex-col items-center">
      <svg width={size} height={size * 0.82} viewBox={`0 0 ${size} ${size}`}>
        <path d={arcPath(startAngle, endAngle)} fill="none" stroke="#1c1c1c" strokeWidth={strokeWidth} strokeLinecap="round" />
        {score > 0 && (
          <path d={arcPath(startAngle, startAngle + filledArc)} fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" />
        )}
        <text x={cx} y={cy + 8} textAnchor="middle" fontSize={size * 0.22} fontWeight="700" fill={color} fontFamily="monospace">
          {Math.round(score)}
        </text>
        <text x={cx} y={cy + size * 0.18} textAnchor="middle" fontSize={size * 0.08} fill="#555" fontFamily="monospace">
          / 100
        </text>
      </svg>
      <p className="text-[10px] font-mono text-term-muted tracking-widest mt-1">{label.toUpperCase()}</p>
    </div>
  );
}
