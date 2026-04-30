"use client";

import React, { useState, useRef, useEffect } from "react";
import Map, { Marker, Popup, NavigationControl, ScaleControl, GeolocateControl, FullscreenControl } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";

interface MapBaseProps {
  initialView?: {
    latitude: number;
    longitude: number;
    zoom: number;
  };
  children?: React.ReactNode;
  onClick?: (e: any) => void;
  onMove?: (e: any) => void;
  style?: React.CSSProperties;
  className?: string;
  mapRef?: any;
}

// Usando OpenStreetMap em vez de MapTiler - gratuito e sem necessidade de API key
const MAP_STYLE = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";

export default function MapBase({
  initialView = { latitude: -30.0346, longitude: -51.2177, zoom: 12 },
  children,
  onClick,
  onMove,
  style,
  className = "w-full h-full",
  mapRef,
}: MapBaseProps) {
  const defaultRef = useRef<any>(null);
  const resolvedRef = mapRef || defaultRef;
  const [viewState, setViewState] = useState(initialView);

  return (
    <div style={style} className={className}>
      <Map
        ref={resolvedRef}
        mapStyle={MAP_STYLE}
        initialViewState={viewState}
        onMove={(evt) => {
          setViewState(evt.viewState);
          if (onMove) onMove(evt);
        }}
        onClick={onClick}
        style={{ width: "100%", height: "100%" }}
        attributionControl={false}
      >
        <NavigationControl position="top-right" />
        <ScaleControl position="bottom-left" maxWidth={100} unit="metric" />
        <GeolocateControl position="top-right" />
        <FullscreenControl position="top-right" />
        
        {children}
      </Map>
    </div>
  );
}
