export const metadata = {
  title: "AgriStack",
  description: "Agri card generator",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Noto Sans, Noto Sans Devanagari, Arial' }}>
        {children}
      </body>
    </html>
  );
}

