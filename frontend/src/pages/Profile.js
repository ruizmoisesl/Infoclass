import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import {
  User,
  Mail,
  Calendar,
  Shield,
  Edit,
  Save,
  X,
  Camera,
  Lock,
  Bell,
  Globe
} from 'lucide-react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

const Profile = () => {
  const { user, logout } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    bio: '',
    phone: '',
    website: ''
  });

  useEffect(() => {
    if (user) {
      setFormData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        bio: user.bio || '',
        phone: user.phone || '',
        website: user.website || ''
      });
      setLoading(false);
    }
  }, [user]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSave = async () => {
    try {
      // Aquí implementarías la actualización del perfil
      console.log('Actualizando perfil:', formData);
      setEditing(false);
    } catch (error) {
      console.error('Error al actualizar perfil:', error);
    }
  };

  const handleCancel = () => {
    setFormData({
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      email: user.email || '',
      bio: user.bio || '',
      phone: user.phone || '',
      website: user.website || ''
    });
    setEditing(false);
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'admin':
        return 'text-red-600 bg-red-100';
      case 'teacher':
        return 'text-blue-600 bg-blue-100';
      case 'student':
        return 'text-green-600 bg-green-100';
      default:
        return 'text-secondary-600 bg-secondary-100';
    }
  };

  const getRoleLabel = (role) => {
    switch (role) {
      case 'admin':
        return 'Administrador';
      case 'teacher':
        return 'Profesor';
      case 'student':
        return 'Estudiante';
      default:
        return role;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">Mi Perfil</h1>
        <p className="text-secondary-600">
          Gestiona tu información personal y configuración
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Información Principal */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-secondary-900">
                Información Personal
              </h2>
              {!editing && (
                <button
                  onClick={() => setEditing(true)}
                  className="btn-secondary"
                >
                  <Edit className="w-4 h-4 mr-2" />
                  Editar
                </button>
              )}
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-2">
                    Nombre
                  </label>
                  {editing ? (
                    <input
                      type="text"
                      name="first_name"
                      value={formData.first_name}
                      onChange={handleChange}
                      className="input-field"
                    />
                  ) : (
                    <p className="text-secondary-900">{user?.first_name}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-2">
                    Apellido
                  </label>
                  {editing ? (
                    <input
                      type="text"
                      name="last_name"
                      value={formData.last_name}
                      onChange={handleChange}
                      className="input-field"
                    />
                  ) : (
                    <p className="text-secondary-900">{user?.last_name}</p>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-2">
                  Correo Electrónico
                </label>
                {editing ? (
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    className="input-field"
                  />
                ) : (
                  <p className="text-secondary-900">{user?.email}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-2">
                  Biografía
                </label>
                {editing ? (
                  <textarea
                    name="bio"
                    value={formData.bio}
                    onChange={handleChange}
                    rows={3}
                    className="input-field"
                    placeholder="Cuéntanos sobre ti..."
                  />
                ) : (
                  <p className="text-secondary-900">
                    {user?.bio || 'Sin biografía'}
                  </p>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-2">
                    Teléfono
                  </label>
                  {editing ? (
                    <input
                      type="tel"
                      name="phone"
                      value={formData.phone}
                      onChange={handleChange}
                      className="input-field"
                    />
                  ) : (
                    <p className="text-secondary-900">
                      {user?.phone || 'No especificado'}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-2">
                    Sitio Web
                  </label>
                  {editing ? (
                    <input
                      type="url"
                      name="website"
                      value={formData.website}
                      onChange={handleChange}
                      className="input-field"
                    />
                  ) : (
                    <p className="text-secondary-900">
                      {user?.website || 'No especificado'}
                    </p>
                  )}
                </div>
              </div>

              {editing && (
                <div className="flex justify-end space-x-3 pt-4 border-t border-secondary-200">
                  <button
                    onClick={handleCancel}
                    className="btn-secondary"
                  >
                    <X className="w-4 h-4 mr-2" />
                    Cancelar
                  </button>
                  <button
                    onClick={handleSave}
                    className="btn-primary"
                  >
                    <Save className="w-4 h-4 mr-2" />
                    Guardar
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Configuración de Cuenta */}
          <div className="card">
            <h2 className="text-lg font-semibold text-secondary-900 mb-6">
              Configuración de Cuenta
            </h2>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-secondary-50 rounded-lg">
                <div className="flex items-center">
                  <Lock className="w-5 h-5 text-secondary-600 mr-3" />
                  <div>
                    <p className="font-medium text-secondary-900">Contraseña</p>
                    <p className="text-sm text-secondary-600">
                      Última actualización hace 30 días
                    </p>
                  </div>
                </div>
                <button className="btn-secondary">
                  Cambiar
                </button>
              </div>

              <div className="flex items-center justify-between p-4 bg-secondary-50 rounded-lg">
                <div className="flex items-center">
                  <Bell className="w-5 h-5 text-secondary-600 mr-3" />
                  <div>
                    <p className="font-medium text-secondary-900">Notificaciones</p>
                    <p className="text-sm text-secondary-600">
                      Gestiona tus preferencias de notificación
                    </p>
                  </div>
                </div>
                <button className="btn-secondary">
                  Configurar
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Avatar y Info Básica */}
          <div className="card text-center">
            <div className="relative inline-block mb-4">
              <div className="w-24 h-24 bg-primary-100 rounded-full flex items-center justify-center mx-auto">
                <User className="w-12 h-12 text-primary-600" />
              </div>
              <button className="absolute bottom-0 right-0 w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center hover:bg-primary-700 transition-colors duration-200">
                <Camera className="w-4 h-4 text-white" />
              </button>
            </div>

            <h3 className="text-xl font-semibold text-secondary-900 mb-2">
              {user?.first_name} {user?.last_name}
            </h3>

            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getRoleColor(user?.role)}`}>
              <Shield className="w-4 h-4 mr-1" />
              {getRoleLabel(user?.role)}
            </span>

            <div className="mt-4 space-y-2 text-sm text-secondary-600">
              <div className="flex items-center justify-center">
                <Mail className="w-4 h-4 mr-2" />
                {user?.email}
              </div>
              <div className="flex items-center justify-center">
                <Calendar className="w-4 h-4 mr-2" />
                Miembro desde {format(new Date(user?.created_at), 'MMM yyyy', { locale: es })}
              </div>
            </div>
          </div>

          {/* Estadísticas Rápidas */}
          <div className="card">
            <h3 className="text-lg font-semibold text-secondary-900 mb-4">
              Estadísticas
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-secondary-600">Cursos</span>
                <span className="font-medium text-secondary-900">3</span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondary-600">Tareas</span>
                <span className="font-medium text-secondary-900">12</span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondary-600">Entregas</span>
                <span className="font-medium text-secondary-900">8</span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondary-600">Promedio</span>
                <span className="font-medium text-secondary-900">85%</span>
              </div>
            </div>
          </div>

          {/* Acciones */}
          <div className="card">
            <h3 className="text-lg font-semibold text-secondary-900 mb-4">
              Acciones
            </h3>
            <div className="space-y-2">
              <button className="w-full btn-secondary text-left">
                <Globe className="w-4 h-4 mr-2" />
                Ver Perfil Público
              </button>
              <button className="w-full btn-secondary text-left">
                <Lock className="w-4 h-4 mr-2" />
                Cambiar Contraseña
              </button>
              <button
                onClick={logout}
                className="w-full btn-danger text-left"
              >
                <X className="w-4 h-4 mr-2" />
                Cerrar Sesión
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
