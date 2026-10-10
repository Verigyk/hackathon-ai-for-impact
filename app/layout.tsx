import type { Metadata } from 'next';
import './globals.css';
import './sncf.css';
export const metadata: Metadata = { title: 'SNCF · Sorties scolaires', description: 'Votre copilote pour les sorties scolaires en Occitanie, avec les trains liO.' };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="fr"><body>{children}</body></html>;
}
