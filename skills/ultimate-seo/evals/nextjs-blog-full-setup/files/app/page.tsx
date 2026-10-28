import Link from "next/link";
import { getAllPosts } from "@/lib/posts";

export default function Home() {
  const posts = getAllPosts();
  return (
    <main>
      <h1>Hi, I'm Jamie. I write about TypeScript, testing and web performance.</h1>
      <ul>
        {posts.map((p) => (
          <li key={p.slug}><Link href={`/blog/${p.slug}`}>{p.title}</Link></li>
        ))}
      </ul>
    </main>
  );
}
