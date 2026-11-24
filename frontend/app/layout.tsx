import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: "GOD'S EYE | Public Safety Intelligence", description: "GOD'S EYE public safety intelligence dashboard with verified Chennai image-refresh sources, a licensed prerecorded Indian traffic demo, real YOLO inference and human oversight." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }
