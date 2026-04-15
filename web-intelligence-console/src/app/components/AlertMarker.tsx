"use client";

import React, { useState } from "react";
import { Marker, Popup } from "react-map-gl";
import { AlertOctagon, AlertTriangle, Info } from "lucide-react";

interface Alert {
  alert_type: string;
  plate_number: string;
  severity: string;
  confidence: number;
  details: any;
  triggered_at: string;
  requires_review: boolean;
}

interface AlertMarkerProps {
  alert: Alert;
  location?: { latitude: number; longitude: number };
  onClick?: () => void;
}

export default function AlertMarker({ alert, location, onClick }: AlertMarkerProps) {
  const [showPopup, setShowPopup] = useState(false);

  // Default location if not provided (use coordinates from details if available)
  const markerLocation = location || alert.details?.location || { latitude: -30.0346, longitude: -51.2177 };

  // Color based on severity
  const getColor = (severity: string) => {
    switch (severity) {
      case "critical": return "#dc2626"; // red-600
      case "high": return "#ef4444"; // red-500
      case "medium": return "#f97316"; // orange-500
      case "low": return "#22c55e"; // green-500
      default: return "#6b7280"; // gray-500
    }
  };

  // Icon based on alert type
  const getIcon = (type: string) => {
    switch (type) {
      case "suspicious_route_match": return AlertOctagon;
      case "pattern_drift": return AlertTriangle;
      case "recurring_route": return AlertTriangle;
      default: return Info;
    }
  };

  const color = getColor(alert.severity);
  const Icon = getIcon(alert.alert_type);

  return (
    <>
      <Marker
        latitude={markerLocation.latitude}
        longitude={markerLocation.longitude}
        onClick={(e: any) => {
          e.originalEvent.stopPropagation();
          setShowPopup(!showPopup);
          if (onClick) onClick();
        }}
      >
        <div
          className="cursor-pointer transform hover:scale-110 transition-transform animate-pulse"
          style={{
            backgroundColor: color,
            borderRadius: "50%",
            width: "32px",
            height: "32px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            border: "3px solid white",
            boxShadow: "0 4px 6px rgba(0, 0, 0, 0.4)",
          }}
        >
          <Icon size={18} color="white" />
        </div>
      </Marker>

      {showPopup && (
        <Popup
          latitude={markerLocation.latitude}
          longitude={markerLocation.longitude}
          anchor="top"
          onClose={() => setShowPopup(false)}
          closeOnClick={false}
        >
          <div className="p-3 min-w-[250px]">
            <div className="flex items-center gap-2 mb-2">
              <Icon size={16} color={color} />
              <h3 className="font-bold text-sm">Alerta</h3>
            </div>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-600">Tipo:</span>
                <span className="font-semibold">{alert.alert_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Placa:</span>
                <span className="font-semibold">{alert.plate_number}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Severidade:</span>
                <span className="font-semibold" style={{ color }}>{alert.severity}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Confiança:</span>
                <span className="font-semibold">{(alert.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Revisão:</span>
                <span className="font-semibold">{alert.requires_review ? "Sim" : "Não"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Data:</span>
                <span className="font-semibold">{new Date(alert.triggered_at).toLocaleString()}</span>
              </div>
            </div>
          </div>
        </Popup>
      )}
    </>
  );
}
