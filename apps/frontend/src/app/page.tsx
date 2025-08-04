import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen p-8">
      <main className="max-w-4xl mx-auto">
        <div className="text-center py-16">
          <h1 className="text-4xl font-bold mb-8">
            RPM - Solar Performance Monitoring
          </h1>
          <p className="text-xl text-muted-foreground mb-8">
            Monitor and analyze solar site performance data
          </p>
          <Link href="/portfolio">
            <Button size="lg">
              View Site Portfolio
            </Button>
          </Link>
        </div>
      </main>
    </div>
  );
}
