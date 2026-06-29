import { describe, expect, it } from 'vitest';

import { getCoordinates, normalizePlace, placesSummary } from './place.utils';

describe('place.utils', () => {
  it('placesSummary handles truncated results', () => {
    expect(placesSummary([{}, {}] as never, 10)).toContain('Showing 2');
  });

  it('getCoordinates validates numbers', () => {
    const place = {
      placeNameId: 1,
      placeName: 'Test',
      geometry: { type: 'Point', coordinates: [172.6, -43.5] as [number, number] },
    };
    expect(getCoordinates(place)).toEqual([172.6, -43.5]);
  });

  it('normalizePlace rejects invalid coordinates', () => {
    expect(
      normalizePlace({
        placeNameId: 1,
        placeName: 'Bad',
        geometry: { type: 'Point', coordinates: [200, 0] },
      }),
    ).toBeNull();
  });
});
