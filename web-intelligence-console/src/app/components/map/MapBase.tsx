"use client";

import React, { useState, useRef, useEffect } from "react";
import Map, { Marker, Popup, NavigationControl, ScaleControl, GeolocateControl, FullscreenControl } from "react-map-gl";
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
}

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || "";

export default function MapBase({
  initialView = { latitude: -30.0346, longitude: -51.2177, zoom: 12 },
  children,
  onClick,
  onMove,
  style,
  className = "w-full h-full",
}: MapBaseProps) {
  const mapRef = useRef<any>(null);
  const [viewState, setViewState] = useState(initialView);

  return (
    <div style={style} className={className}>
      <Map
        ref={mapRef}
        mapStyle={`https://api.maptiler.com/maps/streets/style.json?key=${MAPBOX_TOKEN}`}
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
