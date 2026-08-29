import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "Enterprise KIP | Grounded Technical Documentation Search",
  description:
    "A production RAG demo over curated Docker, Kubernetes, FastAPI, Transformers, LangChain, LangGraph, and Qdrant documentation.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
