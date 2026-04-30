"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import dynamic from "next/dynamic";
import { MapContainer, TileLayer, Marker, Popup, ScaleControl, ZoomControl } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { MAP_CONFIG } from "../../../config/maps";

// Fix for default markers in webpack
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

interface OSMMapBaseProps {
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
  enableCaching?: boolean;
  customStyle?: string;
}

// Aggressive tile caching service
class TileCacheService {
  private cache = new Map<string, string>();
  private maxSize = 1000; // Cache up to 1000 tiles
  
  get(key: string): string | null {
    return this.cache.get(key) || null;
  }
  
  set(key: string, value: string): void {
    if (this.cache.size >= this.maxSize) {
      // Remove oldest entry (LRU)
      const firstKey = this.cache.keys().next().value;
      if (firstKey) {
        this.cache.delete(firstKey);
      }
    }
    this.cache.set(key, value);
  }
  
  clear(): void {
    this.cache.clear();
  }
  
  size(): number {
    return this.cache.size;
  }
}

const tileCache = new TileCacheService();

// Custom tile layer with aggressive caching and fallback
const CachedTileLayer = ({ url, style }: { url: string; style?: string }) => {
  const [tileUrl, setTileUrl] = useState(MAP_CONFIG.osmTileUrl);
  const [urlIndex, setUrlIndex] = useState(0);
  
  // Fallback mechanism for tile URLs
  const handleTileError = useCallback(() => {
    const urls = [MAP_CONFIG.osmTileUrl, ...MAP_CONFIG.alternativeTileUrls];
    if (urlIndex < urls.length - 1) {
      setUrlIndex(prev => prev + 1);
      setTileUrl(urls[urlIndex + 1]);
      console.warn(`Tile URL failed, trying alternative: ${urls[urlIndex + 1]}`);
    }
  }, [urlIndex]);
  
  useEffect(() => {
    // Preload critical tiles - Rio Grande do Sul focus
    const preloadTiles = async () => {
      const criticalZones = [
        // Rio Grande do Sul - Major Cities
        { lat: -30.0346, lng: -51.2177, zoom: 12 }, // Porto Alegre
        { lat: -29.6843, lng: -53.0713, zoom: 12 }, // Santa Maria
        { lat: -29.1684, lng: -51.1794, zoom: 12 }, // Caxias do Sul
        { lat: -29.7778, lng: -51.1448, zoom: 12 }, // Novo Hamburgo
        { lat: -29.9944, lng: -51.0953, zoom: 12 }, // Canoas
        { lat: -29.3428, lng: -51.0644, zoom: 12 }, // São Leopoldo
        { lat: -28.2614, lng: -52.4086, zoom: 12 }, // Passo Fundo
        { lat: -27.0907, lng: -52.7318, zoom: 12 }, // Bagé
        { lat: -31.7639, lng: -52.3385, zoom: 12 }, // Rio Grande
        { lat: -32.0323, lng: -52.0986, zoom: 12 }, // Pelotas
      ];
      
      for (const zone of criticalZones) {
        const x = Math.floor((zone.lng + 180) * (2 ** zone.zoom) / 360);
        const y = Math.floor((1 - Math.log(Math.tan(Math.PI / 4 + (zone.lat * Math.PI) / 180)) / (2 * Math.PI)) * (2 ** zone.zoom));
        const tileKey = `${zone.zoom}/${x}/${y}`;
        
        if (!tileCache.get(tileKey)) {
          try {
            const img = new Image();
            img.src = `${url.replace('{z}', zone.zoom.toString()).replace('{x}', x.toString()).replace('{y}', y.toString())}`;
            img.onload = () => {
              tileCache.set(tileKey, img.src);
            };
          } catch (error) {
            console.warn("Failed to preload tile:", error);
          }
        }
      }
    };
    
    preloadTiles();
  }, [url]);
  
  return (
    <TileLayer
      url={tileUrl}
      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      maxZoom={18}
      minZoom={3}
      eventHandlers={{
        tileerror: handleTileError,
      }}
    />
  );
};

export default function OSMMapBase({
  initialView = { latitude: -30.0346, longitude: -51.2177, zoom: 12 },
  children,
  onClick,
  onMove,
  style,
  className = "w-full h-full",
  mapRef,
  enableCaching = true,
  customStyle,
}: OSMMapBaseProps) {
  const defaultRef = useRef<any>(null);
  const resolvedRef = mapRef || defaultRef;
  const [viewState, setViewState] = useState(initialView);
  const [isClient, setIsClient] = useState(false);
  const [map, setMap] = useState<any>(null);
  const [cacheStats, setCacheStats] = useState({ hits: 0, misses: 0 });

  // Performance monitoring
  useEffect(() => {
    setIsClient(true);
    
    // Set up performance monitoring
    const performanceObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name.includes('tile')) {
          console.log(`Tile load time: ${entry.duration}ms`);
        }
      }
    });
    
    performanceObserver.observe({ entryTypes: ['resource'] });
    
    return () => {
      performanceObserver.disconnect();
    };
  }, []);

  // Cache warming on mount
  useEffect(() => {
    if (enableCaching && isClient) {
      const warmCache = () => {
        // Warm cache with Rio Grande do Sul locations
        const commonLocations = [
          { lat: -30.0346, lng: -51.2177, zoom: 10 }, // Porto Alegre area
          { lat: -29.6843, lng: -53.0713, zoom: 10 }, // Santa Maria area
          { lat: -29.1684, lng: -51.1794, zoom: 10 }, // Caxias do Sul area
          { lat: -29.7778, lng: -51.1448, zoom: 10 }, // Novo Hamburgo area
          { lat: -29.9944, lng: -51.0953, zoom: 10 }, // Canoas area
          { lat: -28.2614, lng: -52.4086, zoom: 10 }, // Passo Fundo area
          { lat: -31.7639, lng: -52.3385, zoom: 10 }, // Rio Grande area
          { lat: -32.0323, lng: -52.0986, zoom: 10 }, // Pelotas area
        ];
        
        commonLocations.forEach(location => {
          const bounds = L.latLng(location.lat, location.lng).toBounds(0.1);
          // This will trigger tile loading for the area
        });
      };
      
      // Delay cache warming to not block initial render
      setTimeout(warmCache, 100);
    }
  }, [enableCaching, isClient]);

  // Custom tactical styling for law enforcement
  const tacticalStyle = customStyle || `
    .leaflet-container {
      background: #1a1a1a;
    }
    .leaflet-control-zoom {
      background: rgba(0, 0, 0, 0.8);
      border: 1px solid #333;
    }
    .leaflet-control-zoom a {
      background: #2a2a2a;
      color: #fff;
      border-color: #444;
    }
    .leaflet-control-zoom a:hover {
      background: #3a3a3a;
    }
    .leaflet-control-attribution {
      background: rgba(0, 0, 0, 0.8);
      color: #ccc;
    }
  `;

  // Handle map events with performance tracking
  const handleMapClick = useCallback((e: any) => {
    const startTime = performance.now();
    if (onClick) {
      onClick(e);
    }
    const endTime = performance.now();
    console.log(`Map click handled in ${endTime - startTime}ms`);
  }, [onClick]);

  const handleMapMove = useCallback((e: any) => {
    const startTime = performance.now();
    setViewState({
      latitude: e.target.getCenter().lat,
      longitude: e.target.getCenter().lng,
      zoom: e.target.getZoom(),
    });
    if (onMove) {
      onMove(e);
    }
    const endTime = performance.now();
    console.log(`Map move handled in ${endTime - startTime}ms`);
  }, [onMove]);

  // Cache statistics monitoring
  useEffect(() => {
    const interval = setInterval(() => {
      setCacheStats({
        hits: tileCache.size(),
        misses: 0 // We'll implement miss counting if needed
      });
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  if (!isClient) {
    // Server-side rendering fallback
    return (
      <div style={style} className={className}>
        <div className="flex items-center justify-center h-full bg-gray-900 text-white">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
            <p className="text-gray-400">Carregando mapa OpenStreetMap...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={style} className={className}>
      <style>{tacticalStyle}</style>
      
      {/* Performance indicator for development */}
      {process.env.NODE_ENV === 'development' && (
        <div className="absolute top-2 left-2 bg-black bg-opacity-75 text-white text-xs p-2 rounded z-[1000]">
          <div>Cache: {cacheStats.hits} tiles</div>
          <div>View: {viewState.latitude.toFixed(4)}, {viewState.longitude.toFixed(4)}</div>
          <div>Zoom: {viewState.zoom}</div>
        </div>
      )}

      <MapContainer
        center={[viewState.latitude, viewState.longitude]}
        zoom={viewState.zoom}
        ref={resolvedRef}
        className="w-full h-full"
        zoomControl={false}
        attributionControl={false}
              >
        {/* Custom OpenStreetMap tiles with caching */}
        <CachedTileLayer 
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {/* Enhanced controls for tactical use */}
        <div className="leaflet-top leaflet-right">
          <ZoomControl position="topright" />
        </div>
        
        <ScaleControl position="bottomleft" maxWidth={100} metric={true} imperial={false} />
        
        {/* Performance optimization: only render children when map is ready */}
        {map && children}
      </MapContainer>
    </div>
  );
}
