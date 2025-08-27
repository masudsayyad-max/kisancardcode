export default function Home() {
  return (
    <main style={{display:'flex',alignItems:'center',justifyContent:'center',height:'100svh',flexDirection:'column',gap:8}}>
      <h1>AgriStack (Next.js)</h1>
      <p>API is being scaffolded. Configure .env and run migrations.</p>
      <code>npx prisma migrate dev --name init</code>
    </main>
  );
}

