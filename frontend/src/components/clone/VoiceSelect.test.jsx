import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import VoiceSelect from './VoiceSelect';

describe('VoiceSelect', () => {
  it('uses the shared searchable picker for long and grouped option lists', () => {
    const onChange = vi.fn();
    render(
      <VoiceSelect
        id="accent"
        label="Accent or dialect"
        value="Auto"
        onChange={onChange}
        options={['Auto']}
        groups={[
          { label: 'English accents', options: ['American', 'Yorkshire'] },
          { label: 'Chinese dialects', options: ['Cantonese'] },
        ]}
      />,
    );

    expect(screen.getByRole('button', { name: 'Accent or dialect' })).toHaveAttribute(
      'id',
      'accent',
    );
    fireEvent.click(screen.getByRole('button', { name: 'Accent or dialect' }));
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'York' } });

    expect(screen.getByRole('option', { name: 'Yorkshire' })).toBeInTheDocument();
    expect(screen.queryByRole('option', { name: 'Cantonese' })).not.toBeInTheDocument();
    fireEvent.mouseDown(screen.getByRole('option', { name: 'Yorkshire' }));
    expect(onChange).toHaveBeenCalledWith('Yorkshire');
  });
});
