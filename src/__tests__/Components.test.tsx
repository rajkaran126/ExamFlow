import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { Button, Input, Badge, Dialog } from '../components/ui';

describe('UI Component Library', () => {
  it('renders Button with variants and handles clicks', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click Me</Button>);

    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeDefined();

    fireEvent.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('renders Input with validation errors', () => {
    render(<Input label="Roll Number" error="Roll number is required" />);

    expect(screen.getByLabelText(/roll number/i)).toBeDefined();
    expect(screen.getByRole('alert').textContent).toBe('Roll number is required');
  });

  it('renders Badge with appropriate variants', () => {
    const { rerender } = render(<Badge variant="success">QUALIFIED</Badge>);
    expect(screen.getByText('QUALIFIED')).toBeDefined();

    rerender(<Badge variant="error">DISQUALIFIED</Badge>);
    expect(screen.getByText('DISQUALIFIED')).toBeDefined();
  });

  it('renders Dialog modal and handles dismiss', () => {
    const handleClose = vi.fn();
    render(
      <Dialog open={true} onClose={handleClose} title="Test Dialog">
        <p>Dialog Body</p>
      </Dialog>
    );

    expect(screen.getByText('Test Dialog')).toBeDefined();
    expect(screen.getByText('Dialog Body')).toBeDefined();
  });
});
