import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/axios';
import {BookOpen,FileText,Users,TrendingUp,Calendar,Clock,AlertCircle,CheckCircle,Plus} from 'lucide-react';
import { formatDateShort } from '../utils/dateUtils';

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    totalCourses: 0,
    totalAssignments: 0,
    pendingAssignments: 0,
    completedAssignments: 0
  });
  const [recentAssignments, setRecentAssignments] = useState([]);
  const [recentCourses, setRecentCourses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Obtener estadísticas
      const [coursesRes, assignmentsRes] = await Promise.all([
        api.get('/api/courses'),
        api.get('/api/assignments')
      ]);

      const courses = coursesRes.data;
      const assignments = assignmentsRes.data;

      setStats({
        totalCourses: courses.length,
        totalAssignments: assignments.length,
        pendingAssignments: assignments.filter(a => a.status === 'pending').length,
        completedAssignments: assignments.filter(a => a.status === 'completed').length
      });

      setRecentCourses(courses.slice(0, 3));
      setRecentAssignments(assignments.slice(0, 5));
    } catch (error) {
      console.error('Error al cargar datos del dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Buenos días';
    if (hour < 18) return 'Buenas tardes';
    return 'Buenas noches';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'pending':
        return 'text-yellow-600 bg-yellow-100';
      case 'overdue':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-secondary-600 bg-secondary-100';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4" />;
      case 'overdue':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-auto">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">
          {getGreeting()}, {user?.first_name}!
        </h1>
        <p className="text-secondary-600">
          Aquí tienes un resumen de tu actividad en InfoClass
        </p>
      </div>

      {/* Estadísticas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-primary-100 rounded-lg">
              <BookOpen className="w-6 h-6 text-primary-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-secondary-600">Cursos</p>
              <p className="text-2xl font-bold text-secondary-900">{stats.totalCourses}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <FileText className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-secondary-600">Tareas</p>
              <p className="text-2xl font-bold text-secondary-900">{stats.totalAssignments}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <Clock className="w-6 h-6 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-secondary-600">Pendientes</p>
              <p className="text-2xl font-bold text-secondary-900">{stats.pendingAssignments}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-secondary-600">Completadas</p>
              <p className="text-2xl font-bold text-secondary-900">{stats.completedAssignments}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cursos Recientes */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-secondary-900">Cursos Recientes</h2>
            <Link
              to="/courses"
              className="text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              Ver todos
            </Link>
          </div>
          <div className="space-y-3">
            {recentCourses.length > 0 ? (
              recentCourses.map((course) => (
                <div key={course.id} className="flex items-center space-x-3 p-3 bg-secondary-50 rounded-lg">
                  <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                    <BookOpen className="w-5 h-5 text-primary-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-secondary-900 truncate">
                      {course.name}
                    </p>
                    <p className="text-xs text-secondary-500">
                      {course.subject} • {course.section}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-6">
                <BookOpen className="w-12 h-12 text-secondary-400 mx-auto mb-2" />
                <p className="text-secondary-500">No tienes cursos aún</p>
                <Link
                  to="/courses"
                  className="inline-flex items-center mt-2 text-sm text-primary-600 hover:text-primary-700"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Explorar cursos
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Tareas Recientes */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-secondary-900">Tareas Recientes</h2>
            <Link
              to="/assignments"
              className="text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              Ver todas
            </Link>
          </div>
          <div className="space-y-3">
            {recentAssignments.length > 0 ? (
              recentAssignments.map((assignment) => (
                <div key={assignment.id} className="flex items-center space-x-3 p-3 bg-secondary-50 rounded-lg">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <FileText className="w-5 h-5 text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-secondary-900 truncate">
                      {assignment.title}
                    </p>
                    <div className="flex items-center space-x-2 mt-1">
                      <Calendar className="w-3 h-3 text-secondary-400" />
                      <p className="text-xs text-secondary-500">
                        {formatDateShort(assignment.due_date)}
                      </p>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(assignment.status)}`}>
                        {getStatusIcon(assignment.status)}
                        <span className="ml-1 capitalize">{assignment.status}</span>
                      </span>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-6">
                <FileText className="w-12 h-12 text-secondary-400 mx-auto mb-2" />
                <p className="text-secondary-500">No tienes tareas asignadas</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Acciones Rápidas */}
      <div className="card">
        <h2 className="text-lg font-semibold text-secondary-900 mb-4">Acciones Rápidas</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/courses"
            className="flex items-center p-4 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors duration-200"
          >
            <BookOpen className="w-5 h-5 text-primary-600 mr-3" />
            <div>
              <p className="font-medium text-primary-900">Explorar Cursos</p>
              <p className="text-sm text-primary-700">Encuentra nuevos cursos</p>
            </div>
          </Link>

          <Link
            to="/assignments"
            className="flex items-center p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors duration-200"
          >
            <FileText className="w-5 h-5 text-blue-600 mr-3" />
            <div>
              <p className="font-medium text-blue-900">Ver Tareas</p>
              <p className="text-sm text-blue-700">Revisa tus asignaciones</p>
            </div>
          </Link>

          <Link
            to="/profile"
            className="flex items-center p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors duration-200"
          >
            <Users className="w-5 h-5 text-green-600 mr-3" />
            <div>
              <p className="font-medium text-green-900">Mi Perfil</p>
              <p className="text-sm text-green-700">Actualiza tu información</p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
