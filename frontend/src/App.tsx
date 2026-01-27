import { Toaster } from "./components/ui/toaster";
import { Toaster as Sonner } from "./components/ui/sonner";
import { TooltipProvider } from "./components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import ExecutiveOverview from "./pages/ExecutiveOverview";
import Segmentation from "./pages/Segmentation";
import ChurnRisk from "./pages/ChurnRisk";
import CLVValue from "./pages/CLVValue";
import CustomerHealth from "./pages/CustomerHealth";
import Customers from "./pages/Customers";
import Alerts from "./pages/Alerts";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<ExecutiveOverview />} />
          <Route path="/segmentation" element={<Segmentation />} />
          <Route path="/churn-risk" element={<ChurnRisk />} />
          <Route path="/clv-value" element={<CLVValue />} />
          <Route path="/customer-health" element={<CustomerHealth />} />
          <Route path="/customers" element={<Customers />} />
          <Route path="/alerts" element={<Alerts />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
