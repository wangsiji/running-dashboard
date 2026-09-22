export interface Activity {
  run_id: number;
  name: string;
  distance: number; // meters
  moving_time: string; // "H:MM:SS"
  type: 'Run' | string;
  subtype?: string;
  start_date: string;
  start_date_local: string;
  location_country: string | null;
  summary_polyline: string | null;
  average_heartrate: number | null;
  average_speed: number; // m/s
  elevation_gain: number | null;
  source: string;
  streak: number;
  /** 最好分段成绩（秒）：高驰口径，马拉松里跑出的最快半马也算半马成绩 */
  best_efforts?: Partial<
    Record<'5k' | '10k' | 'half' | 'marathon', number>
  > | null;
}

export type SportFilter = 'all' | 'Run';
