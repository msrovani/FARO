// F.A.R.O. Map Configuration
export const MAP_CONFIG = {
  // MapTiler API Key (se precisar no futuro)
  maptilerApiKey: process.env.NEXT_PUBLIC_MAPTILER_API_KEY || '',
  
  // OpenStreetMap (padrão - gratuito e funciona sem API key)
  osmTileUrl: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  
  // Alternativas gratuitas caso OSM falhe
  alternativeTileUrls: [
    'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
    'https://{s}.tile.openstreetmap.de/tiles/osmde/{z}/{x}/{y}.png',
    'https://tile.openstreetmap.bzh/br/{z}/{x}/{y}.png'
  ],
  
  // Configurações padrão do mapa
  defaultViewState: {
    latitude: -30.0346,  // Porto Alegre
    longitude: -51.2177,
    zoom: 12
  },
  
  // Limites do Rio Grande do Sul
  bounds: {
    north: -27.0,
    south: -34.0,
    east: -49.0,
    west: -58.0
  }
};
