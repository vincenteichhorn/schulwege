export async function fetchPlaces(): Promise<string[]> {
    const response = await fetch(`/api/places/`);
    if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
    }
    const data = await response.json();
    return data.places;
}

export async function fetchStatusNominatim(place: string): Promise<any> {
    const response = await fetch(`/api/status/${place}`);
    if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
    }
    const data = await response.json();
    return data;
}

export async function startNominatim(place: string): Promise<any> {
    const response = await fetch(`/api/start/${place}`);
    if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
    }
    const data = await response.json();
    return data;
}

export async function stopNominatim(place: string): Promise<any> {
    const response = await fetch(`/api/stop/${place}`);
    if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
    }
    const data = await response.json();
    return data;
}