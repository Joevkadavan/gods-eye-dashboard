import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: "GOD'S EYE | Public Safety Intelligence", description: "An AI-assisted public-safety intelligence dashboard with video analytics, camera-source status, and geographic context." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en" suppressHydrationWarning><body suppressHydrationWarning>{children}</body></html>; }
