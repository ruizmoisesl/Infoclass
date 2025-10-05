import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/axios';
import CreateAssignmentModal from '../components/CreateAssignmentModal';
import CreateAnnouncementModal from '../components/CreateAnnouncementModal';
import {
  BookOpen,
  Users,
  FileText,
  Plus,
  Calendar,
  MapPin,
  Code,
  MoreVertical,
  Edit,
  Bell,
  Settings
} from 'lucide-react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

const CourseDetail = () => {
  const { id } = useParams();
  const { user } = useAuth();
  const [course, setCourse] = useState(null);
  const [assignments, setAssignments] = useState([]);
  const [announcements, setAnnouncements] = useState([]);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [showCreateAssignmentModal, setShowCreateAssignmentModal] = useState(false);
  const [showCreateAnnouncementModal, setShowCreateAnnouncementModal] = useState(false);
  const [error, setError] = useState(null);
  const [assignmentSort, setAssignmentSort] = useState('due_date'); // due_date | created_at
  const [announcementSort, setAnnouncementSort] = useState('recent'); // recent | pinned_first
  const [studentSearch, setStudentSearch] = useState('');
  const [includeArchived, setIncludeArchived] = useState(false);
  const [assignmentsError, setAssignmentsError] = useState(null);
  const [announcementsError, setAnnouncementsError] = useState(null);

  // Utilidad para formatear fechas de forma segura
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

  // Helpers de ordenamiento
  const sortedAssignments = [...assignments].sort((a, b) => {
    if (assignmentSort === 'created_at') {
      return new Date(b.created_at || 0) - new Date(a.created_at || 0);
    }
    // por defecto: due_date asc
    return new Date(a.due_date || 0) - new Date(b.due_date || 0);
  });

  const sortedAnnouncements = [...announcements].sort((a, b) => {
    if (announcementSort === 'pinned_first') {
      if ((b.is_pinned ? 1 : 0) !== (a.is_pinned ? 1 : 0)) return (b.is_pinned ? 1 : 0) - (a.is_pinned ? 1 : 0);
      return new Date(b.created_at || 0) - new Date(a.created_at || 0);
    }
    // recientes primero
    return new Date(b.created_at || 0) - new Date(a.created_at || 0);
  });

  const fetchCourseData = useCallback(async () => {
    setError(null);
    setLoading(true);
    setAssignmentsError(null);
    setAnnouncementsError(null);
    try {
      // 1) Obtener curso primero; si falla, mostramos el error y paramos
      const courseRes = await api.get(`/api/courses/${id}`);
      setCourse(courseRes.data);

      // 2) Cargar el resto en paralelo, pero sin romper si alguno falla
      const isPrivileged = user?.role === 'teacher' || user?.role === 'admin';
      const promises = [
        api.get(`/api/courses/${id}/assignments`, { params: { include_archived: includeArchived } }),
        api.get(`/api/courses/${id}/announcements`),
        ...(isPrivileged ? [api.get(`/api/courses/${id}/students`)] : [])
      ];

      const results = await Promise.allSettled(promises);
      const [assignmentsRes, announcementsRes, studentsRes] = results.map(r => r.status === 'fulfilled' ? r.value : r);

      if (assignmentsRes.status === 'rejected') {
        setAssignments([]);
        setAssignmentsError(assignmentsRes.reason?.response?.data?.message || 'No se pudieron cargar las tareas');
      } else {
        setAssignments(assignmentsRes?.data || []);
      }

      if (announcementsRes.status === 'rejected') {
        setAnnouncements([]);
        setAnnouncementsError(announcementsRes.reason?.response?.data?.message || 'No se pudieron cargar los anuncios');
      } else {
        setAnnouncements(announcementsRes?.data || []);
      }
      setStudents((isPrivileged ? studentsRes?.data : []) || []);
    } catch (err) {
      // Extraer mensaje útil del backend
      const backendMsg = err.response?.data?.message || err.response?.data?.msg;
      setError(backendMsg || 'No se pudo cargar el curso');
      console.error('Error al cargar datos del curso:', err);
      setCourse(null);
      setAssignments([]);
      setAnnouncements([]);
      setStudents([]);
    } finally {
      setLoading(false);
    }
  }, [id, user?.role, includeArchived]);

  useEffect(() => {
    fetchCourseData();
  }, [fetchCourseData]);

  const handleAssignmentCreated = (newAssignment) => {
    setAssignments([newAssignment, ...assignments]);
  };

  const handleAnnouncementCreated = (newAnnouncement) => {
    setAnnouncements([newAnnouncement, ...announcements]);
  };

  const getAssignmentStatus = (assignment) => {
    const now = new Date();
    const dueDate = new Date(assignment.due_date);
    
    if (assignment.submission && assignment.submission.status === 'submitted') {
      return 'submitted';
    }
    
    if (now > dueDate) {
      return 'overdue';
    }
    
    if (dueDate - now < 24 * 60 * 60 * 1000) {
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!course) {
    return (
      <div className="text-center py-12">
        <BookOpen className="w-16 h-16 text-secondary-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-secondary-900 mb-2">
          {error ? 'Error cargando el curso' : 'Curso no encontrado'}
        </h3>
        <p className="text-secondary-600 mb-4">
          {error || 'El curso que buscas no existe o no tienes acceso a él.'}
        </p>
        <Link to="/courses" className="btn-primary">
          Volver a Cursos
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header del Curso */}
      <div className="card">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start space-x-4">
            <div className="w-16 h-16 bg-primary-100 rounded-lg flex items-center justify-center">
              <BookOpen className="w-8 h-8 text-primary-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-secondary-900 mb-2">
                {course.name}
              </h1>
              <p className="text-secondary-600 mb-2">
                {course.description || 'Sin descripción'}
              </p>
              <div className="flex items-center space-x-4 text-sm text-secondary-600">
                <div className="flex items-center">
                  <MapPin className="w-4 h-4 mr-1" />
                  {course.room || 'Aula por definir'}
                </div>
                <div className="flex items-center">
                  <Users className="w-4 h-4 mr-1" />
                  {course.teacher.first_name} {course.teacher.last_name}
                </div>
                <div className="flex items-center">
                  <Calendar className="w-4 h-4 mr-1" />
                  {safeFormatDate(course.created_at)}
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {user?.role === 'teacher' && (
              <>
                <button className="btn-secondary">
                  <Settings className="w-4 h-4 mr-2" />
                  Configurar
                </button>
                <button className="btn-primary">
                  <Edit className="w-4 h-4 mr-2" />
                  Editar
                </button>
              </>
            )}
            <button className="p-2 hover:bg-secondary-100 rounded-lg">
              <MoreVertical className="w-5 h-5 text-secondary-400" />
            </button>
          </div>
        </div>

        {/* Código de Acceso */}
        <div className="bg-primary-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-primary-900">Código de Acceso</p>
              <p className="text-sm text-primary-700">
                Comparte este código para que otros se unan al curso
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <code className="bg-white px-3 py-1 rounded border text-lg font-mono text-primary-900">
                {course.access_code}
              </code>
              <button className="btn-secondary">
                <Code className="w-4 h-4 mr-1" />
                Copiar
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Navegación por Pestañas */}
      <div className="border-b border-secondary-200">
        <nav className="flex space-x-8">
          {[
            { id: 'overview', label: 'Resumen', icon: BookOpen },
            { id: 'assignments', label: 'Tareas', icon: FileText },
            { id: 'announcements', label: 'Anuncios', icon: Bell },
            ...(user?.role === 'teacher' || user?.role === 'admin' ? [{ id: 'students', label: 'Estudiantes', icon: Users }] : [])
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-secondary-500 hover:text-secondary-700 hover:border-secondary-300'
                }`}
              >
                <Icon className="w-4 h-4 mr-2" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Contenido de las Pestañas */}
      <div>
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              {/* Anuncios Recientes */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-secondary-900">
                    Anuncios Recientes
                  </h2>
                  {user?.role === 'teacher' && (
                    <button 
                      onClick={() => setShowCreateAnnouncementModal(true)}
                      className="btn-primary"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Nuevo Anuncio
                    </button>
                  )}
                </div>
                <div className="space-y-3">
                  {announcements.slice(0, 3).map((announcement) => (
                    <div key={announcement.id} className="p-4 bg-secondary-50 rounded-lg">
                      <h3 className="font-medium text-secondary-900 mb-1">
                        {announcement.title}
                      </h3>
                      <p className="text-sm text-secondary-600 line-clamp-2">
                        {announcement.content}
                      </p>
                      <p className="text-xs text-secondary-500 mt-2">
                        {safeFormatDate(announcement.created_at)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Tareas Recientes */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-secondary-900">
                    Tareas Recientes
                  </h2>
                  {user?.role === 'teacher' && (
                    <button 
                      onClick={() => setShowCreateAssignmentModal(true)}
                      className="btn-primary"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Nueva Tarea
                    </button>
                  )}
                </div>
                <div className="space-y-3">
                  {assignments.slice(0, 3).map((assignment) => {
                    const status = getAssignmentStatus(assignment);
                    return (
                      <div key={assignment.id} className="p-4 bg-secondary-50 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-medium text-secondary-900">
                            {assignment.title}
                          </h3>
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(status)}`}>
                            {status}
                          </span>
                        </div>
                        <p className="text-sm text-secondary-600 mb-2">
                          {assignment.description}
                        </p>
                        <div className="flex items-center justify-between text-xs text-secondary-500">
                          <span>
                            Vence: {safeFormatDate(assignment.due_date)}
                          </span>
                          <span>{assignment.max_points} puntos</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Información del Curso */}
              <div className="card">
                <h3 className="text-lg font-semibold text-secondary-900 mb-4">
                  Información del Curso
                </h3>
                <div className="space-y-3 text-sm">
                  <div>
                    <span className="font-medium text-secondary-700">Materia:</span>
                    <span className="ml-2 text-secondary-600">{course.subject}</span>
                  </div>
                  <div>
                    <span className="font-medium text-secondary-700">Sección:</span>
                    <span className="ml-2 text-secondary-600">{course.section}</span>
                  </div>
                  <div>
                    <span className="font-medium text-secondary-700">Aula:</span>
                    <span className="ml-2 text-secondary-600">{course.room}</span>
                  </div>
                  <div>
                    <span className="font-medium text-secondary-700">Profesor:</span>
                    <span className="ml-2 text-secondary-600">
                      {course.teacher.first_name} {course.teacher.last_name}
                    </span>
                  </div>
                </div>
              </div>

              {/* Estadísticas */}
              <div className="card">
                <h3 className="text-lg font-semibold text-secondary-900 mb-4">
                  Estadísticas
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-secondary-600">Estudiantes</span>
                    <span className="font-medium text-secondary-900">{course?.students_count ?? students.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-secondary-600">Tareas</span>
                    <span className="font-medium text-secondary-900">{assignments.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-secondary-600">Anuncios</span>
                    <span className="font-medium text-secondary-900">{announcements.length}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'assignments' && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex items-center gap-3">
                <h2 className="text-lg font-semibold text-secondary-900">Tareas del Curso</h2>
                <span className="text-sm text-secondary-500">({assignments.length})</span>
              </div>
              <div className="flex items-center gap-3">
                <label className="inline-flex items-center gap-2 text-sm text-secondary-600">
                  <input type="checkbox" className="h-4 w-4" checked={includeArchived} onChange={(e) => setIncludeArchived(e.target.checked)} />
                  Incluir archivadas
                </label>
                <select
                  className="input-field"
                  value={assignmentSort}
                  onChange={(e) => setAssignmentSort(e.target.value)}
                >
                  <option value="due_date">Ordenar por fecha límite</option>
                  <option value="created_at">Ordenar por creación</option>
                </select>
                {user?.role === 'teacher' && (
                  <button className="btn-primary" onClick={() => setShowCreateAssignmentModal(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Crear Tarea
                  </button>
                )}
              </div>
            </div>

            {assignmentsError && (
              <div className="p-3 rounded bg-red-50 text-red-700 text-sm">{assignmentsError}</div>
            )}

            {sortedAssignments.length > 0 ? (
              <div className="space-y-3">
                {sortedAssignments.map((assignment) => {
                  const status = getAssignmentStatus(assignment);
                  return (
                    <div key={assignment.id} className="card">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-2">
                            <h3 className="text-base font-semibold text-secondary-900">{assignment.title}</h3>
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(status)}`}>
                              {status === 'due-soon' ? 'Por vencer' : status}
                            </span>
                          </div>
                          <p className="text-sm text-secondary-700 mb-3">{assignment.description || 'Sin descripción'}</p>
                          <div className="flex items-center gap-4 text-xs text-secondary-600">
                            <span>Vence: {safeFormatDate(assignment.due_date)}</span>
                            <span>{assignment.max_points} puntos</span>
                          </div>
                        </div>
                        <Link to={`/assignments/${assignment.id}`} className="btn-primary text-sm ml-4">Ver</Link>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-12">
                <FileText className="w-12 h-12 text-secondary-400 mx-auto mb-4" />
                <p className="text-secondary-600 mb-3">No hay tareas en este curso aún</p>
                {user?.role === 'teacher' && (
                  <button className="btn-primary" onClick={() => setShowCreateAssignmentModal(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Crear Tarea
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'announcements' && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex items-center gap-3">
                <h2 className="text-lg font-semibold text-secondary-900">Anuncios del Curso</h2>
                <span className="text-sm text-secondary-500">({announcements.length})</span>
              </div>
              <div className="flex items-center gap-3">
                <select
                  className="input-field"
                  value={announcementSort}
                  onChange={(e) => setAnnouncementSort(e.target.value)}
                >
                  <option value="recent">Más recientes</option>
                  <option value="pinned_first">Fijados primero</option>
                </select>
                {user?.role === 'teacher' && (
                  <button className="btn-primary" onClick={() => setShowCreateAnnouncementModal(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Crear Anuncio
                  </button>
                )}
              </div>
            </div>

            {announcementsError && (
              <div className="p-3 rounded bg-red-50 text-red-700 text-sm">{announcementsError}</div>
            )}

            {sortedAnnouncements.length > 0 ? (
              <div className="space-y-3">
                {sortedAnnouncements.map((announcement) => (
                  <div key={announcement.id} className="card">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-base font-semibold text-secondary-900">
                          {announcement.title} {announcement.is_pinned && <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-primary-100 text-primary-700">Fijado</span>}
                        </h3>
                        <p className="text-sm text-secondary-700 mt-1">{announcement.content}</p>
                        <p className="text-xs text-secondary-500 mt-2">{safeFormatDate(announcement.created_at)}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Bell className="w-12 h-12 text-secondary-400 mx-auto mb-4" />
                <p className="text-secondary-600 mb-3">No hay anuncios en este curso aún</p>
                {user?.role === 'teacher' && (
                  <button className="btn-primary" onClick={() => setShowCreateAnnouncementModal(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Crear Anuncio
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'students' && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex items-center gap-3">
                <h2 className="text-lg font-semibold text-secondary-900">Estudiantes del Curso</h2>
                <span className="text-sm text-secondary-500">({course?.students_count ?? students.length})</span>
              </div>
              <div className="flex items-center gap-3">
                <input
                  type="text"
                  className="input-field"
                  placeholder="Buscar por nombre o email..."
                  value={studentSearch}
                  onChange={(e) => setStudentSearch(e.target.value)}
                />
              </div>
            </div>

            {students && students.length > 0 ? (
              <div className="space-y-3">
                {students
                  .filter((s) => {
                    const q = studentSearch.toLowerCase();
                    return !q || `${s.first_name} ${s.last_name}`.toLowerCase().includes(q) || (s.email || '').toLowerCase().includes(q);
                  })
                  .map((s) => (
                    <div key={s.id} className="card">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                            <Users className="w-5 h-5 text-primary-600" />
                          </div>
                          <div>
                            <p className="font-medium text-secondary-900">{s.first_name} {s.last_name}</p>
                            <p className="text-sm text-secondary-600">{s.email}</p>
                          </div>
                        </div>
                        {user?.role === 'teacher' || user?.role === 'admin' ? (
                          <div className="text-sm text-secondary-500">
                            {/* Espacio para acciones futuras: ver perfil, remover, etc. */}
                          </div>
                        ) : null}
                      </div>
                    </div>
                  ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Users className="w-12 h-12 text-secondary-400 mx-auto mb-4" />
                <p className="text-secondary-600 mb-2">No hay estudiantes inscritos en este curso</p>
                <p className="text-secondary-500 text-sm">Comparte el código de acceso para que se unan.</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modales */}
      <CreateAssignmentModal
        isOpen={showCreateAssignmentModal}
        onClose={() => setShowCreateAssignmentModal(false)}
        courseId={id}
        onAssignmentCreated={handleAssignmentCreated}
      />

      <CreateAnnouncementModal
        isOpen={showCreateAnnouncementModal}
        onClose={() => setShowCreateAnnouncementModal(false)}
        courseId={id}
        onAnnouncementCreated={handleAnnouncementCreated}
      />
    </div>
  );
};

export default CourseDetail;
