import { render, screen } from '@testing-library/react';
import AgentChat from './AgentChat';

test('renders chatbot title', () => {
  render(<AgentChat />);
  const linkElement = screen.getByText(/강남대학교 챗봇 강냉이/i);
  expect(linkElement).toBeInTheDocument();
});
