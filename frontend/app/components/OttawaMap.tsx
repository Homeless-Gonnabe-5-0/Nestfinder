"use client";

import { useEffect, useState, useRef } from "react";
import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Coordinates
const OTTAWA_CENTER: [number, number] = [45.4215, -75.6972];
const UOTTAWA: [number, number] = [45.4231, -75.6831]; // uOttawa campus
const OTTAWA_BOUNDS: L.LatLngBoundsExpression = [
  [45.25, -76.0], // Southwest
  [45.55, -75.4], // Northeast
];

// Apple emoji pin 📍
const emojiPinIcon = new L.DivIcon({
  className: "emoji-pin-marker",
  html: `<span style="font-size: 36px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));">📍</span>`,
  iconSize: [36, 36],
  iconAnchor: [18, 36],
  popupAnchor: [0, -36],
});

interface LocationMarkerProps {
  position: [number, number] | null;
  setPosition: (pos: [number, number]) => void;
}

function LocationMarker({ position, setPosition }: LocationMarkerProps) {
  useMapEvents({
    click(e) {
      setPosition([e.latlng.lat, e.latlng.lng]);
    },
  });

  return position ? <Marker position={position} icon={emojiPinIcon} /> : null;
}

// Initial zoom animation - starts at uOttawa, zooms out 100%
function InitialZoomAnimation() {
  const map = useMap();

  useEffect(() => {
    // Wait for map to be ready, then animate
    const handleLoad = () => {
      setTimeout(() => {
        map.flyTo(OTTAWA_CENTER, 11, { 
          duration: 1.8,
          easeLinearity: 0.4
        });
      }, 400);
    };

    // Check if map is already loaded
    if (map.getContainer()) {
      handleLoad();
    } else {
      map.whenReady(handleLoad);
    }
  }, []); // Empty deps - only run once on mount

  return null;
}

// Component to fly to a position (when user selects a location)
function FlyToPosition({ position }: { position: [number, number] | null }) {
  const map = useMap();
  const lastPosition = useRef<string | null>(null);
  
  useEffect(() => {
    if (position) {
      const posKey = `${position[0]},${position[1]}`;
      if (lastPosition.current !== posKey) {
        lastPosition.current = posKey;
        map.flyTo(position, 16, { duration: 1 });
      }
    }
  }, [map, position]);

  return null;
}

// Sleek zoom controls - Google Maps style
function CustomZoomControls() {
  const map = useMap();

  return (
    <div className="absolute top-4 right-4 z-[1000] flex flex-col">
      <button
        onClick={() => map.zoomIn()}
        className="w-[40px] h-[40px] bg-white hover:bg-gray-50 active:bg-gray-100 flex items-center justify-center transition-all duration-150 rounded-t-lg shadow-md border border-gray-200/80"
        aria-label="Zoom in"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
          <path d="M12 6v12M6 12h12" stroke="#5f6368" strokeWidth="2" strokeLinecap="round"/>
        </svg>
      </button>
      <button
        onClick={() => map.zoomOut()}
        className="w-[40px] h-[40px] bg-white hover:bg-gray-50 active:bg-gray-100 flex items-center justify-center transition-all duration-150 rounded-b-lg shadow-md border border-t-0 border-gray-200/80"
        aria-label="Zoom out"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
          <path d="M6 12h12" stroke="#5f6368" strokeWidth="2" strokeLinecap="round"/>
        </svg>
      </button>
    </div>
  );
}

interface OttawaMapProps {
  onLocationSelect?: (lat: number, lng: number) => void;
  selectedLocation?: [number, number] | null;
}

export default function OttawaMap({ onLocationSelect, selectedLocation }: OttawaMapProps) {
  const [position, setPosition] = useState<[number, number] | null>(selectedLocation || null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Sync with external selectedLocation changes
  useEffect(() => {
    if (selectedLocation) {
      setPosition(selectedLocation);
    }
  }, [selectedLocation]);

  const handlePositionChange = (newPos: [number, number]) => {
    setPosition(newPos);
    onLocationSelect?.(newPos[0], newPos[1]);
  };

  // Don't render on server
  if (!mounted) {
    return (
      <div className="w-full h-full bg-[var(--bg-secondary)] rounded-2xl flex items-center justify-center">
        <div className="text-[var(--text-muted)] flex items-center gap-2">
          <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
          Loading map...
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full relative rounded-2xl overflow-hidden border border-[var(--border-color)]">
      <MapContainer
        center={UOTTAWA}
        zoom={16}
        maxBounds={OTTAWA_BOUNDS}
        maxBoundsViscosity={1.0}
        minZoom={11}
        maxZoom={18}
        zoomControl={false}
        style={{ height: "100%", width: "100%" }}
        className="z-0"
      >
        {/* OpenStreetMap tiles with POIs visible */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <LocationMarker position={position} setPosition={handlePositionChange} />
        <FlyToPosition position={position} />
        <InitialZoomAnimation />
        <CustomZoomControls />
      </MapContainer>

      {/* Instruction hint - bottom left, compact */}
      <div className="absolute bottom-4 left-4 z-[1000] pointer-events-none">
        <div className="bg-white/95 backdrop-blur-sm rounded-lg px-3 py-2 shadow-md border border-gray-200/60">
          <p className="text-xs text-gray-500 font-medium">
            {position ? "📍 Location set" : "Click to drop a pin"}
          </p>
        </div>
      </div>

      {/* Clear button */}
      {position && (
        <button
          onClick={() => {
            setPosition(null);
            onLocationSelect?.(0, 0);
          }}
          className="absolute bottom-4 right-4 z-[1000] bg-white/95 backdrop-blur-sm rounded-lg px-4 py-2 text-sm font-medium text-gray-700 hover:bg-white hover:text-gray-900 transition-all duration-150 border border-gray-200/60 shadow-md"
        >
          Clear
        </button>
      )}
    </div>
  );
}
