import React, { createContext, useContext, useState, useEffect } from "react";
import { api, User } from "../api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem("inspect_ai_user");
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("inspect_ai_token"));
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (token && !user) {
      api.getMe()
        .then((u) => {
          setUser(u);
          localStorage.setItem("inspect_ai_user", JSON.stringify(u));
        })
        .catch(() => {
          logout();
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (email: string, pass: string) => {
    const res = await api.login({ email, password: pass });
    const userObj: User = {
      id: "USR-LOGGED",
      email: res.email,
      role: res.role,
      full_name: res.full_name
    };
    setToken(res.access_token);
    setUser(userObj);
    localStorage.setItem("inspect_ai_token", res.access_token);
    localStorage.setItem("inspect_ai_user", JSON.stringify(userObj));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("inspect_ai_token");
    localStorage.removeItem("inspect_ai_user");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        logout,
        isAuthenticated: !!token && !!user
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
