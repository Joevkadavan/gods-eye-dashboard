import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Chennai Traffic Sources | GOD\'S EYE',
  description: 'See verified Chennai source availability and location context. Source availability is not a traffic condition.',
};

export default function ChennaiLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return children;
}
