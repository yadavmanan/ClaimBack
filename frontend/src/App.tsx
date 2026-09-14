import { Route, Routes } from "react-router-dom";
import { AppShell } from "./components/ui/AppShell";
import { Dashboard } from "./pages/Dashboard";
import { OpportunityDetail } from "./pages/OpportunityDetail";
import { Vault } from "./pages/Vault";
import { Activity } from "./pages/Activity";

function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/opportunities/:id" element={<OpportunityDetail />} />
        <Route path="/vault" element={<Vault />} />
        <Route path="/activity" element={<Activity />} />
      </Route>
    </Routes>
  );
}

export default App;
