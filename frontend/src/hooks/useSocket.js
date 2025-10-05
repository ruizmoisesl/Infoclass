import { useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import { useAuth } from '../contexts/AuthContext';

const useSocket = () => {
  const socketRef = useRef(null);
  const { user, token } = useAuth();

  useEffect(() => {
    if (user && token) {
      // Conectar al servidor WebSocket
      socketRef.current = io('http://localhost:5000', {
        auth: {
          token: token
        }
      });

      // Unirse a la sala del usuario
      socketRef.current.emit('join_user_room');

      // Manejar eventos de conexión
      socketRef.current.on('connect', () => {
        console.log('Conectado al servidor WebSocket');
      });

      socketRef.current.on('disconnect', () => {
        console.log('Desconectado del servidor WebSocket');
      });

      // Limpiar conexión al desmontar
      return () => {
        if (socketRef.current) {
          socketRef.current.emit('leave_user_room');
          socketRef.current.disconnect();
        }
      };
    }
  }, [user, token]);

  return socketRef.current;
};

export default useSocket;
