import { createContext } from 'react';

export interface DemoContextValue {
  demoActive: boolean;
  toggleDemo: () => void;
  sparkleMode: boolean;
  toggleSparkle: () => void;
}

export const DemoContext = createContext<DemoContextValue>({
  demoActive: false,
  toggleDemo: () => {},
  sparkleMode: false,
  toggleSparkle: () => {},
});
