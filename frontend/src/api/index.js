import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE;

export const register = (username, password) =>
  axios.post(`${API_BASE}/api/auth/register`, { username, password });

export const login = (username, password) =>
  axios.post(`${API_BASE}/api/auth/login`, { username, password });

export const getRooms = () =>
  axios.get(`${API_BASE}/api/chat/rooms`);

export const createRoom = (name, token) =>
  axios.post(`${API_BASE}/api/chat/rooms`, { name }, {
    headers: { Authorization: `Bearer ${token}` }
  });