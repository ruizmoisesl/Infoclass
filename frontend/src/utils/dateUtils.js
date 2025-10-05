import { format } from 'date-fns';
import { es } from 'date-fns/locale';

/**
 * Safely formats a date string using date-fns
 * @param {string|Date} dateString - The date to format
 * @param {string} formatString - The format string (default: 'dd MMM yyyy')
 * @param {object} options - Additional options for date-fns
 * @returns {string} Formatted date string or 'N/A' if invalid
 */
export const formatDate = (dateString, formatString = 'dd MMM yyyy', options = {}) => {
  if (!dateString || dateString === 'null' || dateString === 'undefined') {
    return 'N/A';
  }
  
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      return 'N/A';
    }
    return format(date, formatString, { locale: es, ...options });
  } catch (error) {
    console.error('Error formatting date:', error);
    return 'N/A';
  }
};

/**
 * Formats a date for display in lists (short format)
 * @param {string|Date} dateString - The date to format
 * @returns {string} Formatted date string
 */
export const formatDateShort = (dateString) => {
  return formatDate(dateString, 'dd MMM');
};

/**
 * Formats a date for display in cards (medium format)
 * @param {string|Date} dateString - The date to format
 * @returns {string} Formatted date string
 */
export const formatDateMedium = (dateString) => {
  return formatDate(dateString, 'dd MMM yyyy');
};

/**
 * Formats a date for display with time
 * @param {string|Date} dateString - The date to format
 * @returns {string} Formatted date string
 */
export const formatDateTime = (dateString) => {
  return formatDate(dateString, 'dd MMM yyyy HH:mm');
};

/**
 * Formats a date for display in profile (month and year only)
 * @param {string|Date} dateString - The date to format
 * @returns {string} Formatted date string
 */
export const formatDateProfile = (dateString) => {
  return formatDate(dateString, 'MMM yyyy');
};
