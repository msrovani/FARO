"use client";

import React, { useState } from "react";
import { Marker, Popup, Source, Layer } from "react-map-gl";
import { Route, AlertTriangle } from "lucide-react";

interface SuspiciousRoutePoint {
  latitude: number;
  longitude: number;
}

interface SuspiciousRoute {
  id: string;
  name: string;
  crime_type: string;
  risk_level: string;
  route_points: SuspiciousRoutePoint[];
  direction: string;
  is_active: boolean;
  approval_status: string;
}

interface RouteMarkerProps {
  route: SuspiciousRoute;
  onClick?: () => void;
  editable?: boolean;
  onPointClick?: (index: number) => void;
}

export default function RouteMarker({ route, onClick, editable, onPointClick }: RouteMarkerProps) {
  const [showPopup, setShowPopup] = useState(false);

  // Color based on risk level
  const getColor = (risk: string) => {
    switch (risk) {
      case "critical": return "#dc2626"; // red-600
      case "high": return "#ef4444"; // red-500
      case "medium": return "#f97316"; // orange-500
      case "low": return "#22c55e"; // green-500
      default: return "#6b7280"; // gray-500
    }
  };

  // Line width based on risk
  const getLineWidth = (risk: string) => {
    switch (risk) {
      case "critical": return 6;
      case "high": return 5;
      case "medium": return 4;
      case "low": return 3;
      default: return 2;
    }
  };

  const color = getColor(route.risk_level);
  const lineWidth = getLineWidth(route.risk_level);

  // Create LineString from route points
  const routeGeoJSON = {
    type: "Feature",
    geometry: {
      type: "LineString",
      coordinates: route.route_points.map(p => [p.longitude, p.latitude]),
    },
    properties: {},
  };

  return (
    <>
      {/* Route line */}
      <Source type="geojson" data={routeGeoJSON as any}>
        <Layer
          type="line"
          paint={{
            "line-color": color,
            "line-width": lineWidth,
            "line-opacity": route.is_active ? 0.8 : 0.4,
            "line-dasharray": route.approval_status === "pending" ? [2, 2] : [0],
          }}
        />
      </Source>

      {/* Start marker */}
      {route.route_points.length > 0 && (
        <Marker
          latitude={route.route_points[0].latitude}
          longitude={route.route_points[0].longitude}
          onClick={(e) => {
            e.originalEvent.stopPropagation();
            setShowPopup(!showPopup);
            if (onClick) onClick();
          }}
        >
          <div
            className="cursor-pointer transform hover:scale-110 transition-transform"
            style={{
              backgroundColor: color,
              borderRadius: "50%",
              width: "20px",
              height: "20px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              border: "3px solid white",
              boxShadow: "0 4px 6px rgba(0, 0, 0, 0.3)",
            }}
          >
            <div style={{ width: "8px", height: "8px", backgroundColor: "white", borderRadius: "50%" }} />
          </div>
        </Marker>
      )}

      {/* End marker */}
      {route.route_points.length > 1 && (
        <Marker
          latitude={route.route_points[route.route_points.length - 1].latitude}
          longitude={route.route_points[route.route_points.length - 1].longitude}
          onClick={(e) => {
            e.originalEvent.stopPropagation();
            setShowPopup(!showPopup);
            if (onClick) onClick();
          }}
        >
          <div
            className="cursor-pointer transform hover:scale-110 transition-transform"
            style={{
              backgroundColor: color,
              borderRadius: "50%",
              width: "20px",
              height: "20px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              border: "3px solid white",
              boxShadow: "0 4px 6px rgba(0, 0, 0, 0.3)",
            }}
          >
            <Route size={12} color="white" />
          </div>
        </Marker>
      )}

      {/* Editable points */}
      {editable && route.route_points.map((point, index) => (
        <Marker
          key={index}
          latitude={point.latitude}
          longitude={point.longitude}
          onClick={(e) => {
            e.originalEvent.stopPropagation();
            if (onPointClick) onPointClick(index);
          }}
        >
          <div
            className="cursor-pointer transform hover:scale-110 transition-transform"
            style={{
              backgroundColor: "#3b82f6",
              borderRadius: "50%",
              width: "16px",
              height: "16px",
              border: "2px solid white",
              boxShadow: "0 2px 4px rgba(0, 0, 0, 0.3)",
            }}
          />
        </Marker>
      ))}

      {showPopup && (
        <Popup
          latitude={route.route_points[0].latitude}
          longitude={route.route_points[0].longitude}
          anchor="top"
          onClose={() => setShowPopup(false)}
          closeOnClick={false}
        >
          <div className="p-3 min-w-[200px]">
            <div className="flex items-center gap-2 mb-2">
              <Route size={16} color={color} />
              <h3 className="font-bold text-sm">{route.name}</h3>
            </div>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-600">Tipo:</span>
                <span className="font-semibold">{route.crime_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Risco:</span>
                <span className="font-semibold" style={{ color }}>{route.risk_level}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Direção:</span>
                <span className="font-semibold">{route.direction}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Status:</span>
                <span className="font-semibold">{route.approval_status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Ativa:</span>
                <span className="font-semibold">{route.is_active ? "Sim" : "Não"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Pontos:</span>
                <span className="font-semibold">{route.route_points.length}</span>
              </div>
            </div>
          </div>
        </Popup>
      )}
    </>
  );
}
