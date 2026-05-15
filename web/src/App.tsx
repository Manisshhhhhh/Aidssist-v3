import { useState } from "react";

import { AppShell } from "./components/layout/AppShell";
import { AuthGate } from "./components/auth/AuthGate";
import { AuthProvider } from "./auth/AuthContext";
import { DashboardPage } from "./pages/DashboardPage";
import { UploadPage } from "./pages/UploadPage";
import { WorkspaceProvider } from "./workspace/WorkspaceContext";

export default function App() {
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);

  return (
    <AuthProvider>
      <WorkspaceProvider>
        <AppShell>
          <AuthGate>
            {selectedDatasetId ? (
              <DashboardPage datasetId={selectedDatasetId} onBack={() => setSelectedDatasetId(null)} />
            ) : (
              <UploadPage onOpenDashboard={setSelectedDatasetId} />
            )}
          </AuthGate>
        </AppShell>
      </WorkspaceProvider>
    </AuthProvider>
  );
}
