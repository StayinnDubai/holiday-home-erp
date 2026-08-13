import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { TabViewModule } from 'primeng/tabview';
import { EntityPageConfig } from './entity-page-config.model';
import { EntityPageComponent } from './entity-page.component';
import { PlaceholderComponent } from '../placeholder/placeholder.component';

/** One tab: either a real EntityPageConfig (renders the usual grid+form page) or, for
 * a module that isn't built yet, a placeholder note -- same either/or as app.routes.ts
 * used before this page had tabs, just per-tab instead of per-route. */
export interface PageTab {
  label: string;
  config?: EntityPageConfig;
  placeholderNote?: string;
}

/**
 * Groups several related EntityPageConfig pages that used to be separate sidebar items
 * and routes (e.g. Buildings / Building Contacts / Building Amenities / Building
 * Deposits) into one sidebar item and one page with a tab per config. Each config is
 * unchanged and still points at its own resourcePath -- this is a pure navigation/UI
 * consolidation, not a data-model change (these were always independent lists, e.g. a
 * building_contact just has a `building_id` field, it isn't nested under a specific
 * building's URL).
 */
@Component({
  selector: 'app-tabbed-page',
  standalone: true,
  imports: [CommonModule, TabViewModule, EntityPageComponent, PlaceholderComponent],
  template: `
    <p-tabView>
      <p-tabPanel *ngFor="let tab of tabs" [header]="tab.label">
        <app-entity-page *ngIf="tab.config" [config]="tab.config" [embedded]="true" />
        <app-placeholder
          *ngIf="!tab.config"
          [title]="tab.label"
          [note]="tab.placeholderNote || 'Not built yet.'"
        />
      </p-tabPanel>
    </p-tabView>
  `,
})
export class TabbedPageComponent {
  @Input({ required: true }) tabs: PageTab[] = [];
}
