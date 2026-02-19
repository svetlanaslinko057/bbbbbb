/**
 * O17: Customer Timeline Component
 * Event stream for customer history
 */

import React, { useState, useEffect } from 'react';
import { 
  Clock, ShoppingCart, Package, CreditCard, 
  FileText, AlertTriangle, Shield, Tag,
  RefreshCw, ChevronDown
} from 'lucide-react';
import analyticsService from '../../services/analyticsService';

const eventTypeConfig = {
  ORDER_CREATED: { icon: ShoppingCart, color: 'blue', label: 'Order Created' },
  ORDER_STATUS: { icon: Package, color: 'purple', label: 'Status Change' },
  PAYMENT: { icon: CreditCard, color: 'green', label: 'Payment' },
  TTN_CREATED: { icon: Package, color: 'indigo', label: 'TTN Created' },
  DELIVERY_STATUS: { icon: Package, color: 'teal', label: 'Delivery Update' },
  CRM_NOTE: { icon: FileText, color: 'gray', label: 'Note' },
  NOTIFICATION: { icon: Clock, color: 'yellow', label: 'Notification' },
  GUARD_INCIDENT: { icon: AlertTriangle, color: 'red', label: 'Incident' },
  RISK_UPDATED: { icon: Shield, color: 'orange', label: 'Risk Update' },
  CUSTOMER_BLOCK: { icon: Shield, color: 'red', label: 'Block Status' },
  CUSTOMER_TAG: { icon: Tag, color: 'purple', label: 'Tag Change' },
};

const CustomerTimeline = ({ userId, onClose }) => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [limit, setLimit] = useState(50);

  useEffect(() => {
    const loadTimeline = async () => {
      if (!userId) return;
      try {
        setLoading(true);
        const data = await analyticsService.getTimeline(userId, limit);
        setEvents(data.events || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadTimeline();
  }, [userId, limit]);

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleString('uk-UA', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const TimelineItem = ({ event }) => {
    const config = eventTypeConfig[event.type] || eventTypeConfig.CRM_NOTE;
    const Icon = config.icon;

    return (
      <div className="flex gap-4">
        {/* Timeline line */}
        <div className="flex flex-col items-center">
          <div className={`w-10 h-10 rounded-full bg-${config.color}-100 flex items-center justify-center`}>
            <Icon className={`w-5 h-5 text-${config.color}-600`} />
          </div>
          <div className="w-0.5 h-full bg-gray-200 mt-2"></div>
        </div>

        {/* Content */}
        <div className="pb-6 flex-1">
          <div className="flex items-center justify-between">
            <span className="font-medium text-gray-900">{event.title}</span>
            <span className="text-xs text-gray-400">{formatDate(event.ts)}</span>
          </div>
          <p className="text-sm text-gray-600 mt-1">{event.description}</p>
        </div>
      </div>
    );
  };

  if (!userId) {
    return (
      <div className="text-center py-8 text-gray-500">
        Select a customer to view timeline
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        {error}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6" data-testid="customer-timeline">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Clock className="w-6 h-6 text-blue-600" />
          <h2 className="text-lg font-semibold">Customer Timeline</h2>
          <span className="text-sm text-gray-500">({events.length} events)</span>
        </div>
        {onClose && (
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            &times;
          </button>
        )}
      </div>

      {/* Timeline */}
      {events.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No events found for this customer
        </div>
      ) : (
        <div className="space-y-0">
          {events.map((event, index) => (
            <TimelineItem key={`${event.ts}-${index}`} event={event} />
          ))}
        </div>
      )}

      {/* Load more */}
      {events.length >= limit && (
        <button
          onClick={() => setLimit(l => l + 50)}
          className="w-full mt-4 py-2 flex items-center justify-center gap-2 text-blue-600 hover:bg-blue-50 rounded-lg"
        >
          <ChevronDown className="w-4 h-4" />
          Load More
        </button>
      )}
    </div>
  );
};

export default CustomerTimeline;
