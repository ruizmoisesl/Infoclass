import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/axios';
import CreateAssignmentModal from '../components/CreateAssignmentModal';
import {
  FileText,
  Plus,
  Search,
  Calendar,
  Clock,
  CheckCircle,
  AlertCircle,
  Edit,
  Trash2
} from 'lucide-react';
import { format, isAfter, isBefore } from 'date-fns';
import { es } from 'date-fns/locale';
import { toast } from 'react-toastify';

const Assignments = () => {
  const { user } = useAuth();
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [showModal, setShowModal] = useState(false);
  const [editingAssignment, setEditingAssignment] = useState(null);

  // Formateo seguro de fechas para evitar RangeError cuando due_date es inválido
  const safeFormatDate = (value, fmt = 'dd MMM yyyy') => {
    if (!value) return '—';
    try {
      const d = typeof value === 'string' ? new Date(value) : value;
      if (isNaN(d?.getTime?.())) return '—';
      return format(d, fmt, { locale: es });
    } catch (_) {
      return '—';
    }
  };

  useEffect(() => {
    fetchAssignments();
  }, []);

  const fetchAssignments = async () => {
    try {
      const response = await api.get('/api/assignments');
      setAssignments(response.data);
    } catch (error) {
      console.error('Error al cargar tareas:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (assignment) => {
    setEditingAssignment(assignment);
    setShowModal(true);
  };

  const handleArchiveToggle = async (assignment) => {
    try {
      const next = !assignment.is_archived;
      await api.put(`/api/assignments/${assignment.id}/archive`, { is_archived: next });
      toast.success(next ? 'Tarea archivada' : 'Tarea desarchivada');
      fetchAssignments();
    } catch (error) {
      const msg = error.response?.data?.message || 'Error al actualizar archivo';
      toast.error(msg);
    }
  };

  const handleDelete = async (assignment) => {
    if (!window.confirm('¿Eliminar esta tarea? Esta acción no se puede deshacer.')) return;
    try {
      await api.delete(`/api/assignments/${assignment.id}`);
      toast.success('Tarea eliminada');
      fetchAssignments();
    } catch (error) {
      const msg = error.response?.data?.message || 'Error al eliminar tarea';
      toast.error(msg);
    }
  };

  const handleAssignmentUpdated = () => {
    setShowModal(false);
    setEditingAssignment(null);
    fetchAssignments();
  };

  const getAssignmentStatus = (assignment) => {
    const now = new Date();
    const dueDate = new Date(assignment.due_date);
    
    if (assignment.submission && assignment.submission.status === 'submitted') {
      return 'submitted';
    }
    
    if (isAfter(now, dueDate)) {
      return 'overdue';
    }
    
    if (isBefore(dueDate, new Date(now.getTime() + 24 * 60 * 60 * 1000))) {
      return 'due-soon';
    }
    
    return 'pending';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'submitted':
        return 'text-green-600 bg-green-100';
      case 'overdue':
        return 'text-red-600 bg-red-100';
      case 'due-soon':
        return 'text-yellow-600 bg-yellow-100';
      default:
        return 'text-secondary-600 bg-secondary-100';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'submitted':
        return <CheckCircle className="w-4 h-4" />;
      case 'overdue':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  const filteredAssignments = assignments.filter(assignment => {
    const matchesSearch = assignment.title.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'all' || getAssignmentStatus(assignment) === filterStatus;
    return matchesSearch && matchesFilter;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Tareas</h1>
          <p className="text-secondary-600">
            {user?.role === 'teacher' ? 'Gestiona las tareas de tus cursos' : 'Revisa y entrega tus tareas'}
          </p>
        </div>
        
        {user?.role === 'teacher' && (
          <button className="btn-primary mt-4 sm:mt-0">
            <Plus className="w-4 h-4 mr-2" />
            Crear Tarea
          </button>
        )}
      </div>

      {/* Filtros y Búsqueda */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-secondary-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Buscar tareas..."
            className="input-field pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <select
          className="input-field"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
        >
          <option value="all">Todas</option>
          <option value="pending">Pendientes</option>
          <option value="due-soon">Por vencer</option>
          <option value="overdue">Vencidas</option>
          <option value="submitted">Entregadas</option>
        </select>
      </div>

      {/* Lista de Tareas */}
      <div className="space-y-4">
        {filteredAssignments.map((assignment) => {
          const status = getAssignmentStatus(assignment);
          return (
            <div key={assignment.id} className="card hover:shadow-md transition-shadow duration-200">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <FileText className="w-5 h-5 text-blue-600" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-secondary-900">
                        {assignment.title}
                      </h3>
                      <p className="text-sm text-secondary-600">
                        {assignment.course?.name || 'Curso no disponible'}
                      </p>
                    </div>
                  </div>

                  <p className="text-secondary-700 mb-4 line-clamp-2">
                    {assignment.description || 'Sin descripción'}
                  </p>

                  <div className="flex items-center space-x-4 text-sm text-secondary-600">
                    <div className="flex items-center">
                      <Calendar className="w-4 h-4 mr-1" />
                      {safeFormatDate(assignment.due_date)}
                    </div>
                    <div className="flex items-center">
                      <Clock className="w-4 h-4 mr-1" />
                      {safeFormatDate(assignment.due_date, 'HH:mm')}
                    </div>
                    <div className="text-sm font-medium">
                      {assignment.max_points} puntos
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(status)}`}>
                    {getStatusIcon(status)}
                    <span className="ml-1 capitalize">
                      {status === 'due-soon' ? 'Por vencer' : status}
                    </span>
                  </span>

                  {user?.role === 'teacher' && (
                    <div className="flex items-center space-x-2">
                      <button className="btn-secondary text-sm" onClick={() => handleEdit(assignment)}>
                        <Edit className="w-4 h-4 mr-1" />
                        Editar
                      </button>
                      <button className="btn-secondary text-sm" onClick={() => handleArchiveToggle(assignment)}>
                        {assignment.is_archived ? 'Desarchivar' : 'Archivar'}
                      </button>
                      <button className="btn-secondary text-sm" onClick={() => handleDelete(assignment)}>
                        <Trash2 className="w-4 h-4 mr-1" />
                        Eliminar
                      </button>
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between">
                <div className="flex space-x-3">
                  <Link
                    to={`/assignments/${assignment.id}`}
                    className="btn-primary text-sm"
                  >
                    {user?.role === 'teacher' ? 'Ver Detalles' : 'Ver Tarea'}
                  </Link>
                  {user?.role === 'teacher' && (
                    <button className="btn-secondary text-sm">
                      <Edit className="w-4 h-4 mr-1" />
                      Editar
                    </button>
                  )}
                </div>

                {user?.role === 'teacher' && (
                  <div className="text-sm text-secondary-500">
                    {assignment.submissions?.length || 0} entregas
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {filteredAssignments.length === 0 && (
        <div className="text-center py-12">
          <FileText className="w-16 h-16 text-secondary-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-secondary-900 mb-2">
            {searchTerm ? 'No se encontraron tareas' : 'No tienes tareas asignadas'}
          </h3>
          <p className="text-secondary-600 mb-4">
            {searchTerm 
              ? 'Intenta con otros términos de búsqueda'
              : 'Las tareas aparecerán aquí cuando te inscribas en cursos'
            }
          </p>
        </div>
      )}

      {/* Modal para crear/editar tareas: usamos courseId del item cuando se edita */}
      <CreateAssignmentModal
        isOpen={showModal}
        onClose={() => { setShowModal(false); setEditingAssignment(null); }}
        courseId={editingAssignment?.course?.id || null}
        assignment={editingAssignment ? {
          ...editingAssignment,
          // asegurar ISO para prefill
          due_date: editingAssignment?.due_date || ''
        } : null}
        onAssignmentCreated={fetchAssignments}
        onAssignmentUpdated={handleAssignmentUpdated}
      />
    </div>
  );
};

export default Assignments;
