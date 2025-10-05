import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/axios';
import { toast } from 'react-toastify';
import CreateCourseModal from '../components/CreateCourseModal';
import {
  BookOpen,
  Plus,
  Search,
  Filter,
  Users,
  Calendar,
  MapPin,
  Code,
  MoreVertical,
  Edit,
  Archive,
  
} from 'lucide-react';
import { formatDateMedium } from '../utils/dateUtils';

const Courses = () => {
  const { user } = useAuth();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [enrollCode, setEnrollCode] = useState('');
  const [enrolling, setEnrolling] = useState(false);

  useEffect(() => {
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    try {
      const response = await api.get('/api/courses');
      setCourses(response.data);
    } catch (error) {
      console.error('Error al cargar cursos:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCourseCreated = () => {
    // Refrescar desde servidor para obtener el objeto completo (incluye teacher, created_at, etc.)
    fetchCourses();
  };

  const handleEnroll = async (e) => {
    e.preventDefault();
    setEnrolling(true);
    try {
      await api.post('/api/courses/enroll', { access_code: enrollCode.trim() });
      toast.success('Te has inscrito al curso exitosamente');
      setShowEnrollModal(false);
      setEnrollCode('');
      // refrescar cursos para que aparezca el nuevo curso inscrito
      setLoading(true);
      await fetchCourses();
    } catch (error) {
      const message = error.response?.data?.message || 'Error al inscribirse';
      toast.error(message);
      console.error('Error al inscribirse:', error);
    } finally {
      setEnrolling(false);
    }
  };

  const filteredCourses = courses.filter(course =>
    course.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    course.subject?.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
          <h1 className="text-2xl font-bold text-secondary-900">Cursos</h1>
          <p className="text-secondary-600">
            {user?.role === 'teacher' ? 'Gestiona tus cursos' : 'Explora y únete a cursos'}
          </p>
        </div>
        
        <div className="mt-4 sm:mt-0 flex space-x-3">
          {user?.role === 'student' && (
            <button
              onClick={() => setShowEnrollModal(true)}
              className="btn-secondary"
            >
              <Code className="w-4 h-4 mr-2" />
              Unirse con Código
            </button>
          )}
          {user?.role === 'teacher' && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn-primary"
            >
              <Plus className="w-4 h-4 mr-2" />
              Crear Curso
            </button>
          )}
        </div>
      </div>

      {/* Filtros y Búsqueda */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-secondary-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Buscar cursos..."
            className="input-field pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <button className="btn-secondary">
          <Filter className="w-4 h-4 mr-2" />
          Filtrar
        </button>
      </div>

      {/* Lista de Cursos */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredCourses.map((course) => (
          <div key={course.id} className="card hover:shadow-md transition-shadow duration-200">
            <div className="flex items-start justify-between mb-4">
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                <BookOpen className="w-6 h-6 text-primary-600" />
              </div>
              <div className="relative">
                <button className="p-2 hover:bg-secondary-100 rounded-lg">
                  <MoreVertical className="w-4 h-4 text-secondary-400" />
                </button>
              </div>
            </div>

            <div className="mb-4">
              <h3 className="text-lg font-semibold text-secondary-900 mb-2">
                {course.name}
              </h3>
              <p className="text-sm text-secondary-600 line-clamp-2">
                {course.description || 'Sin descripción'}
              </p>
            </div>

            <div className="space-y-2 mb-4">
              <div className="flex items-center text-sm text-secondary-600">
                <MapPin className="w-4 h-4 mr-2" />
                {course.room || 'Aula por definir'}
              </div>
              <div className="flex items-center text-sm text-secondary-600">
                <Users className="w-4 h-4 mr-2" />
                {course.teacher?.first_name && course.teacher?.last_name
                  ? `${course.teacher.first_name} ${course.teacher.last_name}`
                  : 'Profesor no asignado'}
              </div>
              <div className="flex items-center text-sm text-secondary-600">
                <Calendar className="w-4 h-4 mr-2" />
                {course.created_at
                  ? formatDateMedium(course.created_at)
                  : ''}
              </div>
            </div>

            <div className="flex items-center justify-between">
              <Link
                to={`/courses/${course.id}`}
                className="btn-primary text-sm"
              >
                Ver Curso
              </Link>
              {user?.role === 'teacher' && (
                <div className="flex space-x-2">
                  <button className="p-2 text-secondary-400 hover:text-secondary-600">
                    <Edit className="w-4 h-4" />
                  </button>
                  <button className="p-2 text-secondary-400 hover:text-red-600">
                    <Archive className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {filteredCourses.length === 0 && (
        <div className="text-center py-12">
          <BookOpen className="w-16 h-16 text-secondary-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-secondary-900 mb-2">
            {searchTerm ? 'No se encontraron cursos' : 'No tienes cursos aún'}
          </h3>
          <p className="text-secondary-600 mb-4">
            {searchTerm 
              ? 'Intenta con otros términos de búsqueda'
              : user?.role === 'teacher' 
                ? 'Crea tu primer curso para comenzar'
                : 'Únete a un curso con un código de acceso'
            }
          </p>
          {!searchTerm && user?.role === 'teacher' && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn-primary"
            >
              <Plus className="w-4 h-4 mr-2" />
              Crear Primer Curso
            </button>
          )}
        </div>
      )}

      {/* Modal de Inscripción */}
      {showEnrollModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-secondary-900 mb-4">
              Unirse a un Curso
            </h3>
            <form onSubmit={handleEnroll}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-secondary-700 mb-2">
                  Código de Acceso
                </label>
                <input
                  type="text"
                  placeholder="Ingresa el código del curso"
                  className="input-field"
                  value={enrollCode}
                  onChange={(e) => setEnrollCode(e.target.value)}
                  required
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowEnrollModal(false)}
                  className="btn-secondary"
                >
                  Cancelar
                </button>
                <button type="submit" className="btn-primary">
                  {enrolling ? 'Uniendo...' : 'Unirse'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal de Crear Curso */}
      <CreateCourseModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCourseCreated={handleCourseCreated}
      />
    </div>
  );
};

export default Courses;
