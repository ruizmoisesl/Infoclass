import React, { useState, useRef } from 'react';
import { Upload, X, File, Download, Trash2 } from 'lucide-react';
import api from '../api/axios';
import { toast } from 'react-toastify';

const FileUpload = ({ 
  submissionId = null, 
  assignmentId = null, 
  announcementId = null,
  onFileUploaded = () => {},
  onFileDeleted = () => {},
  existingFiles = [],
  maxFiles = 5,
  maxSizeMB = 10
}) => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelect = (selectedFiles) => {
    const newFiles = Array.from(selectedFiles).slice(0, maxFiles - files.length);
    
    // Validar tamaño de archivos
    const oversizedFiles = newFiles.filter(file => file.size > maxSizeMB * 1024 * 1024);
    if (oversizedFiles.length > 0) {
      toast.error(`Algunos archivos exceden el tamaño máximo de ${maxSizeMB}MB`);
      return;
    }

    setFiles(prev => [...prev, ...newFiles]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFiles = e.dataTransfer.files;
    handleFileSelect(droppedFiles);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const uploadFiles = async () => {
    if (files.length === 0) return;

    setUploading(true);
    const uploadPromises = files.map(async (file) => {
      const formData = new FormData();
      formData.append('file', file);
      if (submissionId) formData.append('submission_id', submissionId);
      if (assignmentId) formData.append('assignment_id', assignmentId);
      if (announcementId) formData.append('announcement_id', announcementId);

      try {
        const response = await api.post('/api/files/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        return response.data.file;
      } catch (error) {
        console.error('Error uploading file:', error);
        toast.error(`Error al subir ${file.name}`);
        return null;
      }
    });

    try {
      const results = await Promise.all(uploadPromises);
      const successfulUploads = results.filter(result => result !== null);
      
      if (successfulUploads.length > 0) {
        toast.success(`${successfulUploads.length} archivo(s) subido(s) exitosamente`);
        onFileUploaded(successfulUploads);
        setFiles([]);
      }
    } catch (error) {
      console.error('Error uploading files:', error);
      toast.error('Error al subir archivos');
    } finally {
      setUploading(false);
    }
  };

  const deleteFile = async (fileId) => {
    try {
      await api.delete(`/api/files/${fileId}`);
      toast.success('Archivo eliminado exitosamente');
      onFileDeleted(fileId);
    } catch (error) {
      console.error('Error deleting file:', error);
      toast.error('Error al eliminar archivo');
    }
  };

  const downloadFile = async (fileId, filename) => {
    try {
      const response = await api.get(`/api/files/${fileId}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading file:', error);
      toast.error('Error al descargar archivo');
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-4">
      {/* Área de subida */}
      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors duration-200 ${
          dragOver
            ? 'border-primary-400 bg-primary-50'
            : 'border-secondary-300 hover:border-primary-300'
        }`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        <Upload className="w-8 h-8 text-secondary-400 mx-auto mb-2" />
        <p className="text-sm text-secondary-600 mb-2">
          Arrastra archivos aquí o haz clic para seleccionar
        </p>
        <p className="text-xs text-secondary-500 mb-4">
          Máximo {maxFiles} archivos, {maxSizeMB}MB por archivo
        </p>
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="btn-primary text-sm"
          disabled={uploading}
        >
          Seleccionar Archivos
        </button>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => handleFileSelect(e.target.files)}
          accept=".txt,.pdf,.png,.jpg,.jpeg,.gif,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.zip,.rar"
        />
      </div>

      {/* Archivos seleccionados para subir */}
      {files.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-secondary-700">Archivos a subir:</h4>
          {files.map((file, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-secondary-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <File className="w-4 h-4 text-secondary-500" />
                <div>
                  <p className="text-sm font-medium text-secondary-900">{file.name}</p>
                  <p className="text-xs text-secondary-500">{formatFileSize(file.size)}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => removeFile(index)}
                className="p-1 text-secondary-400 hover:text-red-500"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={uploadFiles}
            disabled={uploading}
            className="btn-primary w-full"
          >
            {uploading ? 'Subiendo...' : `Subir ${files.length} archivo(s)`}
          </button>
        </div>
      )}

      {/* Archivos existentes */}
      {existingFiles.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-secondary-700">Archivos adjuntos:</h4>
          {existingFiles.map((file) => (
            <div key={file.id} className="flex items-center justify-between p-3 bg-white border border-secondary-200 rounded-lg">
              <div className="flex items-center space-x-3">
                <File className="w-4 h-4 text-secondary-500" />
                <div>
                  <p className="text-sm font-medium text-secondary-900">{file.filename}</p>
                  <p className="text-xs text-secondary-500">{formatFileSize(file.size)}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => downloadFile(file.id, file.filename)}
                  className="p-1 text-secondary-400 hover:text-primary-600"
                  title="Descargar"
                >
                  <Download className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={() => deleteFile(file.id)}
                  className="p-1 text-secondary-400 hover:text-red-500"
                  title="Eliminar"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FileUpload;
