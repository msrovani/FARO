// F.A.R.O. Web Intelligence Console - BMRS Edition
// Sistema de Inteligência Operacional - Brigada Militar do RS
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "F.A.R.O. - Sistema de Inteligência | BMRS",
  description: "Ferramenta de Análise de Rotas e Observações - Sistema Oficial da Brigada Militar do Rio Grande do Sul",
  keywords: ["BMRS", "FARO", "inteligência policial", "segurança pública", "análise operacional"],
  authors: [{ name: "SSI/BMRS" }],
  robots: "noindex, nofollow",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className="antialiased bg-gray-50">
        {children}
      </body>
    </html>
  );
}
