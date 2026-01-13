import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { HotelProvider } from "@/contexts/HotelContext";
import { ErrorBoundary } from "./components/ErrorBoundary";
import UnifiedLogin from "./pages/UnifiedLogin";
import GuestDashboard from "./pages/guest/GuestDashboard";
import GuestChat from "./pages/guest/GuestChat";
import GuestNotifications from "./pages/guest/GuestNotifications";
import RoomService from "./pages/guest/RoomService";
import Housekeeping from "./pages/guest/Housekeeping";
import Transport from "./pages/guest/Transport";
import ServiceHistory from "./pages/guest/ServiceHistory";
import ReceptionDashboard from "./pages/reception/ReceptionDashboard";
import Messages from "./pages/reception/Messages";
import Requests from "./pages/reception/Requests";
import SendNotifications from "./pages/reception/SendNotifications";
import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminRoom from "./pages/admin/AdminRoom";
import AdminServices from "./pages/admin/AdminServices";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <HotelProvider>
        <ErrorBoundary>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<UnifiedLogin />} />
              <Route path="/login" element={<UnifiedLogin />} />
              {/* Guest Routes */}
              <Route path="/guest/dashboard" element={<GuestDashboard />} />
              <Route path="/guest/chat" element={<GuestChat />} />
              <Route path="/guest/notifications" element={<GuestNotifications />} />
              <Route path="/guest/services/room-service" element={<RoomService />} />
              <Route path="/guest/services/housekeeping" element={<Housekeeping />} />
              <Route path="/guest/services/transport" element={<Transport />} />
              <Route path="/guest/services/history" element={<ServiceHistory />} />
              {/* Staff Routes */}
              <Route path="/reception/dashboard" element={<ReceptionDashboard />} />
              <Route path="/reception/messages" element={<Messages />} />
              <Route path="/reception/requests" element={<Requests />} />
              <Route path="/reception/notifications" element={<SendNotifications />} />
              {/* Admin Routes */}
              <Route path="/admin/dashboard" element={<AdminDashboard />} />
              <Route path="/admin/rooms" element={<AdminRoom />} />
              <Route path="/admin/services" element={<AdminServices />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </ErrorBoundary>
      </HotelProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
