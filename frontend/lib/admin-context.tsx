"use client";

import { createContext, useContext } from "react";

export type AdminUser = { email: string; full_name: string; role: string; admin_role: string | null };
export type AdminCtx = { user: AdminUser | null; role: string; loading: boolean };

export const AdminContext = createContext<AdminCtx>({ user: null, role: "viewer", loading: true });
export const useAdmin = () => useContext(AdminContext);
