import { PositionDetail } from "@/components/PositionDetail";

export default function PositionDetailPage({ params }: { params: { id: string } }) {
  return <PositionDetail positionId={params.id} />;
}
