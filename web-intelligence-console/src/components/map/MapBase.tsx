"use client";

import React, { useState, useRef, useEffect } from "react";
import dynamic from "next/dynamic";
import { OSMMapBase, OSMUserTraining, useOSMPerformanceOptimizer } from "../maps/osm";

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
  enableOSM?: boolean;
  showTraining?: boolean;
}

export default function MapBase({
  initialView = { latitude: -30.0346, longitude: -51.2177, zoom: 12 },
  children,
  onClick,
  onMove,
  style,
  className = "w-full h-full",
  mapRef,
  enableOSM = true,
  showTraining = false,
}: MapBaseProps) {
  const [showTrainingModal, setShowTrainingModal] = useState(showTraining);
  const [userCompletedTraining, setUserCompletedTraining] = useState(false);
  const { preloadForView, getMetrics } = useOSMPerformanceOptimizer();

  // Check if user has completed training
  useEffect(() => {
    const trainingCompleted = localStorage.getItem('osm-training-completed');
    if (trainingCompleted) {
      setUserCompletedTraining(true);
    }
  }, []);

  // Preload tiles for initial view
  useEffect(() => {
    if (enableOSM) {
      preloadForView(initialView.latitude, initialView.longitude, initialView.zoom, 2);
    }
  }, [initialView, enableOSM, preloadForView]);

  const handleTrainingComplete = () => {
    setShowTrainingModal(false);
    setUserCompletedTraining(true);
    localStorage.setItem('osm-training-completed', 'true');
  };

  const handleTrainingSkip = () => {
    setShowTrainingModal(false);
  };

  // Show training for first-time users
  useEffect(() => {
    if (enableOSM && !userCompletedTraining && !showTrainingModal) {
      setShowTrainingModal(true);
    }
  }, [enableOSM, userCompletedTraining, showTrainingModal]);

  // If OSM is disabled, return null (fallback to old system)
  if (!enableOSM) {
    return (
      <div style={style} className={className}>
        <div className="flex items-center justify-center h-full bg-gray-900 text-white">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
            <p className="text-gray-400">Carregando mapa...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <OSMMapBase
        initialView={initialView}
        children={children}
        onClick={onClick}
        onMove={onMove}
        style={style}
        className={className}
        mapRef={mapRef}
        enableCaching={true}
      />
      
      {showTrainingModal && (
        <OSMUserTraining
          onComplete={handleTrainingComplete}
          onSkip={handleTrainingSkip}
        />
      )}
    </>
  );
}
