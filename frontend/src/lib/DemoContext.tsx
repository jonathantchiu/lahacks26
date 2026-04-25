import { useState, type ReactNode } from 'react';
import { DemoContext } from './demoContextValue';

export function DemoProvider({ children }: { children: ReactNode }) {
  const [demoActive, setDemoActive] = useState(false);
  const toggleDemo = () => setDemoActive((v) => !v);

  return (
    <DemoContext.Provider value={{ demoActive, toggleDemo }}>
      {children}
    </DemoContext.Provider>
  );
}
