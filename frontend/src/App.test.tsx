// SPDX-License-Identifier: LicenseRef-CubeAlarm-Custom-Attribution
// Copyright (c) 2025 Paul Shapiro
import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders learn react link', () => {
  render(<App />);
  const linkElement = screen.getByText(/learn react/i);
  expect(linkElement).toBeInTheDocument();
});
