import { memo } from 'react';
import type { Activity } from '../core/types';
import { useLocale } from '../core/hooks/useLocale';

interface PersonalBestProps {
  activities: Activity[];
  onSelectActivity?: (a: Activity | null) => void;
}

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0)
    return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  return `${m}:${String(s).padStart(2, '0')}`;
}

// start_date_local 形如 "2026-05-31 06:57:19"，只取日期部分。
function formatDate(d: string): string {
  return d.slice(0, 10);
}

// 距离窗口贴着真实比赛距离（含 GPS 误差余量）。放宽会让训练跑混进来：
// 例如 20.00km 的日常跑不该被算成半马 PB。
const DISTANCES = [
  { key: '5k', zh: '5公里', en: '5K' },
  { key: '10k', zh: '10公里', en: '10K' },
  { key: 'half', zh: '半程马拉松', en: 'Half Marathon' },
  { key: 'marathon', zh: '全程马拉松', en: 'Marathon' },
] as const;

export const PersonalBest = memo(function PersonalBest({
  activities,
  onSelectActivity,
}: PersonalBestProps) {
  const { locale } = useLocale();

  // 按高驰口径取「最好分段」：成绩由 sync 从 FIT 逐点记录算好放进 best_efforts。
  // 这样马拉松里跑出的最快 21.0975km 会算作半马成绩，和手表 App 显示一致。
  const bests = DISTANCES.map(({ key }) => {
    let pick: { activity: Activity; time: number } | null = null;
    for (const a of activities) {
      const t = a.best_efforts?.[key];
      if (t && (!pick || t < pick.time)) pick = { activity: a, time: t };
    }
    return { key, activity: pick?.activity ?? null, time: pick?.time ?? 0 };
  });

  const hasBests = bests.some((b) => b.activity !== null);
  if (!hasBests) return null;

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] px-4 py-3 hover:border-[var(--color-accent)]/30 hover:bg-[var(--color-accent)]/5 hover:shadow-[var(--color-accent)]/5 hover:shadow-lg">
      <h3 className="mb-2 flex items-center gap-1.5 text-sm font-semibold">
        <svg
          className="h-4 w-4 text-[var(--color-accent)]"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
          />
        </svg>
        {locale === 'zh' ? '个人最佳' : 'Personal Best'}
      </h3>

      <div className="divide-y divide-[var(--color-border)]">
        {bests.map(({ key, activity, time }) => (
          <button
            type="button"
            disabled={!activity || !onSelectActivity}
            key={key}
            className={`flex w-full items-center justify-between gap-3 py-2 text-left ${
              activity
                ? '-mx-2 cursor-pointer rounded-lg px-2 transition-colors hover:bg-[var(--color-bg)]'
                : ''
            }`}
            onClick={() => activity && onSelectActivity?.(activity)}
          >
            <span className="text-xs text-[var(--color-text)]">
              {locale === 'zh'
                ? DISTANCES.find((d) => d.key === key)?.zh
                : DISTANCES.find((d) => d.key === key)?.en}
              {activity && (
                <span className="block text-[10px] leading-tight text-[var(--color-muted)]">
                  {formatDate(activity.start_date_local)}
                </span>
              )}
            </span>
            <span
              className={`font-mono text-xs font-bold ${activity ? 'text-[var(--color-accent)]' : 'text-[var(--color-muted)]'}`}
            >
              {activity ? formatTime(time) : '--'}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
});
