import { createContext, useState, useEffect } from "react";

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [username, setUsername] = useState(null);

    useEffect(() => {
        fetch("http://127.0.0.1:5000/me", { credentials: "include" })
            .then(res => res.json())
            .then(json => setUsername(json.token || null))
            .catch(() => setUsername(null));
    }, []);

    return (
        <AuthContext.Provider value={{ username, setUsername }}>
            {children}
        </AuthContext.Provider>
    );
};
