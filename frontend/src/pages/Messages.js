import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/axios';
import {
  MessageSquare,
  Send,
  User,
  Mail,
  Clock,
  Check,
  Plus,
  Search,
  Filter
} from 'lucide-react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import MessageModal from '../components/MessageModal';

const Messages = () => {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showMessageModal, setShowMessageModal] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all'); // all, sent, received, unread

  useEffect(() => {
    fetchMessages();
  }, []);

  const fetchMessages = async () => {
    try {
      const response = await api.get('/api/messages');
      setMessages(response.data);
    } catch (error) {
      console.error('Error al cargar mensajes:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMessageClick = async (message) => {
    if (!message.is_read && message.receiver_id === user.id) {
      try {
        await api.put(`/api/messages/${message.id}/read`);
        message.is_read = true;
        setMessages([...messages]);
      } catch (error) {
        console.error('Error al marcar mensaje como leído:', error);
      }
    }
    setSelectedMessage(message);
  };

  const filteredMessages = messages.filter(message => {
    const matchesSearch = 
      message.subject?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      message.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
      message.sender.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      message.sender.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      message.receiver.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      message.receiver.last_name.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesFilter = 
      filterType === 'all' ||
      (filterType === 'sent' && message.sender_id === user.id) ||
      (filterType === 'received' && message.receiver_id === user.id) ||
      (filterType === 'unread' && !message.is_read && message.receiver_id === user.id);

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
          <h1 className="text-2xl font-bold text-secondary-900">Mensajes</h1>
          <p className="text-secondary-600">
            Comunícate con otros usuarios de la plataforma
          </p>
        </div>
        
        <button
          onClick={() => setShowMessageModal(true)}
          className="btn-primary mt-4 sm:mt-0"
        >
          <Plus className="w-4 h-4 mr-2" />
          Nuevo Mensaje
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lista de Mensajes */}
        <div className="lg:col-span-1">
          <div className="card">
            {/* Filtros y Búsqueda */}
            <div className="space-y-4 mb-6">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-secondary-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Buscar mensajes..."
                  className="input-field pl-10"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              <select
                className="input-field"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
              >
                <option value="all">Todos los mensajes</option>
                <option value="sent">Enviados</option>
                <option value="received">Recibidos</option>
                <option value="unread">No leídos</option>
              </select>
            </div>

            {/* Lista de Mensajes */}
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {filteredMessages.map((message) => {
                const isFromMe = message.sender_id === user.id;
                const otherUser = isFromMe ? message.receiver : message.sender;
                
                return (
                  <div
                    key={message.id}
                    onClick={() => handleMessageClick(message)}
                    className={`p-3 rounded-lg cursor-pointer transition-colors duration-200 ${
                      selectedMessage?.id === message.id
                        ? 'bg-primary-50 border-primary-200'
                        : 'hover:bg-secondary-50'
                    } ${!message.is_read && message.receiver_id === user.id ? 'bg-blue-50' : ''}`}
                  >
                    <div className="flex items-start space-x-3">
                      <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <User className="w-4 h-4 text-primary-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium text-secondary-900 truncate">
                            {otherUser.first_name} {otherUser.last_name}
                          </p>
                          <div className="flex items-center space-x-1">
                            {!message.is_read && message.receiver_id === user.id && (
                              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                            )}
                            <span className="text-xs text-secondary-500">
                              {format(new Date(message.created_at), 'dd MMM', { locale: es })}
                            </span>
                          </div>
                        </div>
                        <p className="text-sm text-secondary-600 truncate">
                          {message.subject || 'Sin asunto'}
                        </p>
                        <p className="text-xs text-secondary-500 truncate">
                          {message.content}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {filteredMessages.length === 0 && (
              <div className="text-center py-8">
                <MessageSquare className="w-12 h-12 text-secondary-400 mx-auto mb-4" />
                <p className="text-secondary-600">
                  {searchTerm ? 'No se encontraron mensajes' : 'No tienes mensajes aún'}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Vista de Mensaje Seleccionado */}
        <div className="lg:col-span-2">
          {selectedMessage ? (
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                    <User className="w-5 h-5 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-secondary-900">
                      {selectedMessage.sender.first_name} {selectedMessage.sender.last_name}
                    </h3>
                    <p className="text-sm text-secondary-600">
                      {selectedMessage.sender.email}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-secondary-600">
                    {format(new Date(selectedMessage.created_at), 'dd MMM yyyy HH:mm', { locale: es })}
                  </p>
                  {selectedMessage.is_read && (
                    <div className="flex items-center text-xs text-green-600 mt-1">
                      <Check className="w-3 h-3 mr-1" />
                      Leído
                    </div>
                  )}
                </div>
              </div>

              {selectedMessage.subject && (
                <div className="mb-4">
                  <h4 className="font-medium text-secondary-900">
                    {selectedMessage.subject}
                  </h4>
                </div>
              )}

              <div className="prose max-w-none">
                <p className="text-secondary-700 whitespace-pre-wrap">
                  {selectedMessage.content}
                </p>
              </div>

              <div className="mt-6 pt-4 border-t border-secondary-200">
                <button
                  onClick={() => setShowMessageModal(true)}
                  className="btn-primary"
                >
                  <Send className="w-4 h-4 mr-2" />
                  Responder
                </button>
              </div>
            </div>
          ) : (
            <div className="card text-center py-12">
              <MessageSquare className="w-16 h-16 text-secondary-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-secondary-900 mb-2">
                Selecciona un mensaje
              </h3>
              <p className="text-secondary-600">
                Elige un mensaje de la lista para ver su contenido
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Modal para Nuevo Mensaje */}
      <MessageModal
        isOpen={showMessageModal}
        onClose={() => setShowMessageModal(false)}
        recipient={selectedMessage ? selectedMessage.sender : null}
      />
    </div>
  );
};

export default Messages;
