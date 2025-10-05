import React, { useState } from 'react';
import { X, Bell, Pin, MessageSquare } from 'lucide-react';
import api from '../api/axios';
import { toast } from 'react-toastify';

const CreateAnnouncementModal = ({ isOpen, onClose, courseId, onAnnouncementCreated }) => {
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    is_pinned: false
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await api.post(`/api/courses/${courseId}/announcements`, formData);
      toast.success('Anuncio creado exitosamente');
      onAnnouncementCreated(response.data.announcement);
      onClose();
      setFormData({
        title: '',
        content: '',
        is_pinned: false
      });
    } catch (error) {
      const message = error.response?.data?.message || 'Error al crear anuncio';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg w-full max-w-lg">
        <div className="flex items-center justify-between p-6 border-b border-secondary-200">
          <h2 className="text-xl font-semibold text-secondary-900">
            Crear Nuevo Anuncio
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-secondary-100 rounded-lg transition-colors duration-200"
          >
            <X className="w-5 h-5 text-secondary-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-2">
              Título del Anuncio *
            </label>
            <div className="relative">
              <Bell className="absolute left-3 top-1/2 transform -translate-y-1/2 text-secondary-400 w-5 h-5" />
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleChange}
                className="input-field pl-10"
                placeholder="Ej: Recordatorio importante"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-2">
              Contenido *
            </label>
            <div className="relative">
              <MessageSquare className="absolute left-3 top-3 text-secondary-400 w-5 h-5" />
              <textarea
                name="content"
                value={formData.content}
                onChange={handleChange}
                rows={6}
                className="input-field pl-10"
                placeholder="Escribe el contenido del anuncio aquí..."
                required
              />
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="is_pinned"
              name="is_pinned"
              checked={formData.is_pinned}
              onChange={handleChange}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-secondary-300 rounded"
            />
            <label htmlFor="is_pinned" className="flex items-center text-sm text-secondary-700">
              <Pin className="w-4 h-4 mr-1" />
              Fijar anuncio (aparecerá al principio)
            </label>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary"
              disabled={loading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={loading}
            >
              {loading ? 'Creando...' : 'Crear Anuncio'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateAnnouncementModal;
