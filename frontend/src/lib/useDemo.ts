import { useContext } from 'react';
import { DemoContext } from './demoContextValue';

export function useDemo() {
  return useContext(DemoContext);
}
