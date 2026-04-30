"use client";

import React, { useState, useCallback } from "react";
import { Image as ImageIcon, AlertCircle, Download, Eye, Settings, Zap } from "lucide-react";

interface UnifiedImageProps {
  imageUrl?: string;
  variants?: {
    thumbnail?: string;
    web?: string;
    storage?: string;
    ocr?: string;
  };
  alt?: string;
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
  showControls?: boolean;
  lazy?: boolean;
  priority?: "high" | "medium" | "low";
  onVariantChange?: (variant: string, url: string) => void;
}

interface ImageMetadata {
  width: number;
  height: number;
  format: string;
  fileSize: number;
  hash: string;
  config: {
    quality: number;
    format: string;
    purpose: string;
  };
}

export function UnifiedImage({
  imageUrl,
  variants,
  alt = "Image",
  size = "md",
  className = "",
  showControls = false,
  lazy = true,
  priority = "medium",
  onVariantChange,
}: UnifiedImageProps) {
  const [currentVariant, setCurrentVariant] = useState<string>("storage");
  const [isLoading, setIsLoading] = useState(true);
  const [imageError, setImageError] = useState(false);
  const [showMetadata, setShowMetadata] = useState(false);
  const [metadata, setMetadata] = useState<ImageMetadata | null>(null);

  // Size configurations
  const sizeClasses = {
    sm: "w-16 h-12",
    md: "w-32 h-24",
    lg: "w-48 h-36",
    xl: "w-64 h-48",
  };

  const sizeClassesContainer = {
    sm: "w-20 h-16",
    md: "w-36 h-28",
    lg: "w-52 h-40",
    xl: "w-68 h-52",
  };

  // Get current image URL based on variant
  const getCurrentUrl = useCallback(() => {
    if (variants && variants[currentVariant as keyof typeof variants]) {
      return variants[currentVariant as keyof typeof variants];
    }
    return imageUrl;
  }, [variants, currentVariant, imageUrl]);

  // Handle image load
  const handleImageLoad = useCallback(() => {
    setIsLoading(false);
    setImageError(false);
  }, []);

  // Handle image error
  const handleImageError = useCallback(() => {
    setIsLoading(false);
    setImageError(true);
  }, []);

  // Handle variant change
  const handleVariantChange = useCallback((variant: string) => {
    setCurrentVariant(variant);
    setIsLoading(true);
    setImageError(false);
    
    const url = getCurrentUrl();
    if (url && onVariantChange) {
      onVariantChange(variant, url);
    }
  }, [getCurrentUrl, onVariantChange]);

  // Fetch metadata
  const fetchMetadata = useCallback(async () => {
    const url = getCurrentUrl();
    if (!url) return;

    try {
      // Extract metadata from image URL or API
      const response = await fetch(`/api/v1/images/info`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ imageUrl: url })
      });
      
      if (response.ok) {
        const data = await response.json();
        setMetadata(data.metadata);
      }
    } catch (error) {
      console.error('Failed to fetch metadata:', error);
    }
  }, [getCurrentUrl]);

  // Placeholder component
  const Placeholder = () => (
    <div className={`${sizeClassesContainer[size]} rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 flex flex-col items-center justify-center ${className}`}>
      <ImageIcon className="h-6 w-6 text-slate-400" />
      {alt && (
        <span className="mt-1 text-xs font-mono font-bold text-slate-500 text-center px-2">
          {alt}
        </span>
      )}
    </div>
  );

  // Loading state
  const LoadingState = () => (
    <div className={`${sizeClassesContainer[size]} relative ${className}`}>
      <div className="absolute inset-0 flex items-center justify-center bg-slate-100 rounded-xl">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-slate-900" />
      </div>
    </div>
  );

  // Error state
  const ErrorState = () => (
    <div className={`${sizeClassesContainer[size]} rounded-xl border-2 border-red-300 bg-red-50 flex flex-col items-center justify-center ${className}`}>
      <AlertCircle className="h-6 w-6 text-red-400" />
      <span className="mt-1 text-xs text-red-600">Failed to load</span>
      {alt && (
        <span className="mt-1 text-xs font-mono text-red-500 text-center px-2">
          {alt}
        </span>
      )}
    </div>
  );

  // Variant selector
  const VariantSelector = () => {
    if (!variants || !showControls) return null;

    const variantOptions = Object.entries(variants).map(([key, url]) => ({
      key,
      label: key.charAt(0).toUpperCase() + key.slice(1),
      url,
      active: currentVariant === key,
    }));

    return (
      <div className="absolute top-2 left-2 bg-black bg-opacity-75 rounded-lg p-1">
        <div className="flex flex-col space-y-1">
          {variantOptions.map(({ key, label, active }) => (
            <button
              key={key}
              onClick={() => handleVariantChange(key)}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                active
                  ? "bg-blue-500 text-white"
                  : "text-white hover:bg-gray-600"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
    );
  };

  // Controls overlay
  const ControlsOverlay = () => {
    if (!showControls) return null;

    return (
      <div className="absolute top-2 right-2 bg-black bg-opacity-75 rounded-lg p-1">
        <div className="flex flex-col space-y-1">
          <button
            onClick={() => setShowMetadata(!showMetadata)}
            className="p-1 text-white hover:bg-gray-600 rounded transition-colors"
            title="Toggle metadata"
          >
            <Settings className="h-4 w-4" />
          </button>
          <button
            onClick={fetchMetadata}
            className="p-1 text-white hover:bg-gray-600 rounded transition-colors"
            title="Refresh metadata"
          >
            <Zap className="h-4 w-4" />
          </button>
          <button
            onClick={() => {
              const url = getCurrentUrl();
              if (url) {
                const link = document.createElement('a');
                link.href = url;
                link.download = `${alt || 'image'}-${currentVariant}.jpg`;
                link.click();
              }
            }}
            className="p-1 text-white hover:bg-gray-600 rounded transition-colors"
            title="Download image"
          >
            <Download className="h-4 w-4" />
          </button>
          <button
            onClick={() => {
              const url = getCurrentUrl();
              if (url) window.open(url, '_blank');
            }}
            className="p-1 text-white hover:bg-gray-600 rounded transition-colors"
            title="View full size"
          >
            <Eye className="h-4 w-4" />
          </button>
        </div>
      </div>
    );
  };

  // Metadata overlay
  const MetadataOverlay = () => {
    if (!showMetadata || !metadata) return null;

    return (
      <div className="absolute bottom-2 left-2 bg-black bg-opacity-75 rounded-lg p-2 max-w-xs">
        <div className="text-xs text-white space-y-1">
          <div><strong>Size:</strong> {metadata.width}×{metadata.height}</div>
          <div><strong>Format:</strong> {metadata.format}</div>
          <div><strong>File size:</strong> {(metadata.fileSize / 1024).toFixed(1)} KB</div>
          <div><strong>Quality:</strong> {metadata.config.quality}%</div>
          <div><strong>Purpose:</strong> {metadata.config.purpose}</div>
          <div><strong>Hash:</strong> {metadata.hash.substring(0, 8)}...</div>
        </div>
      </div>
    );
  };

  // Priority indicator
  const PriorityIndicator = () => {
    if (priority === "low") return null;

    const colors = {
      high: "bg-red-500",
      medium: "bg-yellow-500",
    };

    return (
      <div className={`absolute top-2 right-2 w-2 h-2 rounded-full ${colors[priority]} animate-pulse`} />
    );
  };

  const currentUrl = getCurrentUrl();

  // No image available
  if (!currentUrl || imageError) {
    return <Placeholder />;
  }

  // Loading state
  if (isLoading) {
    return <LoadingState />;
  }

  return (
    <div className={`relative ${sizeClassesContainer[size]} ${className}`}>
      {/* Main image */}
      <img
        src={currentUrl}
        alt={alt}
        className={`${sizeClasses[size]} object-cover rounded-xl border border-slate-200 shadow-sm`}
        loading={lazy ? "lazy" : "eager"}
        onLoad={handleImageLoad}
        onError={handleImageError}
        style={{
          imageRendering: currentVariant === "ocr" ? "pixelated" : "auto",
        }}
      />

      {/* Overlays */}
      <VariantSelector />
      <ControlsOverlay />
      <MetadataOverlay />
      <PriorityIndicator />
    </div>
  );
}

// Hook for unified image handling
export function useUnifiedImage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const processImage = useCallback(async (
    file: File,
    purpose: string = "storage",
    options?: {
      quality?: number;
      format?: string;
      watermark?: boolean;
    }
  ) => {
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('purpose', purpose);
      
      if (options?.quality) formData.append('quality', options.quality.toString());
      if (options?.format) formData.append('format', options.format);
      if (options?.watermark !== undefined) formData.append('watermark', options.watermark.toString());

      const response = await fetch('/api/v1/images/process', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Processing failed: ${response.statusText}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const generateVariants = useCallback(async (
    file: File,
    variants: string[] = ["storage", "web", "thumbnail"]
  ) => {
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('variants', variants.join(','));

      const response = await fetch('/api/v1/images/variants', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Variant generation failed: ${response.statusText}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    processImage,
    generateVariants,
    loading,
    error,
  };
}
