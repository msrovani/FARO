"use client";

import { useEffect, useRef, useCallback } from "react";

// Performance optimization service for OSM maps
export class OSMPerformanceOptimizer {
  private tileCache = new Map<string, HTMLImageElement>();
  private preloadQueue: Array<{ url: string; priority: number }> = [];
  private isPreloading = false;
  private performanceMetrics = {
    tileLoadTimes: [] as number[],
    cacheHitRate: 0,
    totalRequests: 0,
    cacheHits: 0,
  };

  // Aggressive tile preloading for tactical areas - Rio Grande do Sul focus
  private tacticalAreas = [
    // Rio Grande do Sul - Major Cities
    { lat: -30.0346, lng: -51.2177, zoom: 12, name: "Porto Alegre" },
    { lat: -29.6843, lng: -53.0713, zoom: 12, name: "Santa Maria" },
    { lat: -29.1684, lng: -51.1794, zoom: 12, name: "Caxias do Sul" },
    { lat: -29.7778, lng: -51.1448, zoom: 12, name: "Novo Hamburgo" },
    { lat: -29.9944, lng: -51.0953, zoom: 12, name: "Canoas" },
    { lat: -29.3428, lng: -51.0644, zoom: 12, name: "São Leopoldo" },
    { lat: -28.2614, lng: -52.4086, zoom: 12, name: "Passo Fundo" },
    { lat: -27.0907, lng: -52.7318, zoom: 12, name: "Bagé" },
    { lat: -31.7639, lng: -52.3385, zoom: 12, name: "Rio Grande" },
    { lat: -32.0323, lng: -52.0986, zoom: 12, name: "Pelotas" },
    { lat: -28.6394, lng: -53.8151, zoom: 12, name: "Frederico Westphalen" },
    { lat: -27.6404, lng: -54.2045, zoom: 12, name: "Santo Ângelo" },
    { lat: -29.4667, lng: -53.8667, zoom: 12, name: "Uruguaiana" },
    { lat: -30.1288, lng: -51.2261, zoom: 12, name: "Gravataí" },
    { lat: -29.6014, lng: -51.8672, zoom: 12, name: "Viamão" },
  ];

  // Generate tile URL for OpenStreetMap
  private getTileUrl(x: number, y: number, z: number): string {
    return `https://tile.openstreetmap.org/${z}/${x}/${y}.png`;
  }

  // Convert lat/lng to tile coordinates
  private latLngToTile(lat: number, lng: number, zoom: number): { x: number; y: number } {
    const x = Math.floor((lng + 180) * (2 ** zoom) / 360);
    const y = Math.floor((1 - Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 180)) / (2 * Math.PI)) * (2 ** zoom));
    return { x, y };
  }

  // Preload tiles for a specific area
  private preloadArea(area: typeof this.tacticalAreas[0], radius: number = 2): void {
    const center = this.latLngToTile(area.lat, area.lng, area.zoom);
    
    // Preload tiles in a square around the center
    for (let dx = -radius; dx <= radius; dx++) {
      for (let dy = -radius; dy <= radius; dy++) {
        const x = center.x + dx;
        const y = center.y + dy;
        const tileKey = `${area.zoom}/${x}/${y}`;
        
        if (!this.tileCache.has(tileKey)) {
          this.preloadQueue.push({
            url: this.getTileUrl(x, y, area.zoom),
            priority: area.name === "São Paulo" || area.name === "Rio de Janeiro" ? 1 : 2,
          });
        }
      }
    }
  }

  // Process preload queue
  private async processPreloadQueue(): Promise<void> {
    if (this.isPreloading || this.preloadQueue.length === 0) return;
    
    this.isPreloading = true;
    
    // Sort by priority
    this.preloadQueue.sort((a, b) => a.priority - b.priority);
    
    // Process up to 10 tiles at a time to avoid blocking
    const batch = this.preloadQueue.splice(0, 10);
    
    await Promise.all(
      batch.map(({ url }) => this.preloadTile(url))
    );
    
    this.isPreloading = false;
    
    // Continue processing if there are more tiles
    if (this.preloadQueue.length > 0) {
      setTimeout(() => this.processPreloadQueue(), 100);
    }
  }

  // Preload a single tile
  private preloadTile(url: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const startTime = performance.now();
      const img = new Image();
      
      img.onload = () => {
        const loadTime = performance.now() - startTime;
        this.performanceMetrics.tileLoadTimes.push(loadTime);
        this.tileCache.set(url, img);
        resolve();
      };
      
      img.onerror = () => {
        reject(new Error(`Failed to load tile: ${url}`));
      };
      
      img.src = url;
    });
  }

  // Get cached tile or load it
  public async getTile(url: string): Promise<HTMLImageElement> {
    this.performanceMetrics.totalRequests++;
    
    // Check cache first
    if (this.tileCache.has(url)) {
      this.performanceMetrics.cacheHits++;
      this.updateCacheHitRate();
      return this.tileCache.get(url)!;
    }
    
    // Load tile if not cached
    await this.preloadTile(url);
    return this.tileCache.get(url)!;
  }

  // Update cache hit rate
  private updateCacheHitRate(): void {
    this.performanceMetrics.cacheHitRate = 
      (this.performanceMetrics.cacheHits / this.performanceMetrics.totalRequests) * 100;
  }

  // Initialize performance optimization
  public initialize(): void {
    // Preload tactical areas immediately
    this.tacticalAreas.forEach(area => {
      this.preloadArea(area, 2);
    });
    
    // Start processing preload queue
    this.processPreloadQueue();
    
    // Set up periodic cache cleanup
    setInterval(() => {
      this.cleanupCache();
    }, 60000); // Cleanup every minute
  }

  // Clean up old cache entries
  private cleanupCache(): void {
    const maxCacheSize = 500;
    if (this.tileCache.size > maxCacheSize) {
      // Remove oldest entries (simple LRU simulation)
      const entries = Array.from(this.tileCache.entries());
      const toRemove = entries.slice(0, entries.length - maxCacheSize);
      
      toRemove.forEach(([url]) => {
        this.tileCache.delete(url);
      });
    }
  }

  // Get performance metrics
  public getMetrics() {
    const avgLoadTime = this.performanceMetrics.tileLoadTimes.length > 0
      ? this.performanceMetrics.tileLoadTimes.reduce((a, b) => a + b, 0) / this.performanceMetrics.tileLoadTimes.length
      : 0;
    
    return {
      cacheHitRate: this.performanceMetrics.cacheHitRate,
      averageTileLoadTime: avgLoadTime,
      cacheSize: this.tileCache.size,
      totalRequests: this.performanceMetrics.totalRequests,
      preloadQueueSize: this.preloadQueue.length,
    };
  }

  // Preload tiles for current view
  public preloadForView(lat: number, lng: number, zoom: number, radius: number = 1): void {
    const center = this.latLngToTile(lat, lng, zoom);
    
    for (let dx = -radius; dx <= radius; dx++) {
      for (let dy = -radius; dy <= radius; dy++) {
        const x = center.x + dx;
        const y = center.y + dy;
        const url = this.getTileUrl(x, y, zoom);
        
        if (!this.tileCache.has(url)) {
          this.preloadQueue.push({ url, priority: 0 });
        }
      }
    }
    
    this.processPreloadQueue();
  }
}

// React hook for performance optimization
export function useOSMPerformanceOptimizer() {
  const optimizerRef = useRef<OSMPerformanceOptimizer>();
  
  useEffect(() => {
    optimizerRef.current = new OSMPerformanceOptimizer();
    optimizerRef.current.initialize();
    
    return () => {
      // Cleanup if needed
    };
  }, []);
  
  const preloadForView = useCallback((lat: number, lng: number, zoom: number, radius?: number) => {
    optimizerRef.current?.preloadForView(lat, lng, zoom, radius);
  }, []);
  
  const getMetrics = useCallback(() => {
    return optimizerRef.current?.getMetrics() || null;
  }, []);
  
  return {
    preloadForView,
    getMetrics,
  };
}
