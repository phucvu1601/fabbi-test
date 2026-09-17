import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useLogout, fetchCurrentUser } from "../api/auth";
import { queryClient } from "@/lib/queryClient";

export function useAuth() {
  const navigate = useNavigate();
  const logoutMutation = useLogout();

  const token = localStorage.getItem("access_token");
  const isAuthenticated = !!token;

  const {
    data: user,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["currentUser"],
    queryFn: fetchCurrentUser,
    enabled: isAuthenticated,
    retry: false,
  });

  const logout = () => {
    // Helper to clean up tokens and cache before redirecting
    const handleCleanUpAndRedirect = () => {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      queryClient.clear(); // Clear all React Query cache
      navigate("/login");
    };
    logoutMutation.mutate(undefined, {
      onSuccess: () => {
        handleCleanUpAndRedirect();
      },
      onError: () => {
        handleCleanUpAndRedirect();
      },
    });
  };

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    logout,
  };
}
