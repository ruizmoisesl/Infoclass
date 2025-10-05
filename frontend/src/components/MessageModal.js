import React, { useState, useEffect } from 'react';
import { X, Send, User, Search } from 'lucide-react';
import api from '../api/axios';
import { toast } from 'react-toastify';

const MessageModal = ({ isOpen, onClose, recipient = null }) => {
  const [formData, setFormData] = useState({
    receiver_id: recipient?.id || '',
    subject: '',
    content: ''
  });
  const [users, setUsers] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    if (isOpen && !recipient) {
      fetchUsers();
    }
  }, [isOpen, recipient]);

  const fetchUsers = async () => {
    setSearching(true);
    try {
      const response = await api.get('/api/users');
      setUsers(response.data);
    } catch (error) {
      console.error('Error al cargar usuarios:', error);
    } finally {
      setSearching(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await api.post('/api/messages', formData);
      toast.success('Mensaje enviado exitosamente');
      onClose();
      setFormData({
        receiver_id: '',
        subject: '',
        content: ''
      });
    } catch (error) {
      const message = error.response?.data?.message || 'Error al enviar mensaje';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const filteredUsers = users.filter(user =>
    user.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg w-full max-w-md">
        <div className="flex items-center justify-between p-6 border-b border-secondary-200">
          <h2 className="text-xl font-semibold text-secondary-900">
            Enviar Mensaje
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-secondary-100 rounded-lg transition-colors duration-200"
          >
            <X className="w-5 h-5 text-secondary-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {!recipient && (
            <div>
              <label className="block text-sm font-medium text-secondary-700 mb-2">
                Destinatario *
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-secondary-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Buscar usuario..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="input-field pl-10"
                />
              </div>
              
              {searchTerm && (
                <div className="mt-2 max-h-40 overflow-y-auto border border-secondary-200 rounded-lg">
                  {filteredUsers.map((user) => (
                    <button
                      key={user.id}
                      type="button"
                      onClick={() => {
                        setFormData({ ...formData, receiver_id: user.id });
                        setSearchTerm(`${user.first_name} ${user.last_name}`);
                      }}
                      className="w-full flex items-center space-x-3 p-3 hover:bg-secondary-50 hover:text-secondary-900 text-left"
                    >
                      <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                        <User className="w-4 h-4 text-primary-600" />
                      </div>
                      <div>
                        <p className="font-medium text-secondary-900">
                          {user.first_name} {user.last_name}
                        </p>
                        <p className="text-sm text-secondary-600">{user.email}</p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {recipient && (
            <div className="flex items-center space-x-3 p-3 bg-secondary-50 rounded-lg">
              <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-primary-600" />
              </div>
              <div>
                <p className="font-medium text-secondary-900">
                  {recipient.first_name} {recipient.last_name}
                </p>
                <p className="text-sm text-secondary-600">{recipient.email}</p>
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-2">
              Asunto
            </label>
            <input
              type="text"
              name="subject"
              value={formData.subject}
              onChange={handleChange}
              className="input-field"
              placeholder="Asunto del mensaje (opcional)"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-2">
              Mensaje *
            </label>
            <textarea
              name="content"
              value={formData.content}
              onChange={handleChange}
              rows={4}
              className="input-field"
              placeholder="Escribe tu mensaje aquí..."
              required
            />
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
              disabled={loading || !formData.receiver_id}
            >
              {loading ? 'Enviando...' : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Enviar
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default MessageModal;
