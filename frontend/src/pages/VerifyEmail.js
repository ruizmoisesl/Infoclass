import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { toast } from 'react-toastify';
import { CheckCircle, XCircle, Mail, ArrowLeft } from 'lucide-react';

const VerifyEmail = () => {
  const { token } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [verified, setVerified] = useState(false);
  const [error, setError] = useState(null);
  const [resending, setResending] = useState(false);

  useEffect(() => {
    if (token) {
      verifyEmail(token);
    } else {
      setError('Token de verificación no encontrado');
      setLoading(false);
    }
  }, [token]);

  const verifyEmail = async (verificationToken) => {
    try {
      setLoading(true);
      const response = await api.post('/api/auth/verify-email', {
        token: verificationToken
      });

      if (response.data.message) {
        toast.success(response.data.message);
        setVerified(true);
      }
    } catch (error) {
      const message = error.response?.data?.message || 'Error al verificar email';
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const resendVerification = async () => {
    try {
      setResending(true);
      const response = await api.post('/api/auth/resend-verification');
      toast.success(response.data.message);
    } catch (error) {
      const message = error.response?.data?.message || 'Error al reenviar verificación';
      toast.error(message);
    } finally {
      setResending(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50 flex items-center justify-center">
        <div className="max-w-md w-full mx-4">
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold text-secondary-900 mb-2">
              Verificando tu email...
            </h2>
            <p className="text-secondary-600">
              Por favor espera mientras verificamos tu cuenta.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (verified) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50 flex items-center justify-center">
        <div className="max-w-md w-full mx-4">
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-secondary-900 mb-2">
              ¡Email verificado!
            </h2>
            <p className="text-secondary-600 mb-6">
              Tu cuenta ha sido verificada exitosamente. Ya puedes usar todas las funciones de InfoClass.
            </p>
            <button
              onClick={() => navigate('/dashboard')}
              className="btn-primary w-full"
            >
              Ir al Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50 flex items-center justify-center">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white rounded-lg shadow-lg p-8 text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <XCircle className="w-8 h-8 text-red-600" />
          </div>
          <h2 className="text-2xl font-bold text-secondary-900 mb-2">
            Error en la verificación
          </h2>
          <p className="text-secondary-600 mb-6">
            {error || 'No se pudo verificar tu email. El enlace puede haber expirado o ser inválido.'}
          </p>
          
          <div className="space-y-3">
            <button
              onClick={resendVerification}
              disabled={resending}
              className="btn-primary w-full flex items-center justify-center"
            >
              <Mail className="w-4 h-4 mr-2" />
              {resending ? 'Reenviando...' : 'Reenviar email de verificación'}
            </button>
            
            <button
              onClick={() => navigate('/login')}
              className="btn-secondary w-full flex items-center justify-center"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Volver al Login
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VerifyEmail;
