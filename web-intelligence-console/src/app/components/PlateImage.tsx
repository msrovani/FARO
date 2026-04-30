"use client";

import React, { useState } from "react";
import { Image as ImageIcon, AlertCircle } from "lucide-react";

interface PlateImageProps {
  imageUrl?: string;
  plateNumber?: string;
  confidence?: number;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function PlateImage({
  imageUrl,
  plateNumber,
  confidence,
  size = "md",
  className = "",
}: PlateImageProps) {
  const [imageError, setImageError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const sizeClasses = {
    sm: "w-16 h-12",
    md: "w-32 h-24",
    lg: "w-48 h-36",
  };

  const sizeClassesContainer = {
    sm: "w-20 h-16",
    md: "w-36 h-28",
    lg: "w-52 h-40",
  };

  if (!imageUrl || imageError) {
    return (
      <div
        className={`${sizeClassesContainer[size]} rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 flex flex-col items-center justify-center ${className}`}
      >
        <ImageIcon className="h-6 w-6 text-slate-400" />
        {plateNumber && (
          <span className="mt-1 text-xs font-mono font-bold text-slate-500">
            {plateNumber}
          </span>
        )}
      </div>
    );
  }

  return (
    <div className={`relative ${sizeClassesContainer[size]} ${className}`}>
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-100 rounded-xl">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-slate-900" />
        </div>
      )}
      <img
        src={imageUrl}
        alt={`Placa ${plateNumber || "desconhecida"}`}
        className={`${sizeClasses[size]} object-cover rounded-xl border border-slate-200 shadow-sm`}
        onError={() => {
          setImageError(true);
          setIsLoading(false);
        }}
        onLoad={() => setIsLoading(false)}
      />
      {confidence !== undefined && confidence < 0.8 && (
        <div className="absolute top-1 right-1 flex h-5 w-5 items-center justify-center rounded-full bg-amber-100">
          <AlertCircle className="h-3 w-3 text-amber-600" />
        </div>
      )}
    </div>
  );
}
