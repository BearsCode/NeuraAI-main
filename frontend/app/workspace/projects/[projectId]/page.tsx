import { ProjectDetailShell } from "@/components/project-detail-shell";

type Props = {
  params: Promise<{ projectId: string }>;
};

export default async function ProjectPage({ params }: Props) {
  const { projectId } = await params;
  return <ProjectDetailShell projectId={projectId} />;
}
