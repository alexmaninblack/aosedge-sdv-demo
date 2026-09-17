import { afterEach, expect, test, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { PresenterControls, usePresenterControls } from '../../src/app/state/PresenterControls';

vi.mock('../../src/app/state/PresenterReadModelProvider', () => ({
  usePlatformObservation: () => ({ afterAction: () => {} }),
}));
afterEach(cleanup);

function Request({ action }: { action: 'provision' | 'prepare-demo' }) {
  const controls = usePresenterControls();
  return <button disabled={controls.blocked} onClick={() => controls.request({ action })}>Request</button>;
}

test.each(['provision', 'prepare-demo'] as const)('%s confirmation preserves the running simulator', async action => {
  const port = { read: async () => ({ sessionId: 'fixture', active: null, jobs: [], uncertain: false }), submit: vi.fn() };
  render(<PresenterControls port={port as any}><Request action={action}/></PresenterControls>);
  await waitFor(() => expect(screen.getByRole('button', { name: 'Request' })).not.toBeDisabled());
  fireEvent.click(screen.getByRole('button', { name: 'Request' }));
  const dialog = screen.getByRole('dialog');
  expect(dialog).toHaveTextContent('After Cloud Online');
  expect(dialog).toHaveTextContent('stationary Manual');
  expect(dialog).toHaveTextContent('Safe Stop');
  expect(dialog).not.toHaveTextContent(/restarts? the (local )?simulator once/);
  expect(port.submit).not.toHaveBeenCalled();
});
