import React, { createContext, useContext, useState, useEffect } from "react";

interface SessionData {
  sessionId: string;
  filename: string;
  rows: number;
  columns: number;
}

interface SessionContextType {
  sessionId: string | null;
  filename: string | null;
  rows: number | null;
  columns: number | null;
  isSessionActive: boolean;
  setSession: (data: SessionData) => void;
  clearSession: () => void;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export const SessionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [filename, setFilename] = useState<string | null>(null);
  const [rows, setRows] = useState<number | null>(null);
  const [columns, setColumns] = useState<number | null>(null);

  // Initialize from local storage on mount
  useEffect(() => {
    const cachedId = localStorage.getItem("session_id");
    const cachedFilename = localStorage.getItem("session_filename");
    const cachedRows = localStorage.getItem("session_rows");
    const cachedCols = localStorage.getItem("session_columns");

    if (cachedId && cachedFilename) {
      setSessionId(cachedId);
      setFilename(cachedFilename);
      setRows(cachedRows ? parseInt(cachedRows, 10) : null);
      setColumns(cachedCols ? parseInt(cachedCols, 10) : null);
    }
  }, []);

  const setSession = (data: SessionData) => {
    setSessionId(data.sessionId);
    setFilename(data.filename);
    setRows(data.rows);
    setColumns(data.columns);

    localStorage.setItem("session_id", data.sessionId);
    localStorage.setItem("session_filename", data.filename);
    localStorage.setItem("session_rows", data.rows.toString());
    localStorage.setItem("session_columns", data.columns.toString());
  };

  const clearSession = () => {
    setSessionId(null);
    setFilename(null);
    setRows(null);
    setColumns(null);

    localStorage.removeItem("session_id");
    localStorage.removeItem("session_filename");
    localStorage.removeItem("session_rows");
    localStorage.removeItem("session_columns");
  };

  const isSessionActive = !!sessionId;

  return (
    <SessionContext.Provider
      value={{
        sessionId,
        filename,
        rows,
        columns,
        isSessionActive,
        setSession,
        clearSession,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
};

export const useSession = () => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useSession must be used within a SessionProvider");
  }
  return context;
};
