import Link from "next/link";
import { getAllPosts } from "@/lib/posts";

export default function Blog() {
  return (
    <main>
      <h1>Blog</h1>
      {getAllPosts().map((p) => (
        <article key={p.slug}>
          <h2><Link href={`/blog/${p.slug}`}>{p.title}</Link></h2>
          <p>{p.excerpt}</p>
        </article>
      ))}
    </main>
  );
}
