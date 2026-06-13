import SubScoreCard from "./SubScoreCard";
import type { SubScoreData } from "@/types";

interface Props {
  subScores: Record<string, SubScoreData>;
  weightsUsed: Record<string, number>;
}

export default function SubScorePanel({ subScores, weightsUsed }: Props) {
  return (
    <div className="space-y-3">
      {Object.entries(subScores).map(([key, data]) => (
        <SubScoreCard
          key={key}
          sourceKey={key}
          data={data}
          weight={weightsUsed[key] ?? 0}
        />
      ))}
    </div>
  );
}
