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
        
        <div className="grid md:grid-cols-2 gap-8 mt-16">
          <div className="p-6 border rounded-lg">
            <h2 className="text-2xl font-semibold mb-4">Site Overview</h2>
            <p className="text-muted-foreground">
              View performance data for all your solar sites at a glance.
            </p>
          </div>
          
          <div className="p-6 border rounded-lg">
            <h2 className="text-2xl font-semibold mb-4">Detailed Analysis</h2>
            <p className="text-muted-foreground">
              Drill down into specific site data with power curve visualizations.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
