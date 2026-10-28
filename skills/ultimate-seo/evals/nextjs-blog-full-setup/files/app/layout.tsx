import type { ReactNode } from "react";

export const metadata = {
  title: "Jamie's Blog",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html>
      <body>
        <header><a href="/">Jamie Codes</a> · <a href="/blog">Blog</a> · <a href="/about">About</a></header>
        {children}
      </body>
    </html>
  );
}
