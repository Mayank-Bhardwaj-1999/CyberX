import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { storage } from '../services/storage';

export type ReaderMode = 'webview' | 'reader' | 'customTab' | 'auto';

interface ReaderModeContextValue {
  mode: ReaderMode;
  setMode: (m: ReaderMode) => void;
}

const ReaderModeContext = createContext<ReaderModeContextValue | undefined>(undefined);

export const ReaderModeProvider = ({ children }: { children: ReactNode }) => {
  const [mode, setModeState] = useState<ReaderMode>('auto');

  useEffect(() => {
    (async () => {
  const saved = await storage.getReaderMode();
  if (saved) setModeState(saved as ReaderMode);
    })();
  }, []);

  const setMode = (m: ReaderMode) => {
    setModeState(m);
    storage.setReaderMode(m);
  };

  return (
    <ReaderModeContext.Provider value={{ mode, setMode }}>
      {children}
    </ReaderModeContext.Provider>
  );
};

export const useReaderMode = () => {
  const ctx = useContext(ReaderModeContext);
  if (!ctx) throw new Error('useReaderMode must be used within ReaderModeProvider');
  return ctx;
};
