import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/axios';
import { toast } from 'react-toastify';
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
  Eye,
  EyeOff,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { formatDateProfile } from '../utils/dateUtils';

const Profile = () => {
  const { user, logout, updateUser, resendVerification } = useAuth();
  
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [stats, setStats] = useState({
    courses: 0,
    assignments: 0,
    submissions: 0,
    average: 0
  });
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    bio: '',
    phone: '',
    website: ''
  });
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false
  });
  const [notificationSettings, setNotificationSettings] = useState({
    email_notifications: true,
    assignment_reminders: true,
    grade_notifications: true,
    announcement_notifications: true
  });
  const [avatar, setAvatar] = useState(null);
  const [avatarPreview, setAvatarPreview] = useState(null);

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
      loadUserStats();
      loadNotificationSettings();
      setLoading(false);
    }
  }, [user]);

  const loadUserStats = async () => {
    try {
      const response = await api.get('/api/users/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Error al cargar estadísticas:', error);
    }
  };

  const loadNotificationSettings = async () => {
    try {
      const response = await api.get('/api/users/notification-settings');
      setNotificationSettings(response.data);
    } catch (error) {
      console.error('Error al cargar configuración de notificaciones:', error);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handlePasswordChange = (e) => {
    setPasswordData({
      ...passwordData,
      [e.target.name]: e.target.value
    });
  };

  const handleNotificationChange = (e) => {
    setNotificationSettings({
      ...notificationSettings,
      [e.target.name]: e.target.checked
    });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await api.put('/api/users/profile', formData);
      updateUser(response.data.user);
      toast.success('Perfil actualizado exitosamente');
      setEditing(false);
    } catch (error) {
      const message = error.response?.data?.message || 'Error al actualizar perfil';
      toast.error(message);
    } finally {
      setSaving(false);
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

  const handlePasswordSave = async () => {
    if (passwordData.new_password !== passwordData.confirm_password) {
      toast.error('Las contraseñas no coinciden');
      return;
    }

    if (passwordData.new_password.length < 6) {
      toast.error('La contraseña debe tener al menos 6 caracteres');
      return;
    }

    setSaving(true);
    try {
      await api.put('/api/users/password', {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password
      });
      toast.success('Contraseña actualizada exitosamente');
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
      setShowPasswordForm(false);
    } catch (error) {
      const message = error.response?.data?.message || 'Error al actualizar contraseña';
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  const handleNotificationSave = async () => {
    setSaving(true);
    try {
      await api.put('/api/users/notification-settings', notificationSettings);
      toast.success('Configuración de notificaciones actualizada');
      setShowNotifications(false);
    } catch (error) {
      const message = error.response?.data?.message || 'Error al actualizar configuración';
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  const togglePasswordVisibility = (field) => {
    setShowPasswords({
      ...showPasswords,
      [field]: !showPasswords[field]
    });
  };

  const handleAvatarChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        toast.error('El archivo es demasiado grande. Máximo 5MB');
        return;
      }
      
      if (!file.type.startsWith('image/')) {
        toast.error('Solo se permiten archivos de imagen');
        return;
      }

      setAvatar(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setAvatarPreview(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleAvatarUpload = async () => {
    if (!avatar) return;

    setSaving(true);
    try {
      const formData = new FormData();
      formData.append('avatar', avatar);

      const response = await api.post('/api/users/avatar', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      updateUser(response.data.user);
      toast.success('Avatar actualizado exitosamente');
      setAvatar(null);
      setAvatarPreview(null);
    } catch (error) {
      const message = error.response?.data?.message || 'Error al actualizar avatar';
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  const removeAvatar = async () => {
    setSaving(true);
    try {
      await api.delete('/api/users/avatar');
      const updatedUser = { ...user, avatar: null };
      updateUser(updatedUser);
      toast.success('Avatar eliminado exitosamente');
    } catch (error) {
      const message = error.response?.data?.message || 'Error al eliminar avatar';
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  const handleResendVerification = async () => {
    setSaving(true);
    try {
      await resendVerification();
    } finally {
      setSaving(false);
    }
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

          {/* Formulario de Cambio de Contraseña */}
          {showPasswordForm && (
            <div className="card">
              <h2 className="text-lg font-semibold text-secondary-900 mb-6">
                Cambiar Contraseña
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-2">
                    Contraseña Actual
                  </label>
                  <div className="relative">
                    <input
                      type={showPasswords.current ? "text" : "password"}
                      name="current_password"
                      value={passwordData.current_password}
                      onChange={handlePasswordChange}
                      className="input-field pr-10"
                      placeholder="Ingresa tu contraseña actual"
                    />
                    <button
                      type="button"
                      onClick={() => togglePasswordVisibility('current')}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2"
                    >
                      {showPasswords.current ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-2">
                    Nueva Contraseña
                  </label>
                  <div className="relative">
                    <input
                      type={showPasswords.new ? "text" : "password"}
                      name="new_password"
                      value={passwordData.new_password}
                      onChange={handlePasswordChange}
                      className="input-field pr-10"
                      placeholder="Ingresa tu nueva contraseña"
                    />
                    <button
                      type="button"
                      onClick={() => togglePasswordVisibility('new')}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2"
                    >
                      {showPasswords.new ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-2">
                    Confirmar Nueva Contraseña
                  </label>
                  <div className="relative">
                    <input
                      type={showPasswords.confirm ? "text" : "password"}
                      name="confirm_password"
                      value={passwordData.confirm_password}
                      onChange={handlePasswordChange}
                      className="input-field pr-10"
                      placeholder="Confirma tu nueva contraseña"
                    />
                    <button
                      type="button"
                      onClick={() => togglePasswordVisibility('confirm')}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2"
                    >
                      {showPasswords.confirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div className="flex justify-end space-x-3 pt-4 border-t border-secondary-200">
                  <button
                    onClick={() => setShowPasswordForm(false)}
                    className="btn-secondary"
                    disabled={saving}
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handlePasswordSave}
                    className="btn-primary"
                    disabled={saving}
                  >
                    {saving ? 'Guardando...' : 'Guardar Contraseña'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Configuración de Notificaciones */}
          {showNotifications && (
            <div className="card">
              <h2 className="text-lg font-semibold text-secondary-900 mb-6">
                Configuración de Notificaciones
              </h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-secondary-900">Notificaciones por Email</p>
                    <p className="text-sm text-secondary-600">Recibe notificaciones por correo electrónico</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      name="email_notifications"
                      checked={notificationSettings.email_notifications}
                      onChange={handleNotificationChange}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-secondary-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-secondary-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-secondary-900">Recordatorios de Tareas</p>
                    <p className="text-sm text-secondary-600">Recibe recordatorios sobre tareas próximas a vencer</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      name="assignment_reminders"
                      checked={notificationSettings.assignment_reminders}
                      onChange={handleNotificationChange}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-secondary-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-secondary-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-secondary-900">Notificaciones de Calificaciones</p>
                    <p className="text-sm text-secondary-600">Recibe notificaciones cuando se califiquen tus entregas</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      name="grade_notifications"
                      checked={notificationSettings.grade_notifications}
                      onChange={handleNotificationChange}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-secondary-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-secondary-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-secondary-900">Notificaciones de Anuncios</p>
                    <p className="text-sm text-secondary-600">Recibe notificaciones de nuevos anuncios en tus cursos</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      name="announcement_notifications"
                      checked={notificationSettings.announcement_notifications}
                      onChange={handleNotificationChange}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-secondary-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-secondary-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                  </label>
                </div>

                <div className="flex justify-end space-x-3 pt-4 border-t border-secondary-200">
                  <button
                    onClick={() => setShowNotifications(false)}
                    className="btn-secondary"
                    disabled={saving}
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleNotificationSave}
                    className="btn-primary"
                    disabled={saving}
                  >
                    {saving ? 'Guardando...' : 'Guardar Configuración'}
                  </button>
                </div>
              </div>
            </div>
          )}

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
                      Cambia tu contraseña de acceso
                    </p>
                  </div>
                </div>
                <button 
                  onClick={() => setShowPasswordForm(!showPasswordForm)}
                  className="btn-secondary"
                >
                  {showPasswordForm ? 'Cancelar' : 'Cambiar'}
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
                <button 
                  onClick={() => setShowNotifications(!showNotifications)}
                  className="btn-secondary"
                >
                  {showNotifications ? 'Cancelar' : 'Configurar'}
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
              <div className="w-24 h-24 bg-primary-100 rounded-full flex items-center justify-center mx-auto overflow-hidden">
                {user?.avatar || avatarPreview ? (
                  <img 
                    src={avatarPreview || user?.avatar} 
                    alt="Avatar" 
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <User className="w-12 h-12 text-primary-600" />
                )}
              </div>
              <label className="absolute bottom-0 right-0 w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center hover:bg-primary-700 transition-colors duration-200 cursor-pointer">
                <Camera className="w-4 h-4 text-white" />
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleAvatarChange}
                  className="hidden"
                />
              </label>
            </div>

            {avatar && (
              <div className="mb-4 p-3 bg-secondary-50 rounded-lg">
                <p className="text-sm text-secondary-600 mb-2">Nueva imagen seleccionada</p>
                <div className="flex justify-center space-x-2">
                  <button
                    onClick={handleAvatarUpload}
                    disabled={saving}
                    className="btn-primary text-sm px-3 py-1"
                  >
                    {saving ? 'Subiendo...' : 'Subir'}
                  </button>
                  <button
                    onClick={() => {
                      setAvatar(null);
                      setAvatarPreview(null);
                    }}
                    className="btn-secondary text-sm px-3 py-1"
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            )}

            {user?.avatar && !avatar && (
              <div className="mb-4">
                <button
                  onClick={removeAvatar}
                  disabled={saving}
                  className="btn-danger text-sm px-3 py-1"
                >
                  {saving ? 'Eliminando...' : 'Eliminar Avatar'}
                </button>
              </div>
            )}

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
                Miembro desde {formatDateProfile(user?.created_at)}
              </div>
              
              {/* Estado de verificación de email */}
              <div className="mt-4">
                {user?.email_verified ? (
                  <div className="flex items-center justify-center text-green-600 bg-green-50 px-3 py-2 rounded-lg">
                    <CheckCircle className="w-4 h-4 mr-2" />
                    <span className="text-sm font-medium">Email verificado</span>
                  </div>
                ) : (
                  <div className="text-center">
                    <div className="flex items-center justify-center text-orange-600 bg-orange-50 px-3 py-2 rounded-lg mb-2">
                      <XCircle className="w-4 h-4 mr-2" />
                      <span className="text-sm font-medium">Email no verificado</span>
                    </div>
                    <button
                      onClick={handleResendVerification}
                      disabled={saving}
                      className="btn-secondary text-sm px-3 py-1"
                    >
                      {saving ? 'Enviando...' : 'Reenviar verificación'}
                    </button>
                  </div>
                )}
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
                <span className="font-medium text-secondary-900">{stats.courses}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondary-600">Tareas</span>
                <span className="font-medium text-secondary-900">{stats.assignments}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondary-600">Entregas</span>
                <span className="font-medium text-secondary-900">{stats.submissions}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondary-600">Promedio</span>
                <span className="font-medium text-secondary-900">{stats.average}%</span>
              </div>
            </div>
          </div>

          {/* Acciones */}
          <div className="card">
            <h3 className="text-lg font-semibold text-secondary-900 mb-4">
              Acciones
            </h3>
            <div className="space-y-2">
              <button 
                onClick={() => setShowPasswordForm(!showPasswordForm)}
                className="w-full btn-secondary text-left"
              >
                <Lock className="w-4 h-4 mr-2" />
                {showPasswordForm ? 'Cancelar Cambio' : 'Cambiar Contraseña'}
              </button>
              <button 
                onClick={() => setShowNotifications(!showNotifications)}
                className="w-full btn-secondary text-left"
              >
                <Bell className="w-4 h-4 mr-2" />
                {showNotifications ? 'Cancelar Config' : 'Configurar Notificaciones'}
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
