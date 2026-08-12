import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, OnChanges, OnDestroy, Output, SimpleChanges } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AgGridAngular } from 'ag-grid-angular';
import { SELECTION_COLUMN_ID } from 'ag-grid-community';
import type {
  CellClickedEvent,
  CellValueChangedEvent,
  ColDef,
  ColumnResizedEvent,
  ColumnState,
  FilterModel,
  GridApi,
  GridReadyEvent,
  IDatasource,
  IGetRowsParams,
  RowSelectionOptions,
  SelectionColumnDef,
} from 'ag-grid-community';
import { Observable, firstValueFrom } from 'rxjs';
import { ListQuery, ListResponse } from '../../core/models/api.model';

interface SavedView {
  name: string;
  columnState: ColumnState[];
  filterModel: FilterModel;
}

interface PersistedGridState {
  columnState: ColumnState[];
  filterModel: FilterModel;
}

type Density = 'comfortable' | 'compact';

const DENSITY_STORAGE_KEY = 'grid:density';
const ROW_HEIGHTS: Record<Density, number> = { comfortable: 44, compact: 32 };
const HEADER_HEIGHTS: Record<Density, number> = { comfortable: 44, compact: 36 };

/**
 * Shared list-screen grid (plan §5/§6). Every module's list screen wraps this instead of
 * talking to ag-grid-angular directly.
 *
 * Note vs. the original plan wording: true "Server-Side Row Model" is an ag-Grid Enterprise
 * feature. This uses ag-Grid Community's **Infinite Row Model** instead, which is free and
 * gets the same result for our case -- the grid requests one page at a time from a
 * datasource callback, which we translate directly into the backend's page/page_size/
 * sort_by/sort_dir/q/filter_model contract (backend/app/core/pagination.py).
 *
 * Column show/hide, row selection checkboxes, and the "Views"/Columns dropdowns are all
 * hand-rolled (not ag-Grid's Columns Tool Panel / Set Filter, which are Enterprise features)
 * driven by plain Grid API calls -- client-side only, no server round-trip. Per-column
 * filtering (text/number/date) uses ag-Grid Community's free "provided simple filters"
 * (`agTextColumnFilter` etc, set per-column by each config's field type) -- only the Set
 * Filter and Tool Panels are Enterprise-gated, these aren't.
 *
 * `[theme]="'legacy'"` opts out of ag-Grid v33+'s new JS Theming API in favour of the
 * classic CSS theme files (imported in angular.json) -- simpler to reason about for v1
 * and avoids mixing two theming systems with PrimeNG's own theme provider.
 */
@Component({
  selector: 'app-ag-grid-table',
  standalone: true,
  imports: [CommonModule, FormsModule, AgGridAngular],
  template: `
    <div class="grid-toolbar">
      <div class="grid-toolbar__search">
        <i class="pi pi-search"></i>
        <input
          type="text"
          placeholder="Search..."
          [ngModel]="searchTerm"
          (ngModelChange)="onSearchInput($event)"
        />
      </div>

      <div class="grid-toolbar__selection" *ngIf="selectedRows.length > 0">
        <span class="grid-toolbar__selection-count">{{ selectedRows.length }} selected</span>
        <button type="button" class="toolbar-btn" (click)="exportCsv(true)"><i class="pi pi-download"></i> Export selected</button>
        <button type="button" class="toolbar-btn toolbar-btn--danger" (click)="onBulkDeleteClick()">
          <i class="pi pi-trash"></i> Delete selected
        </button>
        <button type="button" class="toolbar-btn toolbar-btn--text" (click)="clearSelection()">Clear</button>
      </div>

      <div class="grid-toolbar__actions" *ngIf="selectedRows.length === 0">
        <button
          type="button"
          class="toolbar-btn toolbar-btn--icon"
          (click)="toggleDensity()"
          [title]="density === 'compact' ? 'Switch to comfortable rows' : 'Switch to compact rows'"
        >
          <i class="pi" [class.pi-arrows-v]="density === 'comfortable'" [class.pi-minus]="density === 'compact'"></i>
        </button>

        <button type="button" class="toolbar-btn toolbar-btn--filter-pill" *ngIf="activeFilterCount > 0" (click)="clearFilters()">
          <i class="pi pi-filter"></i> {{ activeFilterCount }} filter{{ activeFilterCount === 1 ? '' : 's' }} active · Clear
        </button>

        <div class="dropdown" *ngIf="stateKey">
          <button type="button" class="toolbar-btn" (click)="viewsPanelOpen = !viewsPanelOpen; columnsPanelOpen = false">
            <i class="pi pi-bookmark"></i> Views
          </button>
          <div class="dropdown__panel dropdown__panel--wide" *ngIf="viewsPanelOpen">
            <div class="dropdown__empty" *ngIf="savedViews.length === 0">No saved views yet.</div>
            <div class="saved-view" *ngFor="let v of savedViews">
              <button type="button" class="saved-view__name" (click)="applyView(v)">{{ v.name }}</button>
              <button type="button" class="saved-view__delete" title="Delete view" (click)="deleteView(v)">
                <i class="pi pi-times"></i>
              </button>
            </div>
            <div class="save-view-form">
              <input
                type="text"
                placeholder="Save current view as..."
                [(ngModel)]="newViewName"
                (keydown.enter)="saveCurrentView()"
              />
              <button type="button" [disabled]="!newViewName.trim()" (click)="saveCurrentView()"><i class="pi pi-plus"></i></button>
            </div>
          </div>
        </div>

        <div class="dropdown">
          <button type="button" class="toolbar-btn" (click)="columnsPanelOpen = !columnsPanelOpen; viewsPanelOpen = false">
            <i class="pi pi-table"></i> Columns
          </button>
          <div class="dropdown__panel" *ngIf="columnsPanelOpen">
            <label class="dropdown__item" *ngFor="let col of toggleableColumns">
              <input type="checkbox" [checked]="isVisible(col)" (change)="toggleColumn(col, $event)" />
              {{ col.headerName }}
            </label>
          </div>
        </div>

        <button type="button" class="toolbar-btn" (click)="exportCsv(false)"><i class="pi pi-download"></i> Export CSV</button>
      </div>
    </div>
    <ag-grid-angular
      style="width: 100%; flex: 1; min-height: 0;"
      class="ag-theme-quartz"
      [theme]="'legacy'"
      [columnDefs]="columnDefs"
      [rowModelType]="'infinite'"
      [cacheBlockSize]="pageSize"
      [paginationPageSize]="pageSize"
      [paginationPageSizeSelector]="false"
      [pagination]="true"
      [datasource]="datasource"
      [defaultColDef]="defaultColDef"
      [context]="context"
      [rowSelection]="rowSelectionConfig"
      [selectionColumnDef]="selectionColumnDef"
      [rowHeight]="rowHeight"
      [headerHeight]="headerHeight"
      (gridReady)="onGridReady($event)"
      (cellClicked)="onCellClicked($event)"
      (cellValueChanged)="onCellValueChanged($event)"
      (selectionChanged)="onSelectionChanged()"
      (filterChanged)="onFilterChanged()"
      (sortChanged)="onGridStateChanged()"
      (columnVisible)="onGridStateChanged()"
      (columnMoved)="onGridStateChanged()"
      (columnResized)="onColumnResized($event)"
    ></ag-grid-angular>
  `,
  styles: [
    `
      :host {
        display: flex;
        flex-direction: column;
        height: 100%;
      }
      .grid-toolbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        margin-bottom: 0.5rem;
        flex-shrink: 0;
        flex-wrap: wrap;
      }
      .grid-toolbar__search {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 0.4rem 0.65rem;
        background: #fff;
        color: #64748b;
        min-width: 14rem;
        flex: 1;
        max-width: 22rem;
      }
      .grid-toolbar__search input {
        border: none;
        outline: none;
        font-size: 0.85rem;
        flex: 1;
        color: #0f172a;
      }
      .grid-toolbar__actions,
      .grid-toolbar__selection {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-wrap: wrap;
      }
      .grid-toolbar__selection {
        background: #f0fdfa;
        border: 1px solid #99f6e4;
        border-radius: 6px;
        padding: 0.3rem 0.6rem;
      }
      .grid-toolbar__selection-count {
        font-size: 0.85rem;
        font-weight: 600;
        color: #0f766e;
        margin-right: 0.25rem;
      }
      .toolbar-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        border: 1px solid #cbd5e1;
        background: #fff;
        color: #334155;
        border-radius: 6px;
        padding: 0.4rem 0.75rem;
        font-size: 0.85rem;
        font-weight: 600;
        cursor: pointer;
        white-space: nowrap;
      }
      .toolbar-btn:hover {
        background: #f8fafc;
      }
      .toolbar-btn--icon {
        padding: 0.4rem 0.55rem;
      }
      .toolbar-btn--text {
        border-color: transparent;
        background: transparent;
        color: #0f766e;
      }
      .toolbar-btn--danger {
        border-color: #fecaca;
        color: #b91c1c;
      }
      .toolbar-btn--danger:hover {
        background: #fef2f2;
      }
      .toolbar-btn--filter-pill {
        border-color: #99f6e4;
        background: #f0fdfa;
        color: #0f766e;
      }
      .dropdown {
        position: relative;
      }
      .dropdown__panel {
        position: absolute;
        top: calc(100% + 0.25rem);
        right: 0;
        z-index: 20;
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
        padding: 0.5rem;
        min-width: 14rem;
        max-height: 20rem;
        overflow-y: auto;
      }
      .dropdown__panel--wide {
        min-width: 17rem;
      }
      .dropdown__empty {
        padding: 0.5rem;
        font-size: 0.82rem;
        color: #94a3b8;
      }
      .dropdown__item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.35rem 0.5rem;
        font-size: 0.85rem;
        color: #334155;
        border-radius: 4px;
        cursor: pointer;
        white-space: nowrap;
      }
      .dropdown__item:hover {
        background: #f1f5f9;
      }
      .saved-view {
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-radius: 4px;
      }
      .saved-view:hover {
        background: #f1f5f9;
      }
      .saved-view__name {
        flex: 1;
        text-align: left;
        border: none;
        background: transparent;
        padding: 0.4rem 0.5rem;
        font-size: 0.85rem;
        color: #334155;
        cursor: pointer;
      }
      .saved-view__delete {
        border: none;
        background: transparent;
        color: #94a3b8;
        cursor: pointer;
        padding: 0.4rem 0.5rem;
      }
      .saved-view__delete:hover {
        color: #b91c1c;
      }
      .save-view-form {
        display: flex;
        gap: 0.35rem;
        border-top: 1px solid #e2e8f0;
        margin-top: 0.35rem;
        padding-top: 0.4rem;
      }
      .save-view-form input {
        flex: 1;
        min-width: 0;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        padding: 0.3rem 0.45rem;
        font-size: 0.82rem;
      }
      .save-view-form button {
        border: 1px solid #cbd5e1;
        background: #fff;
        border-radius: 4px;
        padding: 0.3rem 0.55rem;
        cursor: pointer;
        color: #334155;
      }
      .save-view-form button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
    `,
  ],
})
export class AgGridTableComponent<T> implements OnChanges, OnDestroy {
  /** Column definitions, same as any ag-Grid ColDef[]. */
  @Input({ required: true }) columnDefs: ColDef[] = [];

  /** Called by the grid for every page it needs; wraps the resource's CrudApiService.list(). */
  @Input({ required: true }) fetchPage!: (query: ListQuery) => Observable<ListResponse<T>>;

  @Input() pageSize = 25;

  /** Passed straight through to ag-Grid's gridOptions.context -- e.g. row-action callbacks
   *  a custom cell renderer (like RowActionsCellRendererComponent) reads back out. */
  @Input() context: unknown;

  /** Unique key for this grid (e.g. the resource path) -- enables persisting column/filter
   * state and named views to localStorage, scoped per grid. Omit to opt out (state resets
   * every visit, and the Views dropdown doesn't appear). */
  @Input() stateKey?: string;

  /** Fired when the user clicks a row outside the Actions cell and outside any inline-editable
   * cell -- the "click a row to see it read-only" convention. */
  @Output() rowView = new EventEmitter<T>();

  /** Fired when the user confirms "Delete selected" for the current checkbox selection. */
  @Output() bulkDelete = new EventEmitter<T[]>();

  /** Fired when an inline-editable cell (currently: boolean checkboxes) changes value. */
  @Output() cellEdited = new EventEmitter<{ data: T; field: string; newValue: unknown }>();

  readonly defaultColDef: ColDef = { sortable: true, resizable: true, filter: false, floatingFilter: true };

  /** Row selection via ag-Grid's own auto-generated checkbox column (selectionColumnDef
   * below just pins + sizes it) -- `enableClickSelection: false` so a plain row click is
   * free to open the read-only View instead (see onCellClicked). No header "select all" --
   * ag-Grid doesn't support one for the Infinite Row Model (there's no fixed "all" to
   * select when the total isn't fully loaded), so rows are selected one at a time. */
  readonly rowSelectionConfig: RowSelectionOptions<T> = {
    mode: 'multiRow',
    checkboxes: true,
    headerCheckbox: false,
    enableClickSelection: false,
  };
  readonly selectionColumnDef: SelectionColumnDef = { pinned: 'left', width: 42, maxWidth: 42, resizable: false };

  datasource!: IDatasource;
  columnsPanelOpen = false;
  viewsPanelOpen = false;
  searchTerm = '';
  activeFilterCount = 0;
  selectedRows: T[] = [];
  savedViews: SavedView[] = [];
  newViewName = '';
  density: Density = (localStorage.getItem(DENSITY_STORAGE_KEY) as Density) || 'comfortable';

  private gridApi?: GridApi<T>;
  private hiddenColIds = new Set<string>();
  private searchDebounce?: ReturnType<typeof setTimeout>;
  private stateSaveDebounce?: ReturnType<typeof setTimeout>;

  get rowHeight(): number {
    return ROW_HEIGHTS[this.density];
  }

  get headerHeight(): number {
    return HEADER_HEIGHTS[this.density];
  }

  /** Columns offered in the show/hide panel -- only "real" data columns (skips the
   * Actions column, which has no `field`, since hiding it would strand the row buttons). */
  get toggleableColumns(): ColDef[] {
    return this.columnDefs.filter((c) => c.field);
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['fetchPage'] || changes['pageSize']) {
      this.datasource = this.buildDatasource();
    }
    if (changes['stateKey']) {
      this.loadSavedViews();
      if (this.gridApi) {
        this.restoreState();
      }
    }
  }

  ngOnDestroy(): void {
    clearTimeout(this.searchDebounce);
    clearTimeout(this.stateSaveDebounce);
  }

  onGridReady(event: GridReadyEvent<T>): void {
    this.gridApi = event.api;
    if (!this.datasource) {
      this.datasource = this.buildDatasource();
    }
    this.loadSavedViews();
    this.restoreState();
  }

  /** Call after a create/update/delete elsewhere so the grid reloads from the server. */
  refresh(): void {
    this.gridApi?.purgeInfiniteCache();
  }

  clearSelection(): void {
    this.gridApi?.deselectAll();
  }

  // ---------------------------------------------------------------------
  // Column show/hide
  // ---------------------------------------------------------------------
  isVisible(col: ColDef): boolean {
    return !this.hiddenColIds.has(col.field as string);
  }

  toggleColumn(col: ColDef, event: Event): void {
    const checked = (event.target as HTMLInputElement).checked;
    const colId = col.field as string;
    if (checked) {
      this.hiddenColIds.delete(colId);
    } else {
      this.hiddenColIds.add(colId);
    }
    this.gridApi?.setColumnsVisible([colId], checked);
    this.saveStateDebounced();
  }

  private syncHiddenFromGridState(): void {
    const state = this.gridApi?.getColumnState() ?? [];
    this.hiddenColIds = new Set(state.filter((s) => s.hide).map((s) => s.colId));
  }

  // ---------------------------------------------------------------------
  // Global quick search (separate from per-column filters -- hits the same `q` param
  // most list endpoints already support).
  // ---------------------------------------------------------------------
  onSearchInput(value: string): void {
    this.searchTerm = value;
    clearTimeout(this.searchDebounce);
    this.searchDebounce = setTimeout(() => this.gridApi?.purgeInfiniteCache(), 400);
  }

  // ---------------------------------------------------------------------
  // Row click -> read-only View
  // ---------------------------------------------------------------------
  onCellClicked(event: CellClickedEvent<T>): void {
    if (!event.data) return;
    if (event.column.getColId() === SELECTION_COLUMN_ID) return;
    if (event.colDef.headerName === 'Actions') return;
    if (event.colDef.editable) return;
    this.rowView.emit(event.data);
  }

  // ---------------------------------------------------------------------
  // Inline editing (currently: boolean checkboxes -- see entity-page.component.ts)
  // ---------------------------------------------------------------------
  onCellValueChanged(event: CellValueChangedEvent<T>): void {
    const field = event.colDef.field;
    if (!field || event.newValue === event.oldValue || !event.data) return;
    this.cellEdited.emit({ data: event.data, field, newValue: event.newValue });
  }

  // ---------------------------------------------------------------------
  // Selection / bulk actions
  // ---------------------------------------------------------------------
  onSelectionChanged(): void {
    this.selectedRows = this.gridApi?.getSelectedRows() ?? [];
  }

  onBulkDeleteClick(): void {
    if (this.selectedRows.length === 0) return;
    this.bulkDelete.emit(this.selectedRows);
  }

  // ---------------------------------------------------------------------
  // Active filters
  // ---------------------------------------------------------------------
  onFilterChanged(): void {
    this.updateActiveFilterCount();
    this.saveStateDebounced();
  }

  clearFilters(): void {
    this.gridApi?.setFilterModel(null);
  }

  private updateActiveFilterCount(): void {
    const model = this.gridApi?.getFilterModel() ?? {};
    this.activeFilterCount = Object.keys(model).length;
  }

  // ---------------------------------------------------------------------
  // Row density -- a global preference (not per-grid), since it's a visual taste setting
  // rather than something tied to one resource's data shape.
  // ---------------------------------------------------------------------
  toggleDensity(): void {
    this.density = this.density === 'comfortable' ? 'compact' : 'comfortable';
    localStorage.setItem(DENSITY_STORAGE_KEY, this.density);
    // `resetRowHeights()` only works for the client-side row model -- this grid uses the
    // Infinite Row Model (see class doc), whose already-rendered rows only pick up a new
    // `rowHeight` by being re-rendered, so re-request the current page instead.
    this.gridApi?.purgeInfiniteCache();
  }

  // ---------------------------------------------------------------------
  // Persisted grid state (column order/width/visibility/sort + filters), keyed by stateKey
  // ---------------------------------------------------------------------
  onGridStateChanged(): void {
    this.syncHiddenFromGridState();
    this.saveStateDebounced();
  }

  onColumnResized(event: ColumnResizedEvent<T>): void {
    if (event.finished) {
      this.saveStateDebounced();
    }
  }

  private saveStateDebounced(): void {
    clearTimeout(this.stateSaveDebounce);
    this.stateSaveDebounce = setTimeout(() => this.saveState(), 400);
  }

  private saveState(): void {
    if (!this.stateKey || !this.gridApi) return;
    const state: PersistedGridState = {
      columnState: this.gridApi.getColumnState(),
      filterModel: this.gridApi.getFilterModel(),
    };
    localStorage.setItem(this.storageKey('state'), JSON.stringify(state));
  }

  private restoreState(): void {
    if (!this.stateKey || !this.gridApi) return;
    const raw = localStorage.getItem(this.storageKey('state'));
    if (!raw) return;
    try {
      const state = JSON.parse(raw) as PersistedGridState;
      if (state.columnState) {
        this.gridApi.applyColumnState({ state: state.columnState, applyOrder: true });
      }
      if (state.filterModel) {
        this.gridApi.setFilterModel(state.filterModel);
      }
      this.syncHiddenFromGridState();
      this.updateActiveFilterCount();
    } catch {
      // Corrupt or old-shape localStorage entry -- ignore, grid just starts from defaults.
    }
  }

  private storageKey(suffix: string): string {
    return `grid:${this.stateKey}:${suffix}`;
  }

  // ---------------------------------------------------------------------
  // Saved named views (column state + filters bundled under a name), also keyed by stateKey
  // ---------------------------------------------------------------------
  private loadSavedViews(): void {
    if (!this.stateKey) {
      this.savedViews = [];
      return;
    }
    const raw = localStorage.getItem(this.storageKey('views'));
    try {
      this.savedViews = raw ? (JSON.parse(raw) as SavedView[]) : [];
    } catch {
      this.savedViews = [];
    }
  }

  private persistSavedViews(): void {
    if (!this.stateKey) return;
    localStorage.setItem(this.storageKey('views'), JSON.stringify(this.savedViews));
  }

  applyView(view: SavedView): void {
    if (!this.gridApi) return;
    this.gridApi.applyColumnState({ state: view.columnState, applyOrder: true });
    this.gridApi.setFilterModel(view.filterModel);
    this.syncHiddenFromGridState();
    this.updateActiveFilterCount();
    this.viewsPanelOpen = false;
  }

  saveCurrentView(): void {
    const name = this.newViewName.trim();
    if (!name || !this.gridApi) return;
    const view: SavedView = {
      name,
      columnState: this.gridApi.getColumnState(),
      filterModel: this.gridApi.getFilterModel(),
    };
    this.savedViews = [...this.savedViews.filter((v) => v.name !== name), view];
    this.persistSavedViews();
    this.newViewName = '';
  }

  deleteView(view: SavedView): void {
    this.savedViews = this.savedViews.filter((v) => v !== view);
    this.persistSavedViews();
  }

  // ---------------------------------------------------------------------
  // CSV export
  // ---------------------------------------------------------------------
  async exportCsv(onlySelected: boolean): Promise<void> {
    const rows = onlySelected ? this.selectedRows : await this.fetchAllRows();
    if (rows.length === 0) return;
    const cols = this.columnDefs.filter((c) => c.field && this.isVisible(c));
    const header = cols.map((c) => this.csvEscape(c.headerName ?? c.field ?? ''));
    const lines = rows.map((r) => cols.map((c) => this.csvEscape((r as Record<string, unknown>)[c.field as string])));
    const csv = [header, ...lines].map((line) => line.join(',')).join('\r\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${this.stateKey ?? 'export'}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  /** Re-fetches every page under the current search/filter/sort (capped, see maxPages) --
   * ag-Grid's own CSV export only covers rows already loaded into the Infinite Row Model's
   * cache, which is wrong for "export everything matching my filter". */
  private async fetchAllRows(): Promise<T[]> {
    const filterModel = this.gridApi?.getFilterModel() ?? {};
    const hasFilters = Object.keys(filterModel).length > 0;
    const sortState = this.gridApi?.getColumnState().find((s) => s.sort);
    const pageSize = 200; // backend's pagination_params caps page_size at 200 (le=200)
    const maxPages = 100; // safety cap: 20,000 rows
    const all: T[] = [];
    for (let page = 1; page <= maxPages; page++) {
      const res = await firstValueFrom(
        this.fetchPage({
          page,
          page_size: pageSize,
          sort_by: sortState?.colId,
          sort_dir: sortState?.sort as 'asc' | 'desc' | undefined,
          q: this.searchTerm || undefined,
          filter_model: hasFilters ? JSON.stringify(filterModel) : undefined,
        })
      );
      all.push(...res.data);
      if (res.data.length < pageSize) break;
    }
    return all;
  }

  private csvEscape(value: unknown): string {
    if (value === null || value === undefined) return '';
    const s = String(value);
    return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  }

  private buildDatasource(): IDatasource {
    return {
      getRows: (params: IGetRowsParams) => {
        const page = Math.floor(params.startRow / this.pageSize) + 1;
        const sortModel = params.sortModel?.[0];
        const hasFilters = params.filterModel && Object.keys(params.filterModel).length > 0;

        this.fetchPage({
          page,
          page_size: this.pageSize,
          sort_by: sortModel?.colId,
          sort_dir: sortModel?.sort as 'asc' | 'desc' | undefined,
          q: this.searchTerm || undefined,
          filter_model: hasFilters ? JSON.stringify(params.filterModel) : undefined,
        }).subscribe({
          next: (res) => params.successCallback(res.data, res.meta.total),
          error: () => params.failCallback(),
        });
      },
    };
  }
}
