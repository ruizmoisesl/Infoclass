import React, { useEffect, useState } from 'react';
import { X, FileText, Calendar, Star } from 'lucide-react';
import api from '../api/axios';
import { toast } from 'react-toastify';
import FileUpload from './FileUpload';

const CreateAssignmentModal = ({ isOpen, onClose, courseId, onAssignmentCreated, assignment, onAssignmentUpdated }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    due_date: '',
    max_points: 100,
    allow_late_submissions: true
  });
  const [loading, setLoading] = useState(false);
  const [assignmentFiles, setAssignmentFiles] = useState([]);

  // Prefill when editing
  useEffect(() => {
    if (assignment) {
      setFormData({
        title: assignment.title || '',
        description: assignment.description || '',
        // Expecting ISO string; if present, convert to input datetime-local format
        due_date: assignment.due_date ? assignment.due_date.slice(0, 16) : '',
        max_points: assignment.max_points ?? 100,
        allow_late_submissions: assignment.allow_late_submissions ?? true
      });
      // Cargar archivos existentes si se está editando
      if (assignment.id) {
        fetchAssignmentFiles(assignment.id);
      }
    } else {
      setFormData({
        title: '',
        description: '',
        due_date: '',
        max_points: 100,
        allow_late_submissions: true
      });
      setAssignmentFiles([]);
    }
  }, [assignment, isOpen]);

  // Función para cargar archivos de la tarea
  const fetchAssignmentFiles = async (assignmentId) => {
    try {
      const response = await api.get(`/api/assignments/${assignmentId}/files`);
      setAssignmentFiles(response.data);
    } catch (error) {
      console.error('Error al cargar archivos de la tarea:', error);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  // Funciones para manejo de archivos
  const handleFileUploaded = (files) => {
    setAssignmentFiles(prev => [...prev, ...files]);
  };

  const handleFileDeleted = (fileId) => {
    setAssignmentFiles(prev => prev.filter(file => file.id !== fileId));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (assignment?.id) {
        // Edit mode
        await api.put(`/api/assignments/${assignment.id}`, {
          ...formData,
          // Ensure ISO string for backend
          due_date: formData.due_date ? new Date(formData.due_date).toISOString() : null
        });
        toast.success('Tarea actualizada');
        onAssignmentUpdated && onAssignmentUpdated({ ...assignment, ...formData });
      } else {
        // Create mode - crear la tarea primero
        const response = await api.post(`/api/courses/${courseId}/assignments`, {
          ...formData,
          due_date: new Date(formData.due_date).toISOString()
        });
        
        const newAssignment = response.data.assignment;
        
        // Si hay archivos pendientes, asociarlos a la nueva tarea
        if (assignmentFiles.length > 0) {
          for (const file of assignmentFiles) {
            try {
              await api.put(`/api/files/${file.id}`, {
                assignment_id: newAssignment.id
              });
            } catch (error) {
              console.error('Error asociando archivo a la tarea:', error);
            }
          }
        }
        
        toast.success('Tarea creada exitosamente');
        onAssignmentCreated && onAssignmentCreated(newAssignment);
      }
      onClose();
      setFormData({ title: '', description: '', due_date: '', max_points: 100, allow_late_submissions: true });
      setAssignmentFiles([]);
    } catch (error) {
      const message = error.response?.data?.message || (assignment?.id ? 'Error al actualizar tarea' : 'Error al crear tarea');
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg w-full max-w-lg max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-6 border-b border-secondary-200 flex-shrink-0">
          <h2 className="text-xl font-semibold text-secondary-900">
            {assignment?.id ? 'Editar Tarea' : 'Crear Nueva Tarea'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-secondary-100 rounded-lg transition-colors duration-200"
          >
            <X className="w-5 h-5 text-secondary-500" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-2">
              Título de la Tarea *
            </label>
            <div className="relative">
              <FileText className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-secondary-400 w-5 h-5" />
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleChange}
                className="input-field pl-12"
                placeholder="Ej: Ejercicios de Álgebra"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-2">
              Descripción
            </label>
            <div className="relative">
              <FileText className="pointer-events-none absolute left-3 top-3 text-secondary-400 w-5 h-5" />
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows={4}
                className="input-field pl-12"
                placeholder="Describe los detalles de la tarea, instrucciones, materiales necesarios..."
              />
            </div>
            {/* Mostrar archivos adjuntos en la descripción */}
            {assignmentFiles.length > 0 && (
              <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm font-medium text-blue-800 mb-2">Archivos adjuntos:</p>
                <div className="space-y-1">
                  {assignmentFiles.map((file) => (
                    <div key={file.id} className="flex items-center text-sm text-blue-700">
                      <FileText className="w-4 h-4 mr-2" />
                      <span className="truncate">{file.original_filename || file.filename}</span>
                      <span className="ml-2 text-blue-600">
                        ({(file.file_size / 1024).toFixed(1)} KB)
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-secondary-700 mb-2">
                Fecha de Entrega *
              </label>
              <div className="relative">
                <Calendar className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-secondary-400 w-5 h-5" />
                <input
                  type="datetime-local"
                  name="due_date"
                  value={formData.due_date}
                  onChange={handleChange}
                  className="input-field pl-12"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-secondary-700 mb-2">
                Puntuación Máxima
              </label>
              <div className="relative">
                <Star className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-secondary-400 w-5 h-5" />
                <input
                  type="number"
                  name="max_points"
                  value={formData.max_points}
                  onChange={handleChange}
                  className="input-field pl-12 pr-12"
                  min="1"
                  max="1000"
                  step="0.1"
                />
              </div>
            </div>
          </div>

          {/* Subida de archivos para la tarea */}
          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-2">
              Archivos Adjuntos (Opcional)
            </label>
            <FileUpload
              assignmentId={assignment?.id}
              onFileUploaded={handleFileUploaded}
              onFileDeleted={handleFileDeleted}
              existingFiles={assignmentFiles}
              maxFiles={5}
              maxSizeMB={10}
            />
          </div>

          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="allow_late_submissions"
              name="allow_late_submissions"
              checked={formData.allow_late_submissions}
              onChange={handleChange}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-secondary-300 rounded"
            />
            <label htmlFor="allow_late_submissions" className="text-sm text-secondary-700">
              Permitir entregas tardías
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
                {loading ? (assignment?.id ? 'Guardando...' : 'Creando...') : (assignment?.id ? 'Guardar Cambios' : 'Crear Tarea')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CreateAssignmentModal;
