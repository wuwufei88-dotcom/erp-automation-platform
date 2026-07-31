import { Routes, Route } from "react-router-dom";
import PageLayout from "./components/layout/PageLayout";
import LandingPage from "./pages/LandingPage";
import DashboardPage from "./pages/DashboardPage";
import ProjectDetailPage from "./pages/ProjectDetailPage";
import SolutionsPage from "./pages/SolutionsPage";
import ResourcesPage from "./pages/ResourcesPage";
import ApiKeysPage from "./pages/ApiKeysPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route element={<PageLayout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/projects/:id" element={<ProjectDetailPage />} />
        <Route path="/solutions" element={<SolutionsPage />} />
        <Route path="/resources" element={<ResourcesPage />} />
        <Route path="/settings/api" element={<ApiKeysPage />} />
      </Route>
    </Routes>
  );
}
