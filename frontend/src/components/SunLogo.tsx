interface Props {
  size?: number;
}

const RAYS = [0, 45, 90, 135, 180, 225, 270, 315];

export default function SunLogo({ size = 22 }: Props) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      aria-label="Solarbitrage logo"
    >
      {/* Rotating rays */}
      <g
        className="animate-sun-spin"
        style={{ transformOrigin: "12px 12px" }}
      >
        {RAYS.map((angle) => (
          <line
            key={angle}
            x1="12" y1="1"
            x2="12" y2="5"
            stroke="#f57c00"
            strokeWidth="1.6"
            strokeLinecap="round"
            transform={`rotate(${angle} 12 12)`}
          />
        ))}
      </g>

      {/* Pulsing center disk */}
      <circle
        cx="12"
        cy="12"
        r="4.5"
        fill="#f57c00"
        className="animate-sun-pulse"
      />

      {/* Inner highlight */}
      <circle
        cx="10.5"
        cy="10.5"
        r="1.2"
        fill="#ffd600"
        opacity="0.45"
        className="animate-sun-pulse"
      />
    </svg>
  );
}
