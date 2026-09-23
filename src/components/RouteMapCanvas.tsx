import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import * as polyline from '@mapbox/polyline';
import type { Activity } from '../core/types';
import { MAPBOX_TOKEN } from '../core/config';
import { useLocale } from '../core/hooks/useLocale';
import './RouteMap.css';

// mapbox-gl v3 默认 REQUIRE_ACCESS_TOKEN=true：没配 token 时（用 CARTO 免费底图）
// 连第三方样式的请求都会抛错，地图永远加载不出来。这里关掉该校验。
if (!MAPBOX_TOKEN) mapboxgl.config.REQUIRE_ACCESS_TOKEN = false;

export interface RouteMapProps {
  activities: Activity[];
  selectedActivity?: Activity | null;
  dark?: boolean;
  onClearSelection?: () => void;
}

const routeCache = new WeakMap<
  Activity,
  {
    type: 'Feature';
    properties: { type: string };
    geometry: { type: 'LineString'; coordinates: number[][] };
  }[]
>();

export function RouteMapCanvas({
  activities,
  selectedActivity,
  dark,
  onClearSelection,
}: RouteMapProps) {
  const { locale } = useLocale();
  const zh = locale === 'zh';
  const panelRef = useRef<HTMLElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const styleReadyRef = useRef(false);
  const cameraRef = useRef<mapboxgl.CameraOptions | null>(null);
  const fittedRef = useRef<unknown>(null);
  const [provider, setProvider] = useState(MAPBOX_TOKEN ? 'mapbox' : 'carto');
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>(
    'loading'
  );
  const [retry, setRetry] = useState(0);
  const style =
    provider === 'mapbox'
      ? `mapbox://styles/mapbox/${dark === false ? 'light' : 'dark'}-v11`
      : `https://basemaps.cartocdn.com/gl/${dark === false ? 'positron' : 'dark-matter'}-gl-style/style.json`;

  const routes = useMemo(() => {
    const items = selectedActivity ? [selectedActivity] : activities;
    return items.flatMap((activity) => {
      const cached = routeCache.get(activity);
      if (cached) return cached;
      if (!activity.summary_polyline) return [];
      try {
        const coordinates = polyline
          .decode(activity.summary_polyline)
          .map(([lat, lng]) => [lng, lat])
          .filter(
            ([lng, lat]) =>
              Number.isFinite(lng) &&
              Number.isFinite(lat) &&
              Math.abs(lng) <= 180 &&
              Math.abs(lat) <= 90
          );
        if (coordinates.length < 2) return [];
        const features = [
          {
            type: 'Feature' as const,
            properties: { type: activity.type },
            geometry: { type: 'LineString' as const, coordinates },
          },
        ];
        routeCache.set(activity, features);
        return features;
      } catch {
        return [];
      }
    });
  }, [activities, selectedActivity]);

  const routeBounds = useMemo(() => {
    const bounds = new mapboxgl.LngLatBounds();
    for (const route of routes) {
      for (const coord of route.geometry.coordinates)
        bounds.extend(coord as [number, number]);
    }
    return bounds;
  }, [routes]);

  const fitRoutes = useCallback(() => {
    const map = mapRef.current;
    if (!map || routeBounds.isEmpty()) return;
    map.fitBounds(routeBounds, {
      padding: { top: 35, bottom: 35, left: 35, right: 65 },
      maxZoom: selectedActivity ? 16 : 13,
      duration: window.matchMedia('(prefers-reduced-motion: reduce)').matches
        ? 0
        : 500,
    });
  }, [routeBounds, selectedActivity]);

  const drawRoutes = useCallback(() => {
    const map = mapRef.current;
    if (!map || !styleReadyRef.current) return;
    const data = { type: 'FeatureCollection' as const, features: routes };
    const source = map.getSource('routes') as
      mapboxgl.GeoJSONSource | undefined;
    if (source) source.setData(data);
    else {
      map.addSource('routes', { type: 'geojson', data });
      map.addLayer({
        id: 'routes',
        type: 'line',
        source: 'routes',
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: {
          'line-color': [
            'match',
            ['get', 'type'],
            'Run',
            '#f97316',
            'Ride',
            '#3b82f6',
            '#4dd2ff',
          ],
        },
      });
    }
    map.setPaintProperty('routes', 'line-width', selectedActivity ? 3.5 : 2);
    map.setPaintProperty('routes', 'line-opacity', selectedActivity ? 1 : 0.7);
    if (fittedRef.current !== routes) {
      fittedRef.current = routes;
      fitRoutes();
    }
  }, [routes, selectedActivity, fitRoutes]);

  useEffect(() => {
    if (!containerRef.current || !panelRef.current) return;
    // CARTO 官方 style 引用了 3 个已从 tiles.basemaps.cartocdn.com 下架的字体
    // （HanWangHeiLight / NanumBarunGothic / Montserrat *Italic），500 时 fetch 直接
    // 404 → mapbox 抛 error 且标注文字渲染不出来。这里在 transformRequest 里把失效
    // 字体改写为等效的现有字体，一行修掉全部 27 个文字图层，无需改 style。
    const FONT_FIX = new Map<string, string>([
      ['HanWangHeiLight%20Regular', 'Noto%20Sans%20Regular'],
      ['NanumBarunGothic%20Regular', 'Noto%20Sans%20Regular'],
      ['Montserrat%20Regular%20Italic', 'Open%20Sans%20Italic'],
      ['Montserrat%20Medium%20Italic', 'Open%20Sans%20Italic'],
    ]);
    const map = new mapboxgl.Map({
      container: containerRef.current,
      accessToken: MAPBOX_TOKEN,
      language: zh ? 'zh-Hans' : 'en',
      transformRequest: (url, resourceType) => {
        if (resourceType === 'Glyphs') {
          for (const [bad, good] of FONT_FIX) {
            if (url.includes(bad)) url = url.replace(bad, good);
          }
        }
        return { url };
      },
      style: { version: 8, sources: {}, layers: [] },
      center: [121.4, 31.2],
      zoom: 10,
      ...cameraRef.current,
      locale: zh
        ? {
            'Map.Title': '跑步路线地图',
            'NavigationControl.ZoomIn': '放大',
            'NavigationControl.ZoomOut': '缩小',
            'NavigationControl.ResetBearing': '恢复朝北',
            'FullscreenControl.Enter': '全屏查看',
            'FullscreenControl.Exit': '退出全屏',
            'AttributionControl.ToggleAttribution': '地图来源',
          }
        : {},
    });
    mapRef.current = map;
    map.addControl(new mapboxgl.NavigationControl(), 'top-right');
    map.addControl(
      new mapboxgl.FullscreenControl({ container: panelRef.current }),
      'top-right'
    );
    map.addControl(
      new mapboxgl.ScaleControl({ unit: 'metric', maxWidth: 90 }),
      'bottom-left'
    );
    const observer = new ResizeObserver(() => map.resize());
    observer.observe(containerRef.current);
    return () => {
      cameraRef.current = {
        center: map.getCenter(),
        zoom: map.getZoom(),
        bearing: map.getBearing(),
        pitch: map.getPitch(),
      };
      observer.disconnect();
      map.remove();
      mapRef.current = null;
    };
  }, [zh]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const onError = (event: mapboxgl.ErrorEvent) => {
      const code = (event.error as Error & { status?: number }).status;
      if (provider === 'mapbox' && (code === 401 || code === 403)) {
        setProvider('carto');
      }
      // 其它错误（个别瓦片/雪碧图 404）不当作底图失败：mapbox-gl 对这些也发 error 事件，
      // 一律标红会把能用的地图误报成「加载失败」。真正失败由下面的超时兜底。
    };
    const onIdle = () => {
      if (styleReadyRef.current) setStatus('ready');
    };
    const onLoading = () => setStatus('loading');
    map.on('error', onError);
    map.on('idle', onIdle);
    map.once('styledataloading', onLoading);
    styleReadyRef.current = false;
    map.setStyle(style, {
      diff: false,
      localFontFamily: undefined,
      localIdeographFontFamily: 'sans-serif',
    });
    // 用 styleReadyRef 而不是 isStyleLoaded()：后者还要等所有瓦片源就绪，
    // 慢网络下必然超过 15 秒 → 误报。这里只判「样式表本身有没有 load 过」。
    const timer = window.setTimeout(() => {
      if (!styleReadyRef.current) setStatus('error');
    }, 20000);
    return () => {
      window.clearTimeout(timer);
      map.off('error', onError);
      map.off('idle', onIdle);
      map.off('styledataloading', onLoading);
    };
  }, [style, provider, retry, zh]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const onStyleLoad = () => {
      styleReadyRef.current = true;
      drawRoutes();
    };
    map.on('style.load', onStyleLoad);
    drawRoutes();
    return () => {
      map.off('style.load', onStyleLoad);
    };
  }, [drawRoutes, style, retry, zh]);

  useEffect(() => {
    let wasFullscreen = document.fullscreenElement === panelRef.current;
    let frame = 0;
    const onFullscreen = () => {
      const isFullscreen = document.fullscreenElement === panelRef.current;
      if (isFullscreen || wasFullscreen) {
        cancelAnimationFrame(frame);
        frame = requestAnimationFrame(() => {
          mapRef.current?.resize();
          fitRoutes();
        });
      }
      wasFullscreen = isFullscreen;
    };
    document.addEventListener('fullscreenchange', onFullscreen);
    return () => {
      cancelAnimationFrame(frame);
      document.removeEventListener('fullscreenchange', onFullscreen);
    };
  }, [fitRoutes]);

  return (
    <section
      ref={panelRef}
      className="route-map"
      aria-label={zh ? '路线地图' : 'Route map'}
    >
      <div className="route-map-header">
        <div className="min-w-0">
          <h2 className="text-base font-semibold">
            {zh ? '路线地图' : 'Route map'}
          </h2>
          <p
            className="truncate text-xs text-[var(--color-muted)]"
            title={selectedActivity?.name}
          >
            {selectedActivity
              ? `${selectedActivity.name} · ${(selectedActivity.distance / 1000).toFixed(1)} km`
              : `${routes.length.toLocaleString()} ${zh ? '条轨迹' : 'routes'}`}
          </p>
        </div>
        <div className="flex shrink-0 gap-2">
          {selectedActivity && onClearSelection && (
            <button className="route-map-action" onClick={onClearSelection}>
              {zh ? '返回总览' : 'Overview'}
            </button>
          )}
          <button
            className="route-map-action"
            disabled={!routes.length}
            onClick={fitRoutes}
            title={zh ? '将所有当前轨迹完整放入视野' : 'Fit all current routes'}
          >
            {zh ? '定位轨迹' : 'Fit routes'}
          </button>
        </div>
      </div>
      <div className="route-map-body">
        <div ref={containerRef} className="h-full w-full" />
        {!routes.length && (
          <div className="route-map-empty" role="status">
            {zh
              ? selectedActivity
                ? '这次活动没有 GPS 轨迹'
                : '当前筛选没有 GPS 轨迹'
              : 'No GPS route available'}
          </div>
        )}
      </div>
      <div className="route-map-footer">
        <span role="status" aria-live="polite">
          {status === 'error'
            ? zh
              ? '底图加载失败，请重试'
              : 'Basemap failed to load'
            : status === 'loading'
              ? zh
                ? '正在加载地图…'
                : 'Loading map…'
              : provider === 'carto'
                ? zh
                  ? '备用底图 · CARTO'
                  : 'Alternative basemap · CARTO'
                : zh
                  ? '底图 · Mapbox'
                  : 'Basemap · Mapbox'}
        </span>
        {(status === 'error' || (provider === 'carto' && !!MAPBOX_TOKEN)) && (
          <button
            className="route-map-action"
            onClick={() => {
              setProvider(MAPBOX_TOKEN ? 'mapbox' : 'carto');
              setRetry((value) => value + 1);
            }}
          >
            {provider === 'carto' && MAPBOX_TOKEN
              ? zh
                ? '重试 Mapbox'
                : 'Retry Mapbox'
              : zh
                ? '重试'
                : 'Retry'}
          </button>
        )}
      </div>
    </section>
  );
}
