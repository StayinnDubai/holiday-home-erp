import { CommonModule } from '@angular/common';
import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CrudApiService } from '../../core/api/crud-api.service';

interface TenancyContractRow {
  id: string;
  contract_number: string;
  status: string;
  start_date: string;
  end_date: string;
}

interface EjariRegistrationRow {
  id: string;
  ejari_contract_number: string | null;
  status: string;
  end_date: string | null;
}

/**
 * "All links to that unit" (landlord, tenancy contract, Ejari, DTCM permit,
 * move-in permit, rental agreement) shown at the bottom of the unit edit view.
 * Landlord comes straight off the unit record (already loaded, no extra call).
 * Tenancy Contracts and Ejari Registrations have real backends, filtered by
 * unit_id. DTCM Permits, Move-in Permits and Rental Agreements don't have a
 * backend yet (frontend-only stub pages) -- shown honestly as not-yet-built
 * rather than faked.
 */
@Component({
  selector: 'app-related-records-field',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="related-records">
      <div class="related-records__group">
        <h4>Landlord(s)</h4>
        <p *ngIf="landlordNames; else noneLandlord">{{ landlordNames }}</p>
        <ng-template #noneLandlord><p class="related-records__none">None linked.</p></ng-template>
      </div>

      <div class="related-records__group">
        <h4>Tenancy contracts <a routerLink="/contracts/tenancy" class="related-records__link">View all →</a></h4>
        <ul *ngIf="contracts.length; else noneContracts">
          <li *ngFor="let c of contracts">{{ c.contract_number }} — {{ c.status }} ({{ c.start_date }} to {{ c.end_date }})</li>
        </ul>
        <ng-template #noneContracts><p class="related-records__none">{{ loading ? 'Loading…' : 'None linked.' }}</p></ng-template>
      </div>

      <div class="related-records__group">
        <h4>Ejari registrations <a routerLink="/contracts/tenancy/ejari" class="related-records__link">View all →</a></h4>
        <ul *ngIf="ejariRegistrations.length; else noneEjari">
          <li *ngFor="let e of ejariRegistrations">{{ e.ejari_contract_number || '(no number)' }} — {{ e.status }}<span *ngIf="e.end_date"> — expires {{ e.end_date }}</span></li>
        </ul>
        <ng-template #noneEjari><p class="related-records__none">{{ loading ? 'Loading…' : 'None linked.' }}</p></ng-template>
      </div>

      <div class="related-records__group related-records__group--stub">
        <h4>DTCM permit</h4>
        <p class="related-records__none">Module not yet built.</p>
      </div>
      <div class="related-records__group related-records__group--stub">
        <h4>Move-in permit</h4>
        <p class="related-records__none">Module not yet built.</p>
      </div>
      <div class="related-records__group related-records__group--stub">
        <h4>Rental agreement</h4>
        <p class="related-records__none">Module not yet built.</p>
      </div>
    </div>
  `,
  styles: [
    `
      .related-records {
        display: flex;
        flex-direction: column;
        gap: 0.9rem;
      }
      .related-records__group h4 {
        margin: 0 0 0.3rem;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        color: #334155;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .related-records__group p,
      .related-records__group ul {
        margin: 0;
        font-size: 0.88rem;
        color: #0f172a;
      }
      .related-records__group ul {
        padding-left: 1.1rem;
      }
      .related-records__none {
        color: #94a3b8 !important;
        font-style: italic;
      }
      .related-records__group--stub h4 {
        color: #94a3b8;
      }
      .related-records__link {
        font-size: 0.7rem;
        font-weight: 500;
        text-transform: none;
        letter-spacing: normal;
        color: #0f766e;
        text-decoration: none;
      }
      .related-records__link:hover {
        text-decoration: underline;
      }
    `,
  ],
})
export class RelatedRecordsFieldComponent implements OnChanges {
  @Input({ required: true }) unitId!: string;
  @Input() landlordNames: string | null = null;

  contracts: TenancyContractRow[] = [];
  ejariRegistrations: EjariRegistrationRow[] = [];
  loading = false;

  constructor(private readonly api: CrudApiService) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['unitId'] && this.unitId) {
      this.refresh();
    }
  }

  private refresh(): void {
    this.loading = true;
    this.api.list<TenancyContractRow>('tenancy-contracts', { page: 1, page_size: 50 }, { unit_id: this.unitId }).subscribe({
      next: (res) => {
        this.contracts = res.data;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      },
    });
    this.api.list<EjariRegistrationRow>('ejari-registrations', { page: 1, page_size: 50 }, { unit_id: this.unitId }).subscribe({
      next: (res) => {
        this.ejariRegistrations = res.data;
      },
    });
  }
}
