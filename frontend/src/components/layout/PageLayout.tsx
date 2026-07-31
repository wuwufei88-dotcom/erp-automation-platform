import { Outlet } from "react-router-dom";
import TopNav from "./TopNav";
import Footer from "./Footer";

export default function PageLayout() {
  return (
    <>
      <TopNav />
      <main style={{ minHeight: "calc(100vh - 64px)" }}>
        <Outlet />
      </main>
      <Footer />
    </>
  );
}
