import { notFound } from "next/navigation";
import { getAllPosts, getPost } from "@/lib/posts";

export function generateStaticParams() {
  return getAllPosts().map((p) => ({ slug: p.slug }));
}

export default async function Post({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = getPost(slug);
  if (!post) notFound();
  return (
    <main>
      <h1>{post.title}</h1>
      <p><time dateTime={post.date}>{post.date}</time></p>
      <img src={post.cover} />
      <div>{post.body}</div>
    </main>
  );
}
