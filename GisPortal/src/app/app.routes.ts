import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./portal/portal').then((m) => m.PortalComponent),
  },
];
