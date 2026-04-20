"use client";

import React, { useState } from "react";
import { Image as ImageIcon, Volume2, Download, ChevronLeft, ChevronRight, X } from "lucide-react";

interface EvidenceItem {
  url: string;
  type: "image" | "audio" | "video";
  filename?: string;
}

interface EvidenceGalleryProps {
  items: EvidenceItem[];
  className?: string;
}

export function EvidenceGallery({ items, className = "" }: EvidenceGalleryProps) {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  if (!items || items.length === 0) {
    return null;
  }

  const selectedItem = selectedIndex !== null ? items[selectedIndex] : null;

  const handlePrevious = () => {
    if (selectedIndex === null) return;
    setSelectedIndex(selectedIndex > 0 ? selectedIndex - 1 : items.length - 1);
  };

  const handleNext = () => {
    if (selectedIndex === null) return;
    setSelectedIndex(selectedIndex < items.length - 1 ? selectedIndex + 1 : 0);
  };

  const handleDownload = (url: string, filename?: string) => {
    const link = document.createElement("a");
    link.href = url;
    link.download = filename || "evidence";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className={className}>
      {/* Thumbnail Grid */}
      <div className="grid grid-cols-4 gap-2">
        {items.map((item, index) => (
          <button
            key={index}
            onClick={() => setSelectedIndex(index)}
            className="relative aspect-square overflow-hidden rounded-lg border border-slate-200 bg-slate-50 hover:border-slate-400 transition-colors"
          >
            {item.type === "image" ? (
              <img
                src={item.url}
                alt={item.filename || `Evidência ${index + 1}`}
                className="h-full w-full object-cover"
              />
            ) : item.type === "audio" ? (
              <div className="flex h-full w-full items-center justify-center">
                <Volume2 className="h-8 w-8 text-slate-400" />
              </div>
            ) : (
              <div className="flex h-full w-full items-center justify-center">
                <ImageIcon className="h-8 w-8 text-slate-400" />
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Lightbox Modal */}
      {selectedItem && selectedIndex !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
          <button
            onClick={() => setSelectedIndex(null)}
            className="absolute top-4 right-4 rounded-full bg-white/10 p-2 text-white hover:bg-white/20 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>

          <div className="relative max-w-4xl max-h-[90vh]">
            {selectedItem.type === "image" ? (
              <img
                src={selectedItem.url}
                alt={selectedItem.filename || "Evidência"}
                className="max-h-[90vh] w-auto rounded-lg"
              />
            ) : selectedItem.type === "audio" ? (
              <div className="flex min-h-[200px] items-center justify-center rounded-lg bg-white p-8">
                <audio controls className="w-full" src={selectedItem.url}>
                  Seu navegador não suporta áudio.
                </audio>
              </div>
            ) : (
              <div className="flex min-h-[400px] items-center justify-center rounded-lg bg-white p-8">
                <video controls className="w-full" src={selectedItem.url}>
                  Seu navegador não suporta vídeo.
                </video>
              </div>
            )}

            {/* Navigation Controls */}
            {items.length > 1 && (
              <>
                <button
                  onClick={handlePrevious}
                  className="absolute left-4 top-1/2 -translate-y-1/2 rounded-full bg-white/10 p-3 text-white hover:bg-white/20 transition-colors"
                >
                  <ChevronLeft className="h-6 w-6" />
                </button>
                <button
                  onClick={handleNext}
                  className="absolute right-4 top-1/2 -translate-y-1/2 rounded-full bg-white/10 p-3 text-white hover:bg-white/20 transition-colors"
                >
                  <ChevronRight className="h-6 w-6" />
                </button>
              </>
            )}

            {/* Download Button */}
            <button
              onClick={() => handleDownload(selectedItem.url, selectedItem.filename)}
              className="absolute bottom-4 right-4 rounded-full bg-white/10 p-3 text-white hover:bg-white/20 transition-colors"
            >
              <Download className="h-6 w-6" />
            </button>

            {/* Counter */}
            {items.length > 1 && (
              <div className="absolute bottom-4 left-4 rounded-full bg-white/10 px-4 py-2 text-sm text-white">
                {selectedIndex + 1} / {items.length}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
