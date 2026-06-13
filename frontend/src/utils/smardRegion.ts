// Bounding box covering Germany + Austria
const DE_AT_BOUNDS = { latMin: 46.2, latMax: 55.2, lonMin: 5.8, lonMax: 17.3 };

export function isInSMARDRegion(lat: number, lon: number): boolean {
  return (
    lat >= DE_AT_BOUNDS.latMin &&
    lat <= DE_AT_BOUNDS.latMax &&
    lon >= DE_AT_BOUNDS.lonMin &&
    lon <= DE_AT_BOUNDS.lonMax
  );
}
