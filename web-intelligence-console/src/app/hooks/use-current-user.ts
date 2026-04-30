"use client";
import { useState, useEffect } from 'react';

export interface CurrentUser {
  id: string;
  email: string;
  full_name: string;
  role: 'intelligence' | 'field_agent' | 'supervisor' | 'admin';
  agency_id: string;
  agency_name?: string;
  agency_type?: 'central' | 'regional' | 'local';
  unit_id?: string;
  unit_name?: string;
  is_authenticated: boolean;
}

export function useCurrentUser() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem('user');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setUser({ ...parsed, is_authenticated: true });
      } catch {
        setUser(null);
      }
    }
    setLoading(false);
  }, []);

  return { user, loading };
}