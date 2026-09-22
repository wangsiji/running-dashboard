import { Component, type ErrorInfo, type ReactNode } from 'react';
import { resetActivityData } from '../core/hooks/useActivities';

interface Props {
  children: ReactNode;
  /** 出错时的标题文案；默认沿用数据加载失败的说法 */
  title?: string;
  /** 局部失败（例如地图）用紧凑样式，不占满整屏 */
  compact?: boolean;
}
interface State {
  hasError: boolean;
  message: string;
}

/**
 * Catches render-time errors thrown by descendants (e.g. the Suspense data
 * source throwing a fetch error instead of a promise) so a failed
 * activities.json load degrades gracefully instead of blanking the page.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: '' };

  static getDerivedStateFromError(error: unknown): State {
    return {
      hasError: true,
      message: error instanceof Error ? error.message : String(error),
    };
  }

  componentDidCatch(error: unknown, _info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error);
  }

  private handleRetry = () => {
    resetActivityData();
    this.setState({ hasError: false, message: '' });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          className={`flex flex-col items-center justify-center gap-3 ${
            this.props.compact
              ? 'min-h-[16rem] rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] p-6'
              : 'min-h-screen'
          }`}
          style={{
            backgroundColor: 'var(--color-bg, #0d1117)',
            color: 'var(--color-muted, #8b949e)',
          }}
        >
          <p
            className="text-base font-medium"
            style={{ color: 'var(--color-text, #e6edf3)' }}
          >
            {this.props.title ?? 'Failed to load activities'}
          </p>
          <p className="text-xs">{this.state.message}</p>
          <button
            type="button"
            onClick={this.handleRetry}
            className="mt-1 rounded-md px-4 py-1.5 text-sm font-medium text-white"
            style={{
              backgroundColor: 'var(--color-accent, #0c4a6e)',
              color: 'var(--color-on-accent, #ffffff)',
            }}
          >
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
