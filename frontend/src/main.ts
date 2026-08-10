import { bootstrapApplication } from '@angular/platform-browser';
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app.component';

// ag-Grid v33+ is modular -- every feature (infinite row model, sorting, etc.) must be
// registered once at startup or the grid renders blank with a console error (#272).
// AllCommunityModule keeps this simple for v1; can be narrowed to only what's used later.
ModuleRegistry.registerModules([AllCommunityModule]);

bootstrapApplication(AppComponent, appConfig)
  .catch((err) => console.error(err));
