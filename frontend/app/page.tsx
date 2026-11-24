import { redirect } from 'next/navigation';

// Keep the approved video-first intelligence dashboard as the public landing page.
// The Chennai source-availability page remains available at /chennai.
export default function HomePage() {
  redirect('/operations');
}
