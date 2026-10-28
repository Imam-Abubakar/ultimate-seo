export type Post = { slug: string; title: string; excerpt: string; date: string; updated?: string; cover: string; body: string };

const posts: Post[] = [
  { slug: "typescript-satisfies", title: "Stop casting: a practical guide to TypeScript's satisfies operator", excerpt: "When to reach for satisfies instead of as, with real examples from a design system codebase.", date: "2026-03-02", cover: "/covers/satisfies.png", body: "..." },
  { slug: "flaky-tests", title: "How we cut flaky tests by 90% in a Playwright suite", excerpt: "The four root causes behind most flaky end-to-end tests and the fixes that stuck.", date: "2026-05-18", updated: "2026-06-01", cover: "/covers/flaky.png", body: "..." },
  { slug: "inp-in-practice", title: "INP in practice: fixing slow interactions on a React dashboard", excerpt: "Profiling and fixing Interaction to Next Paint regressions step by step.", date: "2026-08-09", cover: "/covers/inp.png", body: "..." },
];

export const getAllPosts = () => posts;
export const getPost = (slug: string) => posts.find((p) => p.slug === slug);
