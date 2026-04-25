import { createContext } from 'react';

export interface DemoContextValue {
  demoActive: boolean;
  toggleDemo: () => void;
}

export const DemoContext = createContext<DemoContextValue>({
  demoActive: false,
  toggleDemo: () => {},
});
