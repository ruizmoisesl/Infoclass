import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/axios';
import CreateAssignmentModal from '../components/CreateAssignmentModal';
import FileUpload from '../components/FileUpload';
import {
  FileText,
  Calendar,
  Clock,
  User,
  MessageSquare,
  CheckCircle,
  AlertCircle,
  Edit,
  Save,
  Download,
  File,
  Paperclip,
  Eye,
  X
} from 'lucide-react';
import { format, isAfter, isBefore } from 'date-fns';
import { es } from 'date-fns/locale';
import { toast } from 'react-toastify';

const AssignmentDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [assignment, setAssignment] = useState(null);
  const [submission, setSubmission] = useState(null);
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showEdit, setShowEdit] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submissionContent, setSubmissionContent] = useState('');
  const [feedback, setFeedback] = useState('');
  const [points, setPoints] = useState('');
  const [submissionFiles, setSubmissionFiles] = useState([]);
  const [assignmentFiles, setAssignmentFiles] = useState([]);
  const [submissionFilesMap, setSubmissionFilesMap] = useState({});
  const [selectedPdfFile, setSelectedPdfFile] = useState(null);
  const [showPdfViewer, setShowPdfViewer] = useState(false);
  const [loadingFiles, setLoadingFiles] = useState(new Set());

  // Formateo seguro de fechas para evitar RangeError por valores inválidos
  const safeFormatDate = (value, fmt = 'dd MMM yyyy') => {
    if (!value) return '—';
    try {
      const d = typeof value === 'string' ? new Date(value) : value;
      if (isNaN(d?.getTime?.())) return '—';
      
      // Verificar si la fecha es válida
      if (d.getFullYear() < 1900 || d.getFullYear() > 2100) return '—';
      
      return format(d, fmt, { locale: es });
    } catch (error) {
      console.error('Error formateando fecha:', error, 'Valor:', value);
      return '—';
    }
  };

  // Acciones del profesor sobre la tarea
  const handleArchiveToggle = async () => {
    if (!assignment) return;
    try {
      const next = !assignment.is_archived;
      await api.put(`/api/assignments/${assignment.id}/archive`, { is_archived: next });
      toast.success(next ? 'Tarea archivada' : 'Tarea desarchivada');
      // Refrescar datos
      fetchAssignmentData();
    } catch (error) {
      const msg = error.response?.data?.message || 'Error al actualizar archivo';
      toast.error(msg);
    }
  };

  const handleDelete = async () => {
    if (!assignment) return;
    const confirm = window.confirm('¿Eliminar esta tarea? Esta acción no se puede deshacer.');
    if (!confirm) return;
    try {
      await api.delete(`/api/assignments/${assignment.id}`);
      toast.success('Tarea eliminada');
      navigate('/assignments');
    } catch (error) {
      const msg = error.response?.data?.message || 'Error al eliminar tarea';
      toast.error(msg);
    }
  };

  useEffect(() => {
    fetchAssignmentData();
  }, [id]);

  // Cargar archivos de todas las entregas cuando cambien las entregas
  useEffect(() => {
    if (submissions.length > 0) {
      submissions.forEach(submission => {
        if (!submissionFilesMap[submission.id]) {
          fetchSubmissionFilesById(submission.id);
        }
      });
    }
  }, [submissions]);

  const fetchAssignmentData = async () => {
    setError(null);
    setLoading(true);
    try {
      // 1) Obtener la tarea primero
      const assignmentRes = await api.get(`/api/assignments/${id}`);
      setAssignment(assignmentRes.data);
      
      // Cargar archivos de la tarea
      fetchAssignmentFiles(id);

      // 2) Solo profesores/admin consultan las entregas
      const isPrivileged = user?.role === 'teacher' || user?.role === 'admin';
      if (isPrivileged) {
        const submissionsRes = await api.get(`/api/assignments/${id}/submissions`);
        setSubmissions(submissionsRes.data);
      } else {
        setSubmissions([]);
      }

      // 3) Cargar mi entrega si soy estudiante
      if (user?.role === 'student') {
        try {
          const mySubRes = await api.get(`/api/assignments/${id}/my-submission`);
          const mySub = mySubRes.data || null;
          setSubmission(mySub);
          if (mySub) {
            setSubmissionContent(mySub.content || '');
            // Cargar archivos de la entrega
            fetchSubmissionFiles(mySub.id);
          } else {
            setSubmissionContent('');
            setSubmissionFiles([]);
          }
        } catch (e) {
          // Si 404/403, no hay entrega visible; dejar en null
          setSubmission(null);
          setSubmissionContent('');
        }
      }
    } catch (err) {
      const backendMsg = err.response?.data?.message || err.response?.data?.msg;
      setError(backendMsg || 'No se pudo cargar la tarea');
      if (backendMsg) {
        toast.error(backendMsg);
      }
      console.error('Error al cargar datos de la tarea:', err);
      setAssignment(null);
      setSubmission(null);
      setSubmissions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const response = await api.post(`/api/assignments/${id}/submissions`, {
        content: submissionContent
      });

      setSubmission(response.data);
      setSubmissionContent(response.data?.content || '');
      toast.success('Entrega enviada exitosamente');
      setSubmitting(false);
    } catch (error) {
      const msg = error.response?.data?.message || 'Error al enviar entrega';
      toast.error(msg);
      console.error('Error al enviar entrega:', error);
      setSubmitting(false);
    }
  };

  // Funciones para manejo de archivos
  const fetchSubmissionFiles = async (submissionId) => {
    try {
      const response = await api.get(`/api/submissions/${submissionId}/files`);
      setSubmissionFiles(response.data);
    } catch (error) {
      console.error('Error al cargar archivos:', error);
    }
  };

  // Función para cargar archivos de una entrega específica
  const fetchSubmissionFilesById = async (submissionId) => {
    try {
      const response = await api.get(`/api/submissions/${submissionId}/files`);
      setSubmissionFilesMap(prev => ({
        ...prev,
        [submissionId]: response.data
      }));
    } catch (error) {
      console.error('Error al cargar archivos de la entrega:', error);
    }
  };

  // Función para descargar archivos
  const downloadFile = async (fileId, filename) => {
    try {
      console.log('Iniciando descarga del archivo:', fileId, filename);
      
      const response = await api.get(`/api/files/${fileId}`, {
        responseType: 'blob'
      });
      
      console.log('Respuesta recibida:', response);
      
      // Crear blob y descargar
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.style.display = 'none';
      
      document.body.appendChild(link);
      link.click();
      
      // Limpiar
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success('Archivo descargado exitosamente');
    } catch (error) {
      console.error('Error al descargar archivo:', error);
      const errorMessage = error.response?.data?.message || 'Error al descargar el archivo';
      toast.error(errorMessage);
    }
  };

  // Función para abrir visor PDF
  const openPdfViewer = async (file) => {
    try {
      // Agregar este archivo a la lista de archivos cargando
      setLoadingFiles(prev => new Set(prev).add(file.id));
      console.log('Abriendo PDF:', file);
      
      // Descargar el archivo como blob
      const response = await api.get(`/api/files/${file.id}`, {
        responseType: 'blob'
      });
      
      console.log('PDF descargado:', response);
      
      // Crear blob URL
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const pdfUrl = window.URL.createObjectURL(blob);
      
      setSelectedPdfFile({
        ...file,
        pdfUrl: pdfUrl
      });
      setShowPdfViewer(true);
      
      // Remover este archivo de la lista de archivos cargando
      setLoadingFiles(prev => {
        const newSet = new Set(prev);
        newSet.delete(file.id);
        return newSet;
      });
    } catch (error) {
      console.error('Error al abrir PDF:', error);
      toast.error('Error al abrir el archivo PDF');
      
      // Remover este archivo de la lista de archivos cargando en caso de error
      setLoadingFiles(prev => {
        const newSet = new Set(prev);
        newSet.delete(file.id);
        return newSet;
      });
    }
  };

  // Función para cerrar visor PDF
  const closePdfViewer = () => {
    // Limpiar la URL del blob para evitar memory leaks
    if (selectedPdfFile?.pdfUrl) {
      window.URL.revokeObjectURL(selectedPdfFile.pdfUrl);
    }
    setShowPdfViewer(false);
    setSelectedPdfFile(null);
  };

  // Función para verificar si un archivo es PDF
  const isPdfFile = (filename) => {
    return filename.toLowerCase().endsWith('.pdf');
  };

  const fetchAssignmentFiles = async (assignmentId) => {
    try {
      const response = await api.get(`/api/assignments/${assignmentId}/files`);
      setAssignmentFiles(response.data);
    } catch (error) {
      console.error('Error al cargar archivos de la tarea:', error);
    }
  };

  const handleFileUploaded = (files) => {
    setSubmissionFiles(prev => [...prev, ...files]);
  };

  const handleFileDeleted = (fileId) => {
    setSubmissionFiles(prev => prev.filter(file => file.id !== fileId));
  };

  const handleGrade = async (submissionId) => {
    try {
      await api.post(`/api/submissions/${submissionId}/grade`, {
        points_earned: points,
        feedback: feedback
      });

      // Recargar datos
      fetchAssignmentData();
      setPoints('');
      setFeedback('');
      toast.success('Calificación guardada');
    } catch (error) {
      const msg = error.response?.data?.message || 'Error al calificar';
      toast.error(msg);
      console.error('Error al calificar:', error);
    }
  };

  const getAssignmentStatus = () => {
    if (!assignment) return 'pending';
    
    const now = new Date();
    const dueDate = new Date(assignment.due_date);
    
    if (submission && submission.status === 'submitted') {
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!assignment) {
    return (
      <div className="text-center py-12">
        <FileText className="w-16 h-16 text-secondary-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-secondary-900 mb-2">
          {error ? 'Error cargando la tarea' : 'Tarea no encontrada'}
        </h3>
        <p className="text-secondary-600 mb-4">
          {error || 'La tarea que buscas no existe o no tienes acceso a ella.'}
        </p>
        <Link to="/assignments" className="btn-primary">
          Volver a Tareas
        </Link>
      </div>
    );
  }

  const status = getAssignmentStatus();

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header de la Tarea */}
      <div className="card">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <FileText className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-secondary-900 mb-2">
                {assignment.title}
              </h1>
              <p className="text-secondary-600 mb-2">
                {assignment.course?.name || 'Curso no disponible'}
              </p>
              <div className="flex items-center space-x-4 text-sm text-secondary-600">
                <div className="flex items-center">
                  <Calendar className="w-4 h-4 mr-1" />
                  <span>Fecha de entrega: {safeFormatDate(assignment.due_date, 'dd MMM yyyy')}</span>
                </div>
                <div className="flex items-center">
                  <Clock className="w-4 h-4 mr-1" />
                  <span>Hora: {safeFormatDate(assignment.due_date, 'HH:mm')}</span>
                </div>
                <div className="flex items-center">
                  <span className="text-xs text-secondary-500">
                    Creado: {safeFormatDate(assignment.created_at, 'dd MMM yyyy')}
                  </span>
                </div>
                <div className="text-sm font-medium">
                  {assignment.max_points} puntos
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(status)}`}>
              {getStatusIcon(status)}
              <span className="ml-1 capitalize">
                {status === 'due-soon' ? 'Por vencer' : status}
              </span>
            </span>

            {user?.role === 'teacher' && (
              <div className="flex items-center space-x-2">
                <button className="btn-secondary" onClick={() => setShowEdit(true)}>
                  <Edit className="w-4 h-4 mr-2" />
                  Editar
                </button>
                <button className="btn-secondary" onClick={handleArchiveToggle}>
                  {assignment.is_archived ? 'Desarchivar' : 'Archivar'}
                </button>
                <button className="btn-secondary" onClick={handleDelete}>
                  Eliminar
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Descripción */}
        <div className="prose max-w-none">
          <h3 className="text-lg font-semibold text-secondary-900 mb-2">
            Descripción
          </h3>
          <div className="text-secondary-700 whitespace-pre-wrap">
            {assignment.description || 'Sin descripción'}
          </div>
          
          {/* Archivos adjuntos de la tarea */}
          {assignmentFiles.length > 0 && (
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="text-sm font-medium text-blue-800 mb-3 flex items-center">
                <FileText className="w-4 h-4 mr-2" />
                Archivos adjuntos de la tarea ({assignmentFiles.length})
              </h4>
              <div className="space-y-2">
                {assignmentFiles.map((file) => (
                  <div key={file.id} className="flex items-center justify-between p-3 bg-white rounded border border-blue-100">
                    <div className="flex items-center flex-1 min-w-0">
                      <File className="w-5 h-5 mr-3 text-blue-600 flex-shrink-0" />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-blue-800 truncate">
                          {file.original_filename || file.filename}
                        </p>
                        <p className="text-xs text-blue-600">
                          {(file.file_size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 ml-3">
                      {isPdfFile(file.original_filename || file.filename) && (
                        <button
                          onClick={() => openPdfViewer(file)}
                          disabled={loadingFiles.has(file.id)}
                          className="flex items-center space-x-1 text-blue-600 hover:text-blue-700 text-sm font-medium px-2 py-1 rounded hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <Eye className="w-4 h-4" />
                          <span>{loadingFiles.has(file.id) ? 'Cargando...' : 'Ver'}</span>
                        </button>
                      )}
                      <button
                        onClick={() => downloadFile(file.id, file.original_filename || file.filename)}
                        className="flex items-center space-x-1 text-blue-600 hover:text-blue-700 text-sm font-medium px-2 py-1 rounded hover:bg-blue-50"
                      >
                        <Download className="w-4 h-4" />
                        <span>Descargar</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Entrega del Estudiante */}
      {user?.role === 'student' && (
        <div className="card">
          <h2 className="text-lg font-semibold text-secondary-900 mb-4">
            Mi Entrega
          </h2>

          {submission ? (
            <div className="space-y-4">
              <div className="p-4 bg-secondary-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-secondary-700">
                    Estado: {submission.status}
                  </span>
                  <span className="text-sm text-secondary-600">
                    Enviado: {safeFormatDate(submission.submitted_at, 'dd MMM yyyy HH:mm')}
                  </span>
                </div>
                <div className="text-secondary-700 whitespace-pre-wrap">
                  {submission.content}
                </div>
                {submission.points_earned && (
                  <div className="mt-3 p-3 bg-green-50 rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-green-900">
                        Calificación: {submission.points_earned}/{assignment.max_points}
                      </span>
                      <span className="text-sm  text-green-700">
                        {((submission.points_earned / assignment.max_points) * 100).toFixed(1)}%
                      </span>
                    </div>
                    {submission.feedback && (
                      <div className="mt-2 text-sm text-green-800">
                        <strong>Comentarios:</strong> {submission.feedback}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {submission.status === 'draft' && (
                <form onSubmit={handleSubmit}>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-secondary-700 mb-2">
                      Actualizar Entrega
                    </label>
                    <textarea
                      value={submissionContent}
                      onChange={(e) => setSubmissionContent(e.target.value)}
                      rows={6}
                      className="input-field"
                      placeholder="Escribe tu respuesta aquí..."
                    />
                  </div>
                  
                  {/* Subida de archivos */}
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-secondary-700 mb-2">
                      Archivos Adjuntos
                    </label>
                    <FileUpload
                      submissionId={submission?.id}
                      onFileUploaded={handleFileUploaded}
                      onFileDeleted={handleFileDeleted}
                      existingFiles={submissionFiles}
                      maxFiles={5}
                      maxSizeMB={10}
                    />
                  </div>
                  
                  <div className="flex justify-end space-x-3">
                    <button
                      type="button"
                      className="btn-secondary"
                    >
                      Guardar Borrador
                    </button>
                    <button
                      type="submit"
                      disabled={submitting}
                      className="btn-primary"
                    >
                      {submitting ? 'Enviando...' : 'Enviar Entrega'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-secondary-700 mb-2">
                  Tu Entrega
                </label>
                <textarea
                  value={submissionContent}
                  onChange={(e) => setSubmissionContent(e.target.value)}
                  rows={6}
                  className="input-field"
                  placeholder="Escribe tu respuesta aquí..."
                  required
                />
              </div>
              
              {/* Subida de archivos */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-secondary-700 mb-2">
                  Archivos Adjuntos
                </label>
                <FileUpload
                  assignmentId={assignment?.id}
                  onFileUploaded={handleFileUploaded}
                  onFileDeleted={handleFileDeleted}
                  existingFiles={submissionFiles}
                  maxFiles={5}
                  maxSizeMB={10}
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  className="btn-secondary"
                >
                  Guardar Borrador
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="btn-primary"
                >
                  {submitting ? 'Enviando...' : 'Enviar Entrega'}
                </button>
              </div>
            </form>
          )}
        </div>
      )}

      {/* Entregas para Profesores */}
      {user?.role === 'teacher' && (
        <div className="card">
          <h2 className="text-lg font-semibold text-secondary-900 mb-4">
            Entregas de Estudiantes ({submissions.length})
          </h2>

          <div className="space-y-4">
            {submissions.map((sub) => (
              <div key={sub.id} className="p-4 bg-secondary-50 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                      <User className="w-4 h-4 text-primary-600" />
                    </div>
                    <div>
                      <p className="font-medium text-secondary-900">
                        {sub.student.first_name} {sub.student.last_name}
                      </p>
                      <p className="text-sm text-secondary-600">
                        {sub.student.email}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(sub.status)}`}>
                      {sub.status}
                    </span>
                  </div>
                </div>

                {/* Contenido de texto de la entrega */}
                {sub.content && (
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-secondary-700 mb-2 flex items-center">
                      <MessageSquare className="w-4 h-4 mr-2" />
                      Respuesta del estudiante:
                    </h4>
                    <div className="text-secondary-700 whitespace-pre-wrap bg-white p-3 rounded border">
                      {sub.content}
                    </div>
                  </div>
                )}

                {/* Archivos adjuntos */}
                {submissionFilesMap[sub.id] && submissionFilesMap[sub.id].length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-secondary-700 mb-2 flex items-center">
                      <Paperclip className="w-4 h-4 mr-2" />
                      Archivos adjuntos ({submissionFilesMap[sub.id].length}):
                    </h4>
                    <div className="space-y-2">
                      {submissionFilesMap[sub.id].map((file) => (
                        <div key={file.id} className="flex items-center justify-between bg-white p-3 rounded border">
                          <div className="flex items-center space-x-3">
                            <File className="w-5 h-5 text-secondary-500" />
                            <div>
                              <p className="text-sm font-medium text-secondary-900">
                                {file.original_filename}
                              </p>
                              <p className="text-xs text-secondary-500">
                                {(file.file_size / 1024).toFixed(1)} KB
                              </p>
                            </div>
                          </div>
                          <button
                            onClick={() => downloadFile(file.id, file.original_filename)}
                            className="flex items-center space-x-1 text-primary-600 hover:text-primary-700 text-sm font-medium"
                          >
                            <Download className="w-4 h-4" />
                            <span>Descargar</span>
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between text-sm text-secondary-600">
                  <span>
                    Enviado: {safeFormatDate(sub.submitted_at, 'dd MMM yyyy HH:mm')}
                  </span>
                  {sub.points_earned ? (
                    <span className="font-medium text-green-600">
                      {sub.points_earned}/{assignment.max_points} puntos
                    </span>
                  ) : (
                    <span className="text-secondary-500">Sin calificar</span>
                  )}
                </div>

                {!sub.points_earned && (
                  <div className="mt-3 pt-3 border-t border-secondary-200">
                    <div className="flex items-start space-x-3">
                      <input
                        type="number"
                        placeholder="Puntos"
                        value={points}
                        onChange={(e) => setPoints(e.target.value)}
                        className="input-field w-16 text-center px-1 py-1"
                        min="0"
                        max={assignment.max_points}
                        style={{ minWidth: '4.5rem', maxWidth: '5.5rem', height: '4rem' }}
                      />
                      <div className="flex-1 flex">
                        <textarea
                          placeholder="Feedback (opcional)"
                          value={feedback}
                          onChange={(e) => setFeedback(e.target.value)}
                          className="input-field flex-1 min-h-[3rem] resize-y"
                          rows={2}
                        />
                        <button
                          onClick={() => handleGrade(sub.id)}
                          className="btn-primary whitespace-nowrap ml-3 self-end"
                        >
                          <Save className="w-4 h-4 mr-1" />
                          Calificar
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {sub.feedback && (
                  <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-800">
                      <strong>Comentarios:</strong> {sub.feedback}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>

          {submissions.length === 0 && (
            <div className="text-center py-8">
              <FileText className="w-12 h-12 text-secondary-400 mx-auto mb-4" />
              <p className="text-secondary-600">No hay entregas aún</p>
            </div>
          )}
        </div>
      )}

      {/* Comentarios */}
      <div className="card">
        <h2 className="text-lg font-semibold text-secondary-900 mb-4">
          Comentarios
        </h2>
        <div className="space-y-4">
          <div className="flex space-x-3">
            <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-primary-600" />
            </div>
            <div className="flex-1">
              <textarea
                placeholder="Agregar un comentario..."
                rows={3}
                className="input-field"
              />
              <div className="flex justify-end mt-2">
                <button className="btn-primary">
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Comentar
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modal de edición */}
      {user?.role === 'teacher' && assignment && (
        <CreateAssignmentModal
          isOpen={showEdit}
          onClose={() => setShowEdit(false)}
          courseId={assignment.course?.id}
          assignment={{
            id: assignment.id,
            title: assignment.title,
            description: assignment.description,
            due_date: assignment.due_date,
            max_points: assignment.max_points,
            allow_late_submissions: assignment.allow_late_submissions
          }}
          onAssignmentUpdated={() => {
            setShowEdit(false);
            fetchAssignmentData();
          }}
        />
      )}

      {/* Modal del visor PDF */}
      {showPdfViewer && selectedPdfFile && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full h-full max-w-6xl max-h-[90vh] flex flex-col">
            {/* Header del modal */}
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold text-secondary-900 flex items-center">
                <FileText className="w-5 h-5 mr-2 text-blue-600" />
                {selectedPdfFile.original_filename || selectedPdfFile.filename}
              </h3>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => downloadFile(selectedPdfFile.id, selectedPdfFile.original_filename || selectedPdfFile.filename)}
                  className="flex items-center space-x-1 text-blue-600 hover:text-blue-700 px-3 py-1 rounded hover:bg-blue-50"
                >
                  <Download className="w-4 h-4" />
                  <span>Descargar</span>
                </button>
                <button
                  onClick={closePdfViewer}
                  className="p-2 text-secondary-500 hover:text-secondary-700 rounded hover:bg-secondary-100"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
            
            {/* Contenido del PDF */}
            <div className="flex-1 p-4">
              {loadingFiles.has(selectedPdfFile.id) ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-secondary-600">Cargando PDF...</p>
                  </div>
                </div>
              ) : (
                <iframe
                  src={selectedPdfFile.pdfUrl}
                  className="w-full h-full border-0 rounded"
                  title={selectedPdfFile.original_filename || selectedPdfFile.filename}
                  onError={() => {
                    console.error('Error al cargar PDF en iframe');
                    toast.error('Error al cargar el PDF. Intenta descargarlo directamente.');
                  }}
                />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AssignmentDetail;
