import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { AgGridAngular } from 'ag-grid-angular';
import type { ColDef, GridApi, GridReadyEvent, IDatasource, IGetRowsParams } from 'ag-grid-community';
import { Observable } from 'rxjs';
import { ListQuery, ListResponse } from '../../core/models/api.model';

/**
 * Shared list-screen grid (plan §5/§6). Every module's list screen wraps this instead of
 * talking to ag-grid-angular directly.
 *
 * Note vs. the original plan wording: true "Server-Side Row Model" is an ag-Grid Enterprise
 * feature. This uses ag-Grid Community's **Infinite Row Model** instead, which is free and
 * gets the same result for our case -- the grid requests one page at a time from a
 * datasource callback, which we translate directly into the backend's page/page_size/
 * sort_by/sort_dir/q contract (backend/app/core/pagination.py).
 *
 * `[theme]="'legacy'"` opts out of ag-Grid v33+'s new JS Theming API in favour of the
 * classic CSS theme files (imported in angular.json) -- simpler to reason about for v1
 * and avoids mixing two theming systems with PrimeNG's own theme provider.
 */
@Component({
  selector: 'app-ag-grid-table',
  standalone: true,
  imports: [AgGridAngular],
  template: `
    <ag-grid-angular
      style="width: 100%; height: 100%;"
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
      (gridReady)="onGridReady($event)"
    ></ag-grid-angular>
  `,
})
export class AgGridTableComponent<T> implements OnChanges {
  /** Column definitions, same as any ag-Grid ColDef[]. */
  @Input({ required: true }) columnDefs: ColDef[] = [];

  /** Called by the grid for every page it needs; wraps the resource's CrudApiService.list(). */
  @Input({ required: true }) fetchPage!: (query: ListQuery) => Observable<ListResponse<T>>;

  @Input() pageSize = 25;

  /** Passed straight through to ag-Grid's gridOptions.context -- e.g. row-action callbacks
   *  a custom cell renderer (like RowActionsCellRendererComponent) reads back out. */
  @Input() context: unknown;

  readonly defaultColDef: ColDef = { sortable: true, resizable: true, filter: false };

  datasource!: IDatasource;
  private gridApi?: GridApi;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['fetchPage'] || changes['pageSize']) {
      this.datasource = this.buildDatasource();
    }
  }

  onGridReady(event: GridReadyEvent): void {
    this.gridApi = event.api;
    if (!this.datasource) {
      this.datasource = this.buildDatasource();
    }
  }

  /** Call after a create/update/delete elsewhere so the grid reloads from the server. */
  refresh(): void {
    this.gridApi?.purgeInfiniteCache();
  }

  private buildDatasource(): IDatasource {
    return {
      getRows: (params: IGetRowsParams) => {
        const page = Math.floor(params.startRow / this.pageSize) + 1;
        const sortModel = params.sortModel?.[0];

        this.fetchPage({
          page,
          page_size: this.pageSize,
          sort_by: sortModel?.colId,
          sort_dir: sortModel?.sort as 'asc' | 'desc' | undefined,
        }).subscribe({
          next: (res) => params.successCallback(res.data, res.meta.total),
          error: () => params.failCallback(),
        });
      },
    };
  }
}
