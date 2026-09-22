import { createContext, use, useState, useCallback } from 'react';
import type { ReactNode } from 'react';
import { messages, type Locale } from '../i18n';
import { DEFAULT_LOCALE } from '../config';

interface LocaleContextValue {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string) => string;
}

const LocaleContext = createContext<LocaleContextValue>({
  locale: 'zh',
  setLocale: () => {},
  t: (key) => key,
});

export function LocaleProvider({ children }: { children: ReactNode }) {
  // 不读 localStorage：同域名下的旧站存过 'locale'，会把这里的默认值一直盖掉，
  // 而界面里并没有语言切换入口。默认语言只认 config.yml 的 locale。
  const [locale, setLocale] = useState<Locale>(DEFAULT_LOCALE);

  const updateLocale = useCallback((l: Locale) => setLocale(l), []);

  const t = useCallback(
    (key: string) => {
      return messages[locale][key] || key;
    },
    [locale]
  );

  return (
    <LocaleContext value={{ locale, setLocale: updateLocale, t }}>
      {children}
    </LocaleContext>
  );
}

export function useLocale() {
  return use(LocaleContext);
}
