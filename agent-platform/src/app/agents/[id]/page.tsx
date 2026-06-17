import { notFound } from "next/navigation";
import { AGENTS, getAgent, relatedAgents } from "@/lib/data";
import { AgentDetail } from "@/components/agent-detail";

export function generateStaticParams() {
  return AGENTS.map((a) => ({ id: a.id }));
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const agent = getAgent(id);
  return { title: agent ? `${agent.code} · ${agent.name} — AgentOS` : "Agent — AgentOS" };
}

export default async function AgentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const agent = getAgent(id);
  if (!agent) notFound();
  return <AgentDetail agent={agent} related={relatedAgents(agent)} />;
}
