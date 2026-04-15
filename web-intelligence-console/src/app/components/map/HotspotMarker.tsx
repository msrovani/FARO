"use client";

import React, { useState } from "react";
import { Marker, Popup, Source, Layer } from "react-map-gl";
import { AlertTriangle, Activity } from "lucide-react";

interface HotspotPoint {
  latitude: number;
  longitude: number;
  observation_count: number;
  suspicion_count: number;
  unique_plates: number;
  radius_meters: number;
  intensity_score: number;
}

interface HotspotMarkerProps {
  hotspot: HotspotPoint;
  onClick?: () => void;
}

export default function HotspotMarker({ hotspot, onClick }: HotspotMarkerProps) {
  const [showPopup, setShowPopup] = useState(false);

  // Color based on intensity score
  const getColor = (intensity: number) => {
    if (intensity >= 0.8) return "#dc2626"; // red-600
    if (intensity >= 0.6) return "#f97316"; // orange-500
    if (intensity >= 0.4) return "#eab308"; // yellow-500
    return "#22c55e"; // green-500
  };

  // Size based on observation count
  const getSize = (count: number) => {
    if (count >= 50) return 40;
    if (count >= 30) return 30;
    if (count >= 20) return 25;
    if (count >= 10) return 20;
    return 15;
  };

  const color = getColor(hotspot.intensity_score);
  const size = getSize(hotspot.observation_count);

  return (
    <>
      {/* Heat-like circle */}
      <Source
        type="geojson"
        data={{
          type: "Feature",
          geometry: {
            type: "Point",
            coordinates: [hotspot.longitude, hotspot.latitude],
          },
          properties: {},
        }}
      >
        <Layer
          type="circle"
          paint={{
            "circle-radius": size,
            "circle-color": color,
            "circle-opacity": 0.6,
            "circle-stroke-width": 2,
            "circle-stroke-color": color,
          }}
        />
      </Source>

      {/* Center marker */}
      <Marker
        latitude={hotspot.latitude}
        longitude={hotspot.longitude}
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
            width: `${size}px`,
            height: `${size}px`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            border: "3px solid white",
            boxShadow: "0 4px 6px rgba(0, 0, 0, 0.3)",
          }}
        >
          <Activity size={size * 0.6} color="white" />
        </div>
      </Marker>

      {showPopup && (
        <Popup
          latitude={hotspot.latitude}
          longitude={hotspot.longitude}
          anchor="top"
          onClose={() => setShowPopup(false)}
          closeOnClick={false}
          style={{ zIndex: 1000 }}
        >
          <div className="p-3 min-w-[200px]">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle size={16} color={color} />
              <h3 className="font-bold text-sm">Hotspot</h3>
            </div>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-600">Intensidade:</span>
                <span className="font-semibold">
                  {(hotspot.intensity_score * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Observações:</span>
                <span className="font-semibold">{hotspot.observation_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Suspeitas:</span>
                <span className="font-semibold">{hotspot.suspicion_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Placas Únicas:</span>
                <span className="font-semibold">{hotspot.unique_plates}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Raio:</span>
                <span className="font-semibold">{hotspot.radius_meters}m</span>
              </div>
            </div>
          </div>
        </Popup>
      )}
    </>
  );
}
