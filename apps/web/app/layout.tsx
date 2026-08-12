import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Halcyon Goods — Internal Product Control",
  description: "Company-wide record of every item held in the warehouse.",
  icons: {
    icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#9638;</text></svg>",
  },
};

/**
 * Applied before first paint, so a reader who chose dark never sees a white
 * flash while React hydrates. It only reads storage - the rest of the theme
 * handling lives in the ThemeToggle client component.
 */
const THEME_SCRIPT = `
try {
  var saved = localStorage.getItem('halcyon-theme');
  if (saved) document.documentElement.dataset.theme = saved;
} catch (e) {}
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
      </head>
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
